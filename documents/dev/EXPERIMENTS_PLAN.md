# EXPERIMENTS_PLAN

Eksperymenty do przeprowadzenia przed implementacją. Tylko kwestie faktycznie niepewne — każdy eksperyment ma jasny wynik binarny (założenie potwierdzone / obalone).

---

## E-01: Połączenie pyodbc z SQL Server ERP

**Założenie:** `pyodbc` z odpowiednim ODBC driver połączy się z bazą ERP i wykona SELECT.

**Co sprawdzamy:**
- Który ODBC driver jest zainstalowany na maszynach (`SQL Server` vs `ODBC Driver 17/18 for SQL Server`)
- Czy connection string z Windows Authentication działa
- Czy można utworzyć użytkownika DB z uprawnieniami wyłącznie SELECT i potwierdzić że DML jest blokowane na poziomie bazy

**Wynik sukcesu:** Skrypt zwraca wyniki `SELECT TOP 5 * FROM CDN.ZamNag` jako JSON.

**Ryzyko gdy zawiedzie:** Cały projekt blokuje się — bez połączenia z bazą agent nie działa. Wymaga konfiguracji DB lub alternatywnego sterownika.

---

## E-02: Parsowanie xlsm — wyciągnięcie wartości z formuł XLOOKUP

**Założenie:** `openpyxl` z `data_only=True` zwróci przeliczone wartości komórek zamiast formuł.

**Co sprawdzamy:**
- Czy `data_only=True` zwraca wartości dla arkuszy `Tabele`, `Kolumny`, `Słownik wartości kolumn`
- Arkusze mają formuły XLOOKUP — przy ostatnim zapisie przez Excel wartości są cache'owane; sprawdzamy czy ten cache jest aktualny
- Które arkusze mają puste cache (nigdy nie przeliczone) — te trzeba parsować inaczej

**Wynik sukcesu:** Arkusz `Kolumny` zwraca czytelne wartości (nazwy tabel, nazwy kolumn) bez ciągów `=_xlfn.XLOOKUP(...)`.

**Ryzyko gdy zawiedzie:** Konieczna alternatywna strategia — np. eksport przez makro VBA do CSV przed importem, albo parsowanie HTML zamiast Excel jako źródła pierwotnego.

---

## E-03: SQLite FTS5 z polskimi znakami i przydatność dla schematu ERP

**Założenie:** FTS5 z tokenizerem `unicode61` poprawnie indeksuje i wyszukuje polskie nazwy kolumn oraz opisy; wyniki dla typowych zapytań agenta są użyteczne.

**Co sprawdzamy:**
- Czy wyszukiwanie `kontrahent` znajdzie `kontrahenta`, `Kontrahent`, `kontrahencie` (deklinacja, wielkość liter)
- Czy zapytanie `"nazwa kontrahenta zamówienie"` zwróci właściwe kolumny jako top wyniki
- Czy własne nazwy kolumn (z arkusza `Kolumny_do_LLM`) są wystarczające do dobrego dopasowania — bez nich FTS po kodach SQL (`ZaN_KntGIDNumer`) byłby bezużyteczny

**Wynik sukcesu:** 3 testowe zapytania (`kontrahent zamówienie`, `status dokumentu`, `magazyn towar`) zwracają właściwe kolumny w top 5 wyników.

**Ryzyko gdy zawiedzie:** FTS5 niewystarczający — rozważyć pre-processing opisów (normalizacja, stemming) lub rozszerzenie własnych nazw o synonimy.

---

## E-04: Rejestracja skryptu Python jako MCP tool w Claude Code

**Założenie:** Skrypt Python wywołany jako komenda CLI (`python tools/sql_query.py "..."`) może być zarejestrowany jako narzędzie MCP i wywoływany przez Claude Code wewnątrz VS Code.

**Co sprawdzamy:**
- Mechanizm rejestracji narzędzia w `.claude/` lub `CLAUDE.md`
- Czy Claude Code poprawnie parsuje JSON zwrócony na stdout przez skrypt
- Jaki jest limit rozmiaru wyjścia narzędzia (co się dzieje przy 100 wierszach × 20 kolumn)
- Czy błędy na stderr są widoczne dla agenta

**Wynik sukcesu:** Claude Code wywołuje `sql_query.py` z zapytaniem i otrzymuje poprawny JSON; agent cytuje wynik w odpowiedzi.

**Ryzyko gdy zawiedzie:** Inny mechanizm integracji — może wymagać serwera MCP zamiast skryptów CLI (powrót do Model B).

---

## E-05: Format kodu SQL akceptowanego przez ERP

**Założenie:** Agent generuje SQL w formacie który można bezpośrednio wkleić do konfiguracji ERP.

**Co sprawdzamy:**
- Jaki dokładnie format przyjmuje ERP przy konfiguracji kolumny / filtru / raportu (czysty SQL SELECT? podzapytanie? wyrażenie?)
- Czy są ograniczenia składniowe specyficzne dla ERP (np. zakaz podzapytań, wymagane aliasy, specjalne funkcje)
- Czy format różni się między typami konfiguracji (kolumna vs filtr vs raport)

**Wynik sukcesu:** Udokumentowany format dla każdego typu konfiguracji — wejście do `erp_windows.json` i CLAUDE.md.

**Ryzyko gdy zawiedzie:** Agent generuje SQL który wymaga ręcznej transformacji przed wklejeniem — zmiana definicji "gotowego produktu".

---

## Kolejność wykonania

```
E-01 (pyodbc)          ← blokujący, wykonaj pierwszy
E-02 (xlsm parsing)    ← niezależny od E-01, można równolegle
E-04 (MCP tool)        ← niezależny, można równolegle z E-02
E-03 (FTS5)            ← zależy od E-02 (potrzebuje danych z Excel)
E-05 (format ERP)      ← wymaga dostępu do systemu ERP, może wymagać człowieka
```

---

*Dokument przygotowany: 2026-02-26*
