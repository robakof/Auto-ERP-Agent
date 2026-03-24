---

# === META ===

convention_id: meta-convention

version: "1.0"

status: review

  

# === LIFECYCLE ===

created: 2026-03-24

updated: 2026-03-24

  

# === OWNERSHIP ===

author: architect

owner: architect

approver: human

  

# === SCOPE ===

audience: [architect, prompt_engineer, developer, metodolog]

scope: "Definiuje strukturę wszystkich conventions w projekcie Mrowisko"

  

# === RELATIONSHIPS ===

requires: []

replaces: []

superseded_by: null

  

# === VALIDATION ===

validation: manual

exceptions_require_justification: true

---

  

# META_CONVENTION — Convention for Conventions

  

## TL;DR

  

Convention = YAML frontmatter (metadata) + markdown body (content).

  

**3 levels loading:**

- **Minimal** (session start): YAML + TL;DR

- **Standard** (workflow): + Rules + Examples

- **Full** (update/review): Everything

  

**Status lifecycle:** draft → review → active → deprecated/superseded

  

**Approver:** Human (zawsze)

  

---

  

## Scope & Audience

  

### Audience

  

| Role                | Użycie                                                |
| ------------------- | ----------------------------------------------------- |
| **Architect**       | Tworzy/aktualizuje conventions, review compliance     |
| **Prompt Engineer** | Tworzy WORKFLOW/PROMPT conventions, follows structure |
| **Developer**       | Follows CODE/COMMIT conventions, może propose changes |
| **Metodolog**       | Review alignment conventions z SPIRIT.md              |
| **Human**           | Approves status transitions (draft → review → active) |

  

### Scope

  

**Pokrywa:**

- Struktura każdej convention (required sections)

- YAML frontmatter (metadata fields)

- Status lifecycle (draft → active → deprecated)

- Ownership model (author/owner/approver)

- Loading levels (minimal/standard/full)

  

**NIE pokrywa:**

- Content poszczególnych conventions (to ich owners)

- Enforcement tooling details (future: osobna konwencja)

- Workflow integration specifics (to WORKFLOW_CONVENTION)

  

---

  

## Context / Motivation

  

### Problem

  

Bez META_CONVENTION:

- Każda convention ma inną strukturę

- Brak machine-readable metadata (nie można parsować do DB)

- Brak lifecycle management (kto zatwierdza? kiedy deprecated?)

- Context overload (agent ładuje całą convention gdy potrzebuje TL;DR)

  

### Solution

  

META_CONVENTION definiuje:

1. **Unified structure** — wszystkie conventions tej samej anatomii

2. **Machine-readable metadata** — YAML frontmatter parseable do DB

3. **Lifecycle states** — explicit status transitions

4. **Context levels** — agent ładuje tyle ile potrzebuje

  

### Prior Art

  

Based on research (GPT-5.4 Thinking, 2026-03-24):

- Python PEPs (PEP 1, PEP 12)

- Rust RFCs (RFC 0002)

- MADR (Markdown Any Decision Records)

- IETF RFC Style Guide (RFC 7322)

- SKILL.md pattern (Claude Code ecosystem)

  

---

  

## Rules

  

### R1: YAML Frontmatter Required

  

Każda convention MUSI mieć YAML frontmatter z polami:

  

**Required fields:**

```yaml

---

convention_id: string     # unique identifier (kebab-case)

version: string           # "1.0", "1.1", etc.

status: enum              # draft | review | active | deprecated | superseded

created: date             # YYYY-MM-DD

updated: date             # YYYY-MM-DD

author: string            # kto napisał

owner: string             # kto utrzymuje

approver: string          # kto zatwierdza status transitions

audience: list[string]    # kto używa

scope: string             # co convention pokrywa (1 zdanie)

---

```

  

**Optional fields:**

```yaml

effective_from: date      # kiedy wchodzi w życie

deprecated_from: date     # kiedy deprecated

requires: list[string]    # dependencies (convention_ids)

replaces: list[string]    # co zastępuje

superseded_by: string     # co zastąpiło tę convention

related: list[string]     # powiązane conventions

validation: enum          # manual | schema | linter

exceptions_require_justification: bool

```

  

### R2: Required Markdown Sections

  

Każda convention MUSI mieć sekcje:

  

| Section | Level | Purpose |

| --- | --- | --- |

| **TL;DR** | Minimal | 3-5 bullet points, core essence |

| **Scope & Audience** | Standard | Kto, kiedy, co pokrywa, co NIE |

| **Rules** | Standard | Numerowane reguły (R1, R2...) |

| **Examples** | Standard | Przykłady zgodne z convention |

| **Anti-patterns** | Full | Bad → Why → Good (3-part structure) |

| **Exceptions** | Full | Kiedy można odstąpić, jak udokumentować |

| **Changelog** | Full | Version history |

  

**Optional sections:**

- Context/Motivation (dla complex conventions)

- Migration (gdy breaking changes)

- References (external sources)

  

### R3: Status Lifecycle

  

```

draft ──→ review ──→ active ──→ deprecated

                        │            │

                        └──→ superseded ←──┘

```

  

| Status | Meaning | Who can set |

| --- | --- | --- |

| **draft** | Work in progress | Author |

| **review** | Ready for approval | Author (requests review) |

| **active** | Approved, enforced | Human (approves) |

| **deprecated** | Phasing out, still valid | Human |

| **superseded** | Replaced by new convention | Human (links superseded_by) |

  

**Rule:** Only Human can transition to `active`, `deprecated`, or `superseded`.

  

### R4: Loading Levels

  

Agent systems SHOULD load conventions at appropriate level:

  

**Minimal (session start):**

```python

load_sections(convention, ["TL;DR"])

# ~100 tokens

```

  

**Standard (workflow entry):**

```python

load_sections(convention, ["TL;DR", "Scope & Audience", "Rules", "Examples"])

# ~500 tokens

```

  

**Full (review/update):**

```python

load_sections(convention, all_sections)

# ~1500 tokens

```

  

### R5: Ownership Model

  

| Role | Responsibility |

| --- | --- |

| **Author** | Writes convention content |

| **Owner** | Maintains convention, handles updates |

| **Approver** | Decides status transitions |

  

**Default:** Author = Owner = same person.

**Approver:** Always Human (for now).

  

**Cross-role contributions:**

- Anyone can propose changes (via agent_bus suggest)

- Owner reviews and incorporates

- Human approves status changes

  

### R6: Supersession Over Silent Edits

  

When convention fundamentally changes:

1. Create new convention (version bump or new convention_id)

2. Set old convention `status: superseded`

3. Set old convention `superseded_by: new_convention_id`

4. New convention `replaces: [old_convention_id]`

  

**DO NOT:** Silently rewrite active convention without trace.

  

### R7: Convention Location

  

All conventions live in: `documents/conventions/`

  

**Naming:** `{SCOPE}_CONVENTION.md` (UPPER_CASE)

- `META_CONVENTION.md`

- `WORKFLOW_CONVENTION.md`

- `PROMPT_CONVENTION.md`

- `CODE_CONVENTION.md`

- `COMMIT_CONVENTION.md`

  

---

  

## Examples

  

### Example 1: Minimal Convention (COMMIT_CONVENTION)

  

```yaml

---

convention_id: commit-convention

version: "1.0"

status: active

created: 2026-03-24

updated: 2026-03-24

author: developer

owner: developer

approver: human

audience: [developer, architect, prompt_engineer, erp_specialist]

scope: "Format commit messages"

---

  

# COMMIT_CONVENTION

  

## TL;DR

  

- Format: `type(scope): description`

- Types: feat, fix, refactor, docs, test, chore

- Max 72 chars first line

- Use git_commit.py tool

  

## Rules

  

### R1: Commit Message Format

...

```

  

### Example 2: Loading Levels in Practice

  

**Session start (Architect):**

```

Ładuję conventions dla Architect (minimal level):

- META_CONVENTION: Definiuje strukturę conventions, status: active

- WORKFLOW_CONVENTION: Struktura workflow documents, status: active

```

  

**Workflow entry (checking compliance):**

```

Sprawdzam zgodność z WORKFLOW_CONVENTION:

[Loads TL;DR + Rules + Examples]

```

  

**Updating convention:**

```

Aktualizuję WORKFLOW_CONVENTION:

[Loads full convention including Anti-patterns, Exceptions, Changelog]

```

  

---

  

## Anti-patterns

  

### AP1: Missing YAML Frontmatter

  

**Bad:**

```markdown

# My Convention

  

Some rules here...

```

  

**Why:** Not machine-readable, no metadata, can't track status/ownership.

  

**Good:**

```yaml

---

convention_id: my-convention

version: "1.0"

status: draft

...

---

  

# My Convention

...

```

  

### AP2: Monolithic Loading

  

**Bad:**

```python

# Always load full convention

convention = read_file("WORKFLOW_CONVENTION.md")

# 1500 tokens loaded when agent only needs overview

```

  

**Why:** Context waste, slower processing, unnecessary token cost.

  

**Good:**

```python

# Load appropriate level

if session_start:

    convention = load_sections("WORKFLOW_CONVENTION.md", ["TL;DR"])

elif workflow_entry:

    convention = load_sections("WORKFLOW_CONVENTION.md", ["TL;DR", "Rules", "Examples"])

```

  

### AP3: Silent Breaking Changes

  

**Bad:**

```markdown

# Changed Rules section completely

# No version bump, no changelog entry, no supersession

```

  

**Why:** Agents/humans with cached knowledge will violate "new" rules unknowingly.

  

**Good:**

```yaml

---

version: "2.0"  # bumped

status: active

replaces: ["workflow-convention-v1"]

---

  

## Changelog

- 2.0 (2026-03-25): Breaking change - new Rules structure

```

  

### AP4: Approver = Author

  

**Bad:**

```yaml

author: architect

owner: architect

approver: architect  # Same person approves their own work

```

  

**Why:** No review gate, quality not verified.

  

**Good:**

```yaml

author: architect

owner: architect

approver: human  # External approval

```

  

---

  

## Exceptions

  

### E1: Draft Conventions

  

Draft conventions MAY have incomplete sections (missing Examples, Anti-patterns).

  

**Justification:** Work in progress, will be completed before `review` status.

  

### E2: Urgent Hotfix

  

In emergency, Human MAY approve convention directly to `active` skipping `review`.

  

**Required:** Document reason in Changelog: "Hotfix: [reason], skipped review."

  

### E3: Legacy Conventions

  

Existing conventions (before META_CONVENTION) MAY have temporary non-compliance.

  

**Required:** Migration plan with deadline in Changelog.

  

---

  

## Migration

  

### Existing Conventions to Migrate

  

| Convention | Current Location | Status |

| --- | --- | --- |

| WORKFLOW_CONVENTION | documents/prompt_engineer/ | Needs YAML frontmatter |

| PROMPT_CONVENTION | documents/prompt_engineer/ | Needs YAML frontmatter |

| CODE_STANDARDS | documents/dev/ | Rename to CODE_CONVENTION + YAML |

  

### Migration Steps

  

1. Add YAML frontmatter (required fields)

2. Add TL;DR section

3. Ensure required sections exist (Rules, Examples)

4. Move to `documents/conventions/`

5. Update references in role documents

6. Set status: `active` (after Human approval)

  

### Timeline

  

Migration deadline: Po Human approval META_CONVENTION.

  

---

  

## References

  

- Research: `documents/researcher/research/research_results_meta_convention.md`

- SKILL.md pattern: Claude Code ecosystem

- Python PEP 1: https://peps.python.org/pep-0001/

- MADR: https://adr.github.io/madr/

- Conventional Commits: https://www.conventionalcommits.org/

  

---

  

## Changelog

  

| Version | Date | Changes | Author |

| --- | --- | --- | --- |

| 1.0 | 2026-03-24 | Initial META_CONVENTION based on research | Architect |