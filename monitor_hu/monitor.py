import os
import time
import sys
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Imports locais
from .parser import HUParser
from .notifier import send_telegram
try:
    from . import state
    from . import scheduler
except ImportError:
    import state
    import scheduler

load_dotenv()

HU_USER = os.getenv("HU_USER")
HU_DATA = os.getenv("HU_DATA")

# Lista para guardar o histórico recente na memória (para o Dashboard)
recent_history = []

def add_history(event_type, item):
    """Adiciona um evento ao histórico de exibição (mantém os últimos 5)"""
    timestamp = datetime.now().strftime("%d/%m %H:%M")
    msg = f"{timestamp}: {item}"
    
    icon = "🟢" if event_type == "added" else "🔴"
    recent_history.insert(0, (icon, msg, event_type))
    
    if len(recent_history) > 5:
        recent_history.pop()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def render_dashboard(vagas_atuais, status="Conectado", next_check=0):
    clear_screen()
    now_str = datetime.now().strftime("%d/%m %H:%M:%S")
    count = len(vagas_atuais)
    
    print("╔════════════════════════════════════════════════════╗")
    print("║  MONITOR HU-USP – Especialidades                   ║")
    print("╠════════════════════════════════════════════════════╣")
    print(f"║ Última verificação: {now_str:<30} ║")
    print(f"║ Status: ✅ {status:<38} ║")
    print("╠════════════════════════════════════════════════════╣")
    
    if count > 0:
        print(f"║ NOVAS VAGAS ({count})                                  ║")
        # Mostra até 5 vagas, se tiver mais, resume
        lista_vagas = sorted(list(vagas_atuais))
        for v in lista_vagas[:5]:
            # Corta nomes muito longos para não quebrar o layout
            nome_display = (v[:45] + '..') if len(v) > 45 else v
            print(f"║ • {nome_display:<46} ║")
        
        if len(lista_vagas) > 5:
            restante = len(lista_vagas) - 5
            print(f"║ ... e mais {restante} especialidades...                  ║")
    else:
        print("║ NENHUMA VAGA DISPONÍVEL NO MOMENTO                 ║")
        
    print("╠════════════════════════════════════════════════════╣")
    print("║ Histórico recente                                  ║")
    if recent_history:
        for icon, txt, _ in recent_history:
            # Formata para caber na linha
            txt_display = (txt[:43] + '..') if len(txt) > 43 else txt
            print(f"║ {icon} {txt_display:<44} ║")
    else:
        print("║ - Nenhuma alteração registrada ainda               ║")
    
    print("╚════════════════════════════════════════════════════╝")
    
    if next_check > 0:
        print(f"\n💤 Próxima verificação em {next_check} minutos...")

def main():
    parser = None
    print("Inicializando...")

    try:
        parser = HUParser(HU_USER, HU_DATA)
        parser.ensure_logged()

        while True:
            # 1. Batimento cardíaco
            state.update_heartbeat("running")

            # 2. Atualiza dados
            parser.driver.refresh()
            
            try:
                vagas_atuais = parser.get_dropdown_options()
            except:
                parser.ensure_logged()
                vagas_atuais = parser.get_dropdown_options()

            # 3. Compara com estado anterior
            snapshot = state.load_snapshot()
            vagas_anteriores = set(snapshot.get("especialidades", []))
            
            novas = vagas_atuais - vagas_anteriores
            removidas = vagas_anteriores - vagas_atuais

            # 4. Processa mudanças
            if novas:
                # Formata msg para Telegram (com HTML)
                msg_tg = "🟢 <b>NOVAS ESPECIALIDADES HU:</b>\n" + "\n".join(f"• {n}" for n in novas)
                send_telegram(msg_tg)
                
                # Atualiza histórico visual
                for n in novas:
                    add_history("added", f"{n} abriu")
            
            if removidas:
                for r in removidas:
                    add_history("removed", f"{r} fechou")

            if novas or removidas:
                state.save_snapshot(list(vagas_atuais))
            
            # 5. Renderiza Dashboard
            minutos = scheduler.get_interval_minutes()
            render_dashboard(vagas_atuais, status="Conectado", next_check=minutos)
            
            # Espera
            time.sleep(minutos * 60)

    except KeyboardInterrupt:
        print("\nParando...")
    except Exception:
        error_trace = traceback.format_exc()
        # Se der erro fatal, manda pro telegram mas printa o erro antes de morrer
        print("\n" + error_trace)
        send_telegram(f"🔴 ERRO FATAL NO MONITOR:\n{error_trace}")
        raise
    finally:
        if parser:
            parser.close()

if __name__ == "__main__":
    main()