"""
etykiety_ui.py — Interfejs do generowania etykiet wysyłkowych Word.

Uruchomienie:
    python tools/etykiety_ui.py

Przepływ:
    1. Pobiera listę rok/klient z etykiety_grupy.sql
    2. Użytkownik wybiera rok → klient
    3. Kliknięcie "Generuj" → etykiety_export.generate()
    4. Plik .docx otwiera się automatycznie
"""

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.etykiety_export import generate, _query_products
from tools.lib.sql_client import SqlClient

SQL_GRUPY = Path("solutions/jas/etykiety_grupy.sql")
OUTPUT_DIR = Path("output")


# ---------------------------------------------------------------------------
# Pobieranie danych
# ---------------------------------------------------------------------------

def _fetch_grupy() -> dict[str, list[tuple[str, int]]]:
    """
    Zwraca słownik: {rok_kod: [(klient_kod, klient_gid), ...]}.
    Sortuje lata malejąco, klientów rosnąco.
    """
    sql = SQL_GRUPY.read_text(encoding="utf-8")
    result = SqlClient().execute(sql, inject_top=None)
    if not result["ok"]:
        raise RuntimeError(result["error"]["message"])

    grupy: dict[str, list[tuple[str, int]]] = {}
    for row in result["rows"]:
        rok_gid, rok_kod, klient_gid, klient_kod = row
        grupy.setdefault(rok_kod, []).append((klient_kod, int(klient_gid)))

    for rok in grupy:
        grupy[rok].sort(key=lambda x: x[0])

    return dict(sorted(grupy.items(), reverse=True))


# ---------------------------------------------------------------------------
# Aplikacja
# ---------------------------------------------------------------------------

class EtykietyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Etykiety wysyłkowe")
        self.resizable(False, False)
        self._grupy: dict[str, list[tuple[str, int]]] = {}
        self._build_ui()
        self._load_grupy()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        # Nagłówek
        ttk.Label(frame, text="Generuj etykiety wysyłkowe",
                  font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 14), sticky="w")

        # Rok
        ttk.Label(frame, text="Rok:").grid(row=1, column=0, sticky="w", **pad)
        self._rok_var = tk.StringVar()
        self._rok_cb = ttk.Combobox(frame, textvariable=self._rok_var,
                                    state="readonly", width=20)
        self._rok_cb.grid(row=1, column=1, sticky="w", **pad)
        self._rok_cb.bind("<<ComboboxSelected>>", self._on_rok_change)

        # Klient
        ttk.Label(frame, text="Klient:").grid(row=2, column=0, sticky="w", **pad)
        self._klient_var = tk.StringVar()
        self._klient_cb = ttk.Combobox(frame, textvariable=self._klient_var,
                                        state="readonly", width=30)
        self._klient_cb.grid(row=2, column=1, sticky="w", **pad)

        # Plik wynikowy
        ttk.Label(frame, text="Plik wynikowy:").grid(row=3, column=0, sticky="w", **pad)
        self._output_var = tk.StringVar()
        self._output_entry = ttk.Entry(frame, textvariable=self._output_var, width=34)
        self._output_entry.grid(row=3, column=1, sticky="w", **pad)
        ttk.Button(frame, text="…", width=3,
                   command=self._browse_output).grid(row=3, column=2, padx=(0, 12))

        # Separator
        ttk.Separator(frame, orient="horizontal").grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=8)

        # Przycisk generuj
        self._gen_btn = ttk.Button(frame, text="Generuj",
                                   command=self._on_generate)
        self._gen_btn.grid(row=5, column=0, columnspan=3, pady=(4, 0))

        # Status
        self._status_var = tk.StringVar(value="Ładowanie listy klientów…")
        self._status_lbl = ttk.Label(frame, textvariable=self._status_var,
                                     foreground="gray", wraplength=400)
        self._status_lbl.grid(row=6, column=0, columnspan=3,
                               pady=(10, 0), sticky="w")

        # Pasek postępu
        self._progress = ttk.Progressbar(frame, mode="indeterminate", length=400)
        self._progress.grid(row=7, column=0, columnspan=3, pady=(6, 0))
        self._progress.grid_remove()

    # ------------------------------------------------------------------
    # Logika
    # ------------------------------------------------------------------

    def _load_grupy(self):
        """Pobiera grupy w tle, żeby nie blokować UI."""
        def worker():
            try:
                grupy = _fetch_grupy()
                self.after(0, lambda: self._on_grupy_loaded(grupy))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"Błąd połączenia: {e}", "red"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_grupy_loaded(self, grupy: dict):
        self._grupy = grupy
        self._rok_cb["values"] = list(grupy.keys())
        if grupy:
            self._rok_cb.current(0)
            self._on_rok_change()
        self._set_status("Wybierz rok i klienta, następnie kliknij Generuj.", "gray")

    def _on_rok_change(self, _event=None):
        rok = self._rok_var.get()
        klienci = self._grupy.get(rok, [])
        self._klient_cb["values"] = [k for k, _ in klienci]
        if klienci:
            self._klient_cb.current(0)
        self._update_output_path()

    def _update_output_path(self):
        rok = self._rok_var.get()
        klient = self._klient_var.get().replace(" ", "_")
        if rok and klient:
            path = OUTPUT_DIR / f"etykiety_{rok}_{klient}.docx"
            self._output_var.set(str(path))

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word", "*.docx")],
            initialfile=Path(self._output_var.get()).name if self._output_var.get() else "",
        )
        if path:
            self._output_var.set(path)

    def _on_generate(self):
        rok = self._rok_var.get()
        klient_kod = self._klient_var.get()
        output_str = self._output_var.get().strip()

        if not rok or not klient_kod:
            messagebox.showwarning("Brak wyboru", "Wybierz rok i klienta.")
            return
        if not output_str:
            messagebox.showwarning("Brak ścieżki", "Podaj ścieżkę do pliku wynikowego.")
            return

        klienci = self._grupy.get(rok, [])
        klient_gid = next((gid for kod, gid in klienci if kod == klient_kod), None)
        if klient_gid is None:
            messagebox.showerror("Błąd", f"Nie znaleziono GID dla klienta: {klient_kod}")
            return

        output_path = Path(output_str)
        self._start_generate(klient_gid, klient_kod, rok, output_path)

    def _start_generate(self, klient_gid: int, klient_kod: str, rok: str, output_path: Path):
        self._gen_btn.state(["disabled"])
        self._progress.grid()
        self._progress.start(10)
        self._set_status(f"Pobieranie danych dla {klient_kod} {rok}…", "gray")

        def worker():
            try:
                products = _query_products(klient_gid)
                if not products:
                    self.after(0, lambda: self._finish(
                        None, f"Brak produktów dla {klient_kod} {rok}.", error=True))
                    return
                generate(products, output_path)
                self.after(0, lambda: self._finish(output_path,
                    f"OK — {len(products)} etykiet → {output_path.name}"))
            except Exception as e:
                self.after(0, lambda: self._finish(None, f"Błąd: {e}", error=True))

        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, output_path: Path | None, msg: str, error: bool = False):
        self._progress.stop()
        self._progress.grid_remove()
        self._gen_btn.state(["!disabled"])
        color = "red" if error else "#1a7a1a"
        self._set_status(msg, color)

        if output_path and output_path.exists():
            import subprocess
            subprocess.Popen(["start", "", str(output_path)], shell=True)

    def _set_status(self, msg: str, color: str = "gray"):
        self._status_var.set(msg)
        self._status_lbl.configure(foreground=color)


# ---------------------------------------------------------------------------
# Uruchomienie
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = EtykietyApp()
    app.mainloop()
