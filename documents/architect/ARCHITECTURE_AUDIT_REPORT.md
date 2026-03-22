# Raport audytu architektonicznego: Mrowisko

*Data rozpoczęcia: 2026-03-22*
*Rola: Architect*
*Status: W trakcie (Faza 1-4 zakończone)*

---

## Faza 1: Inspekcja warstwy narzędzi (tools/)

### 1.1 Rozmiary plików

| Kategoria | Liczba | Pliki |
|-----------|--------|-------|
| **God scripts (>300 linii)** | 4 | `wycena_generate.py` (571), `render.py` (449), `agent_bus_cli.py` (402), `offer_pdf_3x3.py` (399) |
| Large (100-300) | ~20 | UI, PDF, eksporty |
| Small (<100) | ~27 | Reszta |

**Severity: Medium**
- 4 pliki przekraczają 300 linii — potencjalne "god scripts"
- `wycena_generate.py` (571 linii) — największy, złożona logika BOM + Excel

**Rekomendacja:** Przegląd god scripts pod kątem wydzielenia logiki do osobnych modułów.

---

### 1.2 Nazewnictwo

| Problem | Przykłady | Severity |
|---------|-----------|----------|
| **Odwrotne nazewnictwo** | `search_bi.py` (powinno: `bi_search.py`), `conversation_search.py` | Low |
| **Sieroty (14 plików)** | `db.py`, `render.py`, `sql_query.py`, `git_commit.py`, `bot_stop.py`... | Low |
| **Duplikaty offer 3x3** | 3 pary: `offer_*.py` + `offer_*_3x3.py` | Medium |

**Obserwacja:** Konwencja `prefix_action.py` dominuje (~38 plików), ale 2 pliki łamią tę konwencję (`search_bi.py`, `conversation_search.py`).

**Rekomendacja:**
1. Rename `search_bi.py` → `bi_search.py` dla spójności
2. Rozważyć wydzielenie wspólnego kodu `offer_base.py` dla wariantów 3x3

---

### 1.3 Kontrakty JSON

| Kategoria | Liczba | Status |
|-----------|--------|--------|
| Używa `print_json()` | 28 | ✓ OK — spójny kontrakt |
| GUI (tkinter) | 4 | ✓ OK — nie potrzebują JSON |
| Migracje | 5 | ✓ OK — jednorazowe skrypty |
| Biblioteki | 4 | ✓ OK — importowane moduły |
| **Potencjalny problem** | 6 | ⚠ Niespójny output |

**Pliki z niespójnym output:**
- `render.py` — powinien mieć `print_json()` dla `--format json`
- `wycena_generate.py` — brak JSON response o statusie
- `offer_generator.py`, `offer_generator_3x3.py` — brak JSON response
- `docs_build_index.py` — print tekstowy zamiast JSON
- `mrowisko_runner.py` — logging tekstowy (może być OK dla runnera)

**Severity: Low**
- Główne narzędzia agentów używają spójnego kontraktu `{"ok": bool, ...}`
- Niespójność dotyczy głównie generatorów plików (PDF, Excel)

---

### 1.4 Zależności i coupling

| Metryka | Wartość |
|---------|---------|
| Moduły w `tools/lib/` | 8 |
| Pliki importujące z lib/ | 40/51 (78%) |
| Pliki bez zależności od lib/ | 11 |

**Moduły lib/:**
- `agent_bus.py` — komunikacja agentów
- `sql_client.py` — połączenie SQL Server
- `excel_writer.py`, `excel_reader.py`, `excel_editor.py` — operacje Excel
- `output.py` — standardowy JSON output
- `wycena_bom.py` — logika BOM dla wycen

**Severity: Low** — lib/ jest dobrze wykorzystywane, większość narzędzi używa wspólnej logiki.

---

### 1.5 Podsumowanie Fazy 1

| Obszar | Severity | Opis |
|--------|----------|------|
| Rozmiary plików | Medium | 4 god scripts (>300 linii), wymaga refaktoru |
| Nazewnictwo | Low | 2 odwrotne nazwy, 14 sierot, duplikaty offer |
| Kontrakty JSON | Low | 28/51 spójne, 6 potencjalnych problemów |
| Zależności | Low | 78% używa lib/, dobrze zorganizowane |

**Ogólna ocena Fazy 1:** System jest w **dobrym stanie**, bez krytycznych problemów. Główny tech debt to 4 god scripts i duplikacja kodu offer 3x3.

---

## Faza 2: Inspekcja agent_bus (mrowisko.db)

### 2.1 Schema bazy danych

12 tabel w mrowisko.db:

| Tabela | Rekordy | Indeksy | Status |
|--------|---------|---------|--------|
| messages | 171 | 2 | ✓ OK |
| suggestions | 131 | 2 | ✓ OK |
| backlog | 93 | 1 | ✓ OK |
| session_log | 112 | 1 | ✓ OK |
| conversation | 1,523 | 1 | ✓ OK |
| sessions | 47 | 0 | ✓ OK (PK) |
| tool_calls | **30,405** | 1 | ⚠ Duża, brak cleanup |
| token_usage | **44,561** | 1 | ⚠ Duża, brak cleanup |
| agent_instances | 8 | 1 | ✓ OK |
| invocation_log | 6 | 0 | ⚠ Brak indeksu |
| **state** | 34 | 2 | ⚠ Legacy — częściowo zmigrowane |
| **trace** | 0 | 1 | ⚠ Martwa tabela |

**Severity: Medium**
- `tool_calls` (30k) i `token_usage` (44k) rosną bez limitu — brak mechanizmu cleanup
- `state` to legacy tabela (34 rekordy), większość danych zmigrowana do suggestions/backlog
- `trace` to martwa tabela (0 rekordów) — nigdy nie używana

**Rekomendacja:**
1. Dodać cleanup policy dla tool_calls/token_usage (np. archiwizacja >30 dni)
2. Rozważyć usunięcie tabeli `trace` (martwa)
3. Rozważyć deprecation tabeli `state` na rzecz suggestions/backlog

---

### 2.2 Integralność danych

| Test | Wynik |
|------|-------|
| Orphaned suggestions (bad backlog_id) | 0 ✓ |
| Orphaned backlog (bad source_id) | 0 ✓ |
| Orphaned tool_calls (bad session_id) | 0 ✓ |
| Orphaned token_usage (bad session_id) | 0 ✓ |

**Severity: Low** — mimo braku formalnych FK constraints, dane są spójne.

---

### 2.3 Transakcje i atomowość

| Obserwacja | Status |
|------------|--------|
| Jawne transakcje (BEGIN/COMMIT) | ✗ Brak |
| Każda operacja commitowana osobno | ✓ (25 commit() w kodzie) |
| Złożone operacje atomowe | ✗ Brak |

**Severity: Low** — przy obecnej skali (jeden agent naraz) nie ma problemu. Przy wielu agentach równolegle mogą być race conditions.

**Rekomendacja:** Przy implementacji runnera (wielu agentów) dodać transakcje dla złożonych operacji.

---

### 2.4 API agent_bus_cli.py

| Metryka | Wartość |
|---------|---------|
| Komendy CLI | 18 |
| Walidacja argumentów | ✓ Solidna (required, choices, type) |
| Spójny output | ✓ Wszystko przez print_json() |

**Komendy:** send, inbox, state, suggest, suggest-bulk, suggestions, suggest-status, suggest-status-bulk, mark-read, backlog-add, backlog-add-bulk, backlog, backlog-update, backlog-update-bulk, log, delete, flag

**Severity: Low** — API jest kompletne i dobrze zwalidowane.

---

### 2.5 Podsumowanie Fazy 2

| Obszar | Severity | Opis |
|--------|----------|------|
| Schema | Medium | 2 legacy tabele (state, trace), brak cleanup dla dużych tabel |
| Integralność | Low | Brak orphans, dane spójne |
| Transakcje | Low | Brak atomowości, ale OK przy jednym agencie |
| API | Low | Kompletne, dobrze zwalidowane |

**Ogólna ocena Fazy 2:** Baza jest w **dobrym stanie**. Główny tech debt to legacy tabele i brak cleanup policy dla rosnących tabel telemetrycznych.

---

## Faza 3: Inspekcja bot/

### 3.1 Struktura i rozmiary

10 plików, 700 linii łącznie:

| Plik | Linie | Rola |
|------|-------|------|
| `pipeline/nlp_pipeline.py` | 218 | Orkiestrator (⚠ za duży) |
| `channels/telegram_channel.py` | 136 | Kanał Telegram |
| `pipeline/sql_validator.py` | 80 | Guardrails SQL |
| `answer_formatter.py` | 79 | Formatowanie odpowiedzi |
| `main.py` | 69 | Entry point |
| `pipeline/conversation.py` | 64 | Context manager |
| `sql_executor.py` | 52 | Executor SQL |

**Architektura warstwowa:**
```
telegram_channel → nlp_pipeline → { validator, executor, formatter, conversation }
```

---

### 3.2 Bezpieczeństwo

| Zabezpieczenie | Status | Szczegóły |
|----------------|--------|-----------|
| **Whitelist użytkowników** | ✓ Solidny | `allowed_users.txt`, `/reload` command |
| **Blokada DML/DDL** | ✓ Solidny | INSERT, UPDATE, DELETE, DROP, EXEC, SP_*, XP_* |
| **Schema isolation** | ✓ Solidny | Tylko AIBI.*, blokada CDN.* |
| **TOP limit** | ✓ Solidny | Max 200 wierszy, default 50 |
| **Single statement** | ✓ Solidny | Blokada multiple statements |
| **Secrets w logach** | ✓ OK | Tylko user_id, brak credentials |

**Severity: Low** — bezpieczeństwo jest solidne.

---

### 3.3 Error handling

| Scenariusz | Obsługa |
|------------|---------|
| Brak tokena Telegram | ✓ Exit z komunikatem |
| Brak whitelist | ✓ Warning, bot działa |
| Błąd SQL | ✓ Retry + friendly message |
| Brak danych | ✓ Friendly message |
| **API Anthropic error** | ✗ **BRAK** — może crashować |
| **Rate limit API** | ✗ **BRAK** — może crashować |
| **File system error** | ✗ **BRAK** — logging/catalog |

**Severity: High** — brak try/except wokół wywołań Anthropic API.

**Rekomendacja:** Dodać obsługę `anthropic.APIError`, `anthropic.RateLimitError` w `_generate_sql()` i `formatter.format()`.

---

### 3.4 Architektura — problemy

| Problem | Severity | Opis |
|---------|----------|------|
| **nlp_pipeline.py — God Object** | Medium | 218 linii, 7 odpowiedzialności (API client, walidacja, execution, formatting, logging, retry, conversation) |
| **In-memory sessions** | Medium | `ConversationManager` traci historię przy restarcie |
| **Brak rate limiting** | Medium | Brak limitu zapytań per user — potencjalnie kosztowne |
| **Retry logic naiwny** | Low | 2 próby hardcoded, brak backoff |
| **Brak rotacji logów** | Low | JSONL logi rosną bez limitu |

---

### 3.5 Podsumowanie Fazy 3

| Obszar | Severity | Opis |
|--------|----------|------|
| Bezpieczeństwo SQL | Low | Solidne guardrails, whitelist |
| Error handling | **High** | Brak obsługi API errors |
| Architektura | Medium | nlp_pipeline.py wymaga rozbicia |
| Operacje | Medium | In-memory sessions, brak rate limiting |

**Ogólna ocena Fazy 3:** Bot jest **funkcjonalny i bezpieczny**, ale wymaga hardening przed produkcją:
1. **Krytyczne:** Dodać try/except dla Anthropic API
2. **Ważne:** Rozbić nlp_pipeline.py na mniejsze komponenty
3. **Ważne:** Dodać rate limiting per user

---

## Faza 4: Inspekcja dokumentacji ról

### 4.1 Rozmiary promptów

| Plik | Linie | Znaki | ~Tokeny |
|------|-------|-------|---------|
| CLAUDE.md | 283 | 11,363 | 2,840 |
| ERP_SPECIALIST.md | 210 | 9,410 | 2,352 |
| PROMPT_ENGINEER.md | 194 | 7,961 | 1,990 |
| ANALYST.md | 191 | 7,423 | 1,855 |
| ARCHITECT.md | 187 | 7,354 | 1,838 |
| DEVELOPER.md | 144 | 6,383 | 1,595 |
| METHODOLOGY.md | 150 | 6,329 | 1,582 |

**Severity: Low** — żaden prompt nie przekracza 5000 tokenów. CLAUDE.md (~2840) jest największy ale OK.

---

### 4.2 Spójność formatu

| Aspekt | Status |
|--------|--------|
| Struktura XML-like tags | ✓ Spójna we wszystkich rolach |
| Sekcje standardowe | ✓ `<mission>`, `<scope>`, `<critical_rules>`, `<session_start>`, `<workflow>`, `<tools>`, `<escalation>`, `<end_of_turn_checklist>` |
| CLAUDE.md | ✓ Używa markdown headers (OK — plik wspólny, nie prompt roli) |

**Severity: Low** — format jest spójny.

---

### 4.3 Nieaktualne odwołania

`arch_check.py` znalazł 39 nieistniejących ścieżek:

| Typ | Liczba | Status |
|-----|--------|--------|
| Szablony `<rola>`, `<temat>` | ~10 | OK — wzorce, nie dosłowne ścieżki |
| Do utworzenia | 2 | ⚠ `documents/architecture/bot.md`, `security.md` |
| Stare tmp/ | ~20 | OK — pliki tymczasowe |
| Zarchiwizowane | ~7 | OK — przeniesione do archive/ |

**Severity: Low** — główne prompty ról nie mają nieaktualnych odwołań.

---

### 4.4 Podsumowanie Fazy 4

| Obszar | Severity | Opis |
|--------|----------|------|
| Rozmiary | Low | Wszystkie <3000 tokenów |
| Format | Low | Spójny XML-like tags |
| Odwołania | Low | 2 pliki do utworzenia (bot.md, security.md) |

**Ogólna ocena Fazy 4:** Dokumentacja ról jest w **dobrym stanie**. Format jest spójny, rozmiary rozsądne. Jedyne zadanie: utworzyć brakujące `documents/architecture/bot.md` i `security.md`.

---

## Następne kroki

- [x] Faza 1: Inspekcja tools/
- [x] Faza 2: Inspekcja agent_bus (mrowisko.db)
- [x] Faza 3: Inspekcja bot/
- [x] Faza 4: Inspekcja dokumentacji ról
- [ ] Faza 5: Inspekcja solutions/, erp_docs/
- [ ] Faza 6: Inspekcja _loom
- [ ] Faza 7: Meta-analiza + raport końcowy

---

*Raport utrzymywany przez: Architect*
*Lokalizacja: documents/architect/ARCHITECTURE_AUDIT_REPORT.md*
