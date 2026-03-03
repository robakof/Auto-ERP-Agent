# ARCHITECTURE: Automatyczny Konfigurator Systemu ERP

*Dokument przygotowany: 2026-02-26 | Zaktualizowany: 2026-03-03*

---

## Część 1 — Agent ERP (Faza 1, zrealizowana)

---

### 1.1 Diagram wysokiego poziomu

```
Użytkownik (VS Code)
        │
        ▼
  Claude Code (agent)
        │
        ├──► python tools/sql_query.py "SELECT ..."
        │           │
        │           └──► SQL Server (read-only, CDN.*)
        │
        ├──► python tools/search_docs.py "zamówienie kontrahent"
        │           │
        │           └──► erp_docs/index/docs.db (SQLite FTS5)
        │
        ├──► python tools/search_solutions.py "kolumna KntKarty"
        │           │
        │           └──► solutions/**/*.sql
        │
        ├──► python tools/search_windows.py "towary"
        │           │
        │           └──► solutions/erp_windows.json
        │
        └──► python tools/save_solution.py ...
                    │
                    └──► solutions/ (zapis po akceptacji człowieka)
```

---

### 1.2 Komponenty systemu

#### Agent — Claude Code

Rdzeń systemu. Operuje wewnątrz VS Code, wywołuje narzędzia jako komendy CLI,
iteruje do uzyskania poprawnego wyniku. Nie ma własnego kodu — to konfiguracja
środowiska (`.env`, `CLAUDE.md`).

#### Narzędzia (tools/)

Skrypty Python wywoływane przez agenta. Każde narzędzie to niezależny proces —
przyjmuje argumenty z CLI, zwraca JSON na stdout, kończy działanie.

| Skrypt | Wejście | Wyjście |
|--------|---------|---------|
| `sql_query.py` | zapytanie SQL | wyniki SELECT jako JSON |
| `search_docs.py` | fraza / tabela | kolumny ERP z opisami i słownikami wartości |
| `search_solutions.py` | fraza / okno | lista rozwiązań SQL z kodem |
| `search_windows.py` | fraza | okna ERP z tabelami i typami konfiguracji |
| `save_solution.py` | kod SQL + metadane | zapis do `solutions/` |
| `update_window_catalog.py` | id + parametry | upsert w `erp_windows.json` |
| `build_index.py` | ścieżka XLSM | rebuild `docs.db` |

#### Indeks dokumentacji (erp_docs/index/docs.db)

SQLite FTS5, budowany z pliku XLSM dokumentacji ERP. Zawiera tabele, kolumny,
relacje, słowniki wartości, przykładowe wartości. Wersjonowany w Git (~7 MB).

#### Baza rozwiązań (solutions/)

```
solutions/
├── erp_windows.json
└── solutions in ERP windows/
    └── [Okno ERP]/
        └── [Widok]/
            ├── filtr.sql       ← kotwica widoku
            ├── columns/[nazwa].sql
            └── filters/[nazwa].sql
```

#### Synchronizacja

Model Git. Agent commituje nowe rozwiązania po akceptacji, developer pushuje,
inni robią `git pull`.

---

### 1.3 Kontrakty JSON narzędzi

**Schemat bazowy:**
```json
{
  "ok": true,
  "data": { "..." : "..." },
  "error": { "type": "...", "message": "..." }
}
```

**`search_solutions.py`:**
```json
{
  "results": [{
    "window": "Okno lista zamówień sprzedaży",
    "view":   "Zamówienia",
    "type":   "columns",
    "name":   "knt_nazwa_w_zamowieniach",
    "sql":    "...",
    "filtr_sql": "..."
  }]
}
```

**`search_windows.py`:**
```json
{
  "results": [{
    "id":            "lista_zamowien_sprzedazy",
    "name":          "Lista zamówień sprzedaży",
    "aliases":       ["okno zamówień", "lista ZO"],
    "primary_table": "CDN.ZamNag",
    "config_types":  ["columns", "filters"]
  }]
}
```

---

### 1.4 Deployment

```
git clone https://github.com/CyperCyper/Auto-ERP-Agent.git
pip install -r requirements.txt
copy .env.example .env   # uzupełnij SQL credentials
python verify.py          # weryfikacja: docs.db, solutions/, SQL Server
```

---

## Część 2 — Warstwa BI + Bot Pytań (Faza 2)

---

### 2.1 Diagram wysokiego poziomu

```
┌─────────────────────────────────────────────────────────────┐
│  Serwer firmowy (Windows, sieć lokalna)                      │
│                                                              │
│  ┌──────────────────────────────────────┐                   │
│  │  Bot Backend (Python serwis, NSSM)   │                   │
│  │                                      │                   │
│  │  ┌────────────┐  ┌────────────────┐  │                   │
│  │  │  Telegram  │  │  WhatsApp      │  │                   │
│  │  │  channel   │  │  channel       │  │                   │
│  │  │ (polling)  │  │  (webhook)     │  │                   │
│  │  └─────┬──────┘  └───────┬────────┘  │                   │
│  │        └────────┬────────┘           │                   │
│  │                 ▼                    │                   │
│  │        NLP Pipeline                  │                   │
│  │         ├─ Report Matcher ───────────┼──► solutions/bi/  │
│  │         └─ SQL Generator ────────────┼──► Claude API     │
│  │                 │                    │    (HTTPS out)     │
│  │                 ▼                    │                   │
│  │        SQL Executor (pyodbc) ─────────┼──► SQL Server     │
│  │                 │                    │    BI schema      │
│  │                 ▼                    │                   │
│  │        Answer Formatter ─────────────┼──► Claude API     │
│  └──────────────────────────────────────┘                   │
│                                                              │
│  Cloudflare Tunnel (tylko WhatsApp webhook, port 8000)       │
└─────────────────────────────────────────────────────────────┘

Zewnętrznie:
├── Telegram API    (HTTPS out od serwera)
├── WhatsApp API    (HTTPS in/out przez Cloudflare Tunnel)
└── Claude API      (HTTPS out od serwera)

SQL Server (ten sam serwer lub sieć lokalna):
├── schema CDN.*    ← baza ERP (bot: brak dostępu)
└── schema BI.*     ← widoki semantyczne (bot: read-only)

Power BI / Excel:
└── DirectQuery / ODBC → SQL Server, schema BI.* (konto CEiM_BI)
```

---

### 2.2 NLP Pipeline

```
Pytanie użytkownika (PL)
        │
        ▼
┌─────────────────┐     dopasowanie    ┌──────────────────────┐
│ Report Matcher  │ ─────────────────► │ Biblioteka raportów  │
│ (Claude API)    │                    │ solutions/bi/reports/ │
└────────┬────────┘                    └──────────────────────┘
         │ brak dopasowania
         ▼
┌─────────────────┐     schemat BI     ┌──────────────────────┐
│ SQL Generator   │ ◄────────────────  │ Katalog BI views     │
│ (Claude API)    │                    │ solutions/bi/        │
└────────┬────────┘                    │ catalog.json         │
         │ SELECT na BI.*              └──────────────────────┘
         ▼
┌─────────────────┐
│ SQL Executor    │ ──► SQL Server, schema BI.* (pyodbc, read-only)
│ (pyodbc)        │
└────────┬────────┘
         │ wyniki JSON
         ▼
┌─────────────────┐
│ Answer Formatter│ ──► Claude API (dane + pytanie → odpowiedź PL)
└────────┬────────┘
         │
         ▼
Odpowiedź do użytkownika (PL)
```

**Co trafia do Claude API:** pytanie + schemat BI (nazwy, opisy kolumn).
Dane z bazy formułowane przez Claude dopiero po ich pobraniu lokalnie —
żadne rekordy nie opuszczają sieci firmowej jako prompt.

---

### 2.3 Schema BI — SQL Server

**Konta SQL:**

| Konto | Uprawnienia | Zastosowanie |
|-------|-------------|-------------|
| `CEiM_Reader` | SELECT na CDN.* | Agent ERP (Faza 1, bez zmian) |
| `CEiM_BI` | SELECT na BI.* (brak CDN.*) | Bot + Power BI + Excel |

**Zasady projektowania widoków:**
- Nazwy widoków: rzeczowniki w liczbie mnogiej, bez prefiksów (`Towary`, `Zamowienia`)
- Nazwy kolumn: PascalCase, opisowe (`NazwaKontrahenta`, `DataZamowienia`)
- Każdy widok ma kolumnę `ID` (klucz — umożliwia relacje w Power BI)
- Widoki nie filtrują danych — zwracają pełne zbiory (filtrowanie po stronie klienta)
- Definicje wersjonowane w `solutions/bi/views/*.sql`

**Priorytety pierwszych widoków:**
1. `BI.Towary` — kartoteki towarowe z grupami, jednostkami, atrybutami
2. `BI.Kontrahenci` — kartoteki kontrahentów z grupami i danymi adresowymi
3. `BI.Zamowienia` — nagłówki zamówień sprzedaży z danymi kontrahenta
4. `BI.PozycjeZamowien` — pozycje zamówień z danymi towaru
5. `BI.DokumentyHandlowe` — faktury, WZ, PZ z nagłówkami
6. `BI.PozycjeDokumentow` — pozycje dokumentów
7. `BI.HistoriaTransakcji` — historia zakupów/sprzedaży per kontrahent/towar

---

### 2.4 Struktura repozytorium (rozszerzona)

```
solutions/
├── erp_windows.json
├── solutions in ERP windows/     ← Faza 1 (bez zmian)
│   └── ...
└── bi/
    ├── catalog.json               ← metadane wszystkich widoków BI
    ├── views/                     ← definicje CREATE VIEW
    │   ├── Towary.sql
    │   ├── Kontrahenci.sql
    │   └── Zamowienia.sql
    └── reports/                   ← biblioteka raportów SQL
        └── [nazwa].sql

tools/
├── (Faza 1 — bez zmian)
├── search_bi.py                   ← wyszukiwanie widoków BI
└── search_reports.py              ← dopasowanie pytania do raportu

bot/
├── main.py                        ← entry point serwisu
├── channels/
│   ├── telegram_channel.py
│   └── whatsapp_channel.py
├── pipeline/
│   ├── nlp_pipeline.py
│   ├── report_matcher.py
│   ├── sql_generator.py
│   └── answer_formatter.py
└── sql_executor.py
```

---

### 2.5 Kanały komunikacji

#### Telegram (testowy) — long polling

```
Serwer firmowy → odpytuje api.telegram.org co N s → odbiera wiadomości
                 (połączenie wychodzące, brak otwierania portów)
```

Autoryzacja: whitelist `TELEGRAM_ALLOWED_IDS` w `.env`.

#### WhatsApp Business (docelowy) — webhook

```
Meta API → POST /webhook → Cloudflare Tunnel → serwer:8000 → bot
```

Cloudflare Tunnel tworzy trwały URL (np. `bot.firma.com`) bez otwierania
portów na firewallu. Serwer sam inicjuje połączenie wychodzące do Cloudflare.

Wymagania przed uruchomieniem:
- Zweryfikowane konto Meta Business Manager
- Dedykowany numer telefonu dla bota
- URL webhooka zarejestrowany w Meta Developer Console

---

### 2.6 Power BI i Excel

Brak dodatkowych komponentów. Schema `BI.*` jest bezpośrednio dostępna
przez standardowe konekcje SQL Server.

**Power BI Desktop:**
```
Get Data → SQL Server → SQLSERVER\SQLEXPRESS → BI → wybierz widoki
Tryb: DirectQuery (dane zawsze aktualne)
Konto: CEiM_BI
```

**Excel:**
```
Data → Get Data → From Database → From SQL Server Database
Server: SQLSERVER\SQLEXPRESS | Database: ERPXL_CEIM | Schema: BI
Konto: CEiM_BI
```

Semantyczne nazwy kolumn eliminują potrzebę transformacji w Power Query.

---

### 2.7 Deployment bota (serwer firmowy)

```bash
# 1. Klonuj repo (lub git pull jeśli już sklonowane)
git clone https://github.com/CyperCyper/Auto-ERP-Agent.git

# 2. Zależności
pip install -r requirements.txt

# 3. Konfiguracja
copy .env.example .env
# Uzupełnij: SQL credentials (CEiM_BI), TELEGRAM_TOKEN,
# WHATSAPP_TOKEN, ANTHROPIC_API_KEY

# 4. Cloudflare Tunnel (jednorazowo dla WhatsApp)
cloudflared tunnel create erp-bot
cloudflared tunnel route dns erp-bot bot.firma.com

# 5. Rejestracja jako serwis Windows
nssm install ERP-Bot python bot\main.py
nssm set ERP-Bot AppDirectory C:\erp-agent
nssm set ERP-Bot AppRestartDelay 5000
nssm start ERP-Bot
```

---

### 2.8 Logowanie

Bot loguje każdą interakcję do pliku lokalnego (`logs/bot/YYYY-MM-DD.jsonl`):

```json
{
  "ts": "2026-03-03T10:15:00",
  "channel": "telegram",
  "user_id": "123456",
  "question": "kto ostatnio zamawiał Bolsiusa?",
  "matched_report": null,
  "generated_sql": "SELECT TOP 5 ...",
  "row_count": 3,
  "answer": "Ostatnio Bolsiusa zamawiała firma X ...",
  "duration_ms": 8200
}
```

Logi są źródłem danych do budowania biblioteki raportów (Faza 2c) —
analiza najczęstszych pytań bez dopasowania do gotowego raportu.

---

## Część 3 — Bezpieczeństwo (podsumowanie)

| Warstwa | Zabezpieczenie |
|---------|---------------|
| SQL Server CDN.* | Konto `CEiM_BI` nie ma dostępu — fizyczna separacja |
| SQL Server BI.* | Konto `CEiM_BI`: SELECT only, bez DDL/DML |
| Bot endpoint | Cloudflare Tunnel — serwer nie ma publicznego IP |
| Claude API | Wysyłamy: pytanie + schemat BI (nazwy kolumn). Zero danych z bazy |
| Autoryzacja użytkowników | Whitelist numerów/ID w `.env` |
| Logi | Lokalne na serwerze firmowym, nie w repozytorium |
