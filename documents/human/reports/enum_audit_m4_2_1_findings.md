# M4.2.1 Enum Audit Findings

**Date:** 2026-03-23
**Tool:** `tools/enum_audit.py`
**Scope:** Production enum values vs Domain model enums

---

## TL;DR

**Domain model:** ✓ **CORRECT** (no real missing values)
**Database:** ⚠ **DATA QUALITY ISSUES** (Unicode + invalid values)

**Next:** M4.3 data cleanup **BEFORE** M4.2.2 CHECK constraints

---

## Findings

### 1. messages.type

**Production:** `['flag_human', 'info', 'suggestion', 'task']`
**Domain model:** `['direct', 'suggestion', 'task', 'escalation']`

**Missing in domain:** `['flag_human', 'info']`

**Analysis:** ✓ **LEGACY values**
- `info` → `MessageType.DIRECT` (via LegacyAPIMapper)
- `flag_human` → `MessageType.ESCALATION` (via LegacyAPIMapper)
- These are backward compatibility aliases, NOT domain model values
- **Action:** SKIP (correct as-is)

---

### 2. suggestions.status

**Production:** `['implemented', 'in_backlog', 'open', 'rejected']`
**Domain model:** `['open', 'implemented', 'rejected', 'deferred']`

**Missing in domain:** `['in_backlog']`

**Analysis:** ✓ **LEGACY alias**
- `in_backlog` → `SuggestionStatus.IMPLEMENTED` (via LegacyAPIMapper)
- Backward compatibility alias, NOT domain model value
- **Action:** SKIP (correct as-is)

---

### 3. backlog.value

**Production:** `['niska', 'srednia', 'wysoka', 'średnia']`
**Domain model:** `['wysoka', 'srednia', 'niska']`

**Missing in domain:** `['średnia']`

**Analysis:** ⚠ **DATA QUALITY ISSUE**
- `średnia` = Unicode variant of `srednia` (ś vs s)
- This is a data corruption / user input issue
- **Action:** **M4.3 data cleanup**
  ```sql
  UPDATE backlog SET value = 'srednia' WHERE value = 'średnia';
  ```

---

### 4. backlog.effort

**Production:** `['duza', 'mala', 'mała', 'mała (opcja 3) / duża (opcja 1)', 'mała-średnia', 'mała–średnia', 'srednia', 'średnia']`
**Domain model:** `['mala', 'srednia', 'duza']`

**Missing in domain:** `['mała', 'mała (opcja 3) / duża (opcja 1)', 'mała-średnia', 'mała–średnia', 'średnia']`

**Analysis:** ⚠ **DATA QUALITY ISSUES**

**Invalid values:**
- `mała` → Unicode variant of `mala` (ł vs l)
- `średnia` → Unicode variant of `srednia`
- `mała (opcja 3) / duża (opcja 1)` → INVALID (should be single value: `duza` or `mala`)
- `mała-średnia` → INVALID (should be `srednia`)
- `mała–średnia` → INVALID (different dash character)

**Action:** **M4.3 data cleanup**
```sql
-- Unicode cleanup
UPDATE backlog SET effort = 'mala' WHERE effort = 'mała';
UPDATE backlog SET effort = 'srednia' WHERE effort = 'średnia';

-- Invalid values (need human decision)
UPDATE backlog SET effort = 'duza' WHERE effort = 'mała (opcja 3) / duża (opcja 1)';  -- OR mala?
UPDATE backlog SET effort = 'srednia' WHERE effort IN ('mała-średnia', 'mała–średnia');
```

---

## Summary

**Categories of "missing" values:**
1. **Legacy API aliases** (2 cases) — ✓ CORRECT (handled by LegacyAPIMapper)
2. **Unicode variants** (2 cases) — ⚠ DATA CLEANUP needed
3. **Invalid values** (3 cases) — ⚠ DATA CLEANUP needed

**Domain model completeness:** ✓ **100%** (all real values present)

**Database data quality:** ⚠ **Issues found** (7 invalid/Unicode values)

---

## Next Steps

**Revised M4 order:**

1. ✓ **M4.2.1:** Enum audit (DONE)
2. **M4.3:** Data cleanup (clean Unicode + invalid values) — **BEFORE CHECK constraints**
3. **M4.2.2:** CHECK constraints (fail fast on write)

**Rationale:** Cannot add CHECK constraints while data has invalid values
→ Clean data first, then enforce constraints

---

## Tool Output

**JSON:** `tmp/enum_audit_findings.json`
**Text:** `documents/human/reports/enum_audit_m4_2_1.txt`
**Script:** `tools/enum_audit.py`

**Usage:**
```bash
# Human-readable report
python tools/enum_audit.py

# JSON output
python tools/enum_audit.py --json
```

---

**Audit complete.** Data cleanup required before CHECK constraints.
