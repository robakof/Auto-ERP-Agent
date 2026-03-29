---
workflow_id: session_end
version: "1.0"
owner_role: all
trigger: "Agent kończy sesję (kontekst >80%, zakończenie zadania, polecenie użytkownika, polecenie dyspozytora)"
participants:
  - agent (owner — każda rola)
related_docs:
  - CLAUDE.md (sekcje: Self-handoff, Logowanie i refleksja, Komunikacja agent-agent)
prerequisites:
  - session_init_done
outputs:
  - type: log
    field: "session log z podsumowaniem"
  - type: suggestion
    field: "obserwacje z sesji (jeśli są)"
  - type: message
    field: "self-handoff (jeśli task niedokończony)"
  - type: state
    field: "backlog items zaktualizowane"
---

# Workflow: Zamknięcie sesji

Każdy agent wykonuje ten workflow przed zakończeniem sesji. Zapewnia że praca
jest udokumentowana, obserwacje zapisane, kontekst nie ginie, inne role wiedzą
co zostało zrobione.

## Outline

1. **Zamknięcie workflow** — zamknij otwarte workflow executions
2. **Backlog** — zaktualizuj statusy zadań
3. **Domknięcie komunikacji** — potwierdź realizację zadań zleconych przez inne role
4. **Sugestie** — zapisz obserwacje z sesji
5. **Log sesji** — podsumowanie do pliku + agent_bus log
6. **Self-handoff** — jeśli task niedokończony, przekaż kontekst
7. **Raport** — powiedz użytkownikowi co zrobiono

---

## Faza 1: Zamknięcie otwartych workflow

**Owner:** agent

### Steps

1. Sprawdź czy masz otwarte workflow executions:
   ```
   py tools/agent_bus_cli.py interrupted-workflows --role <rola>
   ```
2. Dla każdego otwartego workflow:
   - Task zakończony → `workflow-end --execution-id <id> --status completed`
   - Task porzucony → `workflow-end --execution-id <id> --status abandoned`
   - Task w toku (kontynuacja w następnej sesji) → `workflow-end --execution-id <id> --status interrupted`

### Exit gate

PASS: brak otwartych workflow executions.

---

## Faza 2: Aktualizacja backlogu

**Owner:** agent

### Steps

1. Przejrzyj backlog items które realizowałeś w tej sesji.
2. Dla każdego:
   - Zrobiony → `backlog-update --id <id> --status done`
   - Odkładany → `backlog-update --id <id> --status deferred`
   - W toku (kontynuacja) → zostaw `in_progress`

### Exit gate

PASS: statusy backlog items odzwierciedlają stan po sesji.

---

## Faza 3: Domknięcie komunikacji

**Owner:** agent

### Steps

1. Przejrzyj sesję — czy realizowałeś task zlecony przez inną rolę?
2. Jeśli tak — wyślij potwierdzenie z wynikiem:
   - Co zrobiono, jaki commit, gdzie artefakt
   ```
   py tools/agent_bus_cli.py send --from <rola> --to <zlecający> --content-file tmp/potwierdzenie.md
   ```
3. Jeśli nie realizowałeś cudzych tasków — pomiń.

### Exit gate

PASS: wszystkie role zlecające powiadomione LUB brak cudzych tasków.

---

## Faza 4: Sugestie (trzy warstwy)

**Owner:** agent

### Steps

Przejrzyj sesję przez trzy warstwy — od konkretnej do systemowej:

**Warstwa 1 — Bazowa: co odkryłeś w swojej pracy?**
- Reguła domenowa
- Pułapka na którą wpadłeś
- Propozycja narzędzia lub zmiany procesu
- Odkrycie techniczne

**Warstwa 2 — Nakierowania użytkownika: gdzie cię skorygował?**
- Każda korekta ("nie tak, a tak") to potencjalne usprawnienie
- Dlaczego poszedłeś źle? Czy prompt był niejasny, czy zignorowałeś regułę?
- Czy ta korekta dotyczy tylko ciebie czy każdego agenta w tej roli?

**Warstwa 3 — Meta-systemowa: jak wyeliminować klasę problemu?**
- Wyjdź ponad bieżący błąd — czy istnieje zmiana systemowa która sprawia
  że ten typ błędu nie może powstać?
- Przykład: "narzędzie dodane bez aktualizacji promptu" →
  poziom 1: poke do PE → poziom 2: prompt generowany z listy narzędzi automatycznie
- Szukaj rozwiązań które eliminują potrzebę ręcznej synchronizacji,
  ręcznego pamiętania, ręcznego sprawdzania

Dla każdej warstwy — jeśli są obserwacje, zapisz:
- Jedna obserwacja:
  ```
  py tools/agent_bus_cli.py suggest --from <rola> --type <type> --title "..." --content-file tmp/s.md
  ```
- Wiele obserwacji:
  ```
  py tools/agent_bus_cli.py suggest-bulk --from <rola> --bulk-file tmp/refleksje.md
  ```

Jeśli brak obserwacji na danej warstwie — pomiń (nie wymuszaj pustych sugestii).

### Exit gate

PASS: trzy warstwy przejrzane, obserwacje zapisane lub świadomie pominięte.

---

## Faza 5: Log sesji

**Owner:** agent

### Steps

1. Napisz podsumowanie sesji do pliku `tmp/log_sesji_<rola>.md`.
   Struktura:
   - Co było zadaniem
   - Co zrealizowano (commity, artefakty, deliverables)
   - Co zablokowane / nie zrobione
   - Ile workflow wykonano (ID, statusy)
   - Obserwacje procesowe (jeśli nie zapisane jako sugestie)

2. Zapisz log:
   ```
   py tools/agent_bus_cli.py log --role <rola> --content-file tmp/log_sesji_<rola>.md
   ```

### Exit gate

PASS: log sesji zapisany w agent_bus.

---

## Faza 6: Self-handoff (warunkowa)

**Owner:** agent

### Steps

1. Oceń: czy task jest zakończony?
   - Tak → pomiń tę fazę.
   - Nie → kontynuuj.

2. Napisz self-handoff z kontekstem dla następnej sesji:
   - Co zostało do zrobienia
   - Jakie pliki przeczytać
   - Jakie decyzje zostały podjęte
   - Czego NIE powtarzać (pułapki, ślepe uliczki)

3. Wyślij:
   ```
   py tools/agent_bus_cli.py handoff --from <rola> --to <rola> --phase "..." --status PASS --summary "..." --next-action "..."
   ```

### Forbidden

- Nie kopiuj pełnych treści plików — podaj ścieżkę.
- Nie opisuj tego co można odczytać z git log.
- Nie wysyłaj self-handoff gdy task jest zakończony (szum w inbox).

### Exit gate

PASS: self-handoff wysłany LUB task zakończony (handoff zbędny).

---

## Faza 7: Raport

**Owner:** agent

### Steps

1. Powiedz użytkownikowi:
   - Co zrobiono w sesji (krótko — commity, artefakty)
   - Co pozostaje (jeśli cokolwiek)
   - Ścieżki do artefaktów (jeśli powstały)

### Exit gate

PASS: użytkownik poinformowany.

---

## Kiedy wchodzić w ten workflow

- **Kontekst >80%** — zacznij zamykanie sesji
- **Użytkownik mówi "kończymy" / "zamknij sesję"** — natychmiast
- **Task zakończony i brak kolejnych poleceń** — zaproponuj zamknięcie
- **Poke z poleceniem zamknięcia** — natychmiast

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-29 | Formalizacja z praktyki — wzorzec wyekstrahowany z sesji 2779ea7afbbc, 6ec1a456959c, 8fa284a33ef9, 0cf5ef4fbce2 |
