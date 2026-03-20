"""
wycena_ui.py — Interfejs do generowania Wyceny Zniczy.

Uruchomienie:
    python tools/wycena_ui.py

Przepływ:
    1. Pobiera listę grup ofert z ERP (grupy zawierające produkty CZNI)
    2. Użytkownik wybiera grupę oferty → nazwa klienta wypełniana automatycznie
    3. Użytkownik może zmienić nazwę klienta i ścieżkę pliku wynikowego
    4. Kliknięcie "Generuj" → wycena_generate.generate()
    5. Plik .xlsm otwiera się automatycznie
"""

import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient
from tools.wycena_generate import generate

_PROJECT_ROOT = Path(__file__).parent.parent

SQL_OFERTY = """
SELECT g.TwG_GIDNumer, g.TwG_Kod, g.TwG_Nazwa
FROM CDN.TwrGrupy g
WHERE EXISTS (
    SELECT 1 FROM CDN.TwrGrupy child
    WHERE child.TwG_GrONumer = g.TwG_GIDNumer
      AND child.TwG_GIDTyp = 16
      AND child.TwG_Kod LIKE 'CZNI%'
)
ORDER BY g.TwG_Nazwa
"""


# ---------------------------------------------------------------------------
# Pobieranie danych
# ---------------------------------------------------------------------------

def _fetch_oferty() -> list[tuple[int, str, str]]:
    """Zwraca listę (gid, kod, nazwa) grup ofert z produktami CZNI."""
    result = SqlClient().execute(SQL_OFERTY, inject_top=None)
    if not result["ok"]:
        raise RuntimeError(result["error"]["message"])
    return [(int(row[0]), str(row[1]), str(row[2])) for row in result["rows"]]


# ---------------------------------------------------------------------------
# Aplikacja
# ---------------------------------------------------------------------------

class WycenaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generator Wyceny Zniczy")
        self.resizable(False, False)
        self._oferty: list[tuple[int, str, str]] = []
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

        # Katalog oferty
        ttk.Label(frame, text="Katalog:").grid(row=1, column=0, sticky="w", **pad)
        self._oferta_var = tk.StringVar()
        self._oferta_cb = ttk.Combobox(frame, textvariable=self._oferta_var,
                                       state="readonly", width=36)
        self._oferta_cb.grid(row=1, column=1, columnspan=2, sticky="w", **pad)
        self._oferta_cb.bind("<<ComboboxSelected>>", self._on_oferta_change)

        # Plik wynikowy
        ttk.Label(frame, text="Plik wynikowy:").grid(row=2, column=0, sticky="w", **pad)
        self._output_var = tk.StringVar()
        self._output_entry = ttk.Entry(frame, textvariable=self._output_var, width=32)
        self._output_entry.grid(row=2, column=1, sticky="w", **pad)
        ttk.Button(frame, text="…", width=3,
                   command=self._browse_output).grid(row=2, column=2, padx=(0, 12))

        ttk.Separator(frame, orient="horizontal").grid(
            row=3, column=0, columnspan=3, sticky="ew", pady=8)

        self._gen_btn = ttk.Button(frame, text="Generuj", command=self._on_generate)
        self._gen_btn.grid(row=4, column=0, columnspan=3, pady=(4, 0))

        self._status_var = tk.StringVar(value="Ładowanie listy katalogów…")
        self._status_lbl = ttk.Label(frame, textvariable=self._status_var,
                                     foreground="gray", wraplength=420)
        self._status_lbl.grid(row=5, column=0, columnspan=3, pady=(10, 0), sticky="w")

        self._progress = ttk.Progressbar(frame, mode="indeterminate", length=420)
        self._progress.grid(row=6, column=0, columnspan=3, pady=(6, 0))
        self._progress.grid_remove()

    # ------------------------------------------------------------------
    # Logika
    # ------------------------------------------------------------------

    def _load_oferty(self):
        def worker():
            try:
                oferty = _fetch_oferty()
                self.after(0, lambda: self._on_oferty_loaded(oferty))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"Błąd połączenia: {e}", "red"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_oferty_loaded(self, oferty: list):
        self._oferty = oferty
        self._oferta_cb["values"] = [nazwa for _, _, nazwa in oferty]
        if oferty:
            self._oferta_cb.current(0)
            self._on_oferta_change()
        self._set_status("Wybierz katalog i kliknij Generuj.", "gray")

    def _on_oferta_change(self, _event=None):
        idx = self._oferta_cb.current()
        if idx < 0 or idx >= len(self._oferty):
            return
        _, _, nazwa = self._oferty[idx]
        safe = nazwa.replace("/", "-").replace("\\", "-")
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
        idx = self._oferta_cb.current()
        if idx < 0 or idx >= len(self._oferty):
            messagebox.showwarning("Brak wyboru", "Wybierz katalog oferty.")
            return
        output_str = self._output_var.get().strip()
        if not output_str:
            messagebox.showwarning("Brak ścieżki", "Podaj ścieżkę do pliku wynikowego.")
            return

        gid, _, nazwa = self._oferty[idx]
        self._start_generate(gid, nazwa, Path(output_str))

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
            except Exception as e:
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
