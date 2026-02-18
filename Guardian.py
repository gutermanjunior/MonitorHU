import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import yaml
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DATA_DIR = Path("data")


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def read_heartbeat():
    path = DATA_DIR / "heartbeat.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def main():
    config = load_config()
    repeat_minutes = config["guardian"]["error_repeat_minutes"]

    last_notification = None

    while True:
        hb = read_heartbeat()

        if hb:
            last_run = datetime.fromisoformat(hb["last_run"])
            status = hb["status"]

            if status == "error":
                now = datetime.now()

                if (
                    not last_notification
                    or now - last_notification > timedelta(minutes=repeat_minutes)
                ):
                    print("⚠️ Monitor com erro persistente.")
                    last_notification = now

        time.sleep(60)


if __name__ == "__main__":
    main()
