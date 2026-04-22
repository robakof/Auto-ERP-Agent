"""KSeF Config GUI — tkinter interface for editing .env settings.

    py tools/ksef_config_gui.py
    (or double-click ksef_ustawienia.bat)
"""
from __future__ import annotations

import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

# ---- .env reader/writer (preserves comments and order) -----------------------

def read_env(path: Path) -> tuple[list[str], dict[str, str]]:
    """Read .env file. Returns (raw_lines, key_value_dict)."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key, _, val = stripped.partition("=")
            values[key.strip()] = val.strip()
    return lines, values


def write_env(path: Path, lines: list[str], updates: dict[str, str]) -> None:
    """Write updated values back to .env, preserving structure."""
    updated_keys: set[str] = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, _, _ = stripped.partition("=")
            key = key.strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}")
                updated_keys.add(key)
                continue
        new_lines.append(line)
    # Append any new keys not already in file
    for key, val in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={val}")
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


# ---- field definitions -------------------------------------------------------

SECTIONS = [
    ("KSeF API", [
        ("KSEF_ENV", "Srodowisko (demo/test/prod)", "demo"),
        ("KSEF_BASE_URL", "URL API KSeF", ""),
        ("KSEF_NIP", "NIP", ""),
        ("KSEF_TOKEN", "Token autoryzacji", ""),
    ]),
    ("SMTP (email raporty)", [
        ("KSEF_SMTP_HOST", "Serwer SMTP", ""),
        ("KSEF_SMTP_PORT", "Port", "465"),
        ("KSEF_SMTP_USER", "Login SMTP", ""),
        ("KSEF_SMTP_PASS", "Haslo SMTP", ""),
        ("KSEF_SMTP_SSL", "SSL (true/false)", "true"),
    ]),
    ("Raport", [
        ("KSEF_REPORT_FROM", "Nadawca (email)", ""),
        ("KSEF_REPORT_TO", "Odbiorca (email)", ""),
        ("KSEF_REPORT_SUBJECT_PREFIX", "Prefix tematu", "[KSeF]"),
    ]),
    ("Daemon", [
        ("KSEF_DAEMON_INTERVAL", "Interval ticka (sekundy)", "900"),
        ("KSEF_DAEMON_TICK_TIMEOUT", "Tick timeout (sekundy)", "300"),
        ("KSEF_DAEMON_RATE_LIMIT", "Rate limit (dok/min, 0=wyl.)", "10"),
        ("KSEF_DAEMON_ERROR_THRESHOLD", "Prog bledow -> eskalacja (0=wyl.)", "3"),
    ]),
    ("Watchdog", [
        ("KSEF_WATCHDOG_MAX_RESTARTS", "Max restartow / godzine", "5"),
        ("KSEF_WATCHDOG_HEARTBEAT_STALE", "Heartbeat stale (sekundy)", "1200"),
    ]),
]

# Fields where input should be masked
_PASSWORD_FIELDS = {"KSEF_SMTP_PASS", "KSEF_TOKEN"}


_HELP_TEXT = """\
PROGRAMY KSeF — INSTRUKCJA
===========================

System sklada sie z trzech programow (plikow .bat).
Kazdy ma inne zadanie i inny sposob uruchamiania.


1. ksef_ustawienia.bat — USTAWIENIA (ten program)
--------------------------------------------------
Sluzy do zmiany konfiguracji. Otwierasz, zmieniasz
wartosci w zakladkach, klikasz "Zapisz", zamykasz.
Nie musi dzialac caly czas.

Po zmianie ustawien musisz zrestartowac daemon
(zamknij i otworz ponownie ksef_wyslij_demo.bat).


2. ksef_wyslij_demo.bat — DAEMON (wysylka faktur)
--------------------------------------------------
Glowny program — skanuje ERP co 15 minut i wysyla
zatwierdzone faktury do KSeF.

MUSI DZIALAC CALY CZAS. Uruchamiasz go i zostawiasz
otwarte okno terminala. Watchdog pilnuje czy daemon
nie zawisl — jesli tak, restartuje go automatycznie.

Zamkniecie okna = zatrzymanie daemon + watchdog.

Docelowo: zarejestruj jako zadanie w Windows Task
Scheduler z opcja "Uruchom niezaleznie od logowania"
— wtedy dziala nawet po wylogowaniu.

Parametry: odczytuje z pliku .env (zmieniane przez
ten program w zakladkach Daemon i Watchdog).


3. ksef_raport_dzienny.bat — RAPORT (email)
--------------------------------------------
Generuje podsumowanie dnia i wysyla na email.
Uruchamiany raz dziennie (np. o 13:30).

Najlepiej zarejestrowac w Windows Task Scheduler:
  - Wyzwalacz: codziennie, 13:30
  - Akcja: ksef_raport_dzienny.bat
  - "Uruchom niezaleznie od logowania"

Mozna tez uruchomic recznie. Przycisk "Wyslij raport
testowy" w tym programie robi dokladnie to samo.


TASK SCHEDULER — KONFIGURACJA
==============================
1. Otworz: Win+R > taskschd.msc > Enter
2. Akcje > Utworz zadanie
3. Ogolne:
   - Nazwa: "KSeF Daemon" (lub "KSeF Raport")
   - "Uruchom niezaleznie od tego, czy uzytkownik
     jest zalogowany"
   - "Uruchom z najwyzszymi uprawnieniami"
4. Wyzwalacze:
   - Daemon: "Przy uruchomieniu komputera"
   - Raport: "Codziennie" o 13:30
5. Akcje:
   - Program: sciezka do pliku .bat
   - Rozpocznij w: folder z projektem
6. Warunki: odznacz "Uruchom tylko gdy komputer
   jest podlaczony do zasilania"


"""


# ---- GUI ---------------------------------------------------------------------

class ConfigApp:
    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._root.title("KSeF — Ustawienia")
        self._root.resizable(True, True)
        self._entries: dict[str, tk.StringVar] = {}
        self._lines, self._values = read_env(_ENV_PATH)
        self._build_ui()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self._root)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        for section_name, fields in SECTIONS:
            frame = ttk.Frame(notebook, padding=10)
            notebook.add(frame, text=section_name)
            self._build_section(frame, fields)

        # Help tab
        help_frame = ttk.Frame(notebook, padding=10)
        notebook.add(help_frame, text="Instrukcja")
        self._build_help(help_frame)

        btn_frame = ttk.Frame(self._root, padding=5)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Zapisz", command=self._save).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Wyslij raport testowy",
                   command=self._test_email).pack(side="right", padx=5)

    def _build_section(self, parent: ttk.Frame, fields: list[tuple]) -> None:
        for i, (key, label, default) in enumerate(fields):
            ttk.Label(parent, text=label).grid(
                row=i, column=0, sticky="w", padx=(0, 10), pady=3,
            )
            var = tk.StringVar(value=self._values.get(key, default))
            self._entries[key] = var
            show = "*" if key in _PASSWORD_FIELDS else ""
            entry = ttk.Entry(parent, textvariable=var, width=60, show=show)
            entry.grid(row=i, column=1, sticky="ew", pady=3)
        parent.columnconfigure(1, weight=1)

    def _build_help(self, parent: ttk.Frame) -> None:
        text = tk.Text(parent, wrap="word", font=("Segoe UI", 10),
                       bg="#f5f5f5", relief="flat", padx=10, pady=10)
        text.pack(fill="both", expand=True)
        text.insert("1.0", _HELP_TEXT)
        text.config(state="disabled")

    def _save(self) -> None:
        updates = {key: var.get() for key, var in self._entries.items()}
        try:
            write_env(_ENV_PATH, self._lines, updates)
            # Reload lines after save
            self._lines, self._values = read_env(_ENV_PATH)
            messagebox.showinfo("Zapisano", f"Ustawienia zapisane do:\n{_ENV_PATH}")
        except Exception as e:
            messagebox.showerror("Blad", f"Nie udalo sie zapisac:\n{e}")

    def _test_email(self) -> None:
        """Send test report email using current settings."""
        # Save first
        self._save()
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(_PROJECT_ROOT / "tools" / "ksef_report.py"),
                 "--send-email", "--since", "30d"],
                capture_output=True, text=True, timeout=30,
                cwd=str(_PROJECT_ROOT),
            )
            if result.returncode == 0:
                messagebox.showinfo(
                    "Email wyslany",
                    f"Raport testowy wyslany.\n\n{result.stdout.strip()}",
                )
            else:
                messagebox.showerror(
                    "Blad wysylki",
                    f"Kod: {result.returncode}\n\n{result.stderr.strip()[:500]}",
                )
        except Exception as e:
            messagebox.showerror("Blad", f"Nie udalo sie wyslac:\n{e}")


def main() -> None:
    root = tk.Tk()
    # Set minimum size and center
    root.minsize(550, 400)
    root.geometry("650x500")
    ConfigApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
