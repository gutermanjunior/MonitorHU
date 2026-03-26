import os
import time
import sys
import csv
import traceback
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Importações da TUI e Logs
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from .logger import get_logger

# Imports locais
from .parser import HUParser
from .notifier import TelegramBot, send_email
try:
    from . import state
    from . import scheduler
except ImportError:
    import state
    import scheduler

load_dotenv()

HU_USER = os.getenv("HU_USER")
HU_DATA = os.getenv("HU_DATA")
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_FILE = DATA_DIR / "history.csv"

DATA_DIR.mkdir(exist_ok=True)
console = Console()
log = get_logger("Monitor")

class MonitorService:
    def __init__(self):
        self.bot = TelegramBot()
        self.parser = None
        self.paused = False
        self.vagas_atuais = set()
        self.inicio_sessao = datetime.now()
        self.recent_history = []
        self.alvos = []
        self.blacklist = ["PEDIATRIA", "ODONTOLOGIA"]

    def _log_to_csv(self, evento, especialidade):
        file_exists = CSV_FILE.exists()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Data_Hora", "Evento", "Especialidade"])
                writer.writerow([timestamp, evento, especialidade])
        except Exception: pass

    def _gerar_grafico(self):
        try:
            if not CSV_FILE.exists(): return None
            df = pd.read_csv(CSV_FILE)
            df['Data_Hora'] = pd.to_datetime(df['Data_Hora'])
            df_adds = df[df['Evento'] == 'added']
            if len(df_adds) == 0: return "VAZIO"

            df_adds['Hora'] = df_adds['Data_Hora'].dt.hour
            contagem = df_adds['Hora'].value_counts().sort_index()

            plt.figure(figsize=(10, 5))
            contagem.plot(kind='bar', color='#2ecc71', edgecolor='black')
            plt.title('Horários de Liberação de Vagas')
            plt.xlabel('Hora do Dia')
            plt.ylabel('Qtd Vagas')
            plt.grid(axis='y', alpha=0.3)
            
            img_path = DATA_DIR / "relatorio_temp.png"
            plt.savefig(img_path)
            plt.close()
            return str(img_path)
        except Exception: return None

    def _add_history(self, event_type, item):
        timestamp = datetime.now().strftime("%d/%m %H:%M")
        if event_type == "added": icon = "[bold green]🟢[/bold green]"
        elif event_type == "removed": icon = "[bold red]🔴[/bold red]"
        else: icon = "[bold blue]ℹ️[/bold blue]"
            
        self.recent_history.insert(0, f"{icon} {timestamp}: {item}")
        if len(self.recent_history) > 6: self.recent_history.pop()

    def _clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def _render_dashboard(self, status="✅ Conectado", next_check=0):
        self._clear_screen()
        now_str = datetime.now().strftime("%d/%m %H:%M:%S")
        count = len(self.vagas_atuais)
        mode = f"🎯 SNIPER ({len(self.alvos)})" if self.alvos else "🌐 GERAL"
        
        header_table = Table(box=None, show_header=False, expand=True)
        header_table.add_column("Key", style="bold cyan")
        header_table.add_column("Value")
        header_table.add_row("Última verificação:", now_str)
        header_table.add_row("Status:", status)
        header_table.add_row("Modo:", mode)

        if count > 0:
            vagas_text = Text()
            lista = sorted(list(self.vagas_atuais))
            for v in lista[:8]: vagas_text.append(f"• {v}\n", style="bold white")
            if len(lista) > 8: vagas_text.append(f"... e mais {len(lista)-8} vagas", style="dim italic")
            p_vagas = Panel(vagas_text, title=f"[bold green]VAGAS DETECTADAS ({count})[/bold green]", border_style="green", box=box.ROUNDED)
        else:
            p_vagas = Panel("[dim]Nenhuma vaga disponível no momento.[/dim]", title="[bold yellow]VAGAS DETECTADAS (0)[/bold yellow]", border_style="yellow", box=box.ROUNDED)

        if self.recent_history:
            hist_text = Text.from_markup("\n".join(self.recent_history))
        else:
            hist_text = Text("- Nenhuma alteração registrada ainda", style="dim")
            
        p_hist = Panel(hist_text, title="[bold blue]Histórico Recente[/bold blue]", border_style="blue", box=box.ROUNDED)

        console.print(Panel(header_table, title="[bold magenta]🏥 MONITOR HU-USP – Especialidades[/bold magenta]", border_style="magenta", box=box.HEAVY))
        console.print(p_vagas)
        console.print(p_hist)
        
        if next_check > 0:
            console.print(f"\n[cyan]💤 Próxima verificação em {next_check} minutos (Comandos ativos via Telegram...)[/cyan]")
        elif "PAUSADO" in status:
            console.print("\n[yellow]⏸️ Monitoramento PAUSADO. Aguardando /resume no Telegram...[/yellow]")

    def handle_commands(self):
        comandos = self.bot.get_updates()
        for full_cmd in comandos:
            log.info(f"Comando recebido: {full_cmd}")
            parts = full_cmd.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            if cmd == "/ping": self.bot.send("🏓 Pong!")
            elif cmd == "/status":
                tempo = str(datetime.now() - self.inicio_sessao).split('.')[0]
                msg = f"<b>STATUS MONITOR</b>\n⏱️ Uptime: {tempo}\n🔎 Vagas Visíveis: {len(self.vagas_atuais)}"
                self.bot.send(msg)
            elif cmd == "/list":
                if not self.vagas_atuais: self.bot.send("ℹ️ Lista vazia.")
                else: self.bot.send("📋 <b>VAGAS ATUAIS:</b>\n" + "\n".join(f"• {v}" for v in sorted(self.vagas_atuais)))
            elif cmd == "/print":
                self.bot.send("📸 Tirando print...")
                path = self.parser.take_screenshot("cmd_print.png")
                if path:
                    self.bot.send_photo("📸 Screenshot", path)
                    try: os.remove(path)
                    except: pass
                else: self.bot.send("❌ Erro ao tirar print.")
            elif cmd == "/relatorio":
                self.bot.send("📊 Gerando gráfico...")
                path = self._gerar_grafico()
                if path == "VAZIO": self.bot.send("ℹ️ Sem dados suficientes.")
                elif path:
                    self.bot.send_photo("📈 Horários de Pico", path)
                    try: os.remove(path)
                    except: pass
                else: self.bot.send("❌ Erro ou sem arquivo CSV.")
            elif cmd == "/pause":
                self.paused = True
                self.bot.send("⏸️ Pausado.")
                self._render_dashboard(status="[bold yellow]⏸️ PAUSADO[/bold yellow]")
            elif cmd == "/resume":
                self.paused = False
                self.bot.send("▶️ Retomado.")
                self._render_dashboard(status="[bold green]✅ Retomando...[/bold green]")
            elif cmd == "/alvos":
                if not self.alvos: self.bot.send("🌐 Modo GERAL")
                else: self.bot.send(f"🎯 <b>ALVOS ATUAIS:</b>\n" + "\n".join(self.alvos))
            elif cmd == "/add":
                if args:
                    novo = " ".join(args).upper()
                    if novo not in self.alvos:
                        self.alvos.append(novo)
                        self.bot.send(f"✅ Alvo adicionado: {novo}")
                else: self.bot.send("⚠️ Use: /add NOME")
            elif cmd == "/remove":
                if args:
                    nome = " ".join(args).upper()
                    self.alvos = [a for a in self.alvos if nome not in a]
                    self.bot.send(f"🗑️ Removido: {nome}")
                else: self.bot.send("⚠️ Use: /remove NOME")
            elif cmd == "/help":
                self.bot.send("🤖 <b>COMANDOS:</b>\n/status\n/list\n/print\n/relatorio\n/add [NOME]\n/remove [NOME]\n/alvos\n/pause\n/resume")

    def smart_sleep(self, minutes):
        seconds = minutes * 60
        if self.paused:
            self._render_dashboard(status="[bold yellow]⏸️ PAUSADO[/bold yellow]")
            while self.paused:
                self.handle_commands()
                time.sleep(2)
            return

        for _ in range(int(seconds)):
            self.handle_commands()
            if self.paused: return
            time.sleep(1)

    def run(self):
        log.info("=== Iniciando MonitorService v2.9 ===")
        self._clear_screen()
        console.print("[bold green]🚀 Monitor HU (v2.9 - Ultimate Edition)[/bold green]")
        
        try: self.bot.send("🚀 Monitor Iniciado (v2.9)")
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

                # --- LÓGICA DE ESTADO ---
                snapshot = state.load_snapshot()
                vagas_anteriores = set(snapshot.get("especialidades", []))
                is_first_run = snapshot.get("is_first_run", False)
                
                novas = self.vagas_atuais - vagas_anteriores
                removidas = vagas_anteriores - self.vagas_atuais

                if is_first_run:
                    if self.vagas_atuais:
                        self._add_history("system", f"Baseline criado: {len(self.vagas_atuais)} especialidades ocultas.")
                    state.save_snapshot(list(self.vagas_atuais))
                else:
                    if self.alvos:
                        novas_relevantes = {v for v in novas if any(alvo in v.upper() for alvo in self.alvos)}
                    else:
                        novas_relevantes = {v for v in novas if v not in self.blacklist}

                    if novas_relevantes:
                        log.info(f"VAGAS ENCONTRADAS: {novas_relevantes}")
                        
                        # TELEGRAM
                        msg_tg = "🟢 <b>NOVAS VAGAS:</b>\n" + "\n".join(f"• {n}" for n in novas_relevantes)
                        self.bot.send(msg_tg)
                        
                        # E-MAIL
                        msg_email = "O Monitor HU encontrou as seguintes vagas:\n\n" + "\n".join(f"- {n}" for n in novas_relevantes)
                        send_email("Monitor HU: Novas Vagas!", msg_email)

                        # HISTÓRICO E BEEP
                        for n in novas_relevantes:
                            self._add_history("added", f"{n} abriu")
                            
                        sys.stdout.write('\a')
                        sys.stdout.flush()
                    
                    for n in novas: self._log_to_csv("added", n)
                    for r in removidas: 
                        self._log_to_csv("removed", r)
                        self._add_history("removed", f"{r} fechou")

                    if novas or removidas:
                        state.save_snapshot(list(self.vagas_atuais))
                
                minutos = scheduler.get_interval_minutes()
                self._render_dashboard(status="[bold green]✅ Conectado[/bold green]", next_check=minutos)
                self.smart_sleep(minutos)

        except KeyboardInterrupt:
            console.print("\n[bold red]Parando...[/bold red]")
        except Exception:
            console.print_exception()
            raise
        finally:
            if self.parser: self.parser.close()

def main():
    MonitorService().run()

if __name__ == "__main__":
    main()