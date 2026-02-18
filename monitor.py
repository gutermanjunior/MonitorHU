import time
import logging
import yaml
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from scheduler import get_interval_minutes
from parser import HUParser
from state import load_snapshot, save_snapshot, update_heartbeat
from notifier import log_changes, notify_console

load_dotenv()

HU_USER = os.getenv("HU_USER")
HU_DATA = os.getenv("HU_DATA")

EMAIL_CONTA = os.getenv("EMAIL_CONTA")
EMAIL_SENHA = os.getenv("EMAIL_SENHA")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

console = Console()

logging.basicConfig(
    filename="logs/monitor.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def show_dashboard(last_check, added, removed):
    table = Table(title="Monitor HU-USP")

    table.add_column("Status")
    table.add_row("✅ Conectado")

    table.add_column("Última verificação")
    table.add_row(last_check)

    console.print(Panel(table))

    if added or removed:
        console.print(Panel(
            f"Adicionadas: {len(added)}\nRemovidas: {len(removed)}",
            title="Mudanças"
        ))


def main():
    config = load_config()
    machine_id = config["machine_id"]

    console.print("Iniciando monitor...\n")

    while True:
        try:
            update_heartbeat("running")

            parser = HUParser(headless=False)
            current = set(parser.fetch_especialidades())
            parser.close()

            previous_snapshot = load_snapshot()
            previous = set(previous_snapshot["especialidades"])

            added = current - previous
            removed = previous - current

            if added or removed:
                log_changes(machine_id, added, removed)
                notify_console(added, removed)
                save_snapshot(current)

            show_dashboard(time.strftime("%d/%m %H:%M"), added, removed)

            logging.info("Verificação concluída.")

            interval = get_interval_minutes()
            time.sleep(interval * 60)

        except Exception as e:
            logging.error(str(e))
            update_heartbeat("error")
            time.sleep(60)


if __name__ == "__main__":
    main()
