"""
===============================================================================
Projeto: Monitor HU-USP (Especialidades)
Arquivo: monitor.py
Autor: Guterman (guterman.com.br)
Versão: 3.1 (Organized & Clean Exit Edition)
Data: Março de 2026
===============================================================================

Descrição:
    Sistema autônomo de monitoramento de vagas médicas do Hospital Universitário 
    da USP com TUI (Interface de Texto) rica e tolerância a falhas.

Estrutura do Código:
    1. Imports e Configurações
    2. Gestão de Dados e Arquivos
    3. Construção da Interface (TUI)
    4. Comandos e Comunicação (Telegram)
    5. Motor Principal (Loop de Monitoramento)
===============================================================================
"""

# ==============================================================================
# 1. IMPORTS E CONFIGURAÇÕES INICIAIS
# ==============================================================================
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

# Importações da TUI (Rich)
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

# Imports locais
from .logger import get_logger
from .parser import HUParser
from .notifier import TelegramBot, send_email
try:
    from . import state
    from . import scheduler
except ImportError:
    import state
    import scheduler

# Configuração de Ambiente
load_dotenv()
HU_USER = os.getenv("HU_USER")
HU_DATA = os.getenv("HU_DATA")
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_FILE = DATA_DIR / "history.csv"
DATA_DIR.mkdir(exist_ok=True)

# Habilita suporte ANSI nativo (necessário para o Windows Terminal)
os.system("")

# Instâncias globais de logging e interface
console = Console()
log = get_logger("Monitor")


class MonitorService:
    def __init__(self):
        # Controle de Estado Interno
        self.bot = TelegramBot()
        self.parser = None
        self.paused = False
        self.vagas_atuais = set()
        self.inicio_sessao = datetime.now()
        self.recent_history = []
        self.live = None
        
        # Filtros de Especialidades
        self.alvos = []
        self.blacklist = ["PEDIATRIA", "ODONTOLOGIA"]

    # ==========================================================================
    # 2. GESTÃO DE DADOS E ARQUIVOS (Log, CSV, Gráficos)
    # ==========================================================================
    def _log_to_csv(self, evento, especialidade):
        """Salva adições e remoções no history.csv para análises futuras."""
        file_exists = CSV_FILE.exists()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Data_Hora", "Evento", "Especialidade"])
                writer.writerow([timestamp, evento, especialidade])
        except Exception:
            pass

    def _gerar_grafico(self):
        """Lê o history.csv e gera um gráfico de barras com horários de pico."""
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
        except Exception: 
            return None

    def _add_history(self, event_type, item):
        """Adiciona uma nova linha ao painel de 'Histórico Recente' da TUI."""
        timestamp = datetime.now().strftime("%d/%m %H:%M")
        if event_type == "added": icon = "[bold green]🟢[/bold green]"
        elif event_type == "removed": icon = "[bold red]🔴[/bold red]"
        else: icon = "[bold blue]ℹ️[/bold blue]"
            
        self.recent_history.insert(0, f"{icon} {timestamp}: {item}")
        if len(self.recent_history) > 6: self.recent_history.pop()

    # ==========================================================================
    # 3. CONSTRUÇÃO DA INTERFACE (TUI - Rich Layout)
    # ==========================================================================
    def _build_layout(self, status="[bold green]✅ Conectado[/bold green]", next_check=0):
        """Constrói e empacota todos os painéis visuais para o Live renderizar."""
        now_str = datetime.now().strftime("%d/%m %H:%M:%S")
        count = len(self.vagas_atuais)
        mode = f"🎯 SNIPER ({len(self.alvos)})" if self.alvos else "🌐 GERAL"
        
        # 3.1 Cabeçalho
        header_table = Table(box=None, show_header=False, expand=True)
        header_table.add_column("Key", style="bold cyan")
        header_table.add_column("Value")
        header_table.add_row("Última verificação:", now_str)
        header_table.add_row("Status:", status)
        header_table.add_row("Modo:", mode)
        p_header = Panel(header_table, title="[bold magenta]🏥 MONITOR HU-USP – Especialidades[/bold magenta]", border_style="magenta", box=box.HEAVY)

        # 3.2 Lista de Vagas Detectadas
        if count > 0:
            vagas_text = Text()
            lista = sorted(list(self.vagas_atuais))
            for v in lista[:8]: vagas_text.append(f"• {v}\n", style="bold white")
            if len(lista) > 8: vagas_text.append(f"... e mais {len(lista)-8} vagas", style="dim italic")
            p_vagas = Panel(vagas_text, title=f"[bold green]VAGAS DETECTADAS ({count})[/bold green]", border_style="green", box=box.ROUNDED)
        else:
            p_vagas = Panel("[dim]Nenhuma vaga disponível no momento.[/dim]", title="[bold yellow]VAGAS DETECTADAS (0)[/bold yellow]", border_style="yellow", box=box.ROUNDED)

        # 3.3 Painel de Histórico
        if self.recent_history:
            hist_text = Text.from_markup("\n".join(self.recent_history))
        else:
            hist_text = Text("- Nenhuma alteração registrada ainda", style="dim")
        p_hist = Panel(hist_text, title="[bold blue]Histórico Recente[/bold blue]", border_style="blue", box=box.ROUNDED)

        # 3.4 Rodapé de Status
        footer_text = ""
        if next_check > 0:
            footer_text = f"\n[cyan]💤 Próxima verificação em {next_check} minutos (Comandos ativos via Telegram...)[/cyan]"
        elif "PAUSADO" in status:
            footer_text = "\n[yellow]⏸️ Monitoramento PAUSADO. Aguardando /resume no Telegram...[/yellow]"

        return Group(p_header, p_vagas, p_hist, Text.from_markup(footer_text) if footer_text else Text(""))

    # ==========================================================================
    # 4. COMANDOS E COMUNICAÇÃO (Telegram)
    # ==========================================================================
    def handle_commands(self):
        """Lê atualizações do Telegram e executa as ações correspondentes."""
        comandos = self.bot.get_updates()
        for full_cmd in comandos:
            log.info(f"Comando recebido: {full_cmd}")
            parts = full_cmd.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            if cmd == "/ping": 
                self.bot.send("🏓 Pong!")
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
                if self.live: self.live.update(self._build_layout(status="[bold yellow]⏸️ PAUSADO[/bold yellow]"))
            elif cmd == "/resume":
                self.paused = False
                self.bot.send("▶️ Retomado.")
                if self.live: self.live.update(self._build_layout(status="[bold green]✅ Retomando...[/bold green]"))
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

    # ==========================================================================
    # 5. MOTOR PRINCIPAL (Loop e Scheduling)
    # ==========================================================================
    def smart_sleep(self, minutes):
        """Pausa a thread principal permitindo a checagem contínua do Telegram."""
        seconds = minutes * 60
        if self.paused:
            if self.live: self.live.update(self._build_layout(status="[bold yellow]⏸️ PAUSADO[/bold yellow]"))
            while self.paused:
                self.handle_commands()
                time.sleep(2)
            return

        for _ in range(int(seconds)):
            self.handle_commands()
            if self.paused: return
            time.sleep(1)

    def run(self):
        """Inicia a automação, a TUI e o ciclo infinito de monitoramento."""
        log.info("=== Iniciando MonitorService v3.1 (Organized Edition) ===")
        try: self.bot.send("🚀 Monitor Iniciado (v3.1)")
        except: pass

        erro_critico = False # <--- 1. NOVA FLAG DE CONTROLE

        try:
            self.parser = HUParser(HU_USER, HU_DATA)
            self.parser.ensure_logged()

            # APENAS UM ESPAÇO EM BRANCO (Sem cls para não apagar o histórico do terminal)
            print("\n") 

            with Live(self._build_layout(), console=console, screen=True, transient=True, refresh_per_second=4) as live:
                self.live = live

                while True:
                    if self.paused:
                        self.smart_sleep(0)
                        continue
                    
                    state.update_heartbeat("running")

                    try:
                        self.parser.driver.refresh()
                        self.vagas_atuais = self.parser.get_dropdown_options()
                    except Exception:
                        try:
                            self.parser.ensure_logged()
                            self.vagas_atuais = self.parser.get_dropdown_options()
                        except Exception as e:
                            # --- BLOCO DE PROTEÇÃO CONTRA SITE FORA DO AR ---
                            log.warning(f"Falha ao validar a lista de vagas. Site caiu? Erro: {e}")
                            self._add_history("system", "⚠️ Site indisponível. Mantendo cache.")
                            
                            minutos = scheduler.get_interval_minutes()
                            self.live.update(self._build_layout(status="[bold red]⚠️ Erro no Site HU - Aguardando...[/bold red]", next_check=minutos))
                            self.smart_sleep(minutos)
                            continue # O 'continue' pula direto para o próximo ciclo do while, sem apagar o snapshot
                            # ------------------------------------------------

                    snapshot = state.load_snapshot()
                    vagas_anteriores = set(snapshot.get("especialidades", []))
                    is_first_run = snapshot.get("is_first_run", False)
                    
                    novas = self.vagas_atuais - vagas_anteriores
                    removidas = vagas_anteriores - self.vagas_atuais

                    if is_first_run:
                        if self.vagas_atuais:
                            self._add_history("system", f"Baseline criado: {len(self.vagas_atuais)} especialidades.")
                        state.save_snapshot(list(self.vagas_atuais))
                    else:
                        if self.alvos:
                            novas_relevantes = {v for v in novas if any(alvo in v.upper() for alvo in self.alvos)}
                        else:
                            novas_relevantes = {v for v in novas if v not in self.blacklist}

                        if novas_relevantes:
                            log.info(f"VAGAS ENCONTRADAS: {novas_relevantes}")
                            msg_tg = "🟢 <b>NOVAS VAGAS:</b>\n" + "\n".join(f"• {n}" for n in novas_relevantes)
                            self.bot.send(msg_tg)
                            
                            msg_email = "O Monitor HU encontrou as seguintes vagas:\n\n" + "\n".join(f"- {n}" for n in novas_relevantes)
                            send_email("Monitor HU: Novas Vagas!", msg_email)

                            for n in novas_relevantes: self._add_history("added", f"{n} abriu")
                                
                            sys.stdout.write('\a')
                            sys.stdout.flush()
                        
                        for n in novas: self._log_to_csv("added", n)
                        for r in removidas: 
                            self._log_to_csv("removed", r)
                            self._add_history("removed", f"{r} fechou")

                        if novas or removidas:
                            state.save_snapshot(list(self.vagas_atuais))
                    
                    minutos = scheduler.get_interval_minutes()
                    self.live.update(self._build_layout(status="[bold green]✅ Conectado[/bold green]", next_check=minutos))
                    self.smart_sleep(minutos)

        except KeyboardInterrupt:
            # Fechamento manual limpo via Ctrl+C
            if self.live:
                self.live.stop()
        except Exception as e:
            erro_critico = True # <--- 2. MARCA QUE HOUVE ERRO
            log.error(f"Erro fatal no Monitor: {e}", exc_info=True)
            console.print_exception()
            raise
        finally:
            # 3. LIMPEZA DA TELA VEM PRIMEIRO! (É rápido e garantido)
            if not erro_critico:
                # Código ANSI agressivo: Força a saída do buffer alternativo e limpa tudo
                sys.stdout.write("\033[?1049l\033[2J\033[H") 
                sys.stdout.flush()
                os.system('cls' if os.name == 'nt' else 'clear') 
            
            # 4. FECHAMENTO DO SELENIUM DEPOIS (É demorado)
            if self.parser: 
                try:
                    self.parser.close()
                except:
                    pass

def main():
    MonitorService().run()

if __name__ == "__main__":
    main()