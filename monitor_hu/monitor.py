import os
import time
import sys
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Imports locais (Assumindo que estão no mesmo pacote monitor_hu)
from .parser import HUParser
from .notifier import send_telegram
try:
    from . import state
    from . import scheduler
except ImportError:
    # Fallback caso rode como script solto
    import state
    import scheduler

load_dotenv()

HU_USER = os.getenv("HU_USER")
HU_DATA = os.getenv("HU_DATA")

def check_specialties(parser: HUParser):
    # Lógica Real usando o método corrigido
    return parser.get_dropdown_options()

def main():
    parser = None
    print("🚀 Monitor HU Iniciado (v2)")
    send_telegram("🚀 Monitor HU Iniciado")

    try:
        parser = HUParser(HU_USER, HU_DATA)
        parser.ensure_logged()

        while True:
            # 1. Batimento cardíaco para o Guardian não reiniciar o processo
            state.update_heartbeat("running")

            # 2. Verifica vagas
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Verificando...")
            parser.driver.refresh()
            
            # Garante que ainda está logado após refresh
            try:
                vagas_atuais = check_specialties(parser)
            except:
                print("Sessão parece ter caído. Tentando relogar...")
                parser.ensure_logged()
                vagas_atuais = check_specialties(parser)

            # 3. Compara com estado anterior
            snapshot = state.load_snapshot()
            vagas_anteriores = set(snapshot.get("especialidades", []))
            
            novas = vagas_atuais - vagas_anteriores
            removidas = vagas_anteriores - vagas_atuais

            # 4. Notifica e Salva
            if novas:
                msg = "🟢 <b>NOVAS ESPECIALIDADES:</b>\n" + "\n".join(f"• {n}" for n in novas)
                print(msg)
                send_telegram(msg)
            
            if removidas:
                print(f"🔴 Removidas: {removidas}")

            if novas or removidas:
                state.save_snapshot(list(vagas_atuais))
            
            # 5. Dorme pelo tempo inteligente
            minutos = scheduler.get_interval_minutes()
            print(f"💤 Aguardando {minutos} minutos...")
            time.sleep(minutos * 60)

    except KeyboardInterrupt:
        print("\nParando...")
    except Exception:
        error_trace = traceback.format_exc()
        print(error_trace)
        send_telegram(f"🔴 ERRO FATAL NO MONITOR:\n{error_trace}")
        raise # Faz o processo morrer para o Guardian reiniciar
    finally:
        if parser:
            parser.close()

if __name__ == "__main__":
    main()