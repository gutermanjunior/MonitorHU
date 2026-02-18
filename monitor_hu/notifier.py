import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Função Legada (Guardian) ---
def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        TelegramBot().send(message)
    except: pass

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.offset = 0

    def send(self, message: str, parse_mode="HTML"):
        if not self.token: return
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message, "parse_mode": parse_mode}
        try: requests.post(url, data=payload, timeout=10)
        except Exception as e: print(f"Erro Telegram Send: {e}")

    def send_photo(self, caption: str, file_path: str):
        """Envia imagens (para o comando /print e /relatorio)"""
        if not self.token: return
        url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        try:
            with open(file_path, 'rb') as f:
                requests.post(
                    url, 
                    data={'chat_id': self.chat_id, 'caption': caption}, 
                    files={'photo': f},
                    timeout=20
                )
        except Exception as e: print(f"Erro Telegram Photo: {e}")

    def get_updates(self):
        if not self.token: return []
        url = f"https://api.telegram.org/bot{self.token}/getUpdates"
        params = {"offset": self.offset, "timeout": 1}
        try:
            resp = requests.get(url, params=params, timeout=3)
            data = resp.json()
            if not data.get("ok"): return []
            
            valid_commands = []
            for update in data.get("result", []):
                self.offset = update["update_id"] + 1
                msg = update.get("message", {})
                if str(msg.get("chat", {}).get("id")) == str(self.chat_id):
                    text = msg.get("text", "").strip()
                    if text.startswith("/"):
                        valid_commands.append(text)
            return valid_commands
        except: return []