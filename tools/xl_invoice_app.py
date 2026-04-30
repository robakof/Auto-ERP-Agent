"""GUI do importu faktur zakupowych FZ z KSeF XML do Comarch XL.

Użycie:
  python tools/xl_invoice_app.py
"""

import os
import sys
import threading
from datetime import date
from pathlib import Path
from tkinter import (
    Button, Frame, Label, StringVar, Tk, filedialog, messagebox,
)

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

from tools.xl_invoice_bulk import bulk_import

_DEFAULT_REPORT = Path(f"documents/human/reports/xl_invoice_bulk_{date.today().strftime('%Y%m%d')}.xlsx")

_BG        = "#F0F4F8"
_BG_STEP1  = "#DBEAFE"
_BG_STEP2  = "#EFF8EE"
_BG_RESULT = "#F8FAFC"
_FONT      = ("Segoe UI", 10)
_FONT_BOLD = ("Segoe UI", 11, "bold")
_FONT_HEAD = ("Segoe UI", 11, "bold")
_FONT_HINT = ("Segoe UI", 9)


def _format_summary(data: dict) -> str:
    return (
        f"✓ {data['inserted']} zaimportowanych   "
        f"✗ {data['failed']} błędów   "
        f"— {data['skipped']} pominiętych"
    )


class _Step(Frame):
    def __init__(self, parent, title: str, subtitle: str, bg: str, fg_head: str):
        super().__init__(parent, bg=bg, bd=1, relief="solid", padx=14, pady=12)
        Label(self, text=title, font=_FONT_HEAD, bg=bg, fg=fg_head).pack(anchor="w")
        Label(self, text=subtitle, font=_FONT, bg=bg, fg="#555").pack(anchor="w", pady=(2, 0))


class InvoiceApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("Import FZ — CEiM")
        self.configure(padx=20, pady=20, bg=_BG)
        self._xml_dir: Path | None = None
        self._report_path: Path | None = None
        self._build()
        self.resizable(False, False)
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.lift()
        self.focus_force()

    def _build(self):
        self._build_step1()
        self._build_step2()
        self._build_results()

    def _build_step1(self):
        step = _Step(self,
                     "KROK 1 — Wybierz katalog z fakturami XML",
                     "Wskaż folder zawierający pliki KSeF (.xml).",
                     _BG_STEP1, "#1E3A5F")
        step.pack(fill="x", pady=(0, 10))

        row = Frame(step, bg=_BG_STEP1)
        row.pack(fill="x", pady=(8, 0))

        self._dir_label = StringVar(value="(nie wybrano)")
        Button(row, text="Wybierz katalog…", font=_FONT,
               command=self._on_pick_dir,
               bg="#2563EB", fg="white", relief="flat", padx=10, pady=5
               ).pack(side="left")
        Label(row, textvariable=self._dir_label, font=_FONT,
              bg=_BG_STEP1, fg="#333", wraplength=340).pack(side="left", padx=(10, 0))

    def _build_step2(self):
        step = _Step(self,
                     "KROK 2 — Uruchom import",
                     "Importuje wszystkie pliki XML z wybranego katalogu.",
                     _BG_STEP2, "#1A3C1A")
        step.pack(fill="x", pady=(0, 10))

        Label(step, text="⚠  Przed uruchomieniem zamknij Comarch ERP XL.",
              font=_FONT_HINT, bg=_BG_STEP2, fg="#B45309").pack(anchor="w", pady=(4, 0))

        self._run_btn = Button(step, text="▶  Uruchom import", font=_FONT_BOLD,
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

    def _on_pick_dir(self):
        path = filedialog.askdirectory(title="Wybierz katalog z plikami XML")
        if not path:
            return
        self._xml_dir = Path(path)
        xml_count = len(list(self._xml_dir.glob("*.xml")))
        self._dir_label.set(f"{self._xml_dir.name}  ({xml_count} plików .xml)")
        self._run_btn.configure(state="normal" if xml_count > 0 else "disabled")
        self._status_var.set(f"Katalog: {path}  —  {xml_count} plików XML")

    def _on_run(self):
        if not self._xml_dir:
            return
        self._run_btn.configure(state="disabled")
        self._open_btn.configure(state="disabled")
        self._status_var.set("Trwa import…")
        self.update()
        report = _DEFAULT_REPORT

        def _worker():
            result = bulk_import(self._xml_dir, report=report)
            self.after(0, lambda: self._on_done(result, report))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_done(self, result: dict, report: Path):
        self._run_btn.configure(state="normal")
        if not result["ok"]:
            self._status_var.set(f"✗ Błąd: {result['error']['message']}")
            messagebox.showerror("Błąd importu", result["error"]["message"])
            return
        summary = _format_summary(result["data"])
        self._status_var.set(f"{summary}\nRaport: {report}")
        self._report_path = report
        self._open_btn.configure(state="normal")

    def _on_open_report(self):
        if self._report_path and self._report_path.exists():
            os.startfile(str(self._report_path))


def main():
    app = InvoiceApp()
    app.mainloop()


if __name__ == "__main__":
    main()
