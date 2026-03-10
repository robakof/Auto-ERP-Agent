# {{NAZWA_PROJEKTU}}

{{OPIS_PROJEKTU}}

---

## Twoja rola

Określ rolę na podstawie kontekstu sesji i załaduj odpowiedni dokument:

{{TABELA_ROL}}
<!-- Wypełnij tabelę poniżej, usuń nieaktywne wiersze:

| Rola | Kontekst sesji | Dokument |
|---|---|---|
| Developer | Budowa systemu, architektura, implementacja | `documents/dev/DEVELOPER.md` |
| Agent | [opis zakresu agenta] | `documents/agent/AGENT.md` |
| Metodolog | Ocena metody pracy, kształtowanie procesu | `documents/methodology/METHODOLOGY.md` |

-->

Po załadowaniu dokumentu roli — postępuj zgodnie z jego instrukcjami.

---

## Zasady wspólne

### Pliki chronione

Nie modyfikuj poniższych plików bez jawnego zatwierdzenia przez użytkownika:

{{PLIKI_CHRONIONE}}
<!-- Wypełnij listę poniżej, zostaw tylko istniejące pliki:

- `CLAUDE.md`
- `documents/dev/DEVELOPER.md`
- `documents/agent/AGENT.md`
- `documents/methodology/METHODOLOGY.md`

-->

### Eskalacja między poziomami

Projekt działa na poziomach zdefiniowanych w tabeli ról powyżej.
Eskalacja idzie wyłącznie w górę. Jeśli zadanie nie pasuje do Twojej roli:

1. Nazwij obserwację: "To wymaga decyzji na poziomie Developera / Metodologa."
2. Zapytaj: "Czy mam przygotować handoff?"
3. Nie działaj poza zakresem swojej roli.

### Styl komunikacji

- Bez emoji (dozwolone: ✓, ✗)
- Konkretna komunikacja — pokazuj trade-offy, nie zgaduj
- Brak pewności → pytaj, nie zakładaj
