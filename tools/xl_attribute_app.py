"""GUI do zarządzania atrybutami produktów — tkinter, zero dodatkowych zależności.

Użycie:
  python tools/xl_attribute_app.py
"""

import os
import sys
import threading
from datetime import date
from pathlib import Path
from tkinter import (
    Button, Entry, Frame, Label, StringVar, Tk, filedialog, messagebox,
)

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.xl_attribute_bulk import bulk_update
from tools.xl_attribute_template import generate_template

_DEFAULT_REPORT = Path(f"documents/human/reports/xl_attribute_bulk_{date.today().strftime('%Y%m%d')}.xlsx")

_BG        = "#F0F4F8"
_BG_STEP1  = "#DBEAFE"
_BG_STEP2  = "#EFF8EE"
_BG_RESULT = "#F8FAFC"
_FONT      = ("Segoe UI", 10)
_FONT_BOLD = ("Segoe UI", 11, "bold")
_FONT_HEAD = ("Segoe UI", 11, "bold")
_FONT_HINT = ("Segoe UI", 9)


def format_summary(data: dict) -> str:
    """Zwraca jednolinijkowe podsumowanie wyników bulk update."""
    return (
        f"✓ {data['success']} zaktualizowanych   "
        f"✗ {data['failed']} błędów   "
        f"— {data['skipped']} pominiętych"
    )


class _Step(Frame):
    def __init__(self, parent, title: str, subtitle: str, bg: str, fg_head: str):
        super().__init__(parent, bg=bg, bd=1, relief="solid", padx=14, pady=12)
        Label(self, text=title, font=_FONT_HEAD, bg=bg, fg=fg_head).pack(anchor="w")
        Label(self, text=subtitle, font=_FONT, bg=bg, fg="#555").pack(anchor="w", pady=(2, 0))


class AttributeApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("Atrybuty Produktów — CEiM")
        self.resizable(False, False)
        self.configure(padx=20, pady=20, bg=_BG)
        self._picked_file: Path | None = None
        self._report_path: Path | None = None
        self._build()

    # ------------------------------------------------------------------ build

    def _build(self):
        self._build_step1()
        self._build_step2()
        self._build_results()

    def _build_step1(self):
        step = _Step(self,
                     "KROK 1 — Generuj template",
                     "Tworzy plik Excel z atrybutami z bazy ERP.",
                     _BG_STEP1, "#1E3A5F")
        step.pack(fill="x", pady=(0, 10))

        row = Frame(step, bg=_BG_STEP1)
        row.pack(fill="x", pady=(8, 0))

        self._template_label = StringVar(value="(nie wybrano)")
        Button(row, text="Generuj i zapisz jako…", font=_FONT,
               command=self._on_generate,
               bg="#2563EB", fg="white", relief="flat", padx=10, pady=5
               ).pack(side="left")
        Label(row, textvariable=self._template_label, font=_FONT,
              bg=_BG_STEP1, fg="#333", wraplength=330).pack(side="left", padx=(10, 0))

    def _build_step2(self):
        step = _Step(self,
                     "KROK 2 — Aktualizuj atrybuty",
                     "Wskaż wypełniony plik Excel i uruchom aktualizację.",
                     _BG_STEP2, "#1A3C1A")
        step.pack(fill="x", pady=(0, 10))

        row_file = Frame(step, bg=_BG_STEP2)
        row_file.pack(fill="x", pady=(8, 0))
        self._file_label = StringVar(value="(nie wybrano)")
        Button(row_file, text="Wybierz plik…", font=_FONT,
               command=self._on_pick_file,
               bg="#16A34A", fg="white", relief="flat", padx=10, pady=5
               ).pack(side="left")
        Label(row_file, textvariable=self._file_label, font=_FONT,
              bg=_BG_STEP2, fg="#333", wraplength=330).pack(side="left", padx=(10, 0))

        row_ope = Frame(step, bg=_BG_STEP2)
        row_ope.pack(fill="x", pady=(8, 0))
        Label(row_ope, text="Operator ERP:", font=_FONT, bg=_BG_STEP2).pack(side="left")
        self._operator = StringVar()
        Entry(row_ope, textvariable=self._operator, width=12, font=_FONT).pack(side="left", padx=(6, 0))
        Label(row_ope, text="(opcjonalnie)", font=_FONT_HINT,
              bg=_BG_STEP2, fg="#888").pack(side="left", padx=(4, 0))

        self._run_btn = Button(step, text="▶  Uruchom aktualizację", font=_FONT_BOLD,
                               command=self._on_run,
                               bg="#15803D", fg="white", relief="flat",
                               padx=14, pady=7, state="disabled")
        self._run_btn.pack(anchor="w", pady=(12, 0))

    def _build_results(self):
        frame = Frame(self, bg=_BG_RESULT, bd=1, relief="solid", padx=14, pady=12)
        frame.pack(fill="x")

        self._status_var = StringVar(value="Gotowy.")
        Label(frame, textvariable=self._status_var, font=_FONT,
              bg=_BG_RESULT, fg="#222", wraplength=460, justify="left").pack(anchor="w")

        self._open_btn = Button(frame, text="Otwórz raport", font=_FONT,
                                command=self._on_open_report,
                                bg="#6366F1", fg="white", relief="flat",
                                padx=8, pady=3, state="disabled")
        self._open_btn.pack(anchor="w", pady=(8, 0))

    # --------------------------------------------------------------- handlers

    def _on_generate(self):
        path = filedialog.asksaveasfilename(
            title="Zapisz template jako…",
            defaultextension=".xlsx",
            initialfile="Atrybuty produktów - template.xlsx",
            filetypes=[("Excel (.xlsx)", "*.xlsx")],
        )
        if not path:
            return
        self._status_var.set("Generowanie template…")
        self.update()
        result = generate_template(Path(path), akronim_cols=10)
        if result["ok"]:
            self._template_label.set(Path(path).name)
            self._status_var.set(f"✓ Template zapisany: {path}")
        else:
            messagebox.showerror("Błąd generowania", result["error"]["message"])
            self._status_var.set("✗ Błąd generowania template.")

    def _on_pick_file(self):
        path = filedialog.askopenfilename(
            title="Wybierz wypełniony plik Excel",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Wszystkie", "*.*")],
        )
        if not path:
            return
        self._picked_file = Path(path)
        self._file_label.set(Path(path).name)
        self._run_btn.configure(state="normal")
        self._status_var.set(f"Plik wybrany: {Path(path).name}")

    def _on_run(self):
        if not self._picked_file:
            return
        self._run_btn.configure(state="disabled")
        self._open_btn.configure(state="disabled")
        self._status_var.set("Trwa aktualizacja…")
        self.update()

        operator = self._operator.get().strip() or None
        report = _DEFAULT_REPORT

        def _worker():
            result = bulk_update(self._picked_file, operator=operator, report=report)
            self.after(0, lambda: self._on_done(result, report))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_done(self, result: dict, report: Path):
        self._run_btn.configure(state="normal")
        if not result["ok"]:
            self._status_var.set(f"✗ Błąd: {result['error']['message']}")
            messagebox.showerror("Błąd aktualizacji", result["error"]["message"])
            return
        summary = format_summary(result["data"])
        self._status_var.set(f"{summary}\nRaport: {report}")
        self._report_path = report
        self._open_btn.configure(state="normal")

    def _on_open_report(self):
        if self._report_path and self._report_path.exists():
            os.startfile(str(self._report_path))


def main():
    app = AttributeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
