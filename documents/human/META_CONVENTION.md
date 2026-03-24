---
convention_id: meta-convention
version: "1.0"
status: review
created: 2026-03-24
author: architect
owner: architect
approver: dawid
scope: "Defines structure for all conventions in Mrowisko project"
---

# META_CONVENTION

## TL;DR

- Convention = YAML frontmatter + markdown body
- Required sections: TL;DR, Scope, Rules, Examples, Anti-patterns, Changelog
- Status lifecycle: `draft` → `review` → `active` → `deprecated` / `superseded`
- Only Dawid can approve status transitions to `active`
- Language: English (code layer convention)

---

## Scope

**Covers:**
- Structure of every convention (required sections)
- YAML frontmatter (metadata fields)
- Status lifecycle
- Ownership model

**Does NOT cover:**
- Content of individual conventions (their owners decide)
- Enforcement tooling (future: separate convention)

**Audience:** architect, prompt_engineer, developer, metodolog

---

## Rules

### R1: YAML Frontmatter Required

Every convention MUST have YAML frontmatter with fields:

```yaml
---
convention_id: string     # unique identifier (kebab-case)
version: string           # "1.0", "1.1", etc.
status: enum              # draft | review | active | deprecated | superseded
created: date             # YYYY-MM-DD
author: string            # who wrote it
owner: string             # who maintains it
approver: string          # who approves status transitions
scope: string             # what convention covers (1 sentence)
---
```

### R2: Required Markdown Sections

Every convention MUST have these sections:

| Section | Purpose |
|---|---|
| **TL;DR** | 3-5 bullet points, core essence |
| **Scope** | What it covers, what it does NOT, audience |
| **Rules** | Numbered rules (R1, R2...) |
| **Examples** | Examples compliant with convention |
| **Anti-patterns** | Bad → Why → Good (3-part structure) |
| **Changelog** | Version history |

### R3: Status Lifecycle

```
draft ──→ review ──→ active ──→ deprecated
                        │            │
                        └──→ superseded ←──┘
```

| Status | Meaning | Who can set |
|---|---|---|
| **draft** | Work in progress | Author |
| **review** | Ready for approval | Author |
| **active** | Approved, enforced | Dawid only |
| **deprecated** | Phasing out | Dawid only |
| **superseded** | Replaced by new convention | Dawid only |

### R4: Supersession Over Silent Edits

When convention fundamentally changes:
1. Create new version (bump version number)
2. Document change in Changelog
3. If breaking: set old status to `superseded`, create new convention

DO NOT silently rewrite active convention without trace.

### R5: Convention Location

All conventions live in: `documents/conventions/`

Naming: `{SCOPE}_CONVENTION.md` (UPPER_CASE)

---

## Examples

### Example 1: Minimal Convention

```yaml
---
convention_id: commit-convention
version: "1.0"
status: active
created: 2026-03-24
author: developer
owner: developer
approver: dawid
scope: "Commit message format"
---

# COMMIT_CONVENTION

## TL;DR

- Format: `type(scope): description`
- Types: feat, fix, refactor, docs, test, chore
- Use git_commit.py tool

## Scope

Covers: commit message format for all roles.
Does NOT cover: branch naming, PR format.

## Rules

### R1: Message Format
...

## Examples
...

## Anti-patterns
...

## Changelog

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-03-24 | Initial version |
```

### Example 2: Loading Levels

Agents load conventions at appropriate depth:

- **Session start:** YAML frontmatter + TL;DR only (~100 tokens)
- **Workflow entry:** + Scope + Rules + Examples (~500 tokens)
- **Review/update:** Full document (~1000+ tokens)

This is a guideline, not enforced by tooling.

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
```

### AP2: Silent Breaking Changes

**Bad:**
```markdown
# Changed Rules section completely
# No version bump, no changelog entry
```

**Why:** Agents with cached knowledge will violate "new" rules unknowingly.

**Good:**
```yaml
version: "2.0"  # bumped
---

## Changelog
| 2.0 | 2026-03-25 | Breaking: new Rules structure |
```

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-03-24 | Initial META_CONVENTION — minimal version |
