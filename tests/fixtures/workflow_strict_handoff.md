---
workflow_id: test_handoff
version: "1.0"
owner_role: erp_specialist
trigger: "Test workflow with HANDOFF point"
---

## Outline

1. **Draft** — create SQL draft
2. **Handoff** — send to human for approval

---

## Phase 1: Draft

### Step 1: Create Draft

**step_id:** create_draft
**action:** Utwórz draft SQL
**tool:** Write
**command:** `solutions/draft.sql`
**verification:** file_exists solutions/draft.sql
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Cannot create draft file"
**next_step:** send_approval (if PASS), escalate (if FAIL)

### Exit Gate

- **gate_draft_exists:** Draft SQL file created

---

## Phase 2: Approval

### Step 2: Send for Approval

**step_id:** send_approval
**action:** Wyślij draft do zatwierdzenia przez człowieka
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py flag --from erp_specialist --reason-file tmp/approval.md`
**verification:** message_sent
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Could not send approval request"
**next_step:** end (if PASS), escalate (if FAIL)

→ HANDOFF: human. STOP. Czekaj na zatwierdzenie.

### Exit Gate

- **gate_approval_sent:** Approval request sent to human
