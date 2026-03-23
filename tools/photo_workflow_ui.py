"""
photo_workflow_ui.py — Skalowanie zdjęć katalogowych po obróbce w ChatGPT.

Przepływ:
    1. Wskaż folder z przetworzonymi zdjęciami (PNG po ChatGPT).
    2. Wskaż folder wyjściowy (katalogowe).
    3. Kliknij "Skaluj" — proporcjonalne skalowanie Pillow wg wysokości z ERP.
"""

import re
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.photo_preprocess import batch_process

_PROJECT_ROOT = Path(__file__).parent.parent
_PROMPT_MD = _PROJECT_ROOT / "documents/prompt_engineer/PROMPT_PHOTO_PROCESSING.md"


def _load_prompt_a(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"## Prompt A[^\n]*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if not m:
        return ""
    block = re.search(r"```\n(.*?)```", m.group(1), re.DOTALL)
    return block.group(1).strip() if block else ""


class PhotoWorkflowApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Skalowanie zdjęć katalogowych")
        self.resizable(False, False)
        self._prompt = _load_prompt_a(_PROMPT_MD)
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 5}
        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Skalowanie zdjęć katalogowych",
                  font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 14), sticky="w")

        ttk.Button(frame, text="Kopiuj Prompt do ChatGPT",
                   command=self._copy_prompt).grid(
            row=0, column=2, padx=(0, 12), sticky="e")

        # Folder wejściowy (przetworzone przez ChatGPT)
        ttk.Label(frame, text="Przetworzone (ChatGPT):").grid(
            row=1, column=0, sticky="w", **pad)
        self._in_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._in_var, width=42).grid(
            row=1, column=1, sticky="w", **pad)
        ttk.Button(frame, text="…", width=3,
                   command=lambda: self._pick_dir(self._in_var, self._refresh_list)
                   ).grid(row=1, column=2, padx=(0, 12))

        # Folder wyjściowy (katalogowe)
        ttk.Label(frame, text="Katalogowe (output):").grid(
            row=2, column=0, sticky="w", **pad)
        self._out_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._out_var, width=42).grid(
            row=2, column=1, sticky="w", **pad)
        ttk.Button(frame, text="…", width=3,
                   command=lambda: self._pick_dir(self._out_var)
                   ).grid(row=2, column=2, padx=(0, 12))

        # Lista plików
        ttk.Label(frame, text="Pliki PNG do skalowania:").grid(
            row=3, column=0, columnspan=3, sticky="w", padx=12, pady=(8, 2))
        self._listbox = tk.Listbox(frame, height=7, width=55, selectmode="none")
        self._listbox.grid(row=4, column=0, columnspan=3, padx=12)

        ttk.Separator(frame, orient="horizontal").grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=10)

        self._btn = ttk.Button(frame, text="Skaluj", command=self._on_process)
        self._btn.grid(row=6, column=0, columnspan=3)

        self._status_var = tk.StringVar(value="Wskaż foldery i kliknij Skaluj.")
        self._status_lbl = ttk.Label(frame, textvariable=self._status_var,
                                     foreground="gray", wraplength=460)
        self._status_lbl.grid(row=7, column=0, columnspan=3,
                               pady=(8, 0), sticky="w", padx=12)

        self._progress = ttk.Progressbar(frame, mode="determinate", length=460)
        self._progress.grid(row=8, column=0, columnspan=3, padx=12, pady=(4, 8))
        self._progress.grid_remove()

    def _copy_prompt(self):
        self.clipboard_clear()
        self.clipboard_append(self._prompt)
        self._set_status("Prompt skopiowany — wklej do nowej rozmowy w ChatGPT.", "gray")

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
            files = sorted(f for f in d.iterdir()
                           if f.suffix.lower() == ".png" and f.is_file())
            for f in files:
                self._listbox.insert(tk.END, f.name)
            self._set_status(f"{len(files)} plików PNG znalezionych.", "gray")

    def _on_process(self):
        in_dir  = Path(self._in_var.get().strip())
        out_dir = Path(self._out_var.get().strip())

        if not in_dir.is_dir():
            self._set_status("Podaj katalog z przetworzonymi zdjęciami.", "red")
            return
        if not self._out_var.get().strip():
            self._set_status("Podaj katalog wyjściowy.", "red")
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


if __name__ == "__main__":
    PhotoWorkflowApp().mainloop()
