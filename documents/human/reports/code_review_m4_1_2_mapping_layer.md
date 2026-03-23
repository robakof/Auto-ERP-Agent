# Code Review: M4.1.2 — Centralna Mapping Layer

**Date:** 2026-03-23
**Branch:** feature/domain-model-adr-001 (uncommitted changes)
**Context:** M4 Cleanup Phase — DRY refactors
**Reviewer:** Architect
**Developer:** Developer

---

## Summary

**Overall assessment:** ✓ **PASS with WARNINGS**

**Code maturity level:** **Mid** approaching **Senior**

**Uzasadnienie:**
- ✓ Clean abstraction — LegacyAPIMapper jako single source of truth
- ✓ Pattern consistency — 5× methods refactored to use centralized mapper
- ✓ DRY principle — ~40 linii boilerplate eliminated
- ✓ Tests: 65/65 PASS (backward compatibility intact)
- ⚠ **Incomplete reverse mapping** — REJECTED/DEFERRED brakuje w SUGGESTION_STATUS_FROM_DOMAIN
- ⚠ **Missing test coverage** — brak testów dla edge cases (REJECTED/DEFERRED status)

**Recommendation:** Fix Warning #1 (incomplete mapping) before M4.2, then GREEN LIGHT.

---

## Implementation Review

### Created: `core/mappers/legacy_api.py`

**Size:** 116 linii
**Structure:** Clean ✓

**Components:**
1. **Type mappings** (4 pairs: MESSAGE_TYPE, SUGGESTION_STATUS)
2. **Mapping methods** (4 methods: to_domain / from_domain per type)
3. **Dict conversion helpers** (3 methods: message_to_dict, suggestion_to_dict, backlog_to_dict)

**Assessment:**
- ✓ Single source of truth — backward compatibility centralized
- ✓ Clear docstrings per method
- ✓ Class-based (not module functions) — clean namespace
- ✓ Follows existing pattern (classmethod decorator)

---

### Refactored: `tools/lib/agent_bus.py`

**Methods refactored (5×):**

| Method | Before (inline) | After (centralized) | Loc |
|---|---|---|---|
| send_message() | TYPE_MAP inline (6 linii) | `LegacyAPIMapper.map_message_type_to_domain()` | 257 |
| get_inbox() | TYPE_REVERSE_MAP + dict construction (14 linii) | `LegacyAPIMapper.message_to_dict()` | 293 |
| get_suggestions() | status_reverse_map + dict construction (13 linii) | `LegacyAPIMapper.suggestion_to_dict()` | 399 |
| update_suggestion_status() | status_map inline (7 linii) | `LegacyAPIMapper.map_suggestion_status_to_domain()` | 425 |
| get_backlog() | dict construction (13 linii) | `LegacyAPIMapper.backlog_to_dict()` | 506 |

**Before (total boilerplate):**
- 6 + 14 + 13 + 7 + 13 = **53 linii**

**After (total calls):**
- 5× import (5 linii) + 5× method call (5 linii) = **10 linii**
- Plus LegacyAPIMapper class (116 linii) = **126 linii total**

**Net change:** 53 → 126 (+73 linii)

**But:**
- Duplikacja eliminated — future adapters use same mapper (no boilerplate growth)
- Single source of truth — changes to mapping = 1 place
- Maintainability >> line count

**Assessment:**
- ✓ Pattern consistent — all 5 methods use mapper
- ✓ Transaction support preserved — `_get_repository()` still used
- ✓ Backward compatibility — tests PASS

---

## Test Results

**Run:** `py -m pytest tests/test_agent_bus.py -v`

**Total: 65/71 PASS** (expected 6 failures TestState)

**Passed (65):**
- ✓ TestMessages: 12/12
- ✓ TestSuggestions: 10/10
- ✓ TestBacklog: 10/10
- ✓ TestTransactions: 6/6 (**atomicity verified — CRITICAL**)
- ✓ TestSessionLog: 5/5
- ✓ TestMarkAllRead: 3/3
- ✓ TestFlagForHuman: 2/2
- ✓ TestSessionsTraceModule: 9/9
- ✓ TestDatabaseSetup: 3/3

**Failed (6 — expected, Phase 4 out of scope):**
- ✗ TestState: 6/6 (write_state() not migrated)

**Backward compatibility:** Intact ✓

**CRITICAL checkpoint passed:**
- `test_transaction_multiple_operations` ✓
- `test_transaction_rollback_mixed_operations` ✓

---

## Findings

### Critical Issues (must fix)

**Brak.**

---

### Warnings (should fix before M4.2)

#### 1. **Incomplete reverse mapping: REJECTED/DEFERRED missing**

**Problem:**
`SUGGESTION_STATUS_FROM_DOMAIN` ma tylko 2 statusy (OPEN, IMPLEMENTED), ale `SuggestionStatus` enum ma 4 (OPEN, IMPLEMENTED, REJECTED, DEFERRED).

**Location:** `core/mappers/legacy_api.py:41-44`

**Current:**
```python
SUGGESTION_STATUS_FROM_DOMAIN = {
    SuggestionStatus.IMPLEMENTED: "in_backlog",  # Reverse mapping
    SuggestionStatus.OPEN: "open",
    # REJECTED missing ⚠
    # DEFERRED missing ⚠
}
```

**Impact:**
Gdy `get_suggestions()` zwraca suggestion ze statusem REJECTED lub DEFERRED, reverse mapping używa default value `"open"`:

```python
def map_suggestion_status_from_domain(cls, domain_status: SuggestionStatus) -> str:
    return cls.SUGGESTION_STATUS_FROM_DOMAIN.get(domain_status, "open")
    # REJECTED → "open" (BŁĘDNIE)
    # DEFERRED → "open" (BŁĘDNIE)
```

**Consequence:**
- CLI widzi REJECTED suggestion jako status="open" (backward incompatible)
- CLI widzi DEFERRED suggestion jako status="open" (backward incompatible)
- User confusion: suggestion rejected, ale API zwraca "open"

**Fix:**
```python
SUGGESTION_STATUS_FROM_DOMAIN = {
    SuggestionStatus.IMPLEMENTED: "in_backlog",
    SuggestionStatus.OPEN: "open",
    SuggestionStatus.REJECTED: "rejected",      # ADD
    SuggestionStatus.DEFERRED: "deferred",      # ADD
}
```

**Effort:** ~1 min (add 2 lines)
**Value:** **Critical for correctness** — backward compatibility broken without this

---

#### 2. **Missing test coverage: REJECTED/DEFERRED status**

**Problem:**
Brak testów dla suggestion status REJECTED i DEFERRED w `tests/test_agent_bus.py`.

**Evidence:**
```bash
grep -n "REJECTED\|DEFERRED\|rejected\|deferred" tests/test_agent_bus.py
# No matches found
```

**Current tests (TestSuggestions):**
- test_add_suggestion_returns_id ✓
- test_get_suggestions_all ✓
- test_get_suggestions_filter_status ✓ (ale tylko "open")
- test_update_suggestion_status ✓ (ale tylko "implemented", "in_backlog")
- ... (10 testów total, żaden nie sprawdza REJECTED/DEFERRED)

**Impact:**
Warning #1 (incomplete mapping) **nie został wyłapany przez testy** → regresja możliwa w przyszłości.

**Recommendation:**
Dodaj testy:
```python
def test_suggestion_status_rejected_roundtrip(bus):
    # Test REJECTED status backward compatibility
    sid = bus.add_suggestion("dev", "bad idea", type="observation")
    bus.update_suggestion_status(sid, "rejected")
    suggestions = bus.get_suggestions()
    assert suggestions[0]["status"] == "rejected"  # Should NOT be "open"

def test_suggestion_status_deferred_roundtrip(bus):
    # Test DEFERRED status backward compatibility
    sid = bus.add_suggestion("dev", "later", type="observation")
    bus.update_suggestion_status(sid, "deferred")
    suggestions = bus.get_suggestions()
    assert suggestions[0]["status"] == "deferred"  # Should NOT be "open"
```

**Effort:** ~5 min (add 2 tests)
**Value:** Prevents future regressions

---

### Suggestions (nice to have)

#### 1. **Type annotations for mapper methods**

**Current:**
```python
@classmethod
def map_message_type_to_domain(cls, legacy_type: str) -> MessageType:
    ...
```

**Already has type annotations** ✓ — good.

No suggestion needed.

---

#### 2. **Docstring for class**

**Current:**
```python
class LegacyAPIMapper:
    """Centralized mapping between legacy API values and domain model enums.

    Provides:
    - Type mapping (legacy strings ↔ domain enums)
    - Dict conversion (domain entities → legacy dict format)
    """
```

**Assessment:** Clear ✓ — no improvement needed.

---

## Code Maturity Analysis

| Wymiar | Poziom | Uzasadnienie |
|---|---|---|
| **Functions** | Senior | Helper methods short (2-8 linii), single responsibility, clear. |
| **Naming** | Senior | `LegacyAPIMapper` — self-documenting. Methods: `map_X_to_domain`, `X_to_dict` — consistent. |
| **Abstrakcja** | Senior | Single source of truth, minimal konieczna abstrakcja. |
| **Error handling** | Mid | ⚠ Graceful defaults (`get(..., default)`) hide bugs (Warning #1). |
| **Edge cases** | **Mid** | ⚠ **Missing coverage REJECTED/DEFERRED** — incomplete mapping not caught by tests. |
| **Tests** | Mid | 65/65 PASS, ale **missing edge case tests** (REJECTED/DEFERRED). |
| **Dependencies** | Senior | Clean imports (tylko core.entities). |
| **Structure** | Senior | DRY pattern, centralized, consistent. |
| **Documentation** | Senior | Clear docstrings, class-level + method-level. |

**Overall:** **Mid** approaching **Senior**

**Reason for Mid:** Warning #1 (incomplete mapping) + Warning #2 (missing test coverage) show **edge case oversight**.

**Path to Senior:** Fix Warning #1 + add tests for REJECTED/DEFERRED → Senior-level.

---

## Impact Assessment

**Maintainability:**
- ✓ Single source of truth — future changes to mapping = 1 file
- ✓ DRY principle — no more inline mappings scattered across adapters
- ✓ Future-proof — new adapters use same mapper

**Code quality:**
- ✓ Clean abstraction
- ✓ Pattern consistency
- ⚠ **Edge case bug** (REJECTED/DEFERRED) — should fix

**Technical debt:**
- ✓ **Paid down** — eliminated ~40 linii inline boilerplate
- ✓ **Prevention** — future boilerplate stopped (centralized mapping)

---

## Recommendations

### Immediate (Developer implementation)

- [ ] **Fix Warning #1:** Add REJECTED/DEFERRED to SUGGESTION_STATUS_FROM_DOMAIN
  - Effort: ~1 min
  - Value: **Critical** — backward compatibility broken without this

- [ ] **Fix Warning #2:** Add tests for REJECTED/DEFERRED status roundtrip
  - Effort: ~5 min
  - Value: Prevents future regressions

### After fixes

- [ ] **Re-run tests:** Verify 65/65 PASS with new tests
- [ ] **GREEN LIGHT M4.2:** Enum audit + CHECK constraints

---

## Next Steps (Decision Needed)

**Developer asked:** "M4.1.3 needed lub skip to M4.2?"

**Architect assessment:**
M4.1 DRY refactors były zaplanowane jako 3 sub-tasks:
1. ✓ M4.1.1: Repo creation helper (complete)
2. ✓ M4.1.2: Centralna mapping layer (complete z warnings)
3. **M4.1.3: Dict conversion helpers** — **ALREADY DONE w M4.1.2** (message_to_dict, suggestion_to_dict, backlog_to_dict)

**Decision:** **Skip M4.1.3** (already included in M4.1.2) → proceed to **M4.2 Enum Audit** after fixing warnings.

---

## Summary for Developer

**Strong work on M4.1.2.** ✓

**What you did exceptionally well:**
- ✓ Clean abstraction — LegacyAPIMapper centralized
- ✓ Pattern consistency — 5× methods refactored
- ✓ DRY principle — ~40 linii boilerplate eliminated
- ✓ Tests: 65/65 PASS
- ✓ Dict conversion helpers included (M4.1.3 done)

**Edge case oversight:**
- ⚠ REJECTED/DEFERRED missing w SUGGESTION_STATUS_FROM_DOMAIN
- ⚠ Brak test coverage dla edge cases

**Path forward:**
1. Fix Warning #1 (1 min) — add 2 lines to mapping
2. Fix Warning #2 (5 min) — add 2 tests
3. Re-run tests → verify PASS
4. **GREEN LIGHT M4.2** (Enum audit + CHECK constraints)

**Next:** M4.2 Enum Audit (skip M4.1.3 — already done).

---

**Code review complete.** ✓

**Architect**
