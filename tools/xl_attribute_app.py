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
    BooleanVar, Button, Checkbutton, Entry, Frame, Label,
    StringVar, Text, Tk, filedialog, messagebox, scrolledtext,
)

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

from tools.xl_attribute_bulk import bulk_update
from tools.xl_attribute_template import generate_for_akronimy, generate_template

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
    return (
        f"✓ {data['success']} dodanych   "
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
        self.configure(padx=20, pady=20, bg=_BG)
        self._picked_file: Path | None = None
        self._report_path: Path | None = None
        self._build()
        self.resizable(False, False)
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.lift()
        self.focus_force()

    # ------------------------------------------------------------------ build

    def _build(self):
        self._build_step1()
        self._build_step2()
        self._build_results()

    def _build_step1(self):
        step = _Step(self,
                     "KROK 1 — Generuj plik do edycji",
                     "Wpisz kody produktów, pobierz aktualne wartości z ERP.",
                     _BG_STEP1, "#1E3A5F")
        step.pack(fill="x", pady=(0, 10))

        Label(step, text="Kody produktów (oddzielone przecinkami lub nowa linia):",
              font=_FONT, bg=_BG_STEP1, fg="#333").pack(anchor="w", pady=(8, 2))

        self._akronimy_text = Text(step, height=3, width=52, font=_FONT,
                                   bd=1, relief="solid", wrap="word")
        self._akronimy_text.pack(anchor="w")

        row_btns = Frame(step, bg=_BG_STEP1)
        row_btns.pack(fill="x", pady=(8, 0))

        Button(row_btns, text="Generuj plik dla wybranych…", font=_FONT,
               command=self._on_generate_selected,
               bg="#2563EB", fg="white", relief="flat", padx=10, pady=5
               ).pack(side="left")

        Button(row_btns, text="Generuj pełny template…", font=_FONT,
               command=self._on_generate_all,
               bg="#64748B", fg="white", relief="flat", padx=10, pady=5
               ).pack(side="left", padx=(8, 0))

        self._template_label = StringVar(value="")
        Label(step, textvariable=self._template_label, font=_FONT_HINT,
              bg=_BG_STEP1, fg="#1E3A5F", wraplength=460).pack(anchor="w", pady=(4, 0))

    def _build_step2(self):
        step = _Step(self,
                     "KROK 2 — Importuj atrybuty",
                     "Wskaż wypełniony plik Excel i uruchom import przez XL API.",
                     _BG_STEP2, "#1A3C1A")
        step.pack(fill="x", pady=(0, 10))

        Label(step, text="⚠  Przed uruchomieniem zamknij Comarch ERP XL.",
              font=_FONT_HINT, bg=_BG_STEP2, fg="#B45309").pack(anchor="w", pady=(4, 0))

        row_file = Frame(step, bg=_BG_STEP2)
        row_file.pack(fill="x", pady=(8, 0))
        self._file_label = StringVar(value="(nie wybrano)")
        Button(row_file, text="Wybierz plik…", font=_FONT,
               command=self._on_pick_file,
               bg="#16A34A", fg="white", relief="flat", padx=10, pady=5
               ).pack(side="left")
        Label(row_file, textvariable=self._file_label, font=_FONT,
              bg=_BG_STEP2, fg="#333", wraplength=330).pack(side="left", padx=(10, 0))

        self._update_var = BooleanVar(value=False)
        Checkbutton(step, text="Tryb aktualizacji — podmień istniejące atrybuty",
                    variable=self._update_var, font=_FONT,
                    bg=_BG_STEP2, fg="#1A3C1A", activebackground=_BG_STEP2,
                    selectcolor="#D1FAE5"
                    ).pack(anchor="w", pady=(8, 0))
        Label(step,
              text="(bez tej opcji program tylko dopisuje brakujące, nie zmienia istniejących)",
              font=_FONT_HINT, bg=_BG_STEP2, fg="#6B7280").pack(anchor="w")

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

    # --------------------------------------------------------------- handlers

    def _get_akronimy(self) -> list[str]:
        raw = self._akronimy_text.get("1.0", "end").strip()
        parts = [p.strip() for line in raw.splitlines() for p in line.split(",")]
        return [p for p in parts if p]

    def _on_generate_selected(self):
        akronimy = self._get_akronimy()
        if not akronimy:
            messagebox.showwarning("Brak kodów", "Wpisz co najmniej jeden kod produktu.")
            return
        path = filedialog.asksaveasfilename(
            title="Zapisz plik jako…",
            defaultextension=".xlsx",
            initialfile=f"atrybuty_wybrane_{date.today().strftime('%Y%m%d')}.xlsx",
            filetypes=[("Excel (.xlsx)", "*.xlsx")],
        )
        if not path:
            return
        self._status_var.set(f"Generowanie dla {len(akronimy)} produktów…")
        self.update()
        result = generate_for_akronimy(akronimy, Path(path))
        if result["ok"]:
            d = result["data"]
            info = f"✓ Plik zapisany: {Path(path).name}  ({d['products']} produktów)"
            if d.get("not_found"):
                info += f"\n⚠ Nie znaleziono: {', '.join(d['not_found'])}"
            self._template_label.set(info)
            self._status_var.set(info.splitlines()[0])
        else:
            messagebox.showerror("Błąd", result["error"]["message"])
            self._status_var.set("✗ Błąd generowania.")

    def _on_generate_all(self):
        from tools.xl_attribute_template import DEFAULT_OUTPUT
        path = filedialog.asksaveasfilename(
            title="Zapisz pełny template jako…",
            defaultextension=".xlsx",
            initialfile="Atrybuty produktów - template.xlsx",
            filetypes=[("Excel (.xlsx)", "*.xlsx")],
        )
        if not path:
            return
        self._status_var.set("Generowanie pełnego template…")
        self.update()
        result = generate_template(Path(path))
        if result["ok"]:
            self._template_label.set(f"✓ Template zapisany: {Path(path).name}")
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
        update_mode = self._update_var.get()
        if update_mode:
            if not messagebox.askyesno(
                "Tryb aktualizacji",
                "Tryb aktualizacji usunie istniejące atrybuty dla produktów z pliku "
                "i zastąpi je wartościami z pliku.\n\nKontynuować?"
            ):
                return
        self._run_btn.configure(state="disabled")
        self._open_btn.configure(state="disabled")
        self._status_var.set("Trwa import…")
        self.update()
        report = _DEFAULT_REPORT

        def _worker():
            result = bulk_update(self._picked_file, operator=None,
                                 report=report, update=update_mode)
            self.after(0, lambda: self._on_done(result, report))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_done(self, result: dict, report: Path):
        self._run_btn.configure(state="normal")
        if not result["ok"]:
            self._status_var.set(f"✗ Błąd: {result['error']['message']}")
            messagebox.showerror("Błąd importu", result["error"]["message"])
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
