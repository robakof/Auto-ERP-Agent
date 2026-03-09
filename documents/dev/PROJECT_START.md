# Inicjalizacja projektu lub nowej gałęzi

Stosuj ten dokument gdy inicjujesz nowy projekt lub nową gałąź projektu.
Przy bieżących zadaniach w istniejącym projekcie — przejdź bezpośrednio do Phase 3 w DEVELOPER.md.

---

## Skala zadania — dobór dokumentacji

| Skala | Dokumentacja | Kiedy |
|---|---|---|
| Małe / poprawka | Notatka w `progress_log.md` | Kilka godzin, jeden moduł |
| Średnie | `ARCHITECTURE.md` z sekcjami PRD i techstack | Kilka sesji, nowy moduł |
| Duże / projektowe | Osobne `PRD.md` + `TECHSTACK.md` + `ARCHITECTURE.md` | Wiele sesji, wiele modułów |

Zasada: dokumentacja proporcjonalna do złożoności.
Nie twórz PRD dla poprawki. Nie wchodź w duży projekt bez dokumentacji.

---

## Phase 1: Tworzenie dokumentacji projektowej

**Cel:** Stworzyć dokumentację która pozwoli:
- z łatwością zapoznać się z projektem kolejnym asystentom
- uniknąć błędów początkującego i kosztownego przebudowywania

**Wytyczne:**
- Wszystkie dokumenty w folderze `documents/`
- Bądź zwięzły i minimalistyczny
- Unikaj fragmentów kodu w dokumentacji
- Unikaj powtarzania tych samych informacji — zamieszczaj minimalne streszczenie z odniesieniem

### PRD (Product Requirements Document)

**Cel:** Fundament pracy nad projektem i wytyczna dla kolejnych asystentów.

Pomóż zdefiniować wymagania, funkcjonalności i cel projektu.
Zastanów się nad najlepszymi praktykami i architekturą aby uniknąć błędów.
Dopasuj skalowalność i objętość dokumentu do skali projektu.

**Sekcje:**
1. Wprowadzenie i cel
2. Użytkownicy i persony
3. Wymagania funkcjonalne
4. Wymagania niefunkcjonalne
5. Scope i ograniczenia
6. Aspekty techniczne

### Tech Stack i narzędzia

**Cel:** Wybór technologii i rozwiązań architektonicznych.

Na podstawie PRD wybierz razem z użytkownikiem technologię, biblioteki i narzędzia.
Szukaj aktualnych frameworków (sprawdź wersje, community support).
Sugeruj opcje z uzasadnieniem i trade-offami.

### Architektura projektu

**Cel:** Wytyczne do budowy projektu.

Na podstawie PRD i TECHSTACK stwórz ARCHITECTURE.md określający:
architekturę projektu, strukturę plików i modułów, najważniejsze klasy,
technologie i ich użycie, Data Flow, Key Design Patterns.

Dla projektów średnich: ARCHITECTURE.md może zawierać skrócone sekcje PRD i techstack
zamiast osobnych plików — decyduje złożoność.

**Współpraca:**
- Prezentuj dokumenty sekcja po sekcji
- Pytaj o feedback przed przejściem dalej

---

## Phase 2: Planowanie implementacji

### Eksperymenty

**Cel:** Sprawdzenie rozwiązań architektonicznych i założeń projektowych przed implementacją.

Utwórz `EXPERIMENTS_PLAN.md`. Zamieść tylko to co faktycznie jest niepewne lub wymaga
sprawdzenia z powodu kolejnych etapów prac.

Przeprowadź eksperymenty, zaktualizuj dokumentację o wyniki.

### Plan implementacji

**Cel:** Plan pracy podzielony na kamienie milowe.

Utwórz `IMPLEMENTATION_PLAN.md` na podstawie PRD i ARCHITECTURE.
Plan nie powinien być drobiazgowy — dla każdej dużej implementacji tworzony będzie
osobny, mniejszy plan. Powinien zawierać kamienie milowe i podział modułowy.

---

## Przekazanie do Phase 3

Po zatwierdzeniu dokumentacji przez użytkownika — wróć do DEVELOPER.md i przejdź
do Phase 3 (Implementacja sekcja po sekcji).
