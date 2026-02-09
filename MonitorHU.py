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

# --- CONFIGURAÇÃO DE LOGGING DO SISTEMA ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("MonitorHU")

class MonitorHU:
    def __init__(self, intervalo_base=120):
        load_dotenv()
        
        # Configurações
        self.intervalo_base = intervalo_base
        self.url = "https://sistemashu.hu.usp.br/reshu/paciente"
        self.csv_file = "historico_especialidades.csv"
        
        # Credenciais
        self.user = os.getenv("HU_USER")
        self.data_nasc = os.getenv("HU_DATA")
        
        # Notificações
        self.email_conta = os.getenv("EMAIL_CONTA")
        self.email_senha = os.getenv("EMAIL_SENHA")
        self.email_destino = os.getenv("EMAIL_DESTINO")
        self.tg_token = os.getenv("TELEGRAM_TOKEN")
        self.tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # Estado
        self.driver = None
        self.wait = None
        self.especialidades_anteriores = set()
        self.blacklist = ["PEDIATRIA", "ODONTOLOGIA"] # O que ignorar
        self.vagas_notificadas_sessao = set() # Evita spam da mesma vaga
        self.total_vagas_sessao = 0
        self.inicio_sessao = datetime.now()

    def _configurar_driver(self):
        options = webdriver.ChromeOptions()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.wait = WebDriverWait(self.driver, 20)

    def _tocar_alarme(self, mensagem):
        sistema = platform.system()
        try:
            if sistema == "Darwin":
                os.system(f'say -v Luciana "{mensagem}"')
                os.system('afplay /System/Library/Sounds/Glass.aiff')
            elif sistema == "Windows":
                import winsound
                winsound.Beep(1000, 1000)
            else:
                print("\a")
        except:
            pass

    def _enviar_telegram(self, texto, imagem=None):
        try:
            url_msg = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
            url_foto = f"https://api.telegram.org/bot{self.tg_token}/sendPhoto"
            
            if imagem:
                with open(imagem, 'rb') as f:
                    requests.post(url_foto, data={'chat_id': self.tg_chat_id, 'caption': texto}, files={'photo': f})
            else:
                requests.post(url_msg, data={'chat_id': self.tg_chat_id, 'text': texto})
        except Exception as e:
            logger.error(f"Erro Telegram: {e}")

    def _enviar_email(self, assunto, corpo):
        if not self.email_conta: return
        msg = EmailMessage()
        msg.set_content(corpo)
        msg['Subject'] = assunto
        msg['From'] = self.email_conta
        msg['To'] = self.email_destino
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(self.email_conta, self.email_senha)
                smtp.send_message(msg)
        except Exception:
            pass

    def _registrar_csv(self, evento, especialidade):
        existe = os.path.isfile(self.csv_file)
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.csv_file, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not existe:
                    writer.writerow(["Data_Hora", "Evento", "Especialidade"])
                writer.writerow([agora, evento, especialidade])
        except Exception as e:
            logger.error(f"Erro ao salvar CSV: {e}")

    def _preencher_data_js(self, elemento_id, valor):
        self.driver.find_element(By.ID, elemento_id).clear()
        self.driver.execute_script(f"document.getElementById('{elemento_id}').value = '{valor}';")

    def login(self):
        logger.info("Tentando login...")
        self.driver.get(self.url)
        
        try:
            # Espera campo matrícula
            self.wait.until(EC.presence_of_element_located((By.ID, "PacienteMatricula"))).send_keys(self.user)
            self._preencher_data_js("PacienteDataNascimento", self.data_nasc)
            
            self._tocar_alarme("Por favor, resolva o Captcha.")
            print("\n>>> AGUARDANDO RESOLUÇÃO DE CAPTCHA PELO USUÁRIO <<<")
            
            # Espera o dropdown aparecer (Sinal de sucesso)
            self.wait.until(EC.presence_of_element_located((By.ID, "Especialidade")))
            logger.info("Login realizado com sucesso!")
            return True
            
        except TimeoutException:
            logger.warning("Tempo esgotado no login.")
            return False

    def processar_vagas(self, opcoes_atuais):
        # Filtra lixo
        limpeza = {"Selecione a Especialidade...", "", "Selecione..."}
        vagas_limpas = {op for op in opcoes_atuais if op not in limpeza}
        
        # Primeira rodada: Apenas loga o estado inicial
        if not self.especialidades_anteriores:
            self.especialidades_anteriores = vagas_limpas
            logger.info(f"Monitorando {len(vagas_limpas)} especialidades iniciais.")
            for esp in vagas_limpas:
                self._registrar_csv("INICIO_EXECUCAO", esp)
            return

        # Comparação
        novas = vagas_limpas - self.especialidades_anteriores
        removidas = self.especialidades_anteriores - vagas_limpas
        
        # Filtra interesses (Blacklist)
        novas_relevantes = {v for v in novas if v not in self.blacklist}

        # Notificações
        if novas_relevantes:
            # Verifica se já notificamos essas vagas nesta sessão (Anti-Spam)
            novas_frescas = novas_relevantes - self.vagas_notificadas_sessao
            
            if novas_frescas:
                texto = ", ".join(novas_frescas)
                msg = f"🚨 VAGA: {texto}"
                print(f"\n[URGENTE] {msg}")
                
                # Screenshot
                print_name = "vaga_temp.png"
                self.driver.save_screenshot(print_name)
                
                self._enviar_telegram(msg, print_name)
                self._enviar_email("Monitor HU: Vaga!", f"Disponível: {texto}")
                self._tocar_alarme(f"Vaga para {texto}")
                
                self.total_vagas_sessao += len(novas_frescas)
                self.vagas_notificadas_sessao.update(novas_frescas)
                
                try: os.remove(print_name)
                except: pass
        
        # Atualiza Logs e Estado
        for esp in novas: self._registrar_csv("ADICIONADA", esp)
        for esp in removidas: 
            self._registrar_csv("REMOVIDA", esp)
            # Se a vaga saiu, removemos do 'cache de notificação' para avisar se ela voltar
            if esp in self.vagas_notificadas_sessao:
                self.vagas_notificadas_sessao.remove(esp)

        if removidas:
            print(f"\n[-] Saiu: {', '.join(removidas)}")

        self.especialidades_anteriores = vagas_limpas
        
        # Feedback visual (número de vagas)
        print(len(vagas_limpas), end="", flush=True)

    def rodar(self):
        print(f"\n=== MONITOR HU v10 (OOP) ===")
        print(f"Início: {self.inicio_sessao.strftime('%H:%M')}")
        self._enviar_telegram("🚀 Monitor Iniciado")

        ultimo_heartbeat = datetime.now()

        while True: # Loop de "Imortalidade" (Restart Browser)
            try:
                self._configurar_driver()
                if not self.login():
                    self.driver.quit()
                    continue

                while True: # Loop de Monitoramento
                    # Heartbeat
                    if (datetime.now() - ultimo_heartbeat) > timedelta(hours=1):
                        self._enviar_telegram(f"💓 Vivo. Vagas: {len(self.especialidades_anteriores)}")
                        ultimo_heartbeat = datetime.now()

                    self.driver.refresh()
                    
                    # Espera lista
                    elem = self.wait.until(EC.presence_of_element_located((By.ID, "Especialidade")))
                    select = Select(elem)
                    opcoes = {opt.text.strip() for opt in select.options}
                    
                    self.processar_vagas(opcoes)
                    
                    # Intervalo Humanizado (Random entre 90% e 110% do tempo base)
                    jitter = random.uniform(self.intervalo_base * 0.9, self.intervalo_base * 1.1)
                    time.sleep(jitter)

            except KeyboardInterrupt:
                self._finalizar_gracefully()
                break
            except Exception as e:
                logger.error(f"Erro Crítico: {e}. Reiniciando...")
                self._tocar_alarme("Erro crítico.")
                try: self.driver.quit()
                except: pass
                time.sleep(10)

    def _finalizar_gracefully(self):
        duracao = str(datetime.now() - self.inicio_sessao).split('.')[0]
        msg = (f"🛑 Fim Manual.\nTempo: {duracao}\nVagas Totais: {self.total_vagas_sessao}")
        print(f"\n\n{msg}")
        self._enviar_telegram(msg)
        try: self.driver.quit()
        except: pass
        sys.exit(0)

# --- ENTRADA DO PROGRAMA (CLI ARGS) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Monitor de Vagas HU-USP')
    parser.add_argument('--intervalo', type=int, default=120, help='Tempo médio entre verificações (segundos)')
    args = parser.parse_args()

    bot = MonitorHU(intervalo_base=args.intervalo)
    bot.rodar()