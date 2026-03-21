# ARCHITECTURE: Mrowisko

*Dokument przygotowany: 2026-03-21 | Wersja: 1.0*

---

## 1. Wizja systemu

**Mrowisko** — inkubator wirtualnego życia AI. System wieloagentowy, w którym agenci LLM
autonomicznie prowadzą firmę produkcyjną. ERP Comarch XL jest pierwszym terenem działania,
nie celem samym w sobie.

Pełna wizja: `documents/methodology/SPIRIT.md`

### 1.1 Horyzonty rozwoju

| Horyzont | Cel | Status |
|----------|-----|--------|
| H1 | Autonomiczna konfiguracja ERP (widoki BI, kolumny, filtry) | ✓ Zrealizowany |
| H2 | Produkt dla branży ERP (niezależny od Comarch XL) | W planach |
| H3 | Dom roju — metodologia, kultura, pamięć zbiorowa | Wizja |

---

## 2. Diagram wysokiego poziomu

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              CZŁOWIEK                                     │
│                         (nadzór, decyzje)                                │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │ flag / eskalacja
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
│                                 │                                         │
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

## 3. Warstwy systemu

### 3.1 Warstwa agentów

System wieloagentowy z 6 rolami operującymi w Claude Code (VS Code).

| Rola | Zakres | Eskaluje do |
|------|--------|-------------|
| **ERP Specialist** | Konfiguracja okien ERP, widoki BI, kolumny, filtry | Developer |
| **Analityk** | Analiza jakości danych, przegląd widoków BI | Developer |
| **Bot** | Odpowiedzi na pytania o dane ERP (Telegram) | — |
| **Developer** | Budowa narzędzi, integracja, CI/CD | Metodolog |
| **Architect** | Projektowanie architektury, code review, ADR | Metodolog |
| **Prompt Engineer** | Edycja promptów ról, kompresja, wersjonowanie | Metodolog |
| **Metodolog** | Kształtowanie procesu, zasady pracy, wizja | Człowiek |

**Zasada eskalacji:** Wykonawcy (ERP/Analyst/Bot) → Developer/Architect/PE → Metodolog → Człowiek

### 3.2 Warstwa komunikacji (agent_bus)

Centralna szyna komunikacji między agentami. Wszystko w SQLite (`mrowisko.db`).

| Encja | Opis |
|-------|------|
| **messages** | Wiadomości między rolami (send/inbox) |
| **suggestions** | Obserwacje i propozycje (open → in_backlog → implemented) |
| **backlog** | Zadania do realizacji (planned → in_progress → done) |
| **session_logs** | Logi sesji per rola |
| **flags** | Eskalacje do człowieka |

**CLI:** `tools/agent_bus_cli.py` — wszystkie operacje przez JSON stdout.

### 3.3 Warstwa narzędzi

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

### 3.4 Warstwa danych

| Źródło | Technologia | Zawartość |
|--------|-------------|-----------|
| **SQL Server** | MSSQL | ERP Comarch XL (CDN.*), widoki BI (AIBI.*) |
| **docs.db** | SQLite FTS5 | Indeks dokumentacji ERP (~7 MB) |
| **mrowisko.db** | SQLite | Komunikacja agentów, backlog, logi |
| **solutions/** | Pliki .sql + JSON | Rozwiązania SQL, katalog okien ERP |

---

## 4. Komponenty produktowe

### 4.1 Bot Telegram (`bot/`)

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

### 4.2 Oferty katalogowe

Generowanie PDF z ofertami produktowymi na podstawie danych z ERP.

- `tools/offer_generator.py` — logika
- `tools/offer_pdf.py` — renderowanie PDF
- `tools/offer_ui.py` — prosty GUI

### 4.3 Wyceny

Generowanie arkuszy wycen dla klientów.

- `tools/wycena_generate.py` — logika
- `tools/wycena_ui.py` — GUI

### 4.4 Etykiety wysyłkowe

Drukowanie etykiet na podstawie zamówień.

- `tools/etykiety_export.py` — eksport danych
- `tools/etykiety_ui.py` — GUI

---

## 5. Struktura dokumentacji

```
documents/
├── ARCHITECTURE.md        # Ten dokument — architektura systemu
├── architecture/          # Szczegóły per moduł (tworzone w miarę potrzeb)
│   └── (bot.md, erp_agent.md, security.md — do utworzenia)
├── analyst/               # Instrukcje Analityka
├── architect/             # Instrukcje Architekta
├── dev/                   # Instrukcje Developera + plany
├── erp_specialist/        # Instrukcje ERP + workflow SQL
├── methodology/           # SPIRIT.md, METHODOLOGY.md
├── prompt_engineer/       # Konwencje promptów, archiwa
├── archive/               # Zdezaktualizowane dokumenty
└── Wzory plików/          # Szablony ofert, brandbook
```

---

## 6. _loom — seed replikacji

Katalog `_loom/` zawiera minimalne szablony do uruchomienia Mrowiska w nowym projekcie:

- `CLAUDE_template.md` — szablon CLAUDE.md
- `seed.md` — instrukcja bootstrapu
- `documents/` — minimalne prompty ról

Cel: replikacja metodologii do innych domen (nie tylko ERP).

---

## 7. Przepływ pracy

### 7.1 Sesja agenta

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

### 7.2 Workflow gate

Każda rola ma zdefiniowane workflow. Agent:
1. Dopasowuje zadanie do workflow
2. Komunikuje: "Wchodzę w workflow: [nazwa]"
3. Wykonuje kroki workflow

Brak workflow → eskalacja do Prompt Engineer (który tworzy workflow).

---

## 8. Bezpieczeństwo

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

## 9. Otwarte decyzje architektoniczne

| ID | Temat | Status |
|----|-------|--------|
| #90 | Synchronizacja mrowisko.db między maszynami | planned |
| — | Rozdzielenie _loom jako osobnego repo | do rozważenia |
| — | Wersjonowanie promptów ról (git tags?) | do rozważenia |

---

## 10. Słownik

| Termin | Definicja |
|--------|-----------|
| **Agent** | Instancja Claude Code z przypisaną rolą |
| **Rola** | Zestaw uprawnień, narzędzi i workflow (np. ERP Specialist) |
| **Workflow** | Sekwencja kroków realizacji konkretnego typu zadania |
| **Sugestia** | Obserwacja agenta zapisana do przeglądu (suggest) |
| **Backlog** | Kolejka zadań do realizacji |
| **Flag** | Eskalacja do człowieka |
| **Horyzont** | Etap rozwoju projektu (H1/H2/H3) |

---

*Dokument utrzymywany przez: Architect*
*Lokalizacja: documents/ARCHITECTURE.md*
