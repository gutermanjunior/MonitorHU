import subprocess
import sys
import time
from datetime import datetime, timedelta
from .notifier import send_telegram

MAX_CRASHES = 5
CRASH_WINDOW_SECONDS = 60
INITIAL_BACKOFF = 5
MAX_BACKOFF = 300


def start_monitor():
    return subprocess.Popen(
        [sys.executable, "-m", "monitor_hu.monitor"]
    )


def main():
    print("🛡️ Guardian iniciado.")
    send_telegram("🟢 Guardian iniciado.")

    crash_times = []
    backoff = INITIAL_BACKOFF

    monitor = start_monitor()

    try:
        while True:
            retcode = monitor.poll()

            if retcode is not None:
                now = datetime.now()
                crash_times.append(now)

                crash_times = [
                    t for t in crash_times
                    if (now - t).total_seconds() <= CRASH_WINDOW_SECONDS
                ]

                if len(crash_times) >= MAX_CRASHES:
                    send_telegram(
                        "🚨 ALERTA CRÍTICO 🚨\n"
                        "Crash loop detectado. Monitor interrompido."
                    )
                    break

                send_telegram(
                    f"🔴 Monitor caiu. Reiniciando em {backoff}s..."
                )

                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF)
                monitor = start_monitor()

            time.sleep(2)

    except KeyboardInterrupt:
        send_telegram("🛑 Guardian encerrado manualmente.")
        monitor.terminate()
        monitor.wait()


if __name__ == "__main__":
    main()
