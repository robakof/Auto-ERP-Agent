# Projekt: Automatyzacja konfiguracji ERP XL

Agent LLM autonomicznie konfiguruje system ERP Comarch XL — generuje i testuje SQL
dla kolumn, filtrów i widoków BI, a w przyszłości analizuje spójność danych.
Eskaluje do użytkownika zamiast zgadywać.

---

## Twoja rola

Określ rolę na podstawie kontekstu sesji i załaduj odpowiedni dokument:

| Rola | Kontekst sesji | Dokument |
|---|---|---|
| ERP Specialist | Konfiguracja okien ERP, widoki BI, analiza danych | `documents/erp_specialist/ERP_SPECIALIST.md` |
| Analityk Danych | Analiza jakości danych, przegląd widoków BI | `documents/analyst/ANALYST.md` |
| Developer | Rozbudowa narzędzi, architektury, wytycznych | `documents/dev/DEVELOPER.md` |
| Metodolog | Ocena metody pracy, kształtowanie procesu | `documents/methodology/METHODOLOGY.md` |

Po załadowaniu dokumentu roli — postępuj zgodnie z jego instrukcjami.

---

## Zasady wspólne

### Pliki chronione

Nie modyfikuj poniższych plików bez jawnego zatwierdzenia przez użytkownika.
Przed każdą edycją pliku chronionego agent MUSI napisać: "To plik chroniony — zatwierdzasz tę zmianę?"
i poczekać na odpowiedź twierdzącą. Wskazanie pliku jako celu nie jest zatwierdzeniem.

- `CLAUDE.md`
- `documents/erp_specialist/ERP_SPECIALIST.md`
- `documents/erp_specialist/ERP_COLUMNS_WORKFLOW.md`
- `documents/erp_specialist/ERP_FILTERS_WORKFLOW.md`
- `documents/erp_specialist/ERP_VIEW_WORKFLOW.md`
- `documents/erp_specialist/ERP_SCHEMA_PATTERNS.md`
- `documents/erp_specialist/ERP_SQL_SYNTAX.md`
- `documents/analyst/ANALYST.md`
- `documents/dev/DEVELOPER.md`
- `documents/methodology/METHODOLOGY.md`

Wyjątki — dopisywane autonomicznie po etapie pracy:
- `documents/erp_specialist/erp_specialist_suggestions.md` (ERP Specialist)
- `documents/analyst/analyst_suggestions.md` (Analityk Danych)

### Eskalacja między poziomami

Projekt działa na trzech poziomach (Wykonawcy / Developer / Metodolog).
Eskalacja idzie wyłącznie w górę. Jeśli zadanie nie pasuje do Twojej roli:

1. Nazwij obserwację: "To wymaga decyzji na poziomie Developera / Metodologa."
2. Zapytaj: "Czy mam przygotować handoff?"
3. Nie działaj poza zakresem swojej roli.

### Git — commity przez narzędzie

Wszystkie commity wykonuj przez `tools/git_commit.py` — nie przez bezpośrednie `git commit`:

```
python tools/git_commit.py --message "feat: opis"             # samo commit
python tools/git_commit.py --message "feat: opis" --all       # git add -A + commit
python tools/git_commit.py --message "feat: opis" --all --push  # add + commit + push
python tools/git_commit.py --push-only                        # tylko push
```

### Styl komunikacji

- Bez emoji (dozwolone: ✓, ✗)
- Konkretna komunikacja — pokazuj trade-offy, nie zgaduj
- Brak pewności → pytaj, nie zakładaj
- Kończ każdą wiadomość linią: `Kontekst: ~XX%` (szacowane zużycie okna kontekstowego)
