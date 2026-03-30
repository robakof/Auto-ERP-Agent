# ADR-004: Policy Engine — Configurable Tool Enforcement

Date: 2026-03-30
Status: Accepted

## Context

### Problem

Agenci ignoruja workflow gate i inne reguly kontroli. Prompt-level enforcement nie dziala —
agenci pomijaja reguly gdy sa pod presja kontekstu lub gdy regula koliduje z celem.
Diagnoza #530 (dispatcher, 2026-03-29) zidentyfikowala to jako problem #1.

Obecny enforcement:
- Prompty (CLAUDE.md, role docs) — ignorowane
- Hooki (pre_tool_use) — dzialaja mechanicznie, ale pokrywaja tylko safety (rm, memory)
- Brak kontroli workflow compliance

### Wymagania

1. **Atomowa granularity:** per-agent, per-workflow, per-step control nad narzediami
2. **Konfigurowalnosc:** policy definiowana w pliku (nie hardcode w hookach)
3. **Skalowanosc:** 100 agentow, kazdy z innym zestawem uprawnien
4. **Dispatcher jako approver:** eskalacja naruszen do orkiestratora w real-time
5. **Runtime modification:** dispatcher moze modyfikowac policy per-agent bez restartu
6. **Observability:** kazda decyzja (allow/deny/warn/escalate) logowana

### Docelowy model orkiestracji (D4 z planu v2)

**v1:** Agent done → event → orkiestrator → walidacja → poke dalej
**v2:** Agent done → auto-walidacja (policy engine) → direct poke + notify orkiestrator

Policy Engine jest fundamentem obu modeli — waliduje kazde dzialanie agenta.

## Research Summary

### Inspiracje z istniejacych systemow

#### Open Policy Agent (OPA)

- **Policy as Data:** Rego language (deklaratywny, Datalog-inspired). Policy to dane, nie kod.
- **Structured decisions:** Nie tylko allow/deny — zwraca obiekty z metadata
  (reason, next_action, escalation_required). Mapuje sie na nasz warn/escalate.
- **Hierarchical evaluation:** namespace → resource → action → conditions.
  Naturalnie mapuje sie na per-agent → per-workflow → per-step → per-tool.
- **Runtime updates:** Bundle downloads (HTTP polling). Zero-downtime reload.
- **ABAC:** Attribute-based access control — decyzja zalezy od atrybutow kontekstu,
  nie tylko od roli. Pasuje do naszego "workflow context narrows permissions".

#### Kubernetes RBAC + Admission Controllers

- **3-warstwowa autoryzacja:** Identity+Role → Action Interception → Audit Trail.
- **Two-phase enforcement:** Mutating (normalizuj request) → Validating (odrzuc naruszenia).
  Dla nas: Phase 1 = wzbogac context (dodaj workflow_id, step_id), Phase 2 = evaluate policy.
- **Orchestrator as Admission Controller:** Orkiestrator przejmuje kazdy tool call,
  waliduje, decyduje. Agent czeka synchronicznie na verdict.
- **Hot-reload:** Policies w external config (ConfigMap), zmiany bez restartu agenta.
- **Namespace scope = Workflow context:** Kazdy workflow to izolowany namespace uprawnien.

#### AWS IAM

- **Explicit Deny Wins:** Deterministyczna resolution — deny na kazdym poziomie wygrywa.
  Evaluation order: deny first → boundaries → role policies → session policies.
- **Session Policies (kluczowe!):** Tymczasowe scoping — workflow context moze TYLKO
  zwezic uprawnienia roli, NIGDY rozszerzyc. Agent w workflow ma <= uprawnien niz bazowa rola.
  Dokladnie to czego potrzebujemy: workflow restrictions as intersection, not union.
- **Permission Boundaries:** Hard ceiling — nawet jesli dispatcher da runtime override,
  boundary nie pozwoli przekroczyc limitu. Safety net.
- **ABAC tags:** Dynamiczne binding agent → resource group bez zmiany policy.
  Np. tag "owner=erp_specialist" na plikach → policy matchuje po tagu.

### Kluczowe wzorce (potwierdzone researchem)

1. **Policy as Data:** JSON/JSON, nie kod. Wersjonowane w git, review przez Architekta.
   (OPA, K8s — confirmed)
2. **Explicit Deny Wins:** Deterministyczna resolution. Deny > escalate > warn > allow.
   (AWS IAM — confirmed, najwazniejszy wzorzec)
3. **Session Policy = Intersection:** Workflow context ZWEZA uprawnienia roli, nie rozszerza.
   Agent w workflow ma mniej lub rowno niz bazowa rola.
   (AWS IAM session policies — confirmed)
4. **Two-Phase Enforcement:** Phase 1: wzbogac context. Phase 2: evaluate policy.
   (K8s admission controllers — confirmed)
5. **Structured Decisions:** Nie bool, a obiekt: {decision, reason, guidance, escalate_to}.
   (OPA — confirmed)
6. **Hot-Reload:** Policy changes bez restartu. File watch lub poll.
   (K8s ConfigMap, OPA bundles — confirmed)
7. **Audit Trail:** Kazda decyzja logowana: who, what, where, why, decision.
   (K8s audit logging — confirmed)
8. **Permission Boundary:** Hard ceiling — runtime overrides nie moga przekroczyc.
   Safety net przeciw privilege escalation.
   (AWS IAM permission boundaries — confirmed)

## Architecture

### Poziomy granularity

```
Level 0: Global defaults (outside workflow)
  │
  ├── Level 1: Per-role defaults
  │     │
  │     ├── Level 2: Per-workflow overrides
  │     │     │
  │     │     └── Level 3: Per-step overrides (najwyzszy priorytet)
```

Evaluation order: Level 3 > Level 2 > Level 1 > Level 0.
Explicit deny na kazdym poziomie wygrywa (deny > escalate > warn > allow).

**Intersection principle (z AWS IAM session policies):**
Workflow/step policy moze TYLKO zwezic uprawnienia roli bazowej, NIGDY rozszerzyc.
Efektywne uprawnienia = role_permissions ∩ workflow_restrictions ∩ step_restrictions.
Jesli rola nie pozwala Write, workflow nie moze dodac Write.
Safety net: Permission Boundary per rola — hard ceiling, nie do nadpisania runtime override.

### Decision Types

| Decision | Behavior | Agent experience |
|----------|----------|-----------------|
| `allow` | Tool call proceeds | Transparent — agent nie wie o policy |
| `warn` | Tool call proceeds + log | Agent widzi warning message |
| `warn_after(N)` | Allow first N calls, then warn | Soft limit — nie blokuje, informuje |
| `deny` | Tool call blocked | Agent widzi deny message + guidance |
| `escalate` | Tool call paused | Agent czeka na decyzje orkiestratora |

### Policy Schema (JSON)

```json
{
  "version": "1.0",

  "global": {
    "outside_workflow": {
      "Read": "allow",
      "Grep": "allow",
      "Glob": "allow",
      "Bash": {"action": "warn_after", "threshold": 5},
      "Write": {"action": "warn_after", "threshold": 3},
      "Edit": {"action": "warn_after", "threshold": 3},
      "suggest": "allow",
      "inbox": "allow",
      "log": "allow"
    }
  },

  "roles": {
    "dispatcher": {
      "always": {
        "spawn": "deny",
        "kill": "deny",
        "stop": "allow",
        "resume": "allow",
        "poke": "allow"
      }
    },
    "erp_specialist": {
      "always": {
        "Write": {"action": "allow", "paths": ["solutions/**", "tmp/**"]},
        "Bash": {"action": "allow", "commands": ["py tools/erp_*.py", "py tools/sql_query.py"]}
      }
    }
  },

  "workflows": {
    "erp_columns": {
      "tools": {
        "Bash": {"action": "allow", "commands": ["py tools/erp_*.py", "py tools/sql_query.py"]},
        "Write": {"action": "allow", "paths": ["solutions/**"]},
        "Edit": {"action": "allow", "paths": ["solutions/**", "documents/erp_specialist/**"]}
      }
    }
  },

  "steps": {
    "erp_columns.validate_sql": {
      "tools": {
        "Bash": {"action": "allow", "commands": ["py tools/erp_validate.py"]},
        "Write": "deny",
        "Edit": "deny"
      }
    }
  }
}
```

Runtime overrides ustawiane przez dispatchera w DB (tabela policy_overrides).
Mergowane na wierzch JSON policy — wyzszy priorytet.
Np. dispatcher tymczasowo luzuje Write dla sesji debugowej.

### Evaluation Algorithm

```
function evaluate(tool_call, agent_context):
  # 1. Check runtime overrides (highest priority)
  if override exists for agent_context.session_id:
    return override.decision

  # 2. Check per-step policy (Level 3)
  if agent_context.workflow_id AND agent_context.current_step:
    step_key = f"{workflow_id}.{current_step}"
    if step_key in policy.steps:
      return policy.steps[step_key].evaluate(tool_call)

  # 3. Check per-workflow policy (Level 2)
  if agent_context.workflow_id:
    if workflow_id in policy.workflows:
      return policy.workflows[workflow_id].evaluate(tool_call)

  # 4. Check per-role policy (Level 1)
  if agent_context.role in policy.roles:
    role_policy = policy.roles[agent_context.role]
    if "always" in role_policy:
      decision = role_policy.always.evaluate(tool_call)
      if decision != "not_defined":
        return decision

  # 5. Check global defaults (Level 0)
  if agent_context.workflow_active:
    return allow  # in workflow = trusted (Level 2/3 restrict if needed)
  else:
    return policy.global.outside_workflow.evaluate(tool_call)

  # 6. Default: allow (backward compat)
  return allow
```

### Dispatcher Approval Loop (escalate action)

```
1. Hook catches policy violation → decision = escalate
2. Hook creates approval_request in DB:
   {agent_session, tool_name, tool_input_summary, policy_rule, timestamp}
3. Hook returns deny to agent with message:
   "Czekam na zatwierdzenie orkiestratora. Przejdz do innego kroku lub czekaj."
4. Event emitted: "approval_requested" → orkiestrator gets poke/event
5. Orkiestrator reviews:
   - approve → DB update, agent gets poke "Zatwierdzono, ponow operacje"
   - deny + guidance → DB update, agent gets poke "Odrzucono: [powod]. [co zrobic]"
6. Agent retries tool call → hook checks approval → allow/deny based on decision
```

### Integration Points

```
pre_tool_use.py:
  BEFORE existing logic (poke, memory, bash):
    1. Load policy (cached, reload on file change)
    2. Build agent_context (role, session, workflow_id, step from DB)
    3. Evaluate policy
    4. Decision: allow → continue | warn → log + continue | deny → deny_response
       | escalate → create approval_request + deny with "waiting for approval"

live_agents table:
  New columns: workflow_active (bool), current_workflow_id, current_step_id
  Updated by: workflow-start, step-log, workflow-end

policy.json:
  Location: documents/architecture/policy.json (or config/policy.json)
  Versioned in git. Reviewed by Architect.
  Runtime overrides in DB (policy_overrides table).

DB tables (new):
  policy_overrides: {session_id, rule_json, set_by, expires_at}
  approval_requests: {id, agent_session, tool_name, input_summary,
                      policy_rule, status (pending/approved/denied),
                      decided_by, decision_reason, created_at, decided_at}
  policy_audit: {id, agent_session, tool_name, decision, policy_rule,
                 context_json, created_at}
```

## Migration Path: v0 → v1

### v0 (Faza 0 — natychmiastowe)

- `workflow_active` flag w live_agents
- Hook: Write/Edit poza workflow → warn_after(3)
- Config w prostym JSON: `{"warn_threshold": 3, "whitelist": ["Read", "Grep", "Glob"]}`
- Alert do dispatchera (send message)
- Interfejsy kompatybilne z v1 (agent_context, evaluate pattern)

### v1 (Faza 4 — pelny engine)

- JSON policy loader
- 4 poziomy granularity
- 5 decision types
- Dispatcher approval loop
- Runtime overrides
- Audit trail

**Kluczowe:** v0 buduje interfejsy (agent_context, evaluate, decision) ktore v1 rozszerza.
Zero breaking changes przy upgrade v0 → v1.

## Consequences

### Gains

- Mechaniczny enforcement — agenci nie moga ignorowac regul
- Konfigurowalnosc — zmiana policy bez zmiany kodu
- Skalowanosc — 100 agentow, kazdy z innym zestawem uprawnien
- Observability — audit trail kazdej decyzji
- Dispatcher control — runtime overrides, approval loop
- Gradual rollout — v0 (warning) → v1 (enforcement) → v2 (auto-validation)

### Costs

- Hook overhead: ~5-10ms per tool call (policy load + evaluate + log)
- Complexity: policy JSON maintenance, conflict resolution
- Learning curve: agenci i operatorzy musza rozumiec policy model
- DB growth: audit trail (mitigation: 7-day TTL jak events)

### Risks

- **Over-restriction:** zbyt agresywna policy blokuje produktywnosc
  Mitigation: warn_after(N) zamiast deny, gradual tightening
- **Policy conflicts:** sprzeczne reguly na roznych poziomach
  Mitigation: explicit deny wins, evaluation order deterministic
- **Approval bottleneck:** orkiestrator nie odpowiada na escalate
  Mitigation: timeout → auto-deny + flag do czlowieka
- **Config drift:** policy.json out of sync z reality
  Mitigation: audit trail analysis, periodic review

## Open Questions (do rozwiazania przy wdrozeniu)

1. Gdzie policy.json? `config/policy.json` vs `documents/architecture/policy.json`
2. Jak czesto reload policy w hooku? Per-call vs cached + file watch
3. Approval timeout: ile sekund czekac na orkiestratora?
4. Czy v0 JSON config powinien byc podzbiorem v1 JSON (same pole)?
5. Czy policy_audit jest osobna tabela czy reuse events table z ADR-003?

**Nota:** Brakuje fundamentow pod niektore elementy (np. CONVENTION_FILE_STRUCTURE
dla paths w policy). Otwarte kwestie rozwiazujemy przy wdrozeniu — do tego czasu
brakujace konwencje moga juz istniec.
