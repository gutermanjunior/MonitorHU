import csv
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def log_changes(machine_id, added, removed):
    path = DATA_DIR / "history.csv"
    file_exists = path.exists()

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "machine_id", "action", "especialidade"])

        now = datetime.now().isoformat()

        for esp in added:
            writer.writerow([now, machine_id, "added", esp])

        for esp in removed:
            writer.writerow([now, machine_id, "removed", esp])


def notify_console(added, removed):
    if not added and not removed:
        return

    print("\nALTERAÇÃO DETECTADA\n")

    if added:
        print("Adicionadas:")
        for a in added:
            print(f" + {a}")

    if removed:
        print("Removidas:")
        for r in removed:
            print(f" - {r}")
