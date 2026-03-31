---
workflow_id: test_sample
version: "1.0"
owner_role: developer
trigger: "Test workflow for import validation"
participants:
  - developer
  - architect
outputs:
  - type: file
    path: "tmp/test_output.md"
---

## Outline

1. **Verify** — check prerequisites
2. **Implement** — do the work
3. **Review** — send for review

---

## Phase 1: Verify

### Step 1: Check Git Status

**step_id:** verify_git
**action:** Sprawdź czy working tree czysty
**tool:** Bash
**command:** `git status`
**verification:** Output zawiera "nothing to commit"
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "Uncommitted changes block workflow"
**next_step:** read_context (if PASS), escalate (if FAIL)

### Step 2: Read Context

**step_id:** read_context
**action:** Przeczytaj plik kontekstowy
**tool:** Read
**command:** `documents/dev/DEVELOPER.md`
**verification:** file_exists documents/dev/DEVELOPER.md
**on_failure:**
  - retry: no
  - skip: yes
  - escalate: no
  - reason: "Context file missing, can proceed without"
**next_step:** implement (if PASS), implement (if FAIL)

### Exit Gate

- **gate_verify_clean:** Git working tree is clean
- **gate_verify_context:** Context file read successfully

---

## Phase 2: Implement

### Step 3: Write Code

**step_id:** implement
**action:** Napisz kod rozwiązania
**tool:** Write
**command:** `tools/new_tool.py`
**verification:** file_exists tools/new_tool.py
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Code writing failed"
**next_step:** run_tests (if PASS), escalate (if FAIL)

### Step 4: Run Tests

**step_id:** run_tests
**action:** Uruchom testy
**tool:** Bash
**command:** `py -m pytest tests/ -q`
**verification:** test_pass tests/
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Tests failing"
**next_step:** send_review (if PASS), implement (if FAIL)

### Exit Gate

- **gate_impl_code:** Code file exists
- **gate_impl_tests:** All tests pass

---

## Phase 3: Review

### Step 5: Send for Review

**step_id:** send_review
**action:** Wyślij do review przez architect
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from developer --to architect --content-file tmp/review.md`
**verification:** message_sent
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Could not send review message"
**next_step:** end (if PASS), escalate (if FAIL)

→ HANDOFF: architect. STOP. Czekaj na review.

### Decision Point 1: Review Outcome

**decision_id:** review_result
**condition:** Architect approved?
**path_true:** end
**path_false:** implement
**default:** implement

### Exit Gate

- **gate_review_sent:** Review message sent to architect
