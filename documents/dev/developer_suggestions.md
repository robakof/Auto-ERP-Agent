# Sugestie developera

Plik refleksji Developera — dopisywany podczas lub po sesji deweloperskiej.
Archiwizowany przez człowieka razem z Developerem.

Metodolog czyta ten plik i wyłuskuje z niego obserwacje metodologiczne
do własnego `methodology_suggestions.md`.

## Format wpisu

```
### [DATA] Krótki opis sesji / zadania

1. Czy decyzja architektoniczna którą podjąłem była trafna?
   Co bym zmienił?

2. Czy coś co zbudowałem było zbyt skomplikowane na aktualną potrzebę?

3. Czy zauważyłem coś o metodzie pracy lub strukturze projektu
   co nie wynika bezpośrednio z pracy agenta?
```

Jeśli odpowiedź na pytanie jest "nie" lub "nic" — pomiń pytanie.

---

## Wpisy

### [2026-03-09] P1–P4 + bi_discovery + docs_search refactor

1. **Decyzje architektoniczne:**

   `bi_verify.py` wywołuje `export_bi_view()` wewnętrznie (import funkcji, nie subprocess) —
   dobra decyzja, zero narzutu. Ale przez to test wymaga mockowania na poziomie SqlClient,
   co sprawia że testy są sprzężone z implementacją export_bi_view. Akceptowalne, ale warto mieć świadomość.

   `bi_discovery.py` — testy z `_make_multi_cursor` są kruche na kolejność zapytań wewnątrz funkcji.
   Zmiana kolejności GROUP BY / MIN-MAX łamie testy bez zmiany zachowania zewnętrznego.
   Alternatywa: testować przez asercje na outputcie, nie na kolejności calls — ale wymagałoby
   prawdziwej bazy testowej. Na razie akceptowalne.

2. **Zbyt skomplikowane:**

   Nic. Wszystkie narzędzia tej sesji są małe i jednocelowe. Żadnego over-engineeringu.

3. **Obserwacje o metodzie pracy:**

   Sesja była za długa. Wczytałem ~15 plików przez kontekst, 6 narzędzi, i skończyło się na
   przymusowym zamknięciu. Optymalny rytm to: plan → 2-3 narzędzia → commit → zamknięcie.
   Developer powinien sam proponować zamknięcie sesji po każdym logicznym bloku pracy —
   nie czekać aż kontekst się wyczerpie.

   Odkrycie `--useful-only` jako martwej funkcjonalności wyszło dopiero przy pytaniu usera
   o konkretne wywołanie. Takie "ciche założenia" (is_useful wypełnione) powinny być walidowane
   przy budowie narzędzia, a nie odkrywane w produkcji przez agenta.
   Lekcja: przy każdym nowym narzędziu które opiera się na danych zewnętrznych — sprawdź
   pokrycie tych danych zanim wbudujesz logikę filtrującą na ich podstawie.

---

## Archiwum

*(brak wpisów)*
