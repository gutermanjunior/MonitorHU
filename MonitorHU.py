import time
import os
import plataform
import csv
import requests
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

# --- CARREGA CONFIGURAÇÕES ---
load_dotenv()

HU_USER = os.getenv("HU_USER")
HU_DATA = os.getenv("HU_DATA") # Certifique-se que no .env está "10/03/1993"
EMAIL_CONTA = os.getenv("EMAIL_CONTA")
EMAIL_SENHA = os.getenv("EMAIL_SENHA")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- CONFIGURAÇÕES GERAIS ---
URL_LOGIN = "https://sistemashu.hu.usp.br/reshu/paciente"
ARQUIVO_LOG = "historico_especialidades.csv"
INTERVALO = 120 

# LISTA DO QUE IGNORAR (Maiúsculas)
ESPECIALIDADES_IGNORAR = [
    "PEDIATRIA",
]

def preencher_data_na_marra(driver, elemento_id, data_valor):
    """
    Em vez de digitar, injeta o valor direto no HTML via JavaScript.
    Isso resolve problemas com máscaras de campo.
    """
    try:
        # 1. Limpa o campo (Garante que está vazio)
        driver.find_element(By.ID, elemento_id).clear()
        
        # 2. Injeta o valor na força bruta
        script = f"document.getElementById('{elemento_id}').value = '{data_valor}';"
        driver.execute_script(script)
    except Exception as e:
        print(f"Erro ao injetar data: {e}")

def registrar_log(tipo_evento, especialidade):
    arquivo_existe = os.path.isfile(ARQUIVO_LOG)
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ARQUIVO_LOG, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not arquivo_existe:
            writer.writerow(["Data_Hora", "Evento", "Especialidade"])
        writer.writerow([agora, tipo_evento, especialidade])

def enviar_telegram_com_foto(mensagem, arquivo_imagem=None):
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

def tocar_alarme_universal(mensagem):
    sistema = platform.system()
    
    try:
        if sistema == "Darwin":  # macOS
            # Fala a mensagem
            os.system(f'say -v Luciana "{mensagem}"')
            # Toca um som de alerta do sistema
            os.system('afplay /System/Library/Sounds/Glass.aiff')
            
        elif sistema == "Windows": # Windows
            import winsound
            # No Windows, fazer falar nativamente é complexo sem bibliotecas extras.
            # Vamos fazer um Bip longo e agudo (Frequência 1000Hz, 1 seg)
            winsound.Beep(1000, 1000) 
            
            # (Opcional) Se quiser muito que o Windows fale, descomente a linha abaixo:
            # os.system(f'PowerShell -Command "Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{mensagem}\');"')

        else: # Linux
            print("\a") # Bip simples de terminal
            
    except Exception as e:
        print(f"Erro ao tocar som: {e}")

def tentar_login_automatico(driver):
    print("Tentando login automático...")
    try:
        driver.get(URL_LOGIN)
        time.sleep(3)
        
        if len(driver.find_elements(By.ID, "PacienteMatricula")) > 0:
            # Preenche Matrícula
            driver.find_element(By.ID, "PacienteMatricula").send_keys(HU_USER)
            
            # Preenche Data (MÉTODO NOVO VIA JS)
            preencher_data_na_marra(driver, "PacienteDataNascimento", HU_DATA)
            
            print("Dados preenchidos via JavaScript. Resolva o CAPTCHA.")
            tocar_alarme_mac("Dados preenchidos. Resolva o Captcha.")
            return True
    except Exception as e:
        print(f"Falha login auto: {e}")
    return False

# --- INÍCIO ---
print("Iniciando Monitor HU v7 (Correção Data e Voz)...")
enviar_telegram_com_foto("🚀 Robô iniciado.")

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

ultimo_heartbeat = datetime.now()

try:
    tentar_login_automatico(driver)

    print("\n" + "="*50)
    print("AGUARDANDO USUÁRIO:")
    print("1. Confira se a data apareceu corretamente.")
    print("2. Resolva o CAPTCHA e entre.")
    input(">>> DÊ ENTER AQUI QUANDO VER A LISTA DE ESPECIALIDADES <<<")
    print("="*50 + "\n")

    especialidades_anteriores = set()
    primeira_rodada = True

    while True:
        try:
            # Heartbeat (1 hora)
            agora = datetime.now()
            if (agora - ultimo_heartbeat) > timedelta(hours=1):
                enviar_telegram_com_foto(f"💓 Monitor ativo. Hora: {agora.strftime('%H:%M')}")
                ultimo_heartbeat = agora

            driver.refresh()
            time.sleep(5)

            elemento_select = driver.find_element(By.ID, "Especialidade")
            select_obj = Select(elemento_select)
            
            todas_opcoes = {opt.text.strip() for opt in select_obj.options}
            limpeza = {"Selecione a Especialidade...", "", "Selecione..."}
            opcoes_limpas = {op for op in todas_opcoes if op not in limpeza}

            if primeira_rodada:
                especialidades_anteriores = opcoes_limpas
                print(f"Monitorando {len(opcoes_limpas)} especialidades.")
                primeira_rodada = False
            else:
                novas = opcoes_limpas - especialidades_anteriores
                removidas = especialidades_anteriores - opcoes_limpas
                
                # Aplica Filtro (Blacklist)
                novas_interessantes = {v for v in novas if v not in ESPECIALIDADES_IGNORAR}

                if novas_interessantes:
                    texto = ", ".join(novas_interessantes)
                    msg = f"🚨 VAGA ENCONTRADA: {texto}"
                    print(f"\n[URGENTE] {msg}")
                    
                    # Print Screen
                    nome_print = "vaga.png"
                    driver.save_screenshot(nome_print)
                    
                    enviar_telegram_com_foto(msg, nome_print)
                    enviar_email("Monitor HU: Vaga Encontrada", f"Vagas: {texto}")
                    tocar_alarme_mac(f"Atenção Guterman! Vaga para {texto}")
                    
                    try: os.remove(nome_print)
                    except: pass
                
                # Loga tudo
                for esp in novas: registrar_log("ADICIONADA", esp)
                for esp in removidas: registrar_log("REMOVIDA", esp)

                if removidas:
                    print(f"[-] Saiu: {', '.join(removidas)}")

                especialidades_anteriores = opcoes_limpas
            
            print(".", end="", flush=True) 
            time.sleep(INTERVALO)

        except NoSuchElementException:
            print("\n[SESSÃO CAIU] Recuperando...")
            tocar_alarme_mac("Sessão caiu.")
            
            tentar_login_automatico(driver)
            
            enviar_telegram_com_foto("⚠️ Sessão caiu. Aguardando login.")
            print("RESOLVA O CAPTCHA E DÊ ENTER.")
            input(">>> ENTER <<<")
            time.sleep(2)

        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(30)

except KeyboardInterrupt:
    print("\nParando...")
finally:
    driver.quit()