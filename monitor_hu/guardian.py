import os
import subprocess
import sys
import time
from datetime import datetime
from .notifier import send_telegram

MAX_CRASHES = 5
CRASH_WINDOW_SECONDS = 60
INITIAL_BACKOFF = 5
MAX_BACKOFF = 300

def start_monitor():
    return subprocess.Popen([sys.executable, "-m", "monitor_hu.monitor"])

def main():
    print("🛡️ Guardian iniciado.")
    send_telegram("🟢 Guardian iniciado.")

    crash_times = []
    backoff = INITIAL_BACKOFF
    monitor = None
    manual_exit = False 

    try:
        monitor = start_monitor()

        while True:
            retcode = monitor.poll()

            if retcode is not None:
                # Códigos de saída manual (Ctrl+C ou fechamento de janela)
                if retcode == 0 or retcode == 3221225786 or retcode == -1073741510:
                    manual_exit = True
                    break

                now = datetime.now()
                crash_times.append(now)

                crash_times = [
                    t for t in crash_times
                    if (now - t).total_seconds() <= CRASH_WINDOW_SECONDS
                ]

                if len(crash_times) >= MAX_CRASHES:
                    send_telegram("🚨 ALERTA CRÍTICO 🚨\nCrash loop detectado. Monitor interrompido.")
                    print("\n🚨 Crash loop detectado. Encerrando o Guardian.")
                    break

                print(f"🔴 Monitor caiu. Reiniciando em {backoff}s...")
                send_telegram(f"🔴 Monitor caiu. Reiniciando em {backoff}s...")

                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF)
                monitor = start_monitor()

            time.sleep(2)

    except KeyboardInterrupt:
        manual_exit = True
        # REGRA DE OURO: Absolutamente nenhum 'print' aqui! 
        # Isso quebra as coordenadas do terminal para o Rich (processo filho) limpar a tela.

    finally:
        if monitor and monitor.poll() is None:
            try:
                # Dá 3 segundos para a TUI encolher e sumir em paz
                monitor.wait(timeout=3)
            except subprocess.TimeoutExpired:
                monitor.terminate()
        
        # Agora sim, com a TUI já apagada, o Guardian pode imprimir a mensagem de saída
        if manual_exit:
            msg = "🛑 Guardian e Monitor encerrados manualmente."
            print(f"\n✅ {msg}\n")
            try:
                send_telegram(msg)
            except:
                pass
        else:
            print("\n❌ Guardian encerrado devido a falhas.\n")

if __name__ == "__main__":
    main()