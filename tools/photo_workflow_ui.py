"""
photo_workflow_ui.py — Pełny interfejs obróbki zdjęć katalogowych.

Przepływ:
    Krok 1: Kopiuj Prompt A do ChatGPT, przetwórz zdjęcia ręcznie.
    Krok 2: Wskaż foldery (oryginały / przetworzone / katalogowe).
    Krok 3: Kliknij "Skaluj" — batch skalowanie Pillow wg wysokości ERP.
"""

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
import sys
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.photo_preprocess import batch_process

_PROJECT_ROOT = Path(__file__).parent.parent
_PROMPT_MD = _PROJECT_ROOT / "documents/prompt_engineer/PROMPT_PHOTO_PROCESSING.md"


# ---------------------------------------------------------------------------
# Parser prompta
# ---------------------------------------------------------------------------

def _load_prompt_a(md_path: Path) -> str:
    """Wyciąga treść Prompta A (pierwsze blok ``` po nagłówku Prompt A)."""
    text = md_path.read_text(encoding="utf-8")
    # Znajdź sekcję Prompt A
    m = re.search(r"## Prompt A[^\n]*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if not m:
        return "(nie znaleziono Prompta A)"
    section = m.group(1)
    # Wyciągnij pierwszy blok kodu
    block = re.search(r"```\n(.*?)```", section, re.DOTALL)
    return block.group(1).strip() if block else section.strip()


# ---------------------------------------------------------------------------
# Aplikacja
# ---------------------------------------------------------------------------

class PhotoWorkflowApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Obróbka zdjęć katalogowych")
        self.resizable(False, False)
        self._prompt_text = _load_prompt_a(_PROMPT_MD)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Obróbka zdjęć katalogowych",
                  font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 12), sticky="w")

        self._build_step1(frame, start_row=1)
        ttk.Separator(frame, orient="horizontal").grid(
            row=10, column=0, columnspan=3, sticky="ew", pady=10)
        self._build_step2(frame, start_row=11)
        ttk.Separator(frame, orient="horizontal").grid(
            row=20, column=0, columnspan=3, sticky="ew", pady=10)
        self._build_step3(frame, start_row=21)

    def _build_step1(self, frame, start_row):
        r = start_row
        ttk.Label(frame, text="Krok 1 — Prompt GPT-4o",
                  font=("Segoe UI", 10, "bold")).grid(
            row=r, column=0, columnspan=3, sticky="w", padx=12)

        ttk.Label(frame, text="Skopiuj prompt do ChatGPT i przetwórz każde zdjęcie.",
                  foreground="gray").grid(
            row=r+1, column=0, columnspan=3, sticky="w", padx=12, pady=(2, 6))

        self._prompt_box = tk.Text(frame, height=6, width=62, wrap="word",
                                   state="normal", font=("Consolas", 9))
        self._prompt_box.grid(row=r+2, column=0, columnspan=3, padx=12)
        self._prompt_box.insert("1.0", self._prompt_text)
        self._prompt_box.configure(state="disabled")

        ttk.Button(frame, text="Kopiuj do schowka",
                   command=self._copy_prompt).grid(
            row=r+3, column=0, columnspan=3, pady=(6, 0))

    def _build_step2(self, frame, start_row):
        r = start_row
        pad = {"padx": 12, "pady": 4}
        ttk.Label(frame, text="Krok 2 — Foldery",
                  font=("Segoe UI", 10, "bold")).grid(
            row=r, column=0, columnspan=3, sticky="w", padx=12)

        self._in_var  = tk.StringVar()
        self._proc_var = tk.StringVar()
        self._out_var  = tk.StringVar()

        for i, (label, var, cb) in enumerate([
            ("Oryginały (źródłowe):",   self._in_var,   None),
            ("Przetworzone (GPT-4o):",  self._proc_var, self._refresh_list),
            ("Katalogowe (output):",    self._out_var,  None),
        ]):
            ttk.Label(frame, text=label).grid(row=r+1+i, column=0, sticky="w", **pad)
            ttk.Entry(frame, textvariable=var, width=40).grid(
                row=r+1+i, column=1, sticky="w", **pad)
            _cb = cb
            ttk.Button(frame, text="…", width=3,
                       command=lambda v=var, c=_cb: self._pick_dir(v, c)).grid(
                row=r+1+i, column=2, padx=(0, 12))

        ttk.Label(frame, text="Pliki PNG do skalowania:").grid(
            row=r+4, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 2))
        self._listbox = tk.Listbox(frame, height=6, width=62, selectmode="none")
        self._listbox.grid(row=r+5, column=0, columnspan=3, padx=12)

    def _build_step3(self, frame, start_row):
        r = start_row
        ttk.Label(frame, text="Krok 3 — Skalowanie",
                  font=("Segoe UI", 10, "bold")).grid(
            row=r, column=0, columnspan=3, sticky="w", padx=12)

        self._btn = ttk.Button(frame, text="Skaluj", command=self._on_process)
        self._btn.grid(row=r+1, column=0, columnspan=3, pady=(8, 0))

        self._status_var = tk.StringVar(value="Wskaż foldery i kliknij Skaluj.")
        self._status_lbl = ttk.Label(frame, textvariable=self._status_var,
                                     foreground="gray", wraplength=480)
        self._status_lbl.grid(row=r+2, column=0, columnspan=3,
                               pady=(8, 0), sticky="w", padx=12)

        self._progress = ttk.Progressbar(frame, mode="determinate", length=480)
        self._progress.grid(row=r+3, column=0, columnspan=3, padx=12, pady=(4, 8))
        self._progress.grid_remove()

    # ------------------------------------------------------------------
    # Logika
    # ------------------------------------------------------------------

    def _copy_prompt(self):
        self.clipboard_clear()
        self.clipboard_append(self._prompt_text)
        self._set_status("Prompt skopiowany do schowka.", "gray")

    def _pick_dir(self, var: tk.StringVar, callback=None):
        path = filedialog.askdirectory()
        if path:
            var.set(path)
            if callback:
                callback()

    def _refresh_list(self):
        self._listbox.delete(0, tk.END)
        d = Path(self._proc_var.get())
        if d.is_dir():
            files = sorted(d.glob("*.png")) + sorted(d.glob("*.PNG"))
            for f in files:
                self._listbox.insert(tk.END, f.name)
            self._set_status(f"{len(files)} plików PNG w katalogu przetworzonych.", "gray")

    def _on_process(self):
        proc_dir = Path(self._proc_var.get().strip())
        out_dir  = Path(self._out_var.get().strip())

        if not proc_dir.is_dir():
            self._set_status("Podaj katalog przetworzonych (GPT-4o).", "red")
            return
        if not self._out_var.get().strip():
            self._set_status("Podaj katalog wyjściowy (katalogowe).", "red")
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
                result = batch_process(proc_dir, out_dir, progress_cb=on_progress)
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
        errors  = result["errors"]
        msg = f"Gotowe: {n} przetworzone"
        if skipped:
            msg += f"  |  pominięte (brak w ERP): {', '.join(skipped)}"
        if errors:
            msg += f"  |  błędy: {'; '.join(e['file'] for e in errors)}"
        self._set_status(msg, "red" if errors else "#1a7a1a")

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
    PhotoWorkflowApp().mainloop()
