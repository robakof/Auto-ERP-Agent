"""
wycena_ui.py — Interfejs do generowania Wyceny Zniczy.

Uruchomienie:
    python tools/wycena_ui.py

Przepływ:
    1. Pobiera drzewo ofert z 10_OFERTY (GID=9139): Rok -> Klient
    2. Użytkownik wybiera rok → klient
    3. Kliknięcie "Generuj" → wycena_generate.generate()
    4. Plik .xlsm otwiera się automatycznie
"""

import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient
from tools.wycena_generate import generate

_PROJECT_ROOT = Path(__file__).parent.parent
OFERTY_ROOT_GID = 9139

SQL_OFERTY = """
SELECT
    rok.TwG_GIDNumer  AS rok_gid,
    rok.TwG_Nazwa     AS rok_nazwa,
    klient.TwG_GIDNumer AS klient_gid,
    klient.TwG_Nazwa    AS klient_nazwa
FROM CDN.TwrGrupy rok
JOIN CDN.TwrGrupy klient ON klient.TwG_GrONumer = rok.TwG_GIDNumer
WHERE rok.TwG_GrONumer = {root_gid}
  AND EXISTS (
      SELECT 1 FROM CDN.TwrGrupy child
      WHERE child.TwG_GrONumer = klient.TwG_GIDNumer
        AND child.TwG_GIDTyp = 16
        AND child.TwG_Kod LIKE 'CZNI%'
  )
ORDER BY rok.TwG_Nazwa DESC, klient.TwG_Nazwa
"""


# ---------------------------------------------------------------------------
# Pobieranie danych
# ---------------------------------------------------------------------------

def _fetch_oferty() -> dict[str, list[tuple[str, int]]]:
    """Zwraca {rok_nazwa: [(klient_nazwa, klient_gid), ...]}."""
    sql = SQL_OFERTY.format(root_gid=OFERTY_ROOT_GID)
    result = SqlClient().execute(sql, inject_top=None)
    if not result["ok"]:
        raise RuntimeError(result["error"]["message"])
    oferty: dict[str, list[tuple[str, int]]] = {}
    for rok_gid, rok_nazwa, klient_gid, klient_nazwa in result["rows"]:
        oferty.setdefault(rok_nazwa, []).append((klient_nazwa, int(klient_gid)))
    return oferty


# ---------------------------------------------------------------------------
# Aplikacja
# ---------------------------------------------------------------------------

class WycenaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generator Wyceny Zniczy")
        self.resizable(False, False)
        self._oferty: dict[str, list[tuple[str, int]]] = {}
        self._build_ui()
        self._load_oferty()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Generator Wyceny Zniczy",
                  font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 14), sticky="w")

        # Rok
        ttk.Label(frame, text="Rok:").grid(row=1, column=0, sticky="w", **pad)
        self._rok_var = tk.StringVar()
        self._rok_cb = ttk.Combobox(frame, textvariable=self._rok_var,
                                    state="readonly", width=20)
        self._rok_cb.grid(row=1, column=1, columnspan=2, sticky="w", **pad)
        self._rok_cb.bind("<<ComboboxSelected>>", self._on_rok_change)

        # Klient
        ttk.Label(frame, text="Klient:").grid(row=2, column=0, sticky="w", **pad)
        self._klient_var = tk.StringVar()
        self._klient_cb = ttk.Combobox(frame, textvariable=self._klient_var,
                                       state="readonly", width=30)
        self._klient_cb.grid(row=2, column=1, columnspan=2, sticky="w", **pad)
        self._klient_cb.bind("<<ComboboxSelected>>", self._on_klient_change)

        # Plik wynikowy
        ttk.Label(frame, text="Plik wynikowy:").grid(row=3, column=0, sticky="w", **pad)
        self._output_var = tk.StringVar()
        self._output_entry = ttk.Entry(frame, textvariable=self._output_var, width=32)
        self._output_entry.grid(row=3, column=1, sticky="w", **pad)
        ttk.Button(frame, text="…", width=3,
                   command=self._browse_output).grid(row=3, column=2, padx=(0, 12))

        ttk.Separator(frame, orient="horizontal").grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=8)

        self._gen_btn = ttk.Button(frame, text="Generuj", command=self._on_generate)
        self._gen_btn.grid(row=5, column=0, columnspan=3, pady=(4, 0))

        self._status_var = tk.StringVar(value="Ładowanie listy ofert…")
        self._status_lbl = ttk.Label(frame, textvariable=self._status_var,
                                     foreground="gray", wraplength=420)
        self._status_lbl.grid(row=6, column=0, columnspan=3, pady=(10, 0), sticky="w")

        self._progress = ttk.Progressbar(frame, mode="indeterminate", length=420)
        self._progress.grid(row=7, column=0, columnspan=3, pady=(6, 0))
        self._progress.grid_remove()

    # ------------------------------------------------------------------
    # Logika
    # ------------------------------------------------------------------

    def _load_oferty(self):
        def worker():
            try:
                oferty = _fetch_oferty()
                self.after(0, lambda: self._on_oferty_loaded(oferty))
            except Exception:
                self.after(0, lambda: self._set_status(f"Błąd połączenia: {e}", "red"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_oferty_loaded(self, oferty: dict):
        self._oferty = oferty
        self._rok_cb["values"] = list(oferty.keys())
        if oferty:
            self._rok_cb.current(0)
            self._on_rok_change()
        self._set_status("Wybierz rok i klienta, następnie kliknij Generuj.", "gray")

    def _on_rok_change(self, _event=None):
        rok = self._rok_var.get()
        klienci = self._oferty.get(rok, [])
        self._klient_cb["values"] = [k for k, _ in klienci]
        if klienci:
            self._klient_cb.current(0)
        self._update_output_path()

    def _on_klient_change(self, _event=None):
        self._update_output_path()

    def _update_output_path(self):
        klient = self._klient_var.get()
        if klient:
            safe = klient.replace("/", "-").replace("\\", "-")
            self._output_var.set(str(_PROJECT_ROOT / f"Wycena {safe}.xlsm"))

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsm",
            filetypes=[("Excel z makrami", "*.xlsm")],
            initialfile=Path(self._output_var.get()).name if self._output_var.get() else "",
        )
        if path:
            self._output_var.set(path)

    def _on_generate(self):
        rok = self._rok_var.get()
        klient_nazwa = self._klient_var.get()
        if not rok or not klient_nazwa:
            messagebox.showwarning("Brak wyboru", "Wybierz rok i klienta.")
            return
        output_str = self._output_var.get().strip()
        if not output_str:
            messagebox.showwarning("Brak ścieżki", "Podaj ścieżkę do pliku wynikowego.")
            return

        klienci = self._oferty.get(rok, [])
        klient_gid = next((gid for nazwa, gid in klienci if nazwa == klient_nazwa), None)
        if klient_gid is None:
            messagebox.showerror("Błąd", f"Nie znaleziono GID dla: {klient_nazwa}")
            return

        self._start_generate(klient_gid, klient_nazwa, Path(output_str))

    def _start_generate(self, offer_group_id: int, client_name: str, output: Path):
        self._gen_btn.state(["disabled"])
        self._progress.grid()
        self._progress.start(10)
        self._set_status(f"Generowanie wyceny dla {client_name}…", "gray")

        def worker():
            try:
                result = generate(
                    offer_group_id=offer_group_id,
                    client_name=client_name,
                    template=_PROJECT_ROOT / "Wycena 2026 Otorowo Szablon.xlsm",
                    output=output,
                )
                self.after(0, lambda: self._finish(result, f"OK — {result.name}"))
            except Exception:
                self.after(0, lambda: self._finish(None, f"Błąd: {e}", error=True))

        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, output: Path | None, msg: str, error: bool = False):
        self._progress.stop()
        self._progress.grid_remove()
        self._gen_btn.state(["!disabled"])
        self._set_status(msg, "red" if error else "#1a7a1a")
        if output and output.exists():
            subprocess.Popen(["start", "", str(output)], shell=True)

    def _set_status(self, msg: str, color: str = "gray"):
        self._status_var.set(msg)
        self._status_lbl.configure(foreground=color)


# ---------------------------------------------------------------------------
# Uruchomienie
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = WycenaApp()
    app.mainloop()
