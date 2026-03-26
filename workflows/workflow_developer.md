---
workflow_id: developer_operations
version: "2.1"
owner_role: developer
trigger: "Developer otrzymuje zadanie operacyjne lub taktyczne"
related_docs:
  - documents/dev/DEVELOPER.md
  - documents/dev/PROJECT_START.md
prerequisites:
  - session_init_done
outputs:
  - type: commit
  - type: message
    field: "notyfikacje do ról (jeśli narzędzie wspólne)"
---

# Workflow: Developer — zadania operacyjne i taktyczne

Workflow dla małych i średnich zadań Developera.
Duże zadania architektoniczne → `documents/dev/PROJECT_START.md`.

## Outline

Workflow multi-scenario — wybierz sekcję według typu zadania:

1. **Narzędzie** — nowe narzędzie lub rozbudowa istniejącego
2. **Bug fix** — diagnoza i naprawa błędu
3. **Patch** — drobna zmiana (≤5 linii, jeden plik)
4. **Suggestions** — przetwarzanie sugestii od Wykonawców
5. **Zamknięcie** — końcówka sesji (commit, log)

---

## Routing

| Typ zadania | Sekcja |
|---|---|
| Nowe narzędzie / rozbudowa | Narzędzie |
| Bug fix / data fix | Bug fix |
| Drobna zmiana (≤5 linii, jeden plik) | Patch |
| Suggestions od Wykonawców | Suggestions |
| Zamknięcie sesji | Zamknięcie |

---

## Narzędzie (Tool)

**Owner:** developer

### Steps

1. Sprawdź czysty working tree (`git status`). Jeśli brudny → zapytaj czy commitować.
2. Dla średnich zadań: plan per feature do pliku .md (uwzględnij otwarte wątki
   z poprzednich sesji). Zatwierdź z użytkownikiem przed kodem.
3. Zaproponuj pisanie testów najpierw (TDD preferowane).
   3.1. Napisz testy: integration tests (całe flow) + unit tests (funkcje czyste).
        Happy path + edge cases. Mockuj zależności zewnętrzne (DB, API, sieć).
   3.2. Zaimplementuj kod spełniający testy. Test nie przechodzi → napraw kod, nie test.
   3.3. Commit per działająca zmiana.
4. Przy nieomawianych kwestiach w trakcie implementacji — pytaj użytkownika na bieżąco.
   4.1. Po implementacji: przetestuj, pokaż co zrobione, zapytaj o feedback.
   4.2. Poprawki na feedback użytkownika — iteruj aż do zatwierdzenia.
5. Checklist publikacji nowego narzędzia:
   5.1. Czy narzędzie dotyczy >1 roli? Tak → dokumentuj w CLAUDE.md. Nie → w dokumencie roli.
   5.2. Wyślij `agent_bus send` do aktywnych ról (nazwa, składnia, kiedy używać).
   5.3. Zapisz log sesji.

### Forbidden

- Pliki robocze w root projektu (`tmp_*.py`) — narzędzie od razu w `tools/`.
- Kod bez testów jako "gotowy".

### Exit gate

PASS jeśli:
- [ ] Testy przechodzą
- [ ] Narzędzie w `tools/` z testami
- [ ] Notyfikacja do ról (jeśli narzędzie wspólne)
- [ ] Commit + push

---

## Bug fix

**Owner:** developer

### Steps

1. Zdiagnozuj problem — zrozum przyczynę, nie tylko objaw.
   1.1. Blind spot query: czy ten sam błąd nie występuje szerzej?
        Jeden przypadek może być symptomem wzorca.
   1.2. Oceń skalę: ile miejsc dotkniętych? Naprawa ręczna vs narzędzie?
   1.3. Przedstaw diagnozę użytkownikowi — zakres, przyczyna, propozycja naprawy.
2. Napraw. Test. Verify.
   2.1. Commit z opisem przyczyny (nie tylko objawu).

### Forbidden

- Naprawianie jednej instancji gdy jest ich 10 — najpierw diagnoza zasięgu.
- Obejście jednorazowe zamiast naprawy narzędzia.

### Exit gate

PASS jeśli:
- [ ] Przyczyna zidentyfikowana (nie tylko objaw)
- [ ] Zasięg zdiagnozowany (blind spot query)
- [ ] Fix zweryfikowany
- [ ] Commit

---

## Patch

**Owner:** developer

Drobne zmiany istniejących narzędzi — nie bug fix, nie nowe narzędzie.

### Zakres

- Zmiana ≤5 linii kodu
- Jeden plik
- Nie zmienia interfejsu (API, argumenty CLI, format outputu)
- Przykłady: dodanie wartości do enuma, zmiana domyślnego parametru, poprawka walidacji

### Steps

1. Read pliku którego dotyczy zmiana.
2. Edit — wprowadź zmianę.
3. Test smoke (jeśli dotyczy) — upewnij się że narzędzie działa.
4. Commit z opisem zmiany.
5. Jeśli zmiana dotyczy dokumentów instrukcyjnych (CLAUDE.md, workflow/*.md, documents/*/[ROLA].md):
   Wyślij notyfikację do Prompt Engineer — PE jest gatekeeperem spójności promptów
   i musi poinformować inne role o zmianie.

### Forbidden

- Zmiany interfejsu (wymagają workflow Narzędzie + konsultacja z rolami które używają)
- Zmiany >5 linii (oceń czy to nie nowe narzędzie)

### Exit gate

PASS jeśli:
- [ ] Zmiana ≤5 linii, jeden plik
- [ ] Smoke test OK (jeśli dotyczy)
- [ ] Commit
- [ ] Jeśli zmiana dotyczy dokumentów instrukcyjnych → notyfikacja do PE

---

## Suggestions

**Owner:** developer

### Steps

1. Przeczytaj open suggestions:
   ```
   python tools/render.py suggestions --format md --status open
   ```
   Domyślnie → documents/human/suggestions/
   1.1. Dla każdego wpisu oceń: warto wdrożyć / nie warto / wymaga dyskusji.
   1.2. Przedstaw ocenę użytkownikowi — poczekaj na zatwierdzenie.
2. **Przed dodaniem do backlogu:** sprawdź czy funkcjonalność już nie istnieje.
   Sugestie mogą być przestarzałe — zweryfikuj stan kodu (grep, glob, git log).
   2.1. Zatwierdzone i zweryfikowane → dodaj do backlogu:
        ```
        python tools/agent_bus_cli.py backlog-add --title "..." --area <obszar> --content-file tmp/tmp.md
        ```
   2.2. Oznacz suggestion jako implemented:
        ```
        python tools/agent_bus_cli.py suggest-status --id <id> --status implemented
        ```

### Exit gate

PASS jeśli:
- [ ] Każda open suggestion oceniona
- [ ] Użytkownik zatwierdzył decyzje
- [ ] Zatwierdzone przeniesione do backlogu
- [ ] Statusy suggestions zaktualizowane

---

## Zamknięcie sesji

### Steps

1. Jeśli sesja obejmowała zmiany ścieżek lub dokumentacji:
   ```
   python tools/arch_check.py
   ```
2. Commit i push przez `tools/git_commit.py`.
3. Log sesji:
   ```
   python tools/agent_bus_cli.py log --role developer --content-file tmp/log_sesji.md
   ```

---

## Mockup outputu

Gdy zadanie dotyczy formatu lub wyglądu outputu — najpierw pokaż mockup
(kilka linii przykładowego outputu) i zapytaj "tak?" zanim napiszesz kod.
Dwie iteracje na złym formacie kosztują więcej niż jeden krok weryfikacyjny.
