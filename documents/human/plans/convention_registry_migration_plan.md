# Convention Registry — Migration Plan

**Date:** 2026-03-24
**Author:** Architect
**Context:** Backlog #150 — Convention Registry centralizacja

---

## Goal

Migrować existing conventions do centralnej lokalizacji `documents/conventions/`.

**Success criteria:**
- ✓ Wszystkie conventions w `documents/conventions/`
- ✓ Wszystkie references zaktualizowane (PROMPT_ENGINEER.md, DEVELOPER.md, ARCHITECT.md)
- ✓ Każda convention zgodna z META_CONVENTION structure (po zatwierdzeniu META_CONVENTION)
- ✓ Stare pliki usunięte (git rm)
- ✓ Commit + push

---

## Phase 1: Setup (DONE)

**Status:** ✓ Completed (2026-03-24)

- [x] Folder `documents/conventions/` utworzony
- [x] README.md (index conventions) utworzony
- [x] META_CONVENTION.md placeholder utworzony (czeka na research)

---

## Phase 2: META_CONVENTION (IN PROGRESS)

**Status:** Research w toku (message #238 do PE)

**Timeline:** 2-3 dni

**Steps:**
1. [x] Research request wysłany (PE + research agent)
2. [ ] Research results received (`documents/architect/research_results_meta_convention.md`)
3. [ ] Architect analysis (trade-offs, wybór pattern dla Mrowiska)
4. [ ] Architect draft META_CONVENTION (wypełnienie placeholder)
5. [ ] PE review (parseability, zgodność z PROMPT_CONVENTION)
6. [ ] Metodolog review (optional — alignment z SPIRIT)
7. [ ] META_CONVENTION status: ACTIVE

**Blocker:** Migration existing conventions czeka na META_CONVENTION approval (muszą być zgodne ze strukturą)

---

## Phase 3: Migrate Existing Conventions (PLANNED)

**Status:** Czeka na Phase 2 completion

**Timeline:** 1 dzień

### Step 1: WORKFLOW_CONVENTION.md

**Source:** `documents/prompt_engineer/WORKFLOW_CONVENTION.md`
**Destination:** `documents/conventions/WORKFLOW_CONVENTION.md`

**Actions:**
```bash
# 1. Move file
mv documents/prompt_engineer/WORKFLOW_CONVENTION.md documents/conventions/

# 2. Update references
# - documents/prompt_engineer/PROMPT_ENGINEER.md (session_start section)
```

**Verification:**
- [ ] WORKFLOW_CONVENTION.md exists w `documents/conventions/`
- [ ] PROMPT_ENGINEER.md references zaktualizowane
- [ ] Stary plik nie istnieje (git rm)

---

### Step 2: PROMPT_CONVENTION.md

**Source:** `documents/prompt_engineer/PROMPT_CONVENTION.md`
**Destination:** `documents/conventions/PROMPT_CONVENTION.md`

**Actions:**
```bash
# 1. Move file
mv documents/prompt_engineer/PROMPT_CONVENTION.md documents/conventions/

# 2. Update references
# - documents/prompt_engineer/PROMPT_ENGINEER.md (tools section)
```

**Verification:**
- [ ] PROMPT_CONVENTION.md exists w `documents/conventions/`
- [ ] PROMPT_ENGINEER.md references zaktualizowane
- [ ] Stary plik nie istnieje (git rm)

---

### Step 3: CODE_STANDARDS.md → CODE_CONVENTION.md

**Source:** `documents/dev/CODE_STANDARDS.md`
**Destination:** `documents/conventions/CODE_CONVENTION.md`

**Actions:**
```bash
# 1. Rename + move file
mv documents/dev/CODE_STANDARDS.md documents/conventions/CODE_CONVENTION.md

# 2. Update references
# - documents/dev/DEVELOPER.md (scope section)
# - documents/architect/ARCHITECT.md (code_maturity_levels section — optional reference)
```

**Rationale rename:**
- Spójność nazewnictwa (wszystkie conventions: *_CONVENTION.md)
- "CODE_STANDARDS" → "CODE_CONVENTION" (convention = standard, ale konwencja to lepsze naming)

**Verification:**
- [ ] CODE_CONVENTION.md exists w `documents/conventions/`
- [ ] DEVELOPER.md references zaktualizowane
- [ ] Stary plik nie istnieje (git rm)

---

### Step 4: Verify Compliance z META_CONVENTION

**Dla każdej migrowanej convention:**

**Check:**
- [ ] Ma wszystkie obowiązkowe sekcje (zgodnie z META_CONVENTION structure)
- [ ] Ma YAML header (jeśli META_CONVENTION wymaga)
- [ ] Ma template/examples (jeśli META_CONVENTION wymaga)
- [ ] Ma anti-patterns (jeśli META_CONVENTION wymaga)
- [ ] Ma changelog (jeśli META_CONVENTION wymaga)

**Jeśli brakuje sekcji:**
- Update convention (dodaj brakujące sekcje zgodnie z META_CONVENTION template)

**Timeline:** pół dnia (review 3 conventions + fix gaps)

---

### Step 5: Update Role Documents

**Files to update:**

#### PROMPT_ENGINEER.md
**Sections:**
- `<session_start>` — change path WORKFLOW_CONVENTION, PROMPT_CONVENTION
- `<tools>` — change path PROMPT_CONVENTION

**Changes:**
```markdown
# BEFORE
documents/prompt_engineer/WORKFLOW_CONVENTION.md
documents/prompt_engineer/PROMPT_CONVENTION.md

# AFTER
documents/conventions/WORKFLOW_CONVENTION.md
documents/conventions/PROMPT_CONVENTION.md
```

---

#### DEVELOPER.md
**Sections:**
- `<scope>` — change path CODE_STANDARDS → CODE_CONVENTION
- `<session_start>` (jeśli reference do CODE_STANDARDS)

**Changes:**
```markdown
# BEFORE
documents/dev/CODE_STANDARDS.md

# AFTER
documents/conventions/CODE_CONVENTION.md
```

---

#### ARCHITECT.md
**Sections:**
- `<session_start>` — add reference do META_CONVENTION (Architect review każdej nowej convention)
- `<tools>` — add reference do `documents/conventions/README.md` (index conventions)

**Changes:**
```markdown
# ADD to <session_start>
Architect review conventions:
- Każda nowa convention → verify compliance z META_CONVENTION
- Convention Registry: documents/conventions/README.md

# ADD to <tools>
Convention Registry:
- META_CONVENTION.md — struktura każdej convention
- README.md — index wszystkich conventions (existing + planned)
```

---

### Step 6: Update PATTERNS.md (Optional Reference)

**File:** `documents/architecture/PATTERNS.md`

**Section:** Convention First Architecture pattern

**Change:**
```markdown
# BEFORE
**Example:** WORKFLOW_CONVENTION (documents/prompt_engineer/WORKFLOW_CONVENTION.md)

# AFTER
**Example:** WORKFLOW_CONVENTION (documents/conventions/WORKFLOW_CONVENTION.md)
**Meta-level:** META_CONVENTION (documents/conventions/META_CONVENTION.md)
```

**Rationale:**
- PATTERNS.md references WORKFLOW_CONVENTION jako przykład Convention First Architecture
- Update path po migration

---

### Step 7: Git Commit

**Commands:**
```bash
# Stage all changes (migrations + updates + deletions)
git add -A

# Commit
py tools/git_commit.py --message "refactor: Convention Registry migration - centralize conventions to documents/conventions/" --all
```

**Commit message format:**
```
refactor: Convention Registry migration - centralize conventions

- Move WORKFLOW_CONVENTION → documents/conventions/
- Move PROMPT_CONVENTION → documents/conventions/
- Rename CODE_STANDARDS → CODE_CONVENTION + move to documents/conventions/
- Update paths (PROMPT_ENGINEER.md, DEVELOPER.md, ARCHITECT.md, PATTERNS.md)
- Verify compliance z META_CONVENTION (wszystkie conventions)

Related: Backlog #150
```

---

## Phase 4: Priority 1 Conventions (FUTURE)

**Status:** Czeka na Phase 3 completion

**Timeline:** 2-3 tygodnie (research + draft + review każdej convention)

**Conventions to create:**
1. COMMIT_CONVENTION.md
2. FILE_NAMING_CONVENTION.md
3. DB_SCHEMA_CONVENTION.md
4. TEST_CONVENTION.md
5. DOCUMENTATION_CONVENTION.md

**Process (każda convention):**
1. Research (PE + research agent) — 1-2 dni
2. Draft (Owner: Architect/Developer) — pół dnia
3. Review (cross-role) — pół dnia
4. Active (update README.md status) — immediate

---

## Files to Update (Summary)

| File | Change Type | Details |
|---|---|---|
| `documents/prompt_engineer/PROMPT_ENGINEER.md` | Update paths | WORKFLOW_CONVENTION, PROMPT_CONVENTION |
| `documents/dev/DEVELOPER.md` | Update path | CODE_STANDARDS → CODE_CONVENTION |
| `documents/architect/ARCHITECT.md` | Add references | META_CONVENTION, Convention Registry |
| `documents/architecture/PATTERNS.md` | Update path | WORKFLOW_CONVENTION reference |
| `documents/conventions/README.md` | Update status | Migrowane conventions: status ACTIVE |

---

## Rollback Plan (Jeśli coś pójdzie nie tak)

**Jeśli migration fails:**
1. Git revert commit
2. Przywróć stare pliki (git checkout)
3. Debug problem
4. Re-run migration

**Safety:**
- Wszystkie changes w 1 commit (atomic operation)
- Git history zachowuje stare ścieżki (łatwy rollback)

---

## Verification Checklist (Post-Migration)

**Folder structure:**
- [ ] `documents/conventions/` exists
- [ ] `documents/conventions/README.md` exists
- [ ] `documents/conventions/META_CONVENTION.md` exists (status: ACTIVE)
- [ ] `documents/conventions/WORKFLOW_CONVENTION.md` exists
- [ ] `documents/conventions/PROMPT_CONVENTION.md` exists
- [ ] `documents/conventions/CODE_CONVENTION.md` exists

**Old files removed:**
- [ ] `documents/prompt_engineer/WORKFLOW_CONVENTION.md` NOT exists
- [ ] `documents/prompt_engineer/PROMPT_CONVENTION.md` NOT exists
- [ ] `documents/dev/CODE_STANDARDS.md` NOT exists

**References updated:**
- [ ] PROMPT_ENGINEER.md — paths correct
- [ ] DEVELOPER.md — paths correct
- [ ] ARCHITECT.md — references added
- [ ] PATTERNS.md — path correct

**Compliance:**
- [ ] WORKFLOW_CONVENTION.md zgodny z META_CONVENTION structure
- [ ] PROMPT_CONVENTION.md zgodny z META_CONVENTION structure
- [ ] CODE_CONVENTION.md zgodny z META_CONVENTION structure

**Git:**
- [ ] Commit created (message: refactor: Convention Registry migration)
- [ ] Push successful

---

## Timeline Summary

| Phase | Status | Timeline | Blocker |
|---|---|---|---|
| Phase 1: Setup | ✓ Done | — | — |
| Phase 2: META_CONVENTION | In Progress | 2-3 dni | Research results |
| Phase 3: Migrate Existing | Planned | 1 dzień | Phase 2 done |
| Phase 4: Priority 1 Conventions | Future | 2-3 tygodnie | Phase 3 done |

**Total (Phase 1-3):** ~4-5 dni

---

## Next Action

**Czeka na:** Research results od PE (`documents/architect/research_results_meta_convention.md`)

**Po researchu:**
1. Architect analysis → draft META_CONVENTION
2. Review → approval → status ACTIVE
3. Execute Phase 3 (migrate existing conventions)

---

**Last Updated:** 2026-03-24 (Architect)
