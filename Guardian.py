import subprocess
import time
import os
import requests
import sys
from datetime import datetime
from dotenv import load_dotenv

# Carrega configurações
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def enviar_aviso(mensagem):
    try:
        if TOKEN and CHAT_ID:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, data={'chat_id': CHAT_ID, 'text': f"🛡️ GUARDIAN: {mensagem}"}, timeout=5)
    except:
        pass

def rodar_monitor():
    print("🛡️ INICIANDO O MONITOR HU...")
    
    # Passa adiante quaisquer argumentos (ex: --headless)
    cmd = [sys.executable, "MonitorHU.py"] + sys.argv[1:]
    
    processo = None
    
    while True:
        try:
            # Inicia o Monitor
            processo = subprocess.Popen(cmd)
            
            # Fica esperando o Monitor rodar...
            # Se você der CTRL+C aqui, o Python lança KeyboardInterrupt
            processo.wait()
            
            # --- Se chegou aqui, o Monitor fechou sozinho ---
            codigo_saida = processo.returncode
            
            if codigo_saida == 0:
                print("✅ Monitor encerrou corretamente (Manual). Guardian parando.")
                break # Sai do loop infinito
            else:
                # Código != 0 significa erro/crash
                print(f"\n❌ O Monitor caiu! Código: {codigo_saida}")
                enviar_aviso(f"⚠️ O Monitor HU caiu (Código {codigo_saida}). Reiniciando...")
                time.sleep(5)
                print("🔄 Reiniciando...\n")

        except KeyboardInterrupt:
            # --- AQUI ESTÁ A CORREÇÃO ---
            print("\n🛑 Interrupção (CTRL+C) recebida...")
            
            # Verifica se o Monitor ainda está vivo
            if processo and processo.poll() is None:
                print("⏳ Aguardando o Monitor fechar o Chrome corretamente...")
                try:
                    # Espera até 15 segundos para o MonitorHU rodar o driver.quit()
                    processo.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    print("💀 O Monitor demorou demais. Forçando encerramento.")
                    processo.kill() # Mata se travar
            
            print("🛡️ Guardian encerrado.")
            sys.exit(0)

if __name__ == "__main__":
    rodar_monitor()