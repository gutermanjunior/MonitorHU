import os
import traceback
from dotenv import load_dotenv
from .parser import HUParser
from .notifier import send_telegram

load_dotenv()

HU_USER = os.getenv("HU_USER")
HU_DATA = os.getenv("HU_DATA")


def check_specialties(parser: HUParser):
    # MOCK — substitua pela sua lógica real
    return ["Cardiologia", "Dermatologia"]


def main():
    try:
        parser = HUParser(HU_USER, HU_DATA)
        parser.ensure_logged()

        novas = check_specialties(parser)

        if novas:
            msg = "🟢 NOVAS ESPECIALIDADES HU:\n"
            msg += "\n".join(f"• {n}" for n in novas)
            send_telegram(msg)

        parser.close()

    except Exception:
        error_trace = traceback.format_exc()
        send_telegram("🔴 ERRO NO MONITOR:\n\n" + error_trace)
        raise


if __name__ == "__main__":
    main()
