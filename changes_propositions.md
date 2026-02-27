# Plan implementacji — KM3 (CLAUDE.md)

Data: 2026-02-27

---

## Zakres

Stworzenie `ERP_AGENT.md` — instrukcje operacyjne agenta konfiguracyjnego ERP.
Plik oddzielony od `CLAUDE.md` (instrukcje dla agenta deweloperskiego).
Przy deploymencie (KM5) kopiowany jako `CLAUDE.md` do folderu współdzielonego.
Zwięzły, gotowy do działania bez czytania innych dokumentów podczas typowej sesji.

---

## Struktura ERP_AGENT.md

### Sekcja 1: Startup (bez zmian)
Obecna treść — pliki do przeczytania na starcie.

### Sekcja 2: Narzędzia agenta
Sygnatury CLI wszystkich 8 narzędzi + przykład wywołania + kluczowe pola wyjścia.
Nie duplikujemy pełnych kontraktów JSON — tylko to czego agent potrzebuje w robocie.

Narzędzia:
- `sql_query.py` — SELECT na SQL Server
- `search_docs.py` — FTS5 po dokumentacji
- `search_solutions.py` — szukanie wzorców SQL
- `search_windows.py` — identyfikacja okna ERP
- `save_solution.py` — zapis zatwierdzonego SQL
- `update_window_catalog.py` — zarządzanie erp_windows.json
- `build_index.py` — (administ.) przebudowa indeksu

### Sekcja 3: Domyślny workflow

Numerowana lista kroków — agent śledzi ją krok po kroku:

```
1. Zidentyfikuj okno → search_windows.py
   (brak wyników → zapytaj użytkownika, dodaj alias)
2. Odczytaj filtr.sql widoku → wyznacz tabelę główną
3. Sprawdź wzorce → search_solutions.py [okno] [typ]
4. Wyszukaj kolumny → search_docs.py [tabela] [--useful-only]
5. Generuj SQL (per ERP_SQL_SYNTAX.md)
6. Testuj → sql_query.py (zamień {filtrsql} na 1=1)
   (błąd → analiza → poprawka → wróć do 6, maks. 5 iteracji)
7. Prezentuj wynik użytkownikowi
8. Po akceptacji → save_solution.py
9. Nowe okno? → update_window_catalog.py
```

### Sekcja 4: Zarządzanie katalogiem okien

Trzy przypadki:
- **Nowe okno**: po save_solution do nieznanego folderu → odczytaj filtr.sql →
  znajdź primary_table przez `search_docs.py "[prefiks kolumny]"` →
  wywołaj `update_window_catalog.py --id ... --name ... --primary-table ...` →
  zapytaj użytkownika o aliasy
- **Nieznana fraza**: search_windows nie zwraca wyników → pokaż listę znanych okien,
  zapytaj "czy chodzi o X?" → po potwierdzeniu dopisz alias przez
  `update_window_catalog.py --id ... --add-alias "..."`
- **Nowy alias w rozmowie**: użytkownik użył nieznanej nazwy → dopytaj → dopisz alias

### Sekcja 5: Formułowanie zapytań FTS5

Reguły prefix matching — wymagane do skutecznego wyszukiwania:
- Tokenizuj frazę → każde słowo zamień na rdzeń + `*`
  Przykład: `"nagłówek zamówienia"` → `"naglowek* zamowien*"` (bez ogonków)
- Domyślnie `--useful-only` — eliminuje ~95% szumu
- `--table CDN.XXX` gdy znasz już tabelę główną

### Sekcja 6: Reguły eskalacji

Kiedy eskalować do użytkownika (zamiast iterować):
- Po 5 nieudanych iteracjach generowania/testowania
- Brak kolumny w INFORMATION_SCHEMA (problem ze schemą bazy)
- Wynik testu sensownie pusty lub zawiera niespodziewane dane
  (agent nie zna kontekstu biznesowego)
- Potrzebny zapis do pliku który już istnieje (konflikt rozwiązań)

### Sekcja 7: Referencja składni SQL

Jedno zdanie z pointerem do `documents/ERP_SQL_SYNTAX.md`.
Szczegóły składni tam — nie duplikujemy w CLAUDE.md.

---

## Kluczowe decyzje

- Narzędzia: pokazujemy tylko CLI + kluczowe pola (`ok`, `data.results`, `error.type`)
- Workflow jako lista kroków z numerami — agent może ją śledzić
- Aliasy/okna: logika decyzji inline (nie w osobnym dokumencie)
- Brak TDD — plik dokumentacyjny, nie kod

---

*Plan przygotowany: 2026-02-27*
