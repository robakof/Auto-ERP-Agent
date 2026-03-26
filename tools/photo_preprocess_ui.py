"""
photo_preprocess_ui.py — UI do wsadowego skalowania zdjęć katalogowych.

Przepływ:
    1. Użytkownik wybiera katalog wejściowy i wyjściowy.
    2. Podgląd listy plików PNG do przetworzenia.
    3. Kliknięcie "Przetwórz" → batch_process w wątku tła.
    4. Pasek postępu + status na bieżąco.
"""

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.photo_preprocess import batch_process


class PhotoPreprocessApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Obróbka zdjęć katalogowych")
        self.resizable(False, False)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        pad = {"padx": 12, "pady": 5}
        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Obróbka zdjęć katalogowych",
                  font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 12), sticky="w")

        # Katalog wejściowy
        ttk.Label(frame, text="Katalog wejściowy:").grid(row=1, column=0, sticky="w", **pad)
        self._in_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._in_var, width=40).grid(row=1, column=1, sticky="w", **pad)
        ttk.Button(frame, text="…", width=3,
                   command=lambda: self._pick_dir(self._in_var, self._refresh_list)
                   ).grid(row=1, column=2, padx=(0, 12))

        # Katalog wyjściowy
        ttk.Label(frame, text="Katalog wyjściowy:").grid(row=2, column=0, sticky="w", **pad)
        self._out_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._out_var, width=40).grid(row=2, column=1, sticky="w", **pad)
        ttk.Button(frame, text="…", width=3,
                   command=lambda: self._pick_dir(self._out_var)
                   ).grid(row=2, column=2, padx=(0, 12))

        # Lista plików
        ttk.Label(frame, text="Pliki do przetworzenia:").grid(
            row=3, column=0, columnspan=3, sticky="w", padx=12, pady=(8, 2))
        self._listbox = tk.Listbox(frame, height=8, width=55, selectmode="none")
        self._listbox.grid(row=4, column=0, columnspan=3, padx=12, pady=(0, 8))

        ttk.Separator(frame, orient="horizontal").grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=6)

        self._btn = ttk.Button(frame, text="Przetwórz", command=self._on_process)
        self._btn.grid(row=6, column=0, columnspan=3, pady=(2, 0))

        self._status_var = tk.StringVar(value="Wybierz katalogi i kliknij Przetwórz.")
        self._status_lbl = ttk.Label(frame, textvariable=self._status_var,
                                     foreground="gray", wraplength=460)
        self._status_lbl.grid(row=7, column=0, columnspan=3, pady=(8, 0), sticky="w")

        self._progress = ttk.Progressbar(frame, mode="determinate", length=460)
        self._progress.grid(row=8, column=0, columnspan=3, pady=(4, 0))
        self._progress.grid_remove()

    # ------------------------------------------------------------------
    # Logika
    # ------------------------------------------------------------------

    def _pick_dir(self, var: tk.StringVar, callback=None):
        path = filedialog.askdirectory()
        if path:
            var.set(path)
            if callback:
                callback()

    def _refresh_list(self):
        self._listbox.delete(0, tk.END)
        d = Path(self._in_var.get())
        if d.is_dir():
            files = sorted(d.glob("*.png")) + sorted(d.glob("*.PNG"))
            for f in files:
                self._listbox.insert(tk.END, f.name)
            self._set_status(f"{len(files)} plików PNG znalezionych.", "gray")

    def _on_process(self):
        in_dir = Path(self._in_var.get().strip())
        out_dir = Path(self._out_var.get().strip())

        if not in_dir.is_dir():
            messagebox.showwarning("Brak katalogu", "Podaj poprawny katalog wejściowy.")
            return
        if not self._out_var.get().strip():
            messagebox.showwarning("Brak katalogu", "Podaj katalog wyjściowy.")
            return

        self._btn.state(["disabled"])
        self._progress.grid()
        self._progress["value"] = 0
        self._set_status("Pobieranie wysokości z ERP…", "gray")

        def worker():
            def on_progress(current, total, fname):
                pct = round(current / total * 100)
                self.after(0, lambda: self._on_tick(current, total, fname, pct))

            try:
                result = batch_process(in_dir, out_dir, progress_cb=on_progress)
                self.after(0, lambda: self._on_done(result))
            except Exception as e:
                self.after(0, lambda: self._on_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_tick(self, current, total, fname, pct):
        self._progress["value"] = pct
        self._set_status(f"[{current}/{total}] {fname}", "gray")

    def _on_done(self, result):
        self._progress["value"] = 100
        self._btn.state(["!disabled"])
        n = result["processed"]
        skipped = result["skipped"]
        errors = result["errors"]
        msg = f"Gotowe: {n} przetworzone"
        if skipped:
            msg += f", {len(skipped)} pominięte (brak w ERP: {', '.join(skipped)})"
        if errors:
            msg += f", {len(errors)} błędy: {'; '.join(e['file'] for e in errors)}"
        color = "red" if errors else "#1a7a1a"
        self._set_status(msg, color)

    def _on_error(self, msg):
        self._progress.grid_remove()
        self._btn.state(["!disabled"])
        self._set_status(f"Błąd: {msg}", "red")

    def _set_status(self, msg: str, color: str = "gray"):
        self._status_var.set(msg)
        self._status_lbl.configure(foreground=color)


# ---------------------------------------------------------------------------
# Uruchomienie
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    PhotoPreprocessApp().mainloop()
