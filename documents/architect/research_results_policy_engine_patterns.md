# Research: Policy Engine Patterns — OPA, K8s RBAC, AWS IAM

**Data:** 2026-03-30
**Cel:** Wzorce enforcement dla Policy Engine (ADR-004)
**Metoda:** 3 rownolegle researche (OPA, K8s, AWS IAM)

---

## TL;DR — 8 wzorcow do zastosowania

1. **Policy as Data** (OPA, K8s) — YAML/JSON, nie kod
2. **Explicit Deny Wins** (AWS IAM) — deterministyczna resolution
3. **Session Policy = Intersection** (AWS IAM) — workflow zweza, nie rozszerza
4. **Two-Phase Enforcement** (K8s) — normalize context → evaluate policy
5. **Structured Decisions** (OPA) — obiekt z decision + reason + guidance
6. **Hot-Reload** (K8s, OPA) — policy changes bez restartu
7. **Audit Trail** (K8s) — kazda decyzja logowana
8. **Permission Boundary** (AWS IAM) — hard ceiling, nie do nadpisania

---

## Open Policy Agent (OPA)

### Policy Model
- Rego language (deklaratywny, Datalog-inspired)
- Evaluation: Input (structured data) → Policy rules → Decision (arbitrary structured output)
- Policy to dane, nie kod — wersjonowanie, review, runtime update

### Granularity
- ABAC (Attribute-Based Access Control) — decyzja zalezy od atrybutow kontekstu
- Hierarchia: namespace → resource type → action → conditions
- Mapowanie na nasz system: per-agent → per-workflow → per-step → per-tool

### Decision Types
- Nie tylko bool — structured decisions:
  - allow / deny (enforcement)
  - warn / info (advisory)
  - Conditional: "allow if manager approves"
  - Metadata: reason, next_action, escalation_required

### Integration Pattern
1. Request intercepted → extract context
2. HTTP POST do OPA z JSON input
3. OPA evaluates → returns decision object
4. Middleware enforces: allow → proceed, deny → reject, warn → queue for approval

### Runtime Updates
- Bundle downloads (HTTP polling). Zero-downtime reload.
- Local file changes require restart (no hot-reload built-in for files)

### Fit for Mrowisko
- Hierarchical evaluation maps to per-agent → per-workflow → per-step → per-tool
- Conditional decisions enable escalation (deny + escalate_to_human flag)
- Bundle updates allow orchestrator to modify permissions at runtime

---

## Kubernetes RBAC + Admission Controllers

### RBAC Model
- Role: definiuje permissions (resource + verb)
- RoleBinding: przypisuje Role do podmiotu w namespace
- Namespace scope = workflow context (izolowany namespace uprawnien)
- Granularity: namespace → resource → verb

### Admission Controllers
- Interceptor pattern: przechwytuje API call PRZED wykonaniem
- Two-phase:
  1. **Mutating:** normalize/inject defaults (dodaj tracking fields)
  2. **Validating:** reject violations (policy enforcement)
- Synchroniczny — agent czeka na verdict
- Dynamic: webhook-based, external policy evaluation

### Dynamic Policies
- Config w external source (ConfigMap, CRDs)
- Hot-reload: zmiany bez restartu
- Watch pattern: agent/hook sprawdza policy na kazdym call

### Escalation Pattern
- Fail-closed design (declarative constraints)
- ResourceQuota: pre-emptive limits (max concurrent tasks per agent)
- PodSecurityPolicy: constraints bez "ask permission"

### Audit Logging
- Log EVERY decision (allowed/denied) z metadata
- Stages: Request received → Decision made → Response returned
- Context: who, what, where, why (agent, tool, workflow, decision reason)

### Fit for Mrowisko
- Orchestrator as Admission Controller — interceptor pattern
- Two-phase enforcement: wzbogac context → evaluate policy
- Namespace = workflow isolation
- Hot-reload policies z pliku YAML

---

## AWS IAM

### Policy Structure
- 4 elementy: Effect (Allow/Deny), Action, Resource, Condition
- Multiple statements kombinuja sie addytywnie
- Explicit Allow grants access; Explicit Deny ZAWSZE overrides

### Policy Evaluation Logic (deterministyczny)
1. Check for explicit Deny (highest priority)
2. Evaluate Service Control Policies (SCPs)
3. Check resource-based policies
4. Verify permissions boundaries
5. Require explicit Allow in identity-based policies

**Kluczowy wzorzec:** Deny-by-default z exception-based allowlisting.

### Condition Keys (context-driven)
- Time-based: aws:CurrentTime (temporal access windows)
- IP-based: aws:SourceIp (network restrictions)
- Tag-based: aws:PrincipalTag, aws:ResourceTag (ABAC)
- Conditions AND within statement, statements OR between each other

### Session Policies (KLUCZOWE dla nas)
- AssumeRole accepts inline session policies
- Session policies = INTERSECTION z role policy
- **Moga tylko ZWEZIC, nigdy rozszerzyc**
- Enables: dynamic privilege reduction for specific workflows without new roles

### Permission Boundaries
- AND-gate: granted = (identity policy ∩ boundary)
- Boundaries NIE grantuja — tylko cap maximum permissions
- Hard ceiling — safety net against privilege escalation

### Fit for Mrowisko
- Role-based base: agent role z fixed permissions
- Workflow override: session policy narrows permissions (intersection)
- Hard limits: boundaries prevent escalation
- Deterministic conflicts: explicit deny always wins
- ABAC tags: dynamic binding agent → resource groups

---

## Porownanie z naszym podejsciem (ADR-004)

| Aspekt | OPA | K8s | AWS IAM | Mrowisko Policy Engine |
|--------|-----|-----|---------|----------------------|
| Policy format | Rego | YAML (CRD) | JSON | YAML |
| Evaluation | Input→Rules→Decision | Mutate→Validate | Ordered chain | Two-phase + ordered chain |
| Decisions | Structured objects | Allow/Deny | Allow/Deny | allow/warn/deny/escalate |
| Conflict resolution | Last rule wins | OR (any allow) | Explicit deny wins | Explicit deny wins |
| Runtime update | Bundle pull | ConfigMap watch | API call | File watch + DB overrides |
| Granularity | ABAC (flexible) | Namespace/Resource/Verb | Service/Action/Resource | Role/Workflow/Step/Tool |
| Escalation | Custom (metadata) | Fail-closed | None | Dedicated decision type |
| Hard ceiling | No built-in | ResourceQuota | Permission Boundary | Permission Boundary per role |

### Co adoptujemy

1. **Z OPA:** Structured decisions (nie bool), policy as data (YAML)
2. **Z K8s:** Two-phase enforcement, orchestrator as admission controller, audit trail
3. **Z AWS IAM:** Explicit deny wins, session policies (intersection), permission boundaries

### Co NIE adoptujemy

- OPA Rego language — za zlozony, YAML prosty wystarczy
- K8s webhook pattern — za ciezki, hook w procesie wystarczy
- AWS IAM full evaluation chain (SCPs, resource policies) — over-engineering dla naszej skali
