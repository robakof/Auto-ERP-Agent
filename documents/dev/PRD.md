# PRD: Automatyczny Konfigurator Systemu ERP

## 1. Cel projektu

Zbudowanie środowiska deweloperskiego wewnątrz VS Code, w którym agent LLM autonomicznie przeprowadza cały proces konfiguracji systemu ERP (kolumny, filtry, raporty, widoki) — od analizy wymagań, przez eksplorację bazy danych i dokumentacji, po wygenerowanie i zwalidowanie gotowego kodu SQL — ograniczając rolę człowieka wyłącznie do czynności niemożliwych do wykonania programistycznie.

---

## 2. Kontekst i problem

### Obecny proces (AS-IS)

| Krok | Czynność | Osoba/Narzędzie |
|------|----------|-----------------|
| 1 | Dostarczenie LLM przykładów kodu i fragmentów dokumentacji | Człowiek |
| 2 | Generowanie kodu SQL | LLM (chat) |
| 3 | Ręczne przeklejanie kodu do SSMS, uruchomienie, odczyt wyników | Człowiek |
| 4 | Przeklejanie wyników z powrotem do czatu LLM | Człowiek |
| 5 | Cykl poprawek — powtarzany wielokrotnie | Człowiek + LLM |
| 6 | Wklejenie finalnego kodu do systemu ERP | Człowiek |
| 7 | Debugowanie błędów zwracanych przez ERP, dostarczanie nowych przykładów | Człowiek |

**Kluczowe problemy:**
- Wysoki nakład czasu człowieka na mechaniczne przeklejanie danych między narzędziami
- Brak pamięci między sesjami — agent za każdym razem zaczyna od zera
- Brak dostępu agenta do bazy rozwiązań i dokumentacji w czasie rzeczywistym
- Ryzyko błędów przy ręcznym przepisywaniu/kopiowaniu kodu
- Długi czas od wymagania do działającego rozwiązania

### Docelowy proces (TO-BE)

Agent LLM samodzielnie:
1. Pobiera i analizuje wymaganie
2. Odpytuje bazę danych ERP w celu rozpoznania struktury
3. Przeszukuje bazę gotowych rozwiązań (wzorce, przykłady)
4. Przeszukuje dokumentację (Excel, pliki tekstowe, wytyczne)
5. Generuje i iteracyjnie testuje kod SQL
6. Zgłasza człowiekowi wyłącznie akcje wymagające ręcznej interwencji (np. wklejenie do GUI ERP)

---

## 3. Zakres projektu

### W zakresie (in scope)
- Środowisko agentowe w VS Code (Claude Code lub kompatybilny agent)
- Narzędzia agenta do odpytywania bazy SQL Server (SSMS-compatible)
- Baza rozwiązań (solution store) — przeszukiwalna kolekcja wcześniej napisanych fragmentów kodu
- Indeksowana baza dokumentacji ERP (struktury tabel, opisy pól, wytyczne konfiguracji)
- Automatyczny cykl testowania podzapytań weryfikujących poprawność generowanego kodu
- Mechanizm raportowania akcji wymagających interwencji człowieka
- Logi i historia sesji agenta

### Poza zakresem (out of scope)
- Bezpośrednia integracja z GUI systemu ERP (klik automatyczny, RPA)
- Wdrożenie produkcyjne kodu bez akceptacji człowieka
- Modyfikacja struktury bazy danych ERP
- Obsługa baz innych niż SQL Server

---

## 4. Użytkownicy i role

| Rola | Opis | Interakcja z systemem |
|------|------|-----------------------|
| **Konfigurator ERP** | Specjalista konfigurujący kolumny, filtry, raporty | Podaje wymaganie, zatwierdza wynik, wykonuje ręczne akcje w ERP |
| **Developer** | Utrzymuje środowisko, rozszerza bazę rozwiązań i dokumentację | Zarządza narzędziami agenta, aktualizuje indeks dokumentacji |

---

## 5. Wymagania funkcjonalne

### F-01 — Interfejs wejścia wymagania
- Agent przyjmuje wymaganie w języku naturalnym (polskim) opisujące cel konfiguracji
- Wymaganie może zawierać: opis kolumny/filtru/raportu, źródłowe tabele, warunki biznesowe
- Opcjonalnie: załączenie fragmentu dokumentacji lub przykładu bezpośrednio w wymaganiu

### F-02 — Narzędzie: Zapytanie do bazy SQL Server
- Agent wykonuje zapytania SQL do wskazanej bazy danych ERP przez dedykowany skrypt
- Obsługuje: SELECT na widokach i tabelach, sprawdzanie struktury (`INFORMATION_SCHEMA`), testowanie podzapytań
- Wyniki zwracane do agenta w formacie czytelnym (JSON lub tabela)
- Wykonywanie wyłącznie operacji odczytu (SELECT) — zakaz DML/DDL bez jawnej zgody

### F-03 — Narzędzie: Przeszukiwanie bazy rozwiązań
- Baza rozwiązań to kolekcja wcześniej napisanych i zatwierdzonych fragmentów kodu SQL wraz z metadanymi
- Metadane: typ konfiguracji (kolumna/filtr/raport), tabele źródłowe, słowa kluczowe, data dodania
- Agent przeszukuje bazę semantycznie (dopasowanie do kontekstu wymagania) i strukturalnie (słowa kluczowe, tabele)
- Format bazy: katalog plików `.sql` + plik indeksu `.json` lub lekka baza SQLite

### F-04 — Narzędzie: Przeszukiwanie dokumentacji
- Dokumentacja przechowywana lokalnie: pliki Excel (`.xlsx`), pliki tekstowe/Markdown, wytyczne PDF
- Agent indeksuje dokumentację przy starcie (lub na żądanie) i przeszukuje ją semantycznie
- Zwraca relevantne fragmenty: opis pola, dozwolone wartości, logika biznesowa, przykłady

### F-05 — Generowanie i iteracyjne testowanie kodu SQL
- Agent generuje kod SQL na podstawie: wymagania + wyników eksploracji bazy + znalezionych wzorców
- Automatycznie uruchamia podzapytania testujące (np. sprawdzenie czy wynik nie jest pusty, czy typy danych się zgadzają)
- W przypadku błędów SQL: analizuje komunikat błędu, poprawia kod, ponawia test
- Maksymalna liczba iteracji automatycznych: konfigurowalna (domyślnie 5)

### F-06 — Mechanizm eskalacji do człowieka
- Agent zgłasza interwencję, gdy:
  - Wyczerpał limit iteracji bez sukcesu
  - Potrzebuje informacji niemożliwych do uzyskania z bazy/dokumentacji
  - Kod wymaga wklejenia do GUI ERP (krok manualny)
  - Wynik wymaga zatwierdzenia przed zapisem do bazy rozwiązań
- Eskalacja: wyraźny komunikat w terminalu VS Code z opisem potrzebnej akcji i stanem obecnym

### F-07 — Zapis do bazy rozwiązań
- Po akceptacji przez człowieka agent zapisuje nowe rozwiązanie do bazy rozwiązań z pełnymi metadanymi
- Umożliwia tagowanie i kategoryzację nowego rozwiązania

### F-08 — Historia i logi sesji
- Każda sesja agenta logowana: wymaganie wejściowe, kroki pośrednie, wygenerowany kod, wyniki testów
- Logi przechowywane lokalnie w katalogu `logs/` w formacie Markdown lub JSON

---

## 6. Wymagania niefunkcjonalne

| ID | Wymaganie | Miara sukcesu |
|----|-----------|---------------|
| NF-01 | Czas do pierwszego wygenerowanego kodu | < 2 minuty dla typowych wymagań |
| NF-02 | Bezpieczeństwo bazy ERP | Agent wykonuje wyłącznie SELECT; brak możliwości DML/DDL bez jawnego zezwolenia |
| NF-03 | Odtwarzalność | Każdą sesję można odtworzyć z logów |
| NF-04 | Lokalność | Wszystkie dane (dokumentacja, baza rozwiązań, logi) przechowywane lokalnie |
| NF-05 | Rozszerzalność | Dodanie nowego narzędzia agenta nie wymaga modyfikacji rdzenia systemu |

---

## 7. Architektura systemu

```
VS Code (środowisko agenta)
│
├── Agent LLM (Claude Code / MCP Agent)
│   ├── Tool: sql_query          → SQL Server (read-only)
│   ├── Tool: search_solutions   → Solution Store (lokalny katalog)
│   ├── Tool: search_docs        → Doc Index (lokalny indeks)
│   └── Tool: escalate_human     → Terminal output / notyfikacja
│
├── Solution Store
│   ├── solutions/               → pliki .sql z kodem
│   └── index.json               → metadane rozwiązań
│
├── Documentation Index
│   ├── raw/                     → oryginalne pliki (Excel, MD, PDF)
│   └── index/                   → sparsowane i zindeksowane dane
│
└── Logs
    └── sessions/                → logi sesji w formacie MD/JSON
```

### Technologie

| Komponent | Technologia |
|-----------|-------------|
| Agent | Claude Code (MCP) lub LangChain/AutoGen |
| Połączenie z SQL Server | `pyodbc` / `mssql-scripter` / skrypt PowerShell |
| Indeks dokumentacji | Lokalne embeddingi (`sentence-transformers`) lub plik JSON z FTS |
| Baza rozwiązań | Katalog plików `.sql` + `index.json` (SQLite opcjonalnie) |
| Środowisko | VS Code + Python 3.11+ |

---

## 8. Integracje

| System | Typ integracji | Uprawnienia |
|--------|----------------|-------------|
| SQL Server (baza ERP) | ODBC / pyodbc | Read-only (`SELECT`) |
| System ERP (GUI) | Brak automatycznej — człowiek wykonuje ręcznie | N/A |
| Dokumentacja Excel | Lokalny plik — parsowanie przez `openpyxl` | Odczyt |

---

## 9. Definicja sukcesu (Kryteria akceptacji)

| Kryterium | Miara |
|-----------|-------|
| Redukcja ręcznych kroków | ≥ 80% kroków procesu AS-IS wykonywanych przez agenta bez interwencji człowieka |
| Skuteczność generowania | ≥ 70% wymagań rozwiązanych bez eskalacji do człowieka w fazie SQL |
| Brak incydentów bezpieczeństwa | Zero przypadków wykonania DML/DDL na bazie ERP przez agenta |
| Adopcja bazy rozwiązań | Po 3 miesiącach ≥ 50 zatwierdzonych rozwiązań w bazie |

---

## 10. Ryzyka i mitygacje

| Ryzyko | Prawdopodobieństwo | Wpływ | Mitygacja |
|--------|-------------------|-------|-----------|
| Agent generuje błędny SQL wklejony do ERP przez człowieka bez weryfikacji | Średnie | Wysoki | Obligatoryjny krok zatwierdzenia + podgląd diff przed akcją |
| Dokumentacja Excel nieaktualna lub niekompletna | Wysokie | Średni | Mechanizm flagowania brakujących danych + eskalacja do człowieka |
| Limit tokenów LLM przy dużych schematach bazy | Średnie | Średni | Chunking wyników SQL, priorytetyzacja relevantnych fragmentów |
| Brak dostępu sieciowego do SQL Server z VS Code | Niskie | Wysoki | Konfiguracja connection string w `.env`, testy połączenia przy starcie |

---

## 11. Etapy realizacji (Roadmap)

### Faza 1 — Fundament (MVP)
- [ ] Konfiguracja środowiska VS Code + Python
- [ ] Narzędzie `sql_query`: połączenie z SQL Server, wykonywanie SELECT, zwrot wyników
- [ ] Prymitywna baza rozwiązań: katalog `.sql` + ręczny `index.json`
- [ ] Podstawowy agent (Claude Code) z dostępem do `sql_query` i `search_solutions`
- [ ] Mechanizm eskalacji do człowieka (komunikat w terminalu)

### Faza 2 — Dokumentacja i pamięć
- [ ] Parser dokumentacji Excel (`openpyxl`)
- [ ] Indeks dokumentacji z wyszukiwaniem pełnotekstowym
- [ ] Narzędzie `search_docs` dla agenta
- [ ] Logowanie sesji do pliku Markdown

### Faza 3 — Inteligentne testowanie
- [ ] Automatyczny generator podzapytań testujących
- [ ] Pętla iteracyjna z limitem prób
- [ ] Analiza komunikatów błędów SQL i auto-korekta

### Faza 4 — Optymalizacja i skalowanie
- [ ] Semantyczne wyszukiwanie w bazie rozwiązań (embeddingi)
- [ ] Dashboard historii sesji
- [ ] Automatyczny zapis zatwierdzonych rozwiązań do bazy
- [ ] Metryki skuteczności agenta

---

## 12. Otwarte pytania

1. Czy agent ma mieć dostęp do wielu baz (DEV/TEST/PROD) i dynamicznie przełączać środowisko?
2. Jaki format ma dokumentacja Excel — jeden plik z wieloma arkuszami, czy wiele plików?
3. Czy kod wklejany do ERP jest SQL wyzwalany przez GUI, czy inny format (np. XML, skrypt VBA)?
4. Czy wymagana jest obsługa multi-tenancy (wielu klientów ERP z różnymi schematami)?
5. Czy logi sesji mają trafiać do systemu kontroli wersji (Git)?

---

*Dokument przygotowany: 2026-02-26*
*Status: Wersja robocza — do weryfikacji przez zespół*
