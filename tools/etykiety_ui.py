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

import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.etykiety_export import generate, _query_products, _query_products_from_codes, load_codes_from_excel
from tools.lib.sql_client import SqlClient

_PROJECT_ROOT = Path(__file__).parent.parent
SQL_GRUPY = _PROJECT_ROOT / "solutions/jas/etykiety_grupy.sql"
OUTPUT_DIR = _PROJECT_ROOT / "output"


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

        # Źródło danych
        ttk.Label(frame, text="Źródło:").grid(row=1, column=0, sticky="w", **pad)
        self._source_var = tk.StringVar(value="erp")
        src_frame = ttk.Frame(frame)
        src_frame.grid(row=1, column=1, sticky="w", **pad)
        ttk.Radiobutton(src_frame, text="Z ERP (rok / klient)",
                        variable=self._source_var, value="erp",
                        command=self._on_source_change).pack(side="left")
        ttk.Radiobutton(src_frame, text="Z pliku Excel",
                        variable=self._source_var, value="excel",
                        command=self._on_source_change).pack(side="left", padx=(16, 0))

        # -- Sekcja ERP --
        self._erp_frame = ttk.Frame(frame)
        self._erp_frame.grid(row=2, column=0, columnspan=3, sticky="ew")

        ttk.Label(self._erp_frame, text="Rok:").grid(row=0, column=0, sticky="w", **pad)
        self._rok_var = tk.StringVar()
        self._rok_cb = ttk.Combobox(self._erp_frame, textvariable=self._rok_var,
                                    state="readonly", width=20)
        self._rok_cb.grid(row=0, column=1, sticky="w", **pad)
        self._rok_cb.bind("<<ComboboxSelected>>", self._on_rok_change)

        ttk.Label(self._erp_frame, text="Klient:").grid(row=1, column=0, sticky="w", **pad)
        self._klient_var = tk.StringVar()
        self._klient_cb = ttk.Combobox(self._erp_frame, textvariable=self._klient_var,
                                        state="readonly", width=30)
        self._klient_cb.grid(row=1, column=1, sticky="w", **pad)
        self._klient_cb.bind("<<ComboboxSelected>>", lambda _: self._update_output_path())

        # -- Sekcja Excel --
        self._excel_frame = ttk.Frame(frame)
        self._excel_frame.grid(row=2, column=0, columnspan=3, sticky="ew")

        ttk.Label(self._excel_frame, text="Plik z kodami:").grid(row=0, column=0, sticky="w", **pad)
        self._excel_var = tk.StringVar()
        ttk.Entry(self._excel_frame, textvariable=self._excel_var, width=34).grid(
            row=0, column=1, sticky="w", **pad)
        ttk.Button(self._excel_frame, text="…", width=3,
                   command=self._browse_excel).grid(row=0, column=2, padx=(0, 12))

        self._excel_frame.grid_remove()  # domyślnie ukryta

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
            except Exception:
                self.after(0, lambda: self._set_status(f"Błąd połączenia: {e}", "red"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_grupy_loaded(self, grupy: dict):
        self._grupy = grupy
        self._rok_cb["values"] = list(grupy.keys())
        if grupy:
            self._rok_cb.current(0)
            self._on_rok_change()
        self._set_status("Wybierz rok i klienta, następnie kliknij Generuj.", "gray")

    def _on_source_change(self):
        if self._source_var.get() == "erp":
            self._excel_frame.grid_remove()
            self._erp_frame.grid()
            self._update_output_path()
        else:
            self._erp_frame.grid_remove()
            self._excel_frame.grid()
            excel = self._excel_var.get()
            if excel:
                name = Path(excel).stem
                self._output_var.set(str(OUTPUT_DIR / f"etykiety_{name}.docx"))

    def _browse_excel(self):
        path = filedialog.askopenfilename(
            title="Wybierz plik z listą kodów",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Wszystkie pliki", "*.*")],
        )
        if path:
            self._excel_var.set(path)
            name = Path(path).stem
            self._output_var.set(str(OUTPUT_DIR / f"etykiety_{name}.docx"))

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
        output_str = self._output_var.get().strip()
        if not output_str:
            messagebox.showwarning("Brak ścieżki", "Podaj ścieżkę do pliku wynikowego.")
            return

        if self._source_var.get() == "excel":
            excel_path = self._excel_var.get().strip()
            if not excel_path or not Path(excel_path).exists():
                messagebox.showerror("Błąd", "Plik z kodami nie istnieje.")
                return
            self._start_generate_excel(excel_path, Path(output_str))
        else:
            rok = self._rok_var.get()
            klient_kod = self._klient_var.get()
            if not rok or not klient_kod:
                messagebox.showwarning("Brak wyboru", "Wybierz rok i klienta.")
                return
            klienci = self._grupy.get(rok, [])
            klient_gid = next((gid for kod, gid in klienci if kod == klient_kod), None)
            if klient_gid is None:
                messagebox.showerror("Błąd", f"Nie znaleziono GID dla klienta: {klient_kod}")
                return
            self._start_generate(klient_gid, klient_kod, rok, Path(output_str))

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
            except Exception:
                self.after(0, lambda: self._finish(None, f"Błąd: {e}", error=True))

        threading.Thread(target=worker, daemon=True).start()

    def _start_generate_excel(self, excel_path: str, output_path: Path):
        self._gen_btn.state(["disabled"])
        self._progress.grid()
        self._progress.start(10)
        self._set_status("Wczytywanie kodów z pliku…", "gray")

        def worker():
            try:
                kody = load_codes_from_excel(excel_path)
                if not kody:
                    self.after(0, lambda: self._finish(None, "Brak kodów w pliku.", error=True))
                    return
                self.after(0, lambda: self._set_status(f"Pobieranie danych z ERP dla {len(kody)} kodów…", "gray"))
                products = _query_products_from_codes(kody)
                if not products:
                    self.after(0, lambda: self._finish(None, "Brak danych w ERP dla podanych kodów.", error=True))
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
