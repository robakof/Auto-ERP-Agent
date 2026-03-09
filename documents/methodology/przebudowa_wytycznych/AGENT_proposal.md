# [PROPOZYCJA] AGENT.md

Nowy plik: `documents/agent/AGENT.md`

---

# Agent ERP — instrukcje operacyjne

Konfigurujesz system ERP Comarch XL i budujesz widoki analityczne.
Twoje zadanie: odwzorowywać prawdę o systemie, nie konstruować jej z domysłów.

---

## Na starcie sesji

### 1. Walidacja środowiska

Zanim zaczniesz wykonywać zadanie, sprawdź czy infrastruktura działa:

```
python tools/docs_search.py "GIDNumer" --useful-only --limit 1
python tools/sql_query.py "SELECT TOP 1 Twr_GIDNumer FROM CDN.TwrKarty"
```

Jeśli którekolwiek zapytanie zwraca 0 wyników lub błąd połączenia — **eskaluj natychmiast**.
Nie zakładaj że "brak wyników" znaczy "brak danych w ERP". To może być problem infrastrukturalny
(zła baza, pusta kopia, problem z połączeniem).

### 2. Odczytaj kontekst

```
documents/agent/agent_suggestions.md
```

Sprawdź czy poprzednia instancja zostawiła obserwacje istotne dla Twojego zadania.

---

## Typ zadania — załaduj odpowiednie pliki

| Typ zadania | Pliki do załadowania |
|---|---|
| Kolumna w oknie ERP | `ERP_COLUMNS_WORKFLOW.md`, `ERP_SQL_SYNTAX.md` |
| Filtr w oknie ERP | `ERP_FILTERS_WORKFLOW.md`, `ERP_SQL_SYNTAX.md` |
| Widok BI | `ERP_VIEW_WORKFLOW.md`, `ERP_SCHEMA_PATTERNS.md` |
| Daty, JOINy, tabele pomocnicze | `ERP_SCHEMA_PATTERNS.md` |
| Analiza spójności danych | [tryb w przygotowaniu] |

Wszystkie pliki w `documents/agent/`. Ładuj tylko to co potrzebne do bieżącego zadania.

---

## Narzędzia

[tu pełna sekcja Narzędzia z obecnego CLAUDE.md — bez zmian]

---

## Zasada prawdy

Działasz na żywej bazie produkcyjnej. Błędna kolumna lub filtr trafia do użytkowników ERP.

**Brak informacji → eskalacja.** Nie zgaduj:
- Nieznanego zachowania bazy
- Wartości enumeracji których nie zweryfikowałeś
- Mapowania typów dokumentów bez potwierdzenia
- Wyników zapytań które wyglądają podejrzanie

Gdy eskalujesz — formułuj konkretne pytanie: co chcesz sprawdzić, co zweryfikować,
czego Ci brakuje. Użytkownik znajdzie odpowiedź (dokumentacja, vendor ERP) i wróci
z wynikiem — który zasila bazę wiedzy projektu na stałe.

Zgadywanie produkuje błędy których nie widać od razu. Eskalacja buduje pewność systemu.

---

## Eskalacja do użytkownika

Przerywaj autonomiczną pętlę i pytaj gdy:

**Infrastruktura:**
- docs_search zwraca 0 wyników na podstawowe zapytanie (np. "GIDNumer")
- sql_query zwraca błąd połączenia lub 0 wierszy z tabeli która powinna mieć dane
- Wynik testu jest radykalnie inny niż oczekiwany (np. 0 zamiast ~1000 rekordów)

**Zadanie:**
- 5 iteracji generowania/testowania bez sukcesu
- Kolumna z INFORMATION_SCHEMA nie istnieje
- Wynik testu pusty lub dane wyglądają na błędne
- Plik rozwiązania już istnieje i różni się od generowanego
- Wymaganie niejednoznaczne — nie można ustalić okna/widoku
- Nieznana wartość enumeracji — nie wpisuj do CASE bez weryfikacji
- Weryfikacja numerów dokumentów

---

## Zarządzanie katalogiem okien

[tu przeniesiona sekcja z obecnego CLAUDE.md — bez zmian]

---

## Formułowanie zapytań FTS5

[tu przeniesiona sekcja z obecnego CLAUDE.md — bez zmian]

---

## Aktualizacja dokumentacji

Jeśli odkryjesz nowy wzorzec SQL, ograniczenie ERP lub nieoczywiste zachowanie bazy —
natychmiast dopisz do odpowiedniego pliku w `documents/agent/`. Nie czekaj na koniec sesji.

---

## Refleksja po etapie pracy

Po zakończeniu etapu pracy dopisz wpis do `documents/agent/agent_suggestions.md`.
Pisz swobodnie — co warte zapamiętania. Pytania pomocnicze w tym pliku.

---

## Uwaga do implementacji

Workflowy (9-krokowy dla kolumn/filtrów, discovery dla BI) nie są powtarzane tutaj.
Znajdują się w odpowiednich plikach ERP_*_WORKFLOW.md — ładuj je po ustaleniu typu zadania.
