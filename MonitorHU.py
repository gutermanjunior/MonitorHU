import time
import os
import csv
import sys
import random
import argparse
import requests
import smtplib
import platform
import logging
import threading
from email.message import EmailMessage
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# --- CONFIGURAÇÃO GLOBAL ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("MonitorHU")
logging.getLogger("urllib3").setLevel(logging.ERROR)

# ==============================================================================
# SERVIÇO 1: NAVEGAÇÃO (BROWSER SERVICE)
# Responsabilidade: Apenas interagir com o Chrome e o Site do HU
# ==============================================================================
class BrowserService:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.wait = None
        self.url = "https://sistemashu.hu.usp.br/reshu/paciente"
        self.user = os.getenv("HU_USER")
        self.data_nasc = os.getenv("HU_DATA")

    def iniciar(self):
        options = webdriver.ChromeOptions()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.wait = WebDriverWait(self.driver, 20)

    def fechar(self):
        if self.driver:
            try: self.driver.quit()
            except: pass

    def _preencher_data_js(self, elemento_id, valor):
        self.driver.find_element(By.ID, elemento_id).clear()
        self.driver.execute_script(f"document.getElementById('{elemento_id}').value = '{valor}';")

    def login(self):
        print("\n--> Acessando login...")
        self.driver.get(self.url)
        try:
            self.wait.until(EC.presence_of_element_located((By.ID, "PacienteMatricula"))).send_keys(self.user)
            self._preencher_data_js("PacienteDataNascimento", self.data_nasc)
            return "CAPTCHA_NEEDED"
        except TimeoutException:
            return "TIMEOUT"

    def verificar_sucesso_login(self):
        try:
            # Espera até 180s pelo dropdown
            WebDriverWait(self.driver, 180).until(EC.presence_of_element_located((By.ID, "Especialidade")))
            return True
        except:
            return False

    def obter_vagas(self):
        try:
            self.driver.refresh()
            # Espera dinâmica
            elem = self.wait.until(EC.presence_of_element_located((By.ID, "Especialidade")))
            select = Select(elem)
            opcoes = {opt.text.strip() for opt in select.options}
            limpeza = {"Selecione a Especialidade...", "", "Selecione..."}
            return {op for op in opcoes if op not in limpeza}
        except TimeoutException:
            return None # Erro de rede/site
        except Exception as e:
            raise e # Erro crítico (sessão caiu)

    def tirar_screenshot(self, nome_arquivo="print.png"):
        if self.driver:
            self.driver.save_screenshot(nome_arquivo)
            return nome_arquivo
        return None

# ==============================================================================
# SERVIÇO 2: COMUNICAÇÃO (TELEGRAM SERVICE)
# Responsabilidade: Enviar mensagens e ouvir comandos
# ==============================================================================
class TelegramService:
    def __init__(self, controller):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.controller = controller # Referência ao cérebro para executar ações
        self.offset = 0

    def enviar(self, texto, imagem=None):
        try:
            url_msg = f"https://api.telegram.org/bot{self.token}/sendMessage"
            url_foto = f"https://api.telegram.org/bot{self.token}/sendPhoto"
            if imagem:
                with open(imagem, 'rb') as f:
                    requests.post(url_foto, data={'chat_id': self.chat_id, 'caption': texto}, files={'photo': f})
            else:
                requests.post(url_msg, data={'chat_id': self.chat_id, 'text': texto})
        except: pass

    def verificar_novos_comandos(self):
        """Polling manual de updates"""
        try:
            url = f"https://api.telegram.org/bot{self.token}/getUpdates?offset={self.offset}&timeout=1"
            resp = requests.get(url, timeout=3).json()
            
            if not resp.get("ok"): return

            for update in resp.get("result", []):
                self.offset = update["update_id"] + 1
                msg = update.get("message", {})
                
                # Segurança: Só aceita comandos do dono
                if str(msg.get("chat", {}).get("id")) != str(self.chat_id): continue
                
                texto = msg.get("text", "").strip()
                if texto.startswith("/"):
                    self._rotear_comando(texto)
        except: pass

    def _rotear_comando(self, texto):
        """O Roteador de Comandos (Dispatcher)"""
        partes = texto.split()
        cmd = partes[0].lower()
        args = partes[1:] if len(partes) > 1 else []
        
        # Mapa de Comandos -> Funções do Controller
        mapa = {
            '/ping': lambda: self.enviar("🏓 Pong!"),
            '/status': self.controller.comando_status,
            '/print': self.controller.comando_print,
            '/pause': self.controller.comando_pause,
            '/resume': self.controller.comando_resume,
            '/alvos': self.controller.comando_listar_alvos,
            '/help': self.controller.comando_help
        }

        if cmd in mapa:
            mapa[cmd]() # Executa a função
        elif cmd == '/add':
            self.controller.comando_add_alvo(args)
        elif cmd == '/remove':
            self.controller.comando_remove_alvo(args)

# ==============================================================================
# SERVIÇO 3: UTILITÁRIOS (DATA & AUDIO)
# ==============================================================================
class DataService:
    def __init__(self, arquivo="historico_especialidades.csv"):
        self.arquivo = arquivo

    def registrar(self, evento, especialidade):
        existe = os.path.isfile(self.arquivo)
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.arquivo, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not existe: writer.writerow(["Data_Hora", "Evento", "Especialidade"])
                writer.writerow([agora, evento, especialidade])
        except Exception as e:
            print(f"Erro CSV: {e}")

class AudioService:
    @staticmethod
    def tocar_alarme(mensagem):
        sistema = platform.system()
        try:
            if sistema == "Darwin": 
                os.system(f'say -v Luciana "{mensagem}"')
                os.system('afplay /System/Library/Sounds/Glass.aiff')
            elif sistema == "Windows": 
                import winsound
                winsound.Beep(1000, 800)
            else:
                print("\a")
        except: pass

class EmailService:
    def __init__(self):
        self.conta = os.getenv("EMAIL_CONTA")
        self.senha = os.getenv("EMAIL_SENHA")
        self.destino = os.getenv("EMAIL_DESTINO")

    def enviar(self, assunto, corpo):
        if not self.conta: return
        msg = EmailMessage()
        msg.set_content(corpo)
        msg['Subject'] = assunto
        msg['From'] = self.conta
        msg['To'] = self.destino
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(self.conta, self.senha)
                smtp.send_message(msg)
        except: pass

# ==============================================================================
# CONTROLADOR PRINCIPAL (THE BRAIN)
# Responsabilidade: Orquestrar os serviços e conter a lógica de negócio
# ==============================================================================
class MonitorController:
    def __init__(self, intervalo=120, headless=False, alvos_cli=None):
        # Inicializa Serviços
        self.browser = BrowserService(headless)
        self.telegram = TelegramService(self)
        self.data = DataService()
        self.email = EmailService()
        
        # Configurações de Negócio
        self.intervalo_base = intervalo
        self.alvos = [a.strip().upper() for a in alvos_cli.split(',')] if alvos_cli else []
        self.blacklist = ["PEDIATRIA", "ODONTOLOGIA"]
        
        # Estado
        self.especialidades_anteriores = set()
        self.vagas_notificadas_sessao = set()
        self.inicio_sessao = datetime.now()
        self.total_vagas_sessao = 0
        self.paused = False

    # --- LÓGICA DE NEGÓCIO (Monitoramento) ---
    def processar_ciclo(self):
        vagas_atuais = self.browser.obter_vagas()
        
        if vagas_atuais is None: 
            return # Erro temporário no site, tenta próxima

        # Primeira rodada
        if not self.especialidades_anteriores:
            self.especialidades_anteriores = vagas_atuais
            for esp in vagas_atuais: self.data.registrar("INICIO", esp)
            return

        novas = vagas_atuais - self.especialidades_anteriores
        removidas = self.especialidades_anteriores - vagas_atuais

        # Filtros (Sniper vs Geral)
        if self.alvos:
            relevantes = {v for v in novas if any(alvo in v.upper() for alvo in self.alvos)}
        else:
            relevantes = {v for v in novas if v not in self.blacklist}

        # Notificação
        if relevantes:
            frescas = relevantes - self.vagas_notificadas_sessao
            if frescas:
                texto = ", ".join(frescas)
                self._notificar_urgente(texto)
                self.vagas_notificadas_sessao.update(frescas)
                self.total_vagas_sessao += len(frescas)

        # Logs
        for esp in novas: self.data.registrar("ADICIONADA", esp)
        for esp in removidas: 
            self.data.registrar("REMOVIDA", esp)
            if esp in self.vagas_notificadas_sessao: self.vagas_notificadas_sessao.remove(esp)

        if removidas: sys.stdout.write(f"\n[-] Saiu: {', '.join(removidas)}\n")
        
        self.especialidades_anteriores = vagas_atuais
        
        # Atualiza Status Bar
        self._atualizar_terminal(len(vagas_atuais))

    def _notificar_urgente(self, texto):
        msg = f"🚨 VAGA: {texto}"
        sys.stdout.write(f"\n\n[URGENTE] {msg}\n")
        
        # Usa o browser service para tirar print
        print_file = self.browser.tirar_screenshot("vaga_temp.png")
        
        self.telegram.enviar(msg, print_file)
        self.email.enviar("Monitor HU: Vaga!", f"Disponível: {texto}")
        AudioService.tocar_alarme(f"Vaga para {texto}")
        
        if print_file: 
            try: os.remove(print_file)
            except: pass

    def _atualizar_terminal(self, qtd):
        tempo_prox = (datetime.now() + timedelta(seconds=self._calcular_intervalo())).strftime('%H:%M:%S')
        mode_str = "SNIPER" if self.alvos else "GERAL"
        status = "PAUSADO" if self.paused else "ATIVO"
        msg = f"\r[{datetime.now().strftime('%H:%M:%S')}] Vagas: {qtd} | Próx: {tempo_prox} | Mode: {mode_str} | Status: {status}   "
        sys.stdout.write(msg)
        sys.stdout.flush()

    def _calcular_intervalo(self):
        hora = datetime.now().hour
        if 0 <= hora < 6: return 1800
        if 22 <= hora <= 23: return 300
        return random.uniform(self.intervalo_base * 0.9, self.intervalo_base * 1.1)

    # --- COMANDOS DO TELEGRAM (Ações) ---
    def comando_status(self):
        tempo = str(datetime.now() - self.inicio_sessao).split('.')[0]
        msg = (f"🟢 STATUS\n⏱️ Tempo: {tempo}\n🎯 Alvos: {self.alvos}\n"
               f"⏸️ Pausado: {self.paused}\n🔎 Vagas: {len(self.especialidades_anteriores)}")
        self.telegram.enviar(msg)

    def comando_print(self):
        arquivo = self.browser.tirar_screenshot("manual.png")
        if arquivo:
            self.telegram.enviar("📸 Print atual", arquivo)
            os.remove(arquivo)
        else:
            self.telegram.enviar("❌ Erro ao tirar print (Browser fechado?)")

    def comando_pause(self):
        self.paused = True
        self.telegram.enviar("⏸️ Pausado")

    def comando_resume(self):
        self.paused = False
        self.telegram.enviar("▶️ Retomado")

    def comando_listar_alvos(self):
        self.telegram.enviar(f"🎯 Alvos: {self.alvos}" if self.alvos else "Modo Geral")

    def comando_add_alvo(self, args):
        if args:
            novo = " ".join(args).upper()
            if novo not in self.alvos:
                self.alvos.append(novo)
                self.telegram.enviar(f"✅ Adicionado: {novo}")
            else:
                self.telegram.enviar("⚠️ Já existe.")

    def comando_remove_alvo(self, args):
        if args:
            nome = " ".join(args).upper()
            self.alvos = [a for a in self.alvos if nome not in a]
            self.telegram.enviar(f"🗑️ Removido contendo: {nome}")

    def comando_help(self):
        self.telegram.enviar("Comandos: /status, /print, /pause, /resume, /add, /remove, /alvos")

    # --- LOOP PRINCIPAL ---
    def rodar(self):
        print("=== MONITOR HU v14 (MODULAR) ===")
        self.telegram.enviar("🚀 Monitor Iniciado (v14 Modular)")
        AudioService.tocar_alarme("Iniciando")

        while True:
            try:
                self.browser.iniciar()
                status_login = self.browser.login()
                
                if status_login == "CAPTCHA_NEEDED":
                    AudioService.tocar_alarme("Resolva o Captcha")
                    print("\n>>> AGUARDANDO CAPTCHA <<<")
                    
                    # Loop de espera do CAPTCHA com verificação de Telegram
                    logado = False
                    for _ in range(180): # 3 minutos tentando
                        if self.browser.verificar_sucesso_login():
                            logado = True
                            break
                        self.telegram.verificar_novos_comandos()
                        time.sleep(1)
                    
                    if not logado:
                        print("Timeout no Login.")
                        self.browser.fechar()
                        continue

                print("\n[SUCESSO] Logado!")

                # Loop de Monitoramento
                ultimo_hb = datetime.now()
                while True:
                    # Heartbeat
                    if (datetime.now() - ultimo_hb) > timedelta(hours=1):
                        self.telegram.enviar(f"💓 Vivo. Vagas: {len(self.especialidades_anteriores)}")
                        ultimo_hb = datetime.now()

                    # Executa ciclo se não estiver pausado
                    if not self.paused:
                        self.processar_ciclo()
                    else:
                        sys.stdout.write(f"\r[{datetime.now().strftime('%H:%M:%S')}] Status: PAUSADO...       ")
                        sys.stdout.flush()

                    # Smart Wait (Espera ouvindo Telegram)
                    tempo = 5 if self.paused else self._calcular_intervalo()
                    for _ in range(int(tempo)):
                        self.telegram.verificar_novos_comandos()
                        time.sleep(1)

            except KeyboardInterrupt:
                self.browser.fechar()
                print("\nParado pelo usuário.")
                sys.exit()
            except Exception as e:
                print(f"\n[ERRO CRÍTICO] {e}")
                self.browser.fechar()
                time.sleep(10)

# --- ENTRY POINT ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--intervalo', type=int, default=120)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--alvos', type=str, default=None)
    args = parser.parse_args()

    app = MonitorController(intervalo=args.intervalo, headless=args.headless, alvos_cli=args.alvos)
    app.rodar()