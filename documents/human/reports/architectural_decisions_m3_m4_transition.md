# Decyzje Architektoniczne: M3→M4 Transition

**Date:** 2026-03-23
**Context:** Odpowiedź na pytania Developer (msg #206) po M3 Phase 3
**Architect:** Architect
**Developer:** Developer

---

## TL;DR — Decyzje

| Pytanie | Decyzja | Uzasadnienie |
|---------|---------|--------------|
| **1. M4 cleanup timing** | **PRZED Phase 4** | Ekonomiczne: refactor 3 repos < refactor 5 repos. Pattern już stabilny. |
| **2. Legacy API strategy** | **Mapping na boundaries** (canonical = domain model) | Odwracalne, clean internal API, deprecation path możliwy later. |
| **3. Enum audit** | **Proaktywny** (SELECT DISTINCT + CHECK constraints) | Fail fast on write. Eliminuje reactive lag + runtime errors. |
| **4. Data cleanup** | **Migration + grace period** (1 miesiąc) | 1× migration risk < ∞永久 tech debt w kodzie. |

---

## 1. M4 Cleanup Timing: PRZED czy PO Phase 4?

### Trade-off Analysis

**Opcja A: M4 PRZED Phase 4 (Developer recommendation)**

**Pros:**
- ✓ Ekonomiczne: refactor 3 repositories (~3-4h) < refactor 5 repositories (~6-8h)
- ✓ Koszt duplikacji rośnie liniowo: każdy nowy repository = więcej boilerplate
- ✓ Clean base dla Phase 4: session_log/trace adapters używają helpers od początku
- ✓ Momentum: pattern już stabilny (3 examples wystarczą do abstrakcji)

**Cons:**
- ✗ Możliwe że Phase 4 odkryje nowe edge cases wymagające zmiany helpers
  - **Counter:** Pattern identyczny przez 3 repositories — session_log/trace będą strukturalnie identyczne
- ✗ Risk przedwczesnej abstrakcji
  - **Counter:** Boilerplate już widoczny (10× repo creation, 6× type mapping, ~40 linii dict conversion)

**Opcja B: Phase 4 POTEM M4 cleanup**

**Pros:**
- ✓ Więcej examples (5 repos) = potencjalnie lepsze abstrakcje
- ✓ Pełny obraz problemu przed refaktorem

**Cons:**
- ✗ Wyższy koszt refaktoru (5 repos vs 3 repos)
- ✗ Phase 4 duplikuje boilerplate zamiast używać helpers
- ✗ Większy diff w M4 (więcej linii do zmiany = większy risk regression)

### Decision: **M4 PRZED Phase 4** ✓

**Rationale:**
1. **Ekonomiczne:** Refactor 3 tańszy niż 5 (Developer ma rację)
2. **Pattern stabilny:** 3 repositories pokazały identyczny pattern — session_log/trace nie dodadzą nowych insights
3. **Clean momentum:** Phase 4 używa helpers od początku (nie duplikuje boilerplate)
4. **SPIRIT alignment:** "Buduj dom, nie szałas" — helpers są fundamentem, nie prowizorką

**Implementation:**
- M4 cleanup → Phase 4 (session_log, trace adapters)
- Estimated M4 effort: ~3-4 hours (repo helper + dict conversion + type mapping)

---

## 2. Legacy API Strategy: Forever vs Deprecation Path?

### Trade-off Analysis

**Opcja A: Mapping na boundaries (Developer recommendation)**

**Canonical form = domain model.** Mapping tylko w CLI parser/output.

**Pros:**
- ✓ Clean internal API: AgentBus używa domain model (MessageType.DIRECT), nie legacy strings ("info")
- ✓ Single source of truth: mapping layer w 1 miejscu (core/mappers/legacy_api.py)
- ✓ Deprecation path możliwy: remove CLI mapping → update CLI do domain model values
- ✓ Odwracalne: jeśli potrzeba backward compat forever — mapping layer zostaje

**Cons:**
- ✗ Migration effort: przenieś mapping z adapters → CLI boundaries
- ✗ CLI musi robić conversion (input: "info" → DIRECT, output: DIRECT → "info")

**Opcja B: Backward compat forever (mapping w adapters)**

**Legacy API values na zawsze.** AgentBus robi mapping inline.

**Pros:**
- ✓ Status quo (już działa)
- ✓ Brak migration effort

**Cons:**
- ✗ Mapping logic scattered (6+ miejsc w adapters)
- ✗ Brak deprecation path (legacy API永久化)
- ✗ Internal API używa mixed conventions (strings + enums)

### Decision: **Mapping na boundaries** ✓

**Rationale:**
1. **Clean architecture:** Internal API = domain model (canonical), legacy API tylko na boundaries
2. **Single source of truth:** Mapping layer centralizuje backward compat logic
3. **Odwracalne:** Jeśli user chce backward compat forever — mapping layer zostaje; jeśli deprecation — remove mapping
4. **SPIRIT alignment:** "Wybieraj to co skaluje" — centralna mapping layer skaluje lepiej niż scattered inline

**Implementation:**
```
CLI input → LegacyAPIMapper.to_domain → AgentBus (domain model) → Repository
Repository → AgentBus (domain model) → LegacyAPIMapper.from_domain → CLI output
```

**M4 scope:**
- Create `core/mappers/legacy_api.py` (centralna mapping layer)
- Refactor adapters: remove inline TYPE_MAP/TYPE_REVERSE_MAP → delegate to mapper
- CLI remains unchanged (backward compatible)

**Future (opcjonalne):**
- Deprecation path: remove mapper → update CLI do domain model values
- Migration script: `UPDATE messages SET type = 'direct' WHERE type = 'info'`
- Grace period: 1-2 miesiące CLI wspiera oba (legacy + domain)

---

## 3. Enum Audit: Reaktywne vs Proaktywne?

### Trade-off Analysis

**Opcja A: Proaktywny audit (Developer recommendation)**

**SELECT DISTINCT all enum columns → add all production values naraz.**

**Pros:**
- ✓ Eliminuje reactive lag: enum definition = production reality (synchronized)
- ✓ Fail fast: SQLite CHECK constraints enforces valid values **on write** (INSERT/UPDATE)
- ✓ Single pass: 1× audit + fixes vs N× reactive fixes
- ✓ Odkrywa legacy values wcześnie (zanim runtime error w production)

**Cons:**
- ✗ Effort: ~1 hour (SELECT DISTINCT + enum updates + CHECK constraints)
- ✗ Możliwe że production ma invalid values wymagające cleanup

**Opcja B: Reaktywne (status quo)**

**Add enum values when ValidationError occurs.**

**Pros:**
- ✓ Zero upfront effort
- ✓ Add only values actually used

**Cons:**
- ✗ Enum definition lags behind production usage
- ✗ Runtime ValidationError in production (bad UX)
- ✗ Multiple reactive fixes (każda nowa wartość = osobny fix)

### Decision: **Proaktywny audit** ✓

**Rationale:**
1. **Fail fast:** CHECK constraints catch invalid values **on write**, nie na read
2. **Single pass:** 1× effort vs N× reactive fixes
3. **Senior-level approach:** Proactive > reactive (prevent bugs, nie fix bugs)
4. **SPIRIT alignment:** "Automatyzuj siebie" — audit eliminuje manual reactive fixes

**Implementation:**
```sql
-- Audit production values
SELECT DISTINCT status FROM messages;
SELECT DISTINCT area FROM backlog;
SELECT DISTINCT value, effort FROM backlog;

-- Add CHECK constraints (fail fast)
ALTER TABLE messages ADD CONSTRAINT chk_status
  CHECK (status IN ('unread', 'read', 'archived'));

ALTER TABLE backlog ADD CONSTRAINT chk_area
  CHECK (area IN ('ERP', 'Bot', 'Arch', 'Dev', 'Prompt', 'Metodolog'));
```

**M4 scope:**
- Audit script: SELECT DISTINCT per enum column
- Update enums (BacklogArea, BacklogValue, BacklogEffort, MessageStatus, MessageType, SuggestionStatus, SuggestionType)
- Add CHECK constraints per table

**Estimated effort:** ~1 hour

---

## 4. Data Cleanup: Aliasy永久 vs Migration?

### Trade-off Analysis

**Opcja A: Migration + grace period (Developer recommendation)**

**Data cleanup script → grace period (1 miesiąc aliasy) → remove aliasy.**

**Pros:**
- ✓ Clean code long-term: zero aliasy w kodzie po grace period
- ✓ 1× migration risk < ∞永久 tech debt
- ✓ Grace period minimalizuje risk: aliasy fail-safe przez 1 miesiąc
- ✓ Data consistency: baza ma canonical values (nie mixed "średnia"/"srednia")

**Cons:**
- ✗ Migration risk: script może fail (dry run minimalizuje)
- ✗ Effort: ~30 min (script + dry run + verify)

**Opcja B: Aliasy永久 (status quo)**

**Graceful degradation: VALUE_ALIASES w kodzie forever.**

**Pros:**
- ✓ Zero migration risk
- ✓ Backward compatible (stare wartości działają)

**Cons:**
- ✗ Tech debt永久化: aliasy w kodzie forever
- ✗ Baza ma mixed values ("średnia", "srednia", "�rednia") — inconsistent
- ✗ Future developers muszą wiedzieć o aliasach (hidden complexity)

### Decision: **Migration + grace period** ✓

**Rationale:**
1. **Long-term clean:** 1× migration effort eliminuje ∞永久 tech debt
2. **Grace period minimalizuje risk:** Aliasy fail-safe przez 1 miesiąc → zero migration risk production
3. **Data consistency:** Canonical values w bazie (nie mixed)
4. **SPIRIT alignment:** "Buduj dom, nie szałas" — aliasy to prowizorka, migration to fundament

**Implementation:**
```sql
-- Data cleanup script (dry run first)
BEGIN TRANSACTION;

-- Backlog value cleanup
UPDATE backlog SET value = 'niska' WHERE value IN ('�niska', 'niska');
UPDATE backlog SET value = 'srednia' WHERE value IN ('średnia', '�rednia');
UPDATE backlog SET value = 'wysoka' WHERE value IN ('wysok�', 'wysoka');

-- Verify: SELECT DISTINCT value FROM backlog;
-- Expected: ('niska', 'srednia', 'wysoka', NULL)

COMMIT;
-- Lub ROLLBACK jeśli coś źle
```

**Grace period:**
- Keep VALUE_ALIASES w kodzie przez 1 miesiąc (fail-safe)
- Monitor: czy coś zapisuje stare wartości? (jeśli tak → znajdź źródło i fix)
- Po 1 miesiącu: remove aliasy

**M4 scope:**
- Data cleanup script (dry run → execute → verify)
- Grace period: 1 miesiąc aliasy w kodzie (fail-safe)
- Post-grace: remove aliasy (separate commit)

**Estimated effort:** ~30 min cleanup, 0 min grace period (passive), ~10 min remove aliasy

---

## Summary — M4 Cleanup Scope

**Decyzje:**
1. ✓ **M4 PRZED Phase 4** (ekonomiczne, pattern stabilny)
2. ✓ **Mapping na boundaries** (canonical = domain model)
3. ✓ **Proaktywny enum audit** (fail fast, CHECK constraints)
4. ✓ **Migration + grace period** (clean long-term, 1× risk < ∞ debt)

**M4 Implementation Plan:**

### M4.1: DRY Refactors (~3h)

**1. Repo creation helper** (~30 min)
```python
def _get_repository(self, repo_class: Type[Repository]) -> Repository:
    conn = self._conn if self._in_transaction else None
    return repo_class(db_path=self._db_path, conn=conn)
```
Eliminuje 10× duplikację.

**2. Centralna mapping layer** (~2h)
```python
# core/mappers/legacy_api.py
class LegacyAPIMapper:
    MESSAGE_TYPE_TO_DOMAIN = {...}
    MESSAGE_TYPE_FROM_DOMAIN = {...}

    @classmethod
    def map_to_domain(cls, value: str, entity: str) -> Enum: ...

    @classmethod
    def map_from_domain(cls, enum: Enum, entity: str) -> str: ...
```
Eliminuje 6× inline mappings.

**3. Dict conversion helpers** (~30 min)
```python
# core/mappers/legacy_api.py
class LegacyAPIMapper:
    @classmethod
    def message_to_dict(cls, m: Message) -> dict: ...

    @classmethod
    def suggestion_to_dict(cls, s: Suggestion) -> dict: ...

    @classmethod
    def backlog_to_dict(cls, b: BacklogItem) -> dict: ...
```
Eliminuje ~40 linii boilerplate.

### M4.2: Enum Audit + CHECK Constraints (~1h)

**1. Audit script**
```python
# tools/enum_audit.py
SELECT DISTINCT status FROM messages;
SELECT DISTINCT type FROM messages;
SELECT DISTINCT area, value, effort, status FROM backlog;
SELECT DISTINCT status, type FROM suggestions;
```

**2. Update enums** (add missing production values)

**3. CHECK constraints** (fail fast on write)

### M4.3: Data Cleanup + Grace Period (~30 min + 1 miesiąc passive)

**1. Cleanup script** (dry run → execute → verify)
```sql
UPDATE backlog SET value = 'srednia' WHERE value IN ('średnia', '�rednia');
```

**2. Grace period** (1 miesiąc aliasy w kodzie)

**3. Remove aliasy** (po grace period, separate commit)

---

## Estimated Total Effort M4

- **M4.1:** ~3 hours (DRY refactors)
- **M4.2:** ~1 hour (enum audit + CHECK constraints)
- **M4.3:** ~30 min (data cleanup script)
- **Grace period:** 1 miesiąc (passive monitoring)

**Total active effort:** ~4.5 hours (1 sesja)

**Tests:** Verify all tests PASS (backward compatibility intact)

---

## Alignment z SPIRIT.md

**Decyzje aligned z zasadami ducha:**

1. **"Buduj dom, nie szałas"**
   - ✓ Helpers są fundamentem (nie prowizorka)
   - ✓ Migration eliminuje永久 tech debt (dom, nie szałas)

2. **"Wybieraj to co skaluje"**
   - ✓ Centralna mapping layer skaluje (single source of truth)
   - ✓ Refactor 3 < refactor 5 (ekonomiczne skalowanie)

3. **"Wiedza musi przetrwać"**
   - ✓ Mapping layer = trwała dokumentacja backward compat logic
   - ✓ CHECK constraints = trwałe invariants w bazie

4. **"Automatyzuj siebie"**
   - ✓ Proaktywny enum audit eliminuje reactive manual fixes
   - ✓ Helpers eliminują boilerplate (DRY)

---

## Next Steps

**Developer:**
1. ✓ GREEN LIGHT M4 cleanup
2. Start M4.1 (DRY refactors): repo helper → mapping layer → dict conversion
3. M4.2 (enum audit + CHECK constraints)
4. M4.3 (data cleanup script)
5. Verify: all tests PASS, backward compatibility intact
6. Commit: `refactor(m4): DRY cleanup - helpers + mapping layer + enum audit`
7. Grace period: 1 miesiąc aliasy w kodzie (passive)
8. Post-grace: remove aliasy (separate commit)

**Po M4:**
- Phase 4 (session_log, trace adapters) — używa M4 helpers
- Lub: End ADR-001 na M4 (defer Phase 4 indefinitely)

---

**Decyzje architektoniczne complete.** ✓

**Architect**
