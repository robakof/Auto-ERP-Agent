"""
offer_ui.py — Interfejs generatora ofert katalogowych PDF.

Uruchomienie:
    python tools/offer_ui.py
"""

import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.offer_data import load_products
from tools.offer_pdf import generate_pdf

_PROJECT_ROOT = Path(__file__).parent.parent
_DEFAULT_INPUT = str(_PROJECT_ROOT / "documents" / "Wzory plików" / "OFerta katalogowa.xlsx")

LANGUAGES = {"Polski": "pl", "English": "en", "Română": "ro"}

# Brandbook CEiM
COLOR_ORANGE = "#FAA400"
COLOR_BLACK = "#1A1A1A"
COLOR_GRAY = "#6B6B6B"


class OfferApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generator Oferty Katalogowej — CEiM")
        self.resizable(False, False)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        # Pasek nagłówkowy w kolorze firmowym
        header = tk.Frame(self, bg=COLOR_ORANGE, height=6)
        header.pack(fill="x")

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        # Tytuł
        title_frame = tk.Frame(frame, bg="white")
        title_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

        tk.Label(
            title_frame,
            text="Generator Oferty Katalogowej",
            font=("Garamond", 15, "bold"),
            fg=COLOR_BLACK, bg="white",
        ).pack(side="left")

        tk.Label(
            title_frame,
            text="  CEiM",
            font=("Garamond", 15, "bold"),
            fg=COLOR_ORANGE, bg="white",
        ).pack(side="left")

        # Plik wejściowy
        ttk.Label(frame, text="Plik produktów:").grid(row=1, column=0, sticky="w", **pad)
        self._input_var = tk.StringVar(value=_DEFAULT_INPUT)
        ttk.Entry(frame, textvariable=self._input_var, width=38).grid(
            row=1, column=1, sticky="w", **pad)
        ttk.Button(frame, text="…", width=3,
                   command=self._browse_input).grid(row=1, column=2, padx=(0, 12))

        # Plik wyjściowy
        ttk.Label(frame, text="Zapisz PDF jako:").grid(row=2, column=0, sticky="w", **pad)
        self._output_var = tk.StringVar(value=str(_PROJECT_ROOT / "output" / "oferta_katalogowa.pdf"))
        ttk.Entry(frame, textvariable=self._output_var, width=38).grid(
            row=2, column=1, sticky="w", **pad)
        ttk.Button(frame, text="…", width=3,
                   command=self._browse_output).grid(row=2, column=2, padx=(0, 12))

        # Język
        ttk.Label(frame, text="Język:").grid(row=3, column=0, sticky="w", **pad)
        self._lang_var = tk.StringVar(value="Polski")
        lang_cb = ttk.Combobox(
            frame, textvariable=self._lang_var,
            values=list(LANGUAGES.keys()),
            state="readonly", width=16,
        )
        lang_cb.grid(row=3, column=1, sticky="w", **pad)

        ttk.Separator(frame, orient="horizontal").grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=10)

        # Przycisk Generuj — pomarańczowy akcent
        self._gen_btn = tk.Button(
            frame,
            text="  Generuj PDF  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_ORANGE, fg="white",
            activebackground="#e09400", activeforeground="white",
            relief="flat", cursor="hand2",
            command=self._on_generate,
        )
        self._gen_btn.grid(row=5, column=0, columnspan=3, pady=(4, 0))

        # Status
        self._status_var = tk.StringVar(value="Wybierz plik i kliknij Generuj.")
        self._status_lbl = ttk.Label(
            frame, textvariable=self._status_var,
            foreground=COLOR_GRAY, wraplength=440,
        )
        self._status_lbl.grid(row=6, column=0, columnspan=3, pady=(10, 0), sticky="w")

        # Pasek postępu
        self._progress = ttk.Progressbar(frame, mode="indeterminate", length=440)
        self._progress.grid(row=7, column=0, columnspan=3, pady=(6, 4))
        self._progress.grid_remove()

    # ------------------------------------------------------------------
    # Logika
    # ------------------------------------------------------------------

    def _browse_input(self):
        path = filedialog.askopenfilename(
            title="Wybierz plik z listą produktów",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Wszystkie pliki", "*.*")],
            initialfile=Path(self._input_var.get()).name if self._input_var.get() else "",
        )
        if path:
            self._input_var.set(path)

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Zapisz ofertę jako",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=Path(self._output_var.get()).name if self._output_var.get() else "oferta.pdf",
        )
        if path:
            self._output_var.set(path)

    def _set_status(self, msg: str, color: str = COLOR_GRAY):
        self._status_var.set(msg)
        self._status_lbl.configure(foreground=color)

    def _on_generate(self):
        input_path = self._input_var.get().strip()
        output_path = self._output_var.get().strip()
        lang = LANGUAGES.get(self._lang_var.get(), "pl")

        if not input_path or not Path(input_path).exists():
            messagebox.showerror("Błąd", "Plik produktów nie istnieje.")
            return
        if not output_path:
            messagebox.showerror("Błąd", "Podaj ścieżkę do pliku wynikowego.")
            return

        self._gen_btn.configure(state="disabled")
        self._progress.grid()
        self._progress.start(10)
        self._set_status("Generowanie…", COLOR_GRAY)

        def worker():
            try:
                products = load_products(input_path, lang=lang)
                generate_pdf(products, output_path, lang=lang)
                self.after(0, lambda: self._on_done(output_path))
            except Exception:
                self.after(0, lambda: self._on_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_done(self, output_path: str):
        self._progress.stop()
        self._progress.grid_remove()
        self._gen_btn.configure(state="normal")
        self._set_status(f"Gotowe: {output_path}", COLOR_ORANGE)

        if messagebox.askyesno("Gotowe", "PDF wygenerowany.\n\nCzy otworzyć plik?"):
            import subprocess
            subprocess.Popen(["start", "", output_path], shell=True)

    def _on_error(self, error: str):
        self._progress.stop()
        self._progress.grid_remove()
        self._gen_btn.configure(state="normal")
        self._set_status(f"Błąd: {error}", "red")
        messagebox.showerror("Błąd generowania", error)


if __name__ == "__main__":
    app = OfferApp()
    app.mainloop()
