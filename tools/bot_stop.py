"""bot_stop.py — zatrzymuje bota Telegram przez PID zapisany w bot/bot.pid.

Użycie:
    python tools/bot_stop.py
"""

import os
import signal
import sys
from pathlib import Path

PID_FILE = Path(__file__).parent.parent / "bot" / "bot.pid"


def main() -> None:
    if not PID_FILE.exists():
        print(f"Brak pliku PID: {PID_FILE}")
        print("Bot nie jest uruchomiony lub nie zapisał PID.")
        sys.exit(1)

    pid_text = PID_FILE.read_text(encoding="utf-8").strip()
    if not pid_text.isdigit():
        print(f"Nieprawidłowa zawartość pliku PID: '{pid_text}'")
        sys.exit(1)

    pid = int(pid_text)

    try:
        if sys.platform == "win32":
            import subprocess
            result = subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"Bot (PID {pid}) zatrzymany.")
                PID_FILE.unlink(missing_ok=True)
            else:
                print(f"Nie udało się zatrzymać PID {pid}: {result.stderr.strip()}")
                sys.exit(1)
        else:
            os.kill(pid, signal.SIGTERM)
            print(f"Bot (PID {pid}) zatrzymany.")
            PID_FILE.unlink(missing_ok=True)
    except ProcessLookupError:
        print(f"Proces PID {pid} już nie istnieje.")
        PID_FILE.unlink(missing_ok=True)
    except PermissionError:
        print(f"Brak uprawnień do zatrzymania PID {pid}.")
        sys.exit(1)


if __name__ == "__main__":
    main()
