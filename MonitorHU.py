import time
import os
import sys
import csv
import requests
import smtplib
import platform
from email.message import EmailMessage
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Selenium & WebDriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# --- 1. CARREGA CONFIGURAÇÕES DO ARQUIVO .ENV ---
load_dotenv()

HU_USER = os.getenv("HU_USER")
HU_DATA = os.getenv("HU_DATA")
EMAIL_CONTA = os.getenv("EMAIL_CONTA")
EMAIL_SENHA = os.getenv("EMAIL_SENHA")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- 2. CONFIGURAÇÕES DO ROBÔ ---
URL_LOGIN = "https://sistemashu.hu.usp.br/reshu/paciente"
ARQUIVO_LOG = "historico_especialidades.csv"
INTERVALO = 120  # Tempo entre verificações (em segundos)

# LISTA NEGRA (Especialidades para ignorar alertas, mas continua logando no CSV)
ESPECIALIDADES_IGNORAR = [
    "PEDIATRIA",
    "CLÍNICA MÉDICA - RETORNO",
]

# --- 3. FUNÇÕES AUXILIARES ---

def tocar_alarme_universal(mensagem):
    """Toca som compatível com Windows e Mac"""
    sistema = platform.system()
    try:
        if sistema == "Darwin":  # macOS
            os.system(f'say -v Luciana "{mensagem}"')
            os.system('afplay /System/Library/Sounds/Glass.aiff')
        elif sistema == "Windows": # Windows
            import winsound
            winsound.Beep(1000, 1000)
        else:
            print("\a")
    except:
        pass

def preencher_data_na_marra(driver, elemento_id, data_valor):
    """Injeta a data via JS para não brigar com a máscara do input"""
    try:
        driver.find_element(By.ID, elemento_id).clear()
        script = f"document.getElementById('{elemento_id}').value = '{data_valor}';"
        driver.execute_script(script)
    except Exception as e:
        print(f"Erro JS Data: {e}")

def registrar_log(tipo_evento, especialidade):
    """Salva no CSV"""
    arquivo_existe = os.path.isfile(ARQUIVO_LOG)
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ARQUIVO_LOG, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not arquivo_existe:
            writer.writerow(["Data_Hora", "Evento", "Especialidade"])
        writer.writerow([agora, tipo_evento, especialidade])

def enviar_telegram_com_foto(mensagem, arquivo_imagem=None):
    """Envia mensagem para o Telegram (com ou sem foto)"""
    url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    url_foto = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    try:
        if arquivo_imagem:
            with open(arquivo_imagem, 'rb') as foto:
                requests.post(url_foto, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': mensagem}, files={'photo': foto})
        else:
            requests.post(url_msg, data={'chat_id': TELEGRAM_CHAT_ID, 'text': mensagem})
    except:
        pass

def enviar_email(assunto, corpo):
    """Envia e-mail via Gmail"""
    msg = EmailMessage()
    msg.set_content(corpo)
    msg['Subject'] = assunto
    msg['From'] = EMAIL_CONTA
    msg['To'] = EMAIL_DESTINO
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_CONTA, EMAIL_SENHA)
            smtp.send_message(msg)
    except:
        pass

def configurar_driver():
    """Configura o Chrome para parecer humano"""
    options = webdriver.ChromeOptions()
    # User-Agent de um PC comum para evitar bloqueio
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def login_inicial(driver, wait):
    """Executa o fluxo de login e espera o usuário resolver o CAPTCHA"""
    print("Acessando página de login...")
    driver.get(URL_LOGIN)
    
    try:
        # Espera até 20s pelo campo de matrícula
        wait.until(EC.presence_of_element_located((By.ID, "PacienteMatricula"))).send_keys(HU_USER)
        
        # Preenche Data via JavaScript
        preencher_data_na_marra(driver, "PacienteDataNascimento", HU_DATA)
        
        print("\n>>> DADOS PREENCHIDOS. RESOLVA O CAPTCHA E ENTRE. <<<")
        tocar_alarme_universal("Por favor, resolva o Captcha.")
        
        # O programa TRAVA aqui até o elemento 'Especialidade' aparecer na próxima tela
        print("Aguardando carregamento da lista de especialidades...")
        wait.until(EC.presence_of_element_located((By.ID, "Especialidade")))
        
        print("Login detectado com sucesso!")
        return True
        
    except TimeoutException:
        print("Tempo esgotado no login. Tentando recarregar...")
        return False

# --- 4. BLOCO PRINCIPAL (EXECUÇÃO) ---

if __name__ == "__main__":
    inicio_sessao = datetime.now()
    total_vagas_sessao = 0
    
    print("\n" + "="*40)
    print(f"MONITOR HU - VERSÃO FINAL 9.0")
    print(f"Início: {inicio_sessao.strftime('%d/%m %H:%M')}")
    print("Para sair e gerar relatório, pressione CTRL+C")
    print("="*40)

    try:
        # Loop "Imortal" (Recupera se o navegador fechar)
        while True:
            driver = None
            try:
                driver = configurar_driver()
                wait = WebDriverWait(driver, 20)
                
                # Tenta logar (Se falhar, reinicia o loop)
                if not login_inicial(driver, wait):
                    driver.quit()
                    continue 

                enviar_telegram_com_foto("🚀 Monitor HU Conectado.")
                
                especialidades_anteriores = set()
                primeira_rodada = True
                ultimo_heartbeat = datetime.now()

                # Loop de Monitoramento (Enquanto estiver logado)
                while True:
                    # Heartbeat (Sinal de vida a cada 1 hora)
                    agora = datetime.now()
                    if (agora - ultimo_heartbeat) > timedelta(hours=1):
                        tempo_rodando = str(agora - inicio_sessao).split('.')[0]
                        enviar_telegram_com_foto(f"💓 Vivo. Rodando há {tempo_rodando}")
                        ultimo_heartbeat = agora

                    # Atualiza a página
                    driver.refresh()
                    
                    # Espera a lista carregar (Dinâmico)
                    elemento_select = wait.until(EC.presence_of_element_located((By.ID, "Especialidade")))
                    
                    select_obj = Select(elemento_select)
                    todas_opcoes = {opt.text.strip() for opt in select_obj.options}
                    
                    # Remove opções inválidas
                    limpeza = {"Selecione a Especialidade...", "", "Selecione..."}
                    opcoes_limpas = {op for op in todas_opcoes if op not in limpeza}

                    if primeira_rodada:
                        especialidades_anteriores = opcoes_limpas
                        print(f"Monitorando {len(opcoes_limpas)} especialidades.")
                        
                        # --- LOG DO ESTADO INICIAL ---
                        for esp in opcoes_limpas:
                            registrar_log("INICIO_EXECUCAO", esp)
                        
                        primeira_rodada = False
                    else:
                        novas = opcoes_limpas - especialidades_anteriores
                        removidas = especialidades_anteriores - opcoes_limpas
                        
                        # Filtro de Interesse (Blacklist)
                        novas_interessantes = {v for v in novas if v not in ESPECIALIDADES_IGNORAR}

                        if novas_interessantes:
                            texto = ", ".join(novas_interessantes)
                            msg = f"🚨 VAGA: {texto}"
                            print(f"\n[URGENTE] {msg}")
                            
                            total_vagas_sessao += len(novas_interessantes)
                            
                            # Tira Print e Notifica
                            nome_print = "vaga.png"
                            driver.save_screenshot(nome_print)
                            enviar_telegram_com_foto(msg, nome_print)
                            enviar_email("Monitor HU: Vaga Encontrada", f"Vagas disponíveis: {texto}")
                            tocar_alarme_universal(f"Atenção! Vaga para {texto}")
                            
                            try: os.remove(nome_print)
                            except: pass
                        
                        # Loga tudo (Mesmo o que foi ignorado)
                        for esp in novas: registrar_log("ADICIONADA", esp)
                        for esp in removidas: registrar_log("REMOVIDA", esp)

                        if removidas:
                            print(f"\n[-] Saiu: {', '.join(removidas)}")

                        especialidades_anteriores = opcoes_limpas
                    
                    # Mostra NÚMERO DE VAGAS no terminal (ex: 454545...)
                    print(len(opcoes_limpas), end="", flush=True)
                    
                    time.sleep(INTERVALO)

            except TimeoutException:
                print("\n[LENTIDÃO] Site demorando... Recarregando.", end="")
            except NoSuchElementException:
                raise Exception("Elemento sumiu (Sessão deve ter caído)")
            except Exception as e:
                print(f"\n[ERRO CRÍTICO] {e}. Reiniciando em 10s...")
                tocar_alarme_universal("Erro crítico.")
                try: 
                    if driver: driver.quit()
                except: pass
                time.sleep(10)

    # --- ENCERRAMENTO ELEGANTE (CTRL+C) ---
    except KeyboardInterrupt:
        fim_sessao = datetime.now()
        tempo_total = str(fim_sessao - inicio_sessao).split('.')[0]
        
        msg_fim = (
            f"🛑 ROBÔ DESLIGADO MANUALMENTE\n"
            f"⏱️ Tempo online: {tempo_total}\n"
            f"🔎 Vagas encontradas: {total_vagas_sessao}"
        )
        
        print("\n" + "="*40)
        print("ENCERRANDO...")
        print(msg_fim)
        print("="*40)
        
        enviar_telegram_com_foto(msg_fim)
        
        try:
            if driver: driver.quit()
        except: pass
        sys.exit(0)
