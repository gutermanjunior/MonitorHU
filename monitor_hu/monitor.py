import os
import time
import sys
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Imports locais
from .parser import HUParser
from .notifier import TelegramBot
try:
    from . import state
    from . import scheduler
except ImportError:
    import state
    import scheduler

load_dotenv()

HU_USER = os.getenv("HU_USER")
HU_DATA = os.getenv("HU_DATA")

class MonitorService:
    def __init__(self):
        self.bot = TelegramBot()
        self.parser = None
        self.paused = False
        self.vagas_atuais = set()
        self.inicio_sessao = datetime.now()
        
        # Histórico visual para o Dashboard
        self.recent_history = []

    def _add_history(self, event_type, item):
        """Adiciona evento ao histórico visual (mantém os últimos 5)"""
        timestamp = datetime.now().strftime("%d/%m %H:%M")
        msg = f"{timestamp}: {item}"
        icon = "🟢" if event_type == "added" else "🔴"
        self.recent_history.insert(0, (icon, msg))
        
        if len(self.recent_history) > 5:
            self.recent_history.pop()

    def _clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def _render_dashboard(self, status="✅ Conectado", next_check=0):
        """Desenha o painel visual no terminal"""
        self._clear_screen()
        now_str = datetime.now().strftime("%d/%m %H:%M:%S")
        count = len(self.vagas_atuais)
        
        print("╔════════════════════════════════════════════════════╗")
        print("║  MONITOR HU-USP – Especialidades                   ║")
        print("╠════════════════════════════════════════════════════╣")
        print(f"║ Última verificação: {now_str:<30} ║")
        print(f"║ Status: {status:<38} ║")
        print("╠════════════════════════════════════════════════════╣")
        
        if count > 0:
            print(f"║ NOVAS VAGAS ({count})                                  ║")
            lista = sorted(list(self.vagas_atuais))
            for v in lista[:5]:
                nome_display = (v[:45] + '..') if len(v) > 45 else v
                print(f"║ • {nome_display:<46} ║")
            
            if len(lista) > 5:
                rest = len(lista) - 5
                print(f"║ ... e mais {rest} especialidades...                  ║")
        else:
            print("║ NENHUMA VAGA DISPONÍVEL NO MOMENTO                 ║")
            
        print("╠════════════════════════════════════════════════════╣")
        print("║ Histórico recente                                  ║")
        if self.recent_history:
            for icon, txt in self.recent_history:
                txt_display = (txt[:43] + '..') if len(txt) > 43 else txt
                print(f"║ {icon} {txt_display:<44} ║")
        else:
            print("║ - Nenhuma alteração registrada ainda               ║")
        
        print("╚════════════════════════════════════════════════════╝")
        
        if next_check > 0:
            print(f"\n💤 Próxima verificação em {next_check} minutos (Ouvindo Telegram...)")
        elif status.startswith("⏸️"):
            print("\n⏸️ Monitoramento PAUSADO. Aguardando comando /resume...")

    def handle_commands(self):
        """Processa comandos recebidos pelo Telegram"""
        comandos = self.bot.get_updates()
        
        for cmd in comandos:
            c = cmd.lower().split()[0]
            
            if c == "/ping":
                self.bot.send("🏓 Pong!")
            
            elif c == "/status":
                tempo = str(datetime.now() - self.inicio_sessao).split('.')[0]
                status_icon = "⏸️ PAUSADO" if self.paused else "✅ RODANDO"
                msg = (
                    f"<b>STATUS MONITOR HU</b>\n"
                    f"Status: {status_icon}\n"
                    f"Uptime: {tempo}\n"
                    f"Vagas visíveis: {len(self.vagas_atuais)}"
                )
                self.bot.send(msg)

            elif c == "/list":
                if not self.vagas_atuais:
                    self.bot.send("ℹ️ Nenhuma vaga detectada ou lista vazia.")
                else:
                    lista = sorted(list(self.vagas_atuais))
                    msg = "📋 <b>LISTA DE ESPECIALIDADES:</b>\n\n"
                    msg += "\n".join(f"• {v}" for v in lista)
                    self.bot.send(msg)

            elif c == "/pause":
                self.paused = True
                self.bot.send("⏸️ Monitoramento <b>PAUSADO</b>.")
                self._render_dashboard(status="⏸️ PAUSADO")

            elif c == "/resume":
                self.paused = False
                self.bot.send("▶️ Monitoramento <b>RETOMADO</b>.")
                self._render_dashboard(status="✅ Retomando...")

    def smart_sleep(self, minutes):
        """Dorme mas continua ouvindo o Telegram"""
        seconds = minutes * 60
        
        if self.paused:
            self._render_dashboard(status="⏸️ PAUSADO")
            while self.paused:
                self.handle_commands()
                time.sleep(2)
            return

        for _ in range(int(seconds)):
            self.handle_commands()
            if self.paused: 
                return
            time.sleep(1)

    def run(self):
        self._clear_screen()
        print("🚀 Monitor HU Iniciado (v2.3)")
        
        try:
            self.bot.send("🚀 Monitor Iniciado")
        except: pass
        
        try:
            self.parser = HUParser(HU_USER, HU_DATA)
            self.parser.ensure_logged()

            while True:
                if self.paused:
                    self.smart_sleep(0)
                    continue

                state.update_heartbeat("running")

                try:
                    self.parser.driver.refresh()
                    self.vagas_atuais = self.parser.get_dropdown_options()
                except:
                    self.parser.ensure_logged()
                    self.vagas_atuais = self.parser.get_dropdown_options()

                snapshot = state.load_snapshot()
                vagas_anteriores = set(snapshot.get("especialidades", []))
                
                novas = self.vagas_atuais - vagas_anteriores
                removidas = vagas_anteriores - self.vagas_atuais

                # CORREÇÃO DO <B>: Separação de mensagens
                if novas:
                    # Mensagem formatada (HTML) apenas para o Telegram
                    msg_tg = "🟢 <b>NOVAS VAGAS:</b>\n" + "\n".join(f"• {n}" for n in novas)
                    self.bot.send(msg_tg)
                    
                    # Atualiza o histórico visual (Dashboard)
                    for n in novas:
                        self._add_history("added", f"{n} abriu")
                
                if removidas:
                    for r in removidas:
                        self._add_history("removed", f"{r} fechou")
                    # Log rápido de fechamento se quiser debug
                    # print(f"🔴 Fechou: {removidas}")

                if novas or removidas:
                    state.save_snapshot(list(self.vagas_atuais))
                
                minutos = scheduler.get_interval_minutes()
                self._render_dashboard(status="✅ Conectado", next_check=minutos)
                
                self.smart_sleep(minutos)

        except KeyboardInterrupt:
            print("\nParando...")
            try: self.bot.send("🛑 Monitor desligado manualmente.")
            except: pass
        except Exception:
            error_trace = traceback.format_exc()
            try: self.bot.send(f"🔴 ERRO FATAL:\n<pre>{error_trace}</pre>")
            except: pass
            raise
        finally:
            if self.parser:
                self.parser.close()

def main():
    service = MonitorService()
    service.run()

if __name__ == "__main__":
    main()