# ARCHITECTURE: Mrowisko

*Dokument przygotowany: 2026-03-21 | Wersja: 1.1*

---

## 1. Słownik

> Poznaj nomenklaturę przed czytaniem szczegółów.

| Termin | Definicja |
|--------|-----------|
| **Agent** | Instancja Claude Code z przypisaną rolą |
| **Rola** | Zestaw uprawnień, narzędzi i workflow (np. ERP Specialist) |
| **Workflow** | Sekwencja kroków realizacji konkretnego typu zadania |
| **Sugestia** | Obserwacja agenta zapisana do przeglądu (suggest) |
| **Backlog** | Kolejka zadań do realizacji |
| **Flag** | Eskalacja do człowieka |
| **Horyzont** | Etap rozwoju projektu (H1/H2/H3) |
| **Wykonawca** | Rola realizująca zadania domenowe (ERP Specialist, Analityk, Bot) |
| **Meta-rola** | Rola budująca system (Developer, Architect, PE, Metodolog) |

---

## 2. Wizja systemu

**Mrowisko** — inkubator wirtualnego życia AI. System wieloagentowy, w którym agenci LLM
autonomicznie prowadzą firmę produkcyjną. ERP Comarch XL jest pierwszym terenem działania,
nie celem samym w sobie.

Pełna wizja: `documents/methodology/SPIRIT.md`

### 2.1 Horyzonty rozwoju

| Horyzont | Cel | Status |
|----------|-----|--------|
| H1 | Autonomiczna konfiguracja ERP (widoki BI, kolumny, filtry) | ✓ Zrealizowany |
| H2 | Produkt dla branży ERP (niezależny od Comarch XL) | W planach |
| H3 | Dom roju — metodologia, kultura, pamięć zbiorowa | Wizja |

---

## 3. Diagram wysokiego poziomu

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              CZŁOWIEK                                     │
│                         (nadzór, decyzje)                                │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │ flag / eskalacja (każda rola może)
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         WARSTWA AGENTÓW (Claude Code)                     │
│                                                                           │
│  ┌─────────────┐  ┌───────────┐  ┌─────────────┐  ┌─────────────────────┐│
│  │ Metodolog   │  │ Architect │  │ Prompt Eng. │  │      Developer      ││
│  │ (proces)    │  │ (system)  │  │ (prompty)   │  │    (narzędzia)      ││
│  └──────┬──────┘  └─────┬─────┘  └──────┬──────┘  └──────────┬──────────┘│
│         │               │               │                    │           │
│         └───────────────┴───────┬───────┴────────────────────┘           │
│                     (wielokanałowa komunikacja)                          │
│                          ┌──────┴──────┐                                  │
│                          │  agent_bus  │                                  │
│                          │ (mrowisko.db)│                                 │
│                          └──────┬──────┘                                  │
│                                 │                                         │
│         ┌───────────────────────┼───────────────────────┐                 │
│         │                       │                       │                 │
│  ┌──────▼──────┐  ┌─────────────▼───────────┐  ┌───────▼───────┐         │
│  │ERP Specialist│  │      Analityk          │  │     Bot       │         │
│  │(konfiguracja)│  │   (jakość danych)      │  │  (Telegram)   │         │
│  └──────┬───────┘  └───────────┬────────────┘  └───────┬───────┘         │
└─────────┼──────────────────────┼───────────────────────┼─────────────────┘
          │                      │                       │
          ▼                      ▼                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         WARSTWA NARZĘDZI (tools/)                         │
│                                                                           │
│  sql_query │ docs_search │ solutions_search │ excel_export │ bi_*        │
│  windows_* │ offer_*     │ wycena_*         │ etykiety_*   │ data_quality│
│                                                                           │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐  ┌─────────────────────┐  ┌─────────────────────────┐
│   SQL Server    │  │    SQLite Local     │  │     Pliki (solutions/)  │
│  CDN.* / AIBI.* │  │ docs.db │ mrowisko.db│ │   erp_windows.json      │
└─────────────────┘  └─────────────────────┘  └─────────────────────────┘
```

---

## 4. Warstwy systemu

### 4.1 Warstwa agentów

System wieloagentowy z 6 rolami operującymi w Claude Code (VS Code).

| Rola | Zakres | Typ |
|------|--------|-----|
| **ERP Specialist** | Konfiguracja okien ERP, widoki BI, kolumny, filtry | Wykonawca |
| **Analityk** | Analiza jakości danych, przegląd widoków BI | Wykonawca |
| **Bot** | Odpowiedzi na pytania o dane ERP (Telegram) | Wykonawca |
| **Developer** | Budowa narzędzi, integracja, CI/CD | Meta-rola |
| **Architect** | Projektowanie architektury, code review, ADR | Meta-rola |
| **Prompt Engineer** | Edycja promptów ról, kompresja, wersjonowanie | Meta-rola |
| **Metodolog** | Kształtowanie procesu, zasady pracy, wizja | Meta-rola |

**Model eskalacji:** Wielokanałowy, nie hierarchiczny.

- Każda rola może eskalować do **człowieka** (flag)
- Developer ↔ Architect ↔ Prompt Engineer — wzajemna komunikacja
- Wykonawcy → Meta-role (gdy problem wykracza poza domenę)
- Meta-role → Metodolog (gdy problem dotyczy procesu/wizji)

### 4.2 Warstwa komunikacji (agent_bus)

Centralna szyna komunikacji między agentami. Wszystko w SQLite (`mrowisko.db`).

| Encja | Opis |
|-------|------|
| **messages** | Wiadomości między rolami (send/inbox) |
| **suggestions** | Obserwacje i propozycje (open → in_backlog → implemented) |
| **backlog** | Zadania do realizacji (planned → in_progress → done) |
| **session_log** | Logi sesji per rola |
| **flags** | Eskalacje do człowieka |

**Historia sesji (również w mrowisko.db):**

| Tabela | Zawartość |
|--------|-----------|
| **sessions** | Metadane sesji Claude Code |
| **conversation** | Pełna historia wiadomości |
| **tool_calls** | Wywołania narzędzi |
| **token_usage** | Zużycie tokenów |

**CLI:** `tools/agent_bus_cli.py` — wszystkie operacje przez JSON stdout.

### 4.3 Warstwa narzędzi

~50 skryptów Python w `tools/`. Każde narzędzie:
- Przyjmuje argumenty CLI
- Zwraca JSON na stdout
- Jest niezależnym procesem (brak stanu między wywołaniami)

| Kategoria | Narzędzia |
|-----------|-----------|
| **ERP** | sql_query, docs_search, solutions_search, windows_search, solutions_save |
| **Excel** | excel_export, excel_export_bi, excel_read_stats, excel_read_rows |
| **BI** | bi_catalog_add, bi_discovery, bi_plan_generate, bi_verify, search_bi |
| **Oferty** | offer_generator, offer_pdf, offer_ui |
| **Wyceny** | wycena_generate, wycena_ui |
| **Etykiety** | etykiety_export, etykiety_ui |
| **Data Quality** | data_quality_init, data_quality_query, data_quality_report |
| **Sesja** | session_init, render.py, git_commit.py, conversation_search |
| **Komunikacja** | agent_bus_cli, agent_bus_server |

**Współdzielona logika:** `tools/lib/` (SqlClient, ExcelWriter, ExcelReader, AgentBus, output)

### 4.4 Warstwa danych

| Źródło | Technologia | Zawartość |
|--------|-------------|-----------|
| **SQL Server** | MSSQL | ERP Comarch XL (CDN.*), widoki BI (AIBI.*) |
| **docs.db** | SQLite FTS5 | Indeks dokumentacji ERP (~7 MB) |
| **mrowisko.db** | SQLite | Komunikacja agentów, backlog, logi, historia sesji |
| **solutions/** | Pliki .sql + JSON | Rozwiązania SQL, katalog okien ERP |

---

## 5. Komponenty produktowe

### 5.1 Bot Telegram (`bot/`)

Odpowiada na pytania o dane ERP w naturalnym języku.

```
Pytanie użytkownika → NLP Pipeline → SQL → Answer Formatter → Odpowiedź
```

| Moduł | Rola |
|-------|------|
| `channels/telegram_channel.py` | Long polling, whitelist użytkowników |
| `pipeline/nlp_pipeline.py` | Match raport lub generuj SQL ad-hoc |
| `pipeline/sql_validator.py` | Guardrails: blokada DML, TOP 100, timeout |
| `sql_executor.py` | Wykonanie SQL na AIBI.* |
| `answer_formatter.py` | Dane + pytanie → odpowiedź PL |

*Szczegóły techniczne: patrz `documents/architecture/bot.md` (do utworzenia)*

### 5.2 Oferty katalogowe

Generowanie PDF z ofertami produktowymi na podstawie danych z ERP.

### 5.3 Wyceny

Generowanie arkuszy wycen dla klientów.

### 5.4 Etykiety wysyłkowe

Drukowanie etykiet na podstawie zamówień.

---

## 6. Struktura dokumentacji

> **UWAGA:** Struktura wymaga refaktoru — chaos, brak folderu dla człowieka.

```
documents/
├── ARCHITECTURE.md        # Ten dokument — architektura systemu
├── architecture/          # Szczegóły per moduł (do utworzenia)
├── analyst/               # Instrukcje Analityka
├── architect/             # Instrukcje Architekta
├── dev/                   # Instrukcje Developera + plany
├── erp_specialist/        # Instrukcje ERP + workflow SQL
├── methodology/           # SPIRIT.md, METHODOLOGY.md
├── prompt_engineer/       # Konwencje promptów, archiwa
├── archive/               # Zdezaktualizowane dokumenty
└── Wzory plików/          # Szablony ofert, brandbook
```

**Problem:** Brak wydzielonego folderu dla człowieka (eksporty, plany, backlogi, sugestie, propozycje do review). Powinien być Obsidian-friendly.

---

## 7. _loom — seed replikacji

Katalog `_loom/` zawiera minimalne szablony do uruchomienia Mrowiska w nowym projekcie:

- `CLAUDE_template.md` — szablon CLAUDE.md
- `seed.md` — instrukcja bootstrapu
- `documents/` — minimalne prompty ról

Cel: replikacja metodologii do innych domen (nie tylko ERP).

**Problem architektoniczny:** Odpinalność meta-warstwy od wykonawczej.

Przy wdrożeniu u klienta:
- Zostawiamy: role wykonawcze (ERP Specialist, Analityk, Bot)
- Odpinamy: meta-role (Developer, Architect, PE, Metodolog)

Wymaga przemyślenia struktury repo tak, aby "narzędzia do tworzenia narzędzi" były łatwo odpinalne i przypinalne.

---

## 8. Przepływ pracy

### 8.1 Sesja agenta

```
1. session_init.py --role <rola>
   → generuje session_id
   → zwraca prompt roli (doc_content)

2. Agent czyta inbox i backlog
   → agent_bus_cli.py inbox/backlog

3. Agent realizuje zadania zgodnie z workflow roli
   → używa narzędzi z tools/
   → loguje postęp (agent_bus_cli.py log)

4. Agent zapisuje obserwacje
   → agent_bus_cli.py suggest

5. Agent kończy sesję lub eskaluje
   → agent_bus_cli.py flag (gdy potrzebna decyzja człowieka)
```

### 8.2 Workflow gate

Każda rola ma zdefiniowane workflow. Agent:
1. Dopasowuje zadanie do workflow
2. Komunikuje: "Wchodzę w workflow: [nazwa]"
3. Wykonuje kroki workflow

Brak workflow → eskalacja do Prompt Engineer (który tworzy workflow).

---

## 9. Bezpieczeństwo

| Warstwa | Zabezpieczenie |
|---------|---------------|
| SQL Server CDN.* | Konto CEIM_AIBI nie ma dostępu (fizyczna separacja) |
| SQL Server AIBI.* | SELECT only, brak DDL/DML |
| Generowany SQL | Walidator: blokada DML/EXEC, TOP 100, timeout 30s |
| Bot endpoint | Cloudflare Tunnel (brak publicznego IP) |
| Użytkownicy bota | Whitelist ID w `.env` |
| Pliki chronione | Lista w CLAUDE.md — wymagają zatwierdzenia przed edycją |

*Szczegóły: patrz `documents/architecture/security.md` (do utworzenia)*

---

## 10. Otwarte decyzje architektoniczne

| ID | Temat | Status |
|----|-------|--------|
| #90 | Synchronizacja mrowisko.db między maszynami | planned |
| — | Odpinalność meta-warstwy (_loom) od wykonawczej | do zaprojektowania |
| — | Folder dla człowieka (Obsidian-friendly) | do zaprojektowania |
| — | Wersjonowanie promptów ról (git tags?) | do rozważenia |

---

*Dokument utrzymywany przez: Architect*
*Lokalizacja: documents/ARCHITECTURE.md*
