# Plan refactoru: render.py

**Źródło:** Backlog #105 (Audyt Faza 1.1)
**Problem:** "God script — 449 linii. Renderuje różne typy danych."
**Rekomendacja:** Wydzielić renderery per typ do osobnych funkcji/modułów.

---

## Obecna struktura

```
render.py (449 linii)
├── VIEWS dict (konfiguracja widoków)
├── fetch(view, bus, args) → list[dict]
├── render_json(data, title, output)
├── render_backlog_md(data, title, output)
├── render_suggestions_md(data, title, output)
├── render_md(data, columns, title, output)  # ogólny
├── render_xlsx(data, columns, title, output)
├── render_session_trace_xlsx(trace, output)
└── main() + argparse
```

**Funkcje już są wydzielone** — nie ma jednej wielkiej funkcji która robi wszystko.
Renderery są podzielone per typ (backlog_md, suggestions_md, session_trace_xlsx).

**Pytanie:** Co dokładnie chcemy poprawić?

---

## Diagnoza: czy to rzeczywiście "god script"?

| Metryka | Wartość | Ocena |
|---------|---------|-------|
| Liczba linii | 449 | Średnie (nie małe, nie ogromne) |
| Liczba odpowiedzialności | 3 | **Fetch, Render, CLI routing** |
| Funkcje | 9 | Dobrze podzielone |
| Duplikacja | Niska | Wspólne funkcje (render_md, render_xlsx) używane przez wiele widoków |
| Spójność | Wysoka | Wszystkie renderery używają tego samego interfejsu |

**Verdict:** To **NIE jest god script** w sensie "jedna funkcja 500 linii".
To jest **monolityczny moduł** — wszystko w jednym pliku.

**Czy to problem?**
Zależy:
- ✓ Łatwo znaleźć kod (wszystko w jednym miejscu)
- ✓ Łatwo dodać nowy renderer (kopiuj wzorzec)
- ✗ Trudno rozwijać równolegle (konflikt merge przy zmianach)
- ✗ Trudno testować izolowane renderery (trzeba importować cały moduł)

---

## Opcje refaktoru

### Opcja A: Wydzielenie rendererów do tools/lib/renderers/

**Struktura:**
```
tools/
├── render.py (CLI orchestrator, ~100 linii)
└── lib/
    └── renderers/
        ├── __init__.py
        ├── json_renderer.py
        ├── md_renderer.py (render_md, render_backlog_md, render_suggestions_md)
        ├── xlsx_renderer.py (render_xlsx, render_session_trace_xlsx)
        └── base.py (wspólne typy, stałe: VALUE_COLORS, STATUS_COLORS)
```

**Trade-offs:**
- ✓ Łatwiejsze testowanie (izolowane moduły)
- ✓ Lepsze SRP (każdy renderer w osobnym pliku)
- ✗ Więcej plików (4 zamiast 1)
- ✗ Dłuższa ścieżka do kodu (render.py → import renderers → md_renderer.py)

**Effort:** Mały (Move funkcji, update importów, testy smoke)

---

### Opcja B: Wydzielenie rendererów per widok

**Struktura:**
```
tools/lib/renderers/
├── backlog_renderer.py
├── suggestions_renderer.py
├── inbox_renderer.py
├── session_log_renderer.py
├── session_trace_renderer.py
└── base.py
```

**Trade-offs:**
- ✓ Najwyższe SRP (jeden renderer = jeden widok)
- ✗ Duplikacja kodu (render_md powtarzany 3x: inbox, session-log, messages)
- ✗ Najwięcej plików (6+ zamiast 1)

**Effort:** Średni (Wymaga deduplikacji wspólnych funkcji)

---

### Opcja C: Status quo (pozostaw jak jest)

**Argument:** render.py jest dobrze zorganizowany. 449 linii dla narzędzia CLI z 6 widokami i 3 formatami to OK.

**Trade-offs:**
- ✓ Zero kosztów refaktoru
- ✓ Kod działa, jest czytelny
- ✗ Nie rozwiązuje "god script" perception z audytu

**Effort:** 0

---

### Opcja D: Minimalne — wydziel tylko session_trace_xlsx

**Struktura:**
```
tools/
├── render.py (410 linii — bez session_trace)
└── lib/
    └── renderers/
        └── session_trace_renderer.py (render_session_trace_xlsx)
```

**Argument:** session_trace ma najbardziej oddzielną logikę (nie używa VIEWS dict, ma własne kolumny, osobny flow w main()).

**Trade-offs:**
- ✓ Mały wysiłek
- ✓ Usuwa najbardziej odizolowany kod
- ✗ Nie rozwiązuje fundamentalnego problemu ("wszystko w jednym pliku")

**Effort:** Bardzo mały

---

## Rekomendacja Developera

**Opcja A** — wydzielenie per format (json, md, xlsx).

**Uzasadnienie:**
1. Renderery różnią się głównie **formatem outputu**, nie **typem widoku**
   (backlog_md i suggestions_md to oba MD, tylko z różnym layoutem)
2. Wspólny kod (render_md, render_xlsx) pozostaje współdzielony — zero duplikacji
3. Testy łatwiejsze (import md_renderer, feed mockup data, assert output)
4. SRP zwiększone: jeden moduł = jeden format
5. Effort mały: Move funkcji + update importów + smoke test

**Struktura docelowa:**
```
tools/render.py
  └─ import renderers.json_renderer, renderers.md_renderer, renderers.xlsx_renderer
  └─ main() route do właściwego renderera

tools/lib/renderers/
  ├── __init__.py
  ├── base.py              # VALUE_COLORS, STATUS_COLORS, wspólne typy
  ├── json_renderer.py     # render_json()
  ├── md_renderer.py       # render_md, render_backlog_md, render_suggestions_md
  └── xlsx_renderer.py     # render_xlsx, render_session_trace_xlsx
```

---

## Alternatywna perspektywa

Jeśli celem audytu było "rozbij god script" — to **może diagnoza była błędna**.

449 linii to nie god script. render.py robi dokładnie to co powinien: renderuje widoki.
Nie ma nadmiarowych odpowiedzialności (nie łączy się z API, nie przetwarza logiki biznesowej).

**Pytanie do user:** Czy problem to rozmiar pliku, czy coś innego?
Może prawdziwy problem to:
- Brak testów dla rendererów?
- Trudność dodawania nowych formatów?
- Brak spójnego interfejsu renderer?

---

## Następne kroki

1. **Decyzja:** User wybiera opcję A / B / C / D
2. **Plan szczegółowy:** Jeśli A → lista plików do utworzenia + interfejs rendererów
3. **Testy:** Napisać najpierw testy dla obecnych rendererów (TDD - najpierw test, potem refactor)
4. **Refactor:** Move kod do nowych modułów
5. **Verify:** Smoke test wszystkich kombinacji (view × format)
6. **Commit**

---

**Oczekiwana odpowiedź:**
- Jeśli User potwierdza Opcję A → przechodzę do implementacji
- Jeśli User wybiera inną opcję → dostosowuję plan
- Jeśli User pyta "po co to robić?" → dyskusja czy diagnoza audytu była trafna
