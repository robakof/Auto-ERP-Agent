# PRD Faza 2: Warstwa Semantyczna BI + Bot Pytań

*Dokument przygotowany: 2026-03-03*
*Status: Wersja robocza*

---

## 1. Cel fazy

Zbudowanie warstwy semantycznej nad bazą ERP (widoki SQL z czytelnymi nazwami),
która służy trzem celom jednocześnie:

1. **Raportowanie** — Power BI i Excel łączą się z `BI.*` bezpośrednio, bez znajomości schematu CDN
2. **Bot pytań** — pracownicy zadają pytania w języku naturalnym, bot odpytuje `BI.*`
3. **Szybszy agent ERP** — agent Fazy 1 używa `BI.*` zamiast budować JOINy z CDN.*

---

## 2. Kontekst i problem

### AS-IS

Agent konfigurujący ERP (Faza 1) odpytuje bezpośrednio tabele `CDN.*`.
Każde zapytanie wymaga znajomości schematu: złożone JOINy, nieczytelne nazwy
kolumn (`ZaN_KntGIDNumer`), konieczność przeglądania dokumentacji.

Pracownicy chcący uzyskać informacje z systemu (np. "kto ostatnio zamawiał
Bolsiusa?") muszą każdorazowo angażować konfiguratora lub developera.

### TO-BE

```
Pracownik (WhatsApp)
    │  "Kto ostatnio zamawiał Bolsiusa?"
    ▼
Bot Backend
    ├── identyfikuje intencję
    ├── sprawdza bibliotekę raportów (gotowe zapytania)
    │       hit → wykonuje gotowy SQL z parametrami
    │       miss → generuje SQL ad-hoc z BI views
    ├── wykonuje SELECT na schema BI (read-only)
    └── formułuje odpowiedź w języku naturalnym
    │
    ▼
Pracownik otrzymuje odpowiedź w ~10 sekund
```

Warstwa BI skraca agenta — zamiast budować JOINy przez `CDN.TwrKarty`
+ `CDN.ZamNag` + `CDN.KntKarty`, pyta `BI.Zamowienia` gdzie wszystko jest już złączone.

---

## 3. Zakres

### W zakresie

- Schema `BI` z semantycznymi widokami SQL (tworzone przez człowieka)
- Dokumentacja widoków w repozytorium (agent i deweloper wiedzą co jest dostępne)
- Bot backend: NLP → SQL → odpowiedź w języku naturalnym (polskim)
- Kanał testowy: Telegram
- Kanał docelowy: WhatsApp Business
- Biblioteka raportów SQL (gotowe zapytania dla częstych pytań)
- Rozszerzenie agenta ERP o wyszukiwanie w BI views

### Poza zakresem

- Comarch API (kolejna faza)
- Zapis danych przez bota (wyłącznie odczyt)
- Tworzenie widoków BI przez agenta (człowiek tworzy, agent dokumentuje i używa)
- Budowa dashboardów Power BI (warstwa BI *umożliwia* to — sama budowa poza zakresem)

---

## 4. Użytkownicy i role

| Rola | Opis | Interakcja |
|------|------|-----------|
| **Pracownik** | Zadaje pytania o dane w języku naturalnym | WhatsApp / Telegram |
| **Konfigurator ERP** | Rozszerza agent o nowe widoki i raporty | VS Code + Claude Code |
| **Developer** | Tworzy i utrzymuje widoki BI, zarządza infrastrukturą | SQL Server + Git |

---

## 5. Wymagania funkcjonalne

### F-01 — Schema BI (widoki semantyczne)

- Dedykowany schema SQL (`BI`) na istniejącym SQL Serverze
- Widoki pokrywają kluczowe encje biznesowe: towary, kontrahenci, zamówienia,
  dokumenty handlowe, historia transakcji
- Czytelne nazwy widoków i kolumn (np. `BI.Zamowienia.NazwaKontrahenta`)
- Tworzone i modyfikowane przez człowieka (Developer)
- Definicje widoków wersjonowane w repozytorium Git (`solutions/bi/views/`)
- Konto agenta/bota: read-only na schema `BI`, brak dostępu do `CDN.*`
- **Kompatybilność z Power BI i Excel z definicji** — połączenie przez DirectQuery
  (Power BI) lub Power Query / ODBC (Excel) bez żadnej dodatkowej pracy

### F-02 — Dokumentacja widoków BI

- Każdy widok opisany w pliku YAML/SQL z komentarzem: cel, kolumny, przykładowe pytania
- Narzędzie `search_bi.py` — agent przeszukuje dostępne widoki po słowach kluczowych
- Integracja z istniejącym workflow agenta (Krok 2: odczytaj kontekst → sprawdź BI views)

### F-03 — Bot backend

- Uruchomiony jako serwis Windows (serwer firmowy, sieć lokalna)
- Przyjmuje pytanie w języku naturalnym (polskim)
- Pipeline:
  1. Dopasuj do biblioteki raportów (parametryzowane zapytania)
  2. Jeśli brak dopasowania → wygeneruj SQL ad-hoc z BI views (Claude API)
  3. Wykonaj SELECT (read-only, schema BI)
  4. Sformułuj odpowiedź w języku naturalnym
- Loguje pytania i odpowiedzi (źródło danych do budowy biblioteki raportów)
- Obsługuje brak wyników, błędy SQL, pytania poza zakresem

### F-04 — Kanał Telegram (testowy)

- Telegram Bot API (bez weryfikacji biznesowej)
- Cel: weryfikacja całego pipeline przed wdrożeniem WhatsApp
- Dostęp: tylko zdefiniowane ID użytkowników (whitelist)

### F-05 — Kanał WhatsApp Business (docelowy)

- Meta WhatsApp Business API (Cloud API lub BSP)
- Wymaga: zweryfikowane konto Meta Business
- Ten sam backend co Telegram — kanał to tylko warstwa transportowa
- Dostęp: numer telefonu na whiteliście lub autoryzacja przez komendę /start

### F-06 — Biblioteka raportów SQL

- Zbiór gotowych, przetestowanych zapytań SQL z parametrami
- Format: pliki `.sql` w `solutions/bi/reports/` z metadanymi (przykładowe pytania,
  parametry, opis)
- Budowana iteracyjnie na podstawie logów pytań bota
- Bot sprawdza bibliotekę przed generowaniem ad-hoc → szybciej i pewniej
- Narzędzie `search_reports.py` — dopasowanie pytania do gotowego raportu

### F-07 — Rozszerzenie agenta ERP

- Agent ERP (Faza 1) otrzymuje dostęp do `search_bi.py` i `search_reports.py`
- Workflow: przed budowaniem JOIN z CDN.* sprawdź czy BI views pokrywają zapytanie
- Zapisuje nowe raporty do biblioteki po zatwierdzeniu przez człowieka

---

## 6. Wymagania niefunkcjonalne

| ID | Wymaganie | Miara |
|----|-----------|-------|
| NF-01 | Czas odpowiedzi bota | < 15 sekund dla gotowego raportu, < 30 s ad-hoc |
| NF-02 | Bezpieczeństwo danych | Bot i agent: read-only na schema BI, zero dostępu do CDN.* |
| NF-03 | Lokalność danych | Zapytania SQL nie wychodzą poza sieć firmową; do Claude API trafia tylko pytanie i schemat BI |
| NF-04 | Dostępność bota | Serwis Windows z auto-restartem (99% uptime w godzinach pracy) |
| NF-05 | Audytowalność | Wszystkie pytania i odpowiedzi logowane lokalnie |

---

## 7. Architektura

```
Serwer firmowy (Windows, sieć lokalna)
│
├── Bot Backend (Python serwis)
│   ├── Moduł kanałów
│   │   ├── telegram_channel.py    ← Telegram Bot API
│   │   └── whatsapp_channel.py    ← Meta Cloud API
│   ├── nlp_pipeline.py            ← pytanie → SQL (Claude API)
│   ├── report_matcher.py          ← dopasowanie do biblioteki raportów
│   └── sql_executor.py            ← SELECT na schema BI (read-only)
│
└── SQL Server (istniejący)
    ├── schema CDN.*               ← baza ERP (bot: brak dostępu)
    └── schema BI.*                ← widoki semantyczne (bot: read-only)
        ├── BI.Towary
        ├── BI.Kontrahenci
        ├── BI.Zamowienia
        ├── BI.DokumentyHandlowe
        └── ...

Repozytorium Git
├── solutions/bi/
│   ├── views/                     ← definicje CREATE VIEW (wersjonowane)
│   │   ├── Towary.sql
│   │   ├── Kontrahenci.sql
│   │   └── Zamowienia.sql
│   ├── reports/                   ← biblioteka raportów SQL
│   │   └── [nazwa].sql
│   └── catalog.json               ← metadane widoków (dla search_bi.py)
│
└── tools/
    ├── search_bi.py               ← wyszukiwanie widoków BI
    └── search_reports.py          ← dopasowanie pytania do raportu
```

---

## 8. Kwestie otwarte

| # | Pytanie | Wpływ |
|---|---------|-------|
| O-01 | Autoryzacja użytkowników bota — whitelist numerów/ID, czy coś innego? | Bezpieczeństwo |
| O-02 | Nazwa konta SQL dla bota (read-only na BI) — istniejące czy nowe? | Deployment |
| O-03 | Priorytet pierwszych widoków BI — jakie encje najpilniej potrzebne? | Zakres Fazy 2a |
| O-04 | Rejestracja Meta Business Account — kto to robi i kiedy? | Harmonogram F-05 |
| O-05 | Do jakiego stopnia odpowiedzi bota mają być opisowe vs tabelaryczne? | UX |

---

## 9. Etapy realizacji

### Faza 2a — Fundament BI (widoki + narzędzia)

- [ ] Struktura `solutions/bi/` w repozytorium
- [ ] Pierwsze widoki BI (priorytety z O-03)
- [ ] `search_bi.py` — narzędzie przeszukiwania katalogu widoków
- [ ] Rozszerzenie agenta ERP o `search_bi.py`

### Faza 2b — Bot backend + Telegram

- [ ] Bot backend jako serwis Windows (Python)
- [ ] Pipeline NLP → SQL → odpowiedź
- [ ] Kanał Telegram (whitelist użytkowników)
- [ ] Logowanie pytań i odpowiedzi
- [ ] Testy end-to-end (5+ pytań reprezentatywnych)

### Faza 2c — Biblioteka raportów

- [ ] Analiza logów bota → identyfikacja częstych pytań
- [ ] `search_reports.py` + format plików raportów
- [ ] Rozszerzenie agenta ERP o zapis nowych raportów
- [ ] Integracja z pipeline bota (raport → ad-hoc fallback)

### Faza 2d — WhatsApp Business

- [ ] Rejestracja Meta Business Account
- [ ] `whatsapp_channel.py` (ten sam backend)
- [ ] Testy i wdrożenie produkcyjne

---

## 10. Definicja sukcesu

| Kryterium | Miara |
|-----------|-------|
| Pokrycie BI views | Widoki pokrywają ≥ 80% pytań zadawanych przez pracowników |
| Skuteczność bota | ≥ 70% pytań odpowiedzianych poprawnie bez interwencji człowieka |
| Adopcja | Po 1 miesiącu ≥ 5 aktywnych użytkowników bota |
| Czas odpowiedzi | Mediana < 15 s |
