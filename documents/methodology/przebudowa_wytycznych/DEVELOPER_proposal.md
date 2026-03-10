# [PROPOZYCJA] DEVELOPER.md (rename z AI_GUIDELINES.md)

Zmiana nazwy: `documents/dev/AI_GUIDELINES.md` → `documents/dev/DEVELOPER.md`

---

## Zmiany do wprowadzenia

### 1. Routing header na górze (nowy)

```markdown
# Developer — instrukcje operacyjne

## Na starcie sesji

1. Przeczytaj `documents/dev/backlog.md` — aktualny stan priorytetów
2. Przeczytaj `documents/agent/agent_suggestions.md` — nowe obserwacje agenta
   Oceń każdy wpis, przedstaw ocenę użytkownikowi, poczekaj na zatwierdzenie.
   Zatwierdzone → backlog.md | Przetworzone → Archiwum w agent_suggestions.md
3. Przeczytaj `documents/dev/progress_log.md` — stan projektu
```

### 2. Nowa sekcja: Skala zadania

Dodać po sekcji Progress Log, przed Phase 1:

```markdown
## Skala zadania

Przed rozpoczęciem pracy oceń skalę zadania:

**Małe / poprawka** (kilka godzin, jeden moduł):
→ Zaplanuj w backlog.md, implementuj zgodnie z workflow Phase 3.

**Średnie** (kilka sesji, nowy moduł):
→ Stwórz `ARCHITECTURE.md` z sekcjami: cel, techstack, struktura.
  Zatwierdź z użytkownikiem przed implementacją.

**Duże / projektowe** (wiele sesji, wiele modułów):
→ Zaproponuj nową gałąź projektu.
  Przejdź z użytkownikiem przez `PROJECT_START.md`.
  Wynik: osobne pliki PRD.md + TECHSTACK.md + ARCHITECTURE.md.

Zasada: dokumentacja proporcjonalna do złożoności.
Nie twórz PRD dla poprawki. Nie wchodź w duży projekt bez dokumentacji.
```

### 3. Phase 1 i Phase 2 — zostają, ale z nagłówkiem kontekstu

Dodać przed Phase 1:

```markdown
## Inicjalizacja projektu lub nowej gałęzi

Poniższe fazy (Phase 1-2) stosuj gdy inicjujesz nowy projekt lub nową gałąź.
Przy bieżących zadaniach w istniejącym projekcie — przejdź bezpośrednio do Phase 3.
Szczegółowy workflow inicjalizacji: `documents/dev/PROJECT_START.md`
```

### 4. Sekcja "ZMIANY W AI_GUIDELINES" → "ZMIANY W DEVELOPER.MD"

```markdown
## ZMIANY W DEVELOPER.MD

Jakiekolwiek modyfikacje tego pliku wymagają jawnego zatwierdzenia przez użytkownika.
```

### 5. Poprawka ścieżki Progress Log

Obecna ścieżka: `documentation/progress_log.md` → poprawić na `documents/dev/progress_log.md`

---

## Co pozostaje bez zmian

Cały workflow Phase 3, komendy powłoki, code quality, security, communication.
Treść merytoryczna tych sekcji jest aktualna.

---

## Nowy plik: PROJECT_START.md

Wyodrębnić z AI_GUIDELINES Phase 1 i Phase 2 do osobnego pliku `documents/dev/PROJECT_START.md`.
W DEVELOPER.md zostaje skrócona referencja + zasada skali zadania.

PROJECT_START.md zawiera:
- Phase 1: dokumentacja projektowa (PRD, TECHSTACK, ARCHITECTURE)
- Phase 2: eksperymenty i plan implementacji
- Reguła skali: kiedy ARCHITECTURE.md z sekcjami, kiedy osobne pliki
