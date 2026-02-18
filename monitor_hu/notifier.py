import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Função Legada (Usada pelo Guardian) ---
def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    # Cria uma instância temporária apenas para enviar
    bot = TelegramBot()
    bot.send(message)


# --- Nova Classe Robusta ---
class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.offset = 0  # Para controlar mensagens já lidas

    def send(self, message: str, parse_mode="HTML"):
        if not self.token or not self.chat_id:
            print("Telegram não configurado.")
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        try:
            requests.post(url, data=payload, timeout=10)
        except Exception as e:
            print(f"Erro Telegram Send: {e}")

    def get_updates(self):
        """Busca novas mensagens (comandos) no Telegram"""
        if not self.token: return []

        url = f"https://api.telegram.org/bot{self.token}/getUpdates"
        params = {
            "offset": self.offset,
            "timeout": 1  # Long polling curto
        }

        try:
            resp = requests.get(url, params=params, timeout=3)
            data = resp.json()
            
            if not data.get("ok"): return []

            updates = data.get("result", [])
            valid_commands = []

            for update in updates:
                # Atualiza offset para não ler a mesma msg duas vezes
                self.offset = update["update_id"] + 1
                
                message = update.get("message", {})
                # Segurança: Só aceita comandos do SEU chat_id
                if str(message.get("chat", {}).get("id")) == str(self.chat_id):
                    text = message.get("text", "").strip()
                    if text.startswith("/"):
                        valid_commands.append(text)
            
            return valid_commands

        except Exception:
            return []