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

# Imports locais
from .parser import HUParser
from .notifier import TelegramBot, send_email
from .logger import get_logger

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

# Inicia o logger para o módulo Monitor
log = get_logger("Monitor")

# Garante que a pasta de dados exista
DATA_DIR.mkdir(exist_ok=True)

class MonitorService:
    def __init__(self):
        self.bot = TelegramBot()
        self.parser = None
        self.paused = False
        self.vagas_atuais = set()
        self.inicio_sessao = datetime.now()
        self.recent_history = []
        
        # Modo Sniper (Alvos)
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
        except Exception as e:
            log.error(f"Falha ao escrever no history.csv: {e}")

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
            log.info("Gráfico de relatório gerado com sucesso.")
            return str(img_path)
        except Exception as e:
            log.error(f"Erro ao gerar gráfico: {e}")
            return None

    def _add_history(self, event_type, item):
        timestamp = datetime.now().strftime("%d/%m %H:%M")
        msg = f"{timestamp}: {item}"
        icon = "🟢" if event_type == "added" else "🔴"
        self.recent_history.insert(0, (icon, msg))
        if len(self.recent_history) > 5: self.recent_history.pop()

    def _clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def _render_dashboard(self, status="✅ Conectado", next_check=0):
        self._clear_screen()
        now_str = datetime.now().strftime("%d/%m %H:%M:%S")
        count = len(self.vagas_atuais)
        mode = f"🎯 SNIPER ({len(self.alvos)})" if self.alvos else "🌐 GERAL"
        
        print("╔════════════════════════════════════════════════════╗")
        print("║  MONITOR HU-USP – Especialidades                   ║")
        print("╠════════════════════════════════════════════════════╣")
        print(f"║ Última verificação: {now_str:<30} ║")
        print(f"║ Status: {status:<18} Modo: {mode:<13} ║")
        print("╠════════════════════════════════════════════════════╣")
        
        if count > 0:
            print(f"║ VAGAS DETECTADAS ({count})                                 ║")
            lista = sorted(list(self.vagas_atuais))
            for v in lista[:5]:
                nome_display = (v[:43] + '..') if len(v) > 43 else v
                print(f"║ • {nome_display:<46} ║")
            if len(lista) > 5:
                restantes = len(lista) - 5
                print(f"║ ... e mais {restantes:<35} ║")
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
            print(f"\n💤 Próxima verificação em {next_check} minutos (Comandos ativos...)")
        elif status.startswith("⏸️"):
            print("\n⏸️ Monitoramento PAUSADO. Aguardando comando /resume...")

    def handle_commands(self):
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
                mode = f"🎯 SNIPER ({len(self.alvos)})" if self.alvos else "🌐 GERAL"
                msg = (f"<b>STATUS MONITOR</b>\n"
                       f"⏱️ Uptime: {tempo}\n"
                       f"🛠️ Modo: {mode}\n"
                       f"🔎 Vagas Visíveis: {len(self.vagas_atuais)}")
                self.bot.send(msg)

            elif cmd == "/list":
                if not self.vagas_atuais: self.bot.send("ℹ️ Lista vazia.")
                else:
                    msg = "📋 <b>VAGAS ATUAIS:</b>\n\n" + "\n".join(f"• {v}" for v in sorted(self.vagas_atuais))
                    self.bot.send(msg)

            elif cmd == "/print":
                self.bot.send("📸 Tirando print...")
                path = self.parser.take_screenshot("cmd_print.png")
                if path:
                    self.bot.send_photo("📸 Screenshot Atual", path)
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
                self._render_dashboard(status="⏸️ PAUSADO")
                log.info("Operação pausada pelo usuário.")

            elif cmd == "/resume":
                self.paused = False
                self.bot.send("▶️ Retomado.")
                self._render_dashboard(status="✅ Retomando...")
                log.info("Operação retomada pelo usuário.")

            elif cmd == "/alvos":
                if not self.alvos: self.bot.send("🌐 Modo GERAL (Monitorando tudo exceto blacklist)")
                else: self.bot.send(f"🎯 <b>ALVOS ATUAIS:</b>\n" + "\n".join(self.alvos))

            elif cmd == "/add":
                if args:
                    novo = " ".join(args).upper()
                    if novo not in self.alvos:
                        self.alvos.append(novo)
                        self.bot.send(f"✅ Alvo adicionado: {novo}")
                        log.info(f"Alvo adicionado: {novo}")
                else: self.bot.send("⚠️ Use: /add NOME")

            elif cmd == "/remove":
                if args:
                    nome = " ".join(args).upper()
                    self.alvos = [a for a in self.alvos if nome not in a]
                    self.bot.send(f"🗑️ Removido: {nome}")
                    log.info(f"Alvo removido: {nome}")
                else: self.bot.send("⚠️ Use: /remove NOME")
            
            elif cmd == "/help":
                help_txt = (
                    "🤖 <b>COMANDOS:</b>\n"
                    "/status - Estado do bot\n"
                    "/list - Ver vagas atuais\n"
                    "/print - Foto da tela\n"
                    "/relatorio - Gráfico de horários\n"
                    "/add [NOME] - Adicionar alvo\n"
                    "/remove [NOME] - Remover alvo\n"
                    "/alvos - Ver lista de alvos\n"
                    "/pause - Pausar\n"
                    "/resume - Retomar"
                )
                self.bot.send(help_txt)

    def smart_sleep(self, minutes):
        seconds = minutes * 60
        if self.paused:
            self._render_dashboard(status="⏸️ PAUSADO")
            while self.paused:
                self.handle_commands()
                time.sleep(2)
            return

        for _ in range(int(seconds)):
            self.handle_commands()
            if self.paused: return
            time.sleep(1)

    def run(self):
        log.info("=== Iniciando MonitorService v2.6 ===")
        self._clear_screen()
        print("🚀 Monitor HU (v2.6 - Application Logging)")
        try: self.bot.send("🚀 Monitor Iniciado (v2.6)")
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
                except Exception as e:
                    log.warning(f"Erro na verificação, tentando restaurar: {e}")
                    self.parser.ensure_logged()
                    self.vagas_atuais = self.parser.get_dropdown_options()

                snapshot = state.load_snapshot()
                vagas_anteriores = set(snapshot.get("especialidades", []))
                
                novas = self.vagas_atuais - vagas_anteriores
                removidas = vagas_anteriores - self.vagas_atuais

                if self.alvos:
                    novas_relevantes = {v for v in novas if any(alvo in v.upper() for alvo in self.alvos)}
                else:
                    novas_relevantes = {v for v in novas if v not in self.blacklist}

                if novas_relevantes:
                    log.info(f"VAGAS ENCONTRADAS: {novas_relevantes}")
                    
                    msg_tg = "🟢 <b>NOVAS VAGAS:</b>\n" + "\n".join(f"• {n}" for n in novas_relevantes)
                    self.bot.send(msg_tg)
                    
                    msg_email = "O Monitor HU encontrou as seguintes vagas disponíveis:\n\n" + "\n".join(f"- {n}" for n in novas_relevantes)
                    send_email("Monitor HU: Novas Vagas Abertas!", msg_email)

                    for n in novas_relevantes:
                        self._add_history("added", f"{n} abriu")
                
                for n in novas: self._log_to_csv("added", n)
                for r in removidas: 
                    self._log_to_csv("removed", r)
                    log.info(f"VAGA ENCERRADA: {r}")

                if removidas:
                    for r in removidas: self._add_history("removed", f"{r} fechou")

                if novas or removidas:
                    state.save_snapshot(list(self.vagas_atuais))
                
                minutos = scheduler.get_interval_minutes()
                self._render_dashboard(status="✅ Conectado", next_check=minutos)
                
                log.info(f"Check finalizado ({len(self.vagas_atuais)} vagas visíveis). Dormindo por {minutos} minutos.")
                self.smart_sleep(minutos)

        except KeyboardInterrupt:
            log.info("Execução interrompida manualmente pelo usuário.")
            print("\nParando...")
            try: self.bot.send("🛑 Desligado manualmente.")
            except: pass
        except Exception as e:
            log.error("ERRO FATAL NA EXECUÇÃO DO MONITOR", exc_info=True)
            error_trace = traceback.format_exc()
            try: self.bot.send(f"🔴 ERRO FATAL:\n<pre>{error_trace}</pre>")
            except: pass
            raise
        finally:
            log.info("Encerrando ciclo principal do MonitorService.")
            if self.parser: self.parser.close()

def main():
    MonitorService().run()

if __name__ == "__main__":
    main()