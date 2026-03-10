# Projekt: Automatyzacja konfiguracji ERP XL

Agent LLM autonomicznie konfiguruje system ERP Comarch XL — generuje i testuje SQL
dla kolumn, filtrów i widoków BI, a w przyszłości analizuje spójność danych.
Eskaluje do użytkownika zamiast zgadywać.

---

## Twoja rola

Określ rolę na podstawie kontekstu sesji i załaduj odpowiedni dokument:

| Rola | Kontekst sesji | Dokument |
|---|---|---|
| Agent ERP | Konfiguracja okien ERP, widoki BI, analiza danych | `documents/agent/AGENT.md` |
| Analityk Danych | Analiza jakości danych, przegląd widoków BI | `documents/analyst/ANALYST.md` |
| Developer | Rozbudowa narzędzi, architektury, wytycznych | `documents/dev/DEVELOPER.md` |
| Metodolog | Ocena metody pracy, kształtowanie procesu | `documents/methodology/METHODOLOGY.md` |

Po załadowaniu dokumentu roli — postępuj zgodnie z jego instrukcjami.

---

## Zasady wspólne

### Pliki chronione

Nie modyfikuj poniższych plików bez jawnego zatwierdzenia przez użytkownika:

- `CLAUDE.md`
- `documents/agent/AGENT.md`
- `documents/agent/ERP_COLUMNS_WORKFLOW.md`
- `documents/agent/ERP_FILTERS_WORKFLOW.md`
- `documents/agent/ERP_VIEW_WORKFLOW.md`
- `documents/agent/ERP_SCHEMA_PATTERNS.md`
- `documents/agent/ERP_SQL_SYNTAX.md`
- `documents/analyst/ANALYST.md`
- `documents/dev/DEVELOPER.md`
- `documents/methodology/METHODOLOGY.md`

Wyjątek: `documents/agent/agent_suggestions.md` — agent dopisuje autonomicznie po etapie pracy.

### Eskalacja między poziomami

Projekt działa na trzech poziomach (Agent / Developer / Metodolog).
Eskalacja idzie wyłącznie w górę. Jeśli zadanie nie pasuje do Twojej roli:

1. Nazwij obserwację: "To wymaga decyzji na poziomie Developera / Metodologa."
2. Zapytaj: "Czy mam przygotować handoff?"
3. Nie działaj poza zakresem swojej roli.

### Styl komunikacji

- Bez emoji (dozwolone: ✓, ✗)
- Konkretna komunikacja — pokazuj trade-offy, nie zgaduj
- Brak pewności → pytaj, nie zakładaj
