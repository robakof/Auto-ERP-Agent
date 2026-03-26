# Research: META_CONVENTION — Convention Design Best Practices

**Base prompt:** `documents/researcher/prompts/01 EXPLORATORY_BASE_PROMPT.md`

**Thoroughness:** very thorough

---

## Mission (specifics)

Map the landscape of how successful projects define, structure, and enforce conventions. Show what's proven — not what we guess. We need to understand meta-conventions (conventions for creating conventions) to build a solid foundation for Mrowisko's convention system.

**Context:**
Mrowisko is building a convention registry system. Before drafting META_CONVENTION (the convention that governs all conventions), we need research on best practices from proven projects.

**Baseline Pattern:**
Claude Code ecosystem already has a proven convention pattern: **SKILL.md** (YAML frontmatter + markdown body). This is our baseline. External research supplements this — adds versioning, enforcement, ownership patterns that SKILL.md lacks.

**Critical:** This research must be **objective** — report what exists, how different projects approach conventions, what trade-offs they make. **Do NOT evaluate fit for Mrowisko** — that's Architect's job after research.

---

## Baseline: SKILL.md Pattern (Claude Code)

**What we already have:**

Claude Code ecosystem uses SKILL.md as convention for skills. Structure:

```yaml
---
name: "skill-name"
description: "what it does"
disable-model-invocation: true  # auto-invokable vs manual
allowed-tools: [Read, Write, Bash]  # behavior control
context: fork  # execution isolation
---
# Markdown body
Instructions here...
```

**Properties:**
- ✓ Machine-readable (YAML frontmatter)
- ✓ Human-readable (Markdown body)
- ✓ Lightweight (thin entry file, heavy content in supporting files)
- ✓ Proven (ecosystem standard)
- ✗ No explicit versioning field
- ✗ No conflict resolution
- ✗ No cross-role contribution model
- ✗ Enforcement limited to allowed-tools

**Research Insight (from claude_code_extensions 2.md):**
> "Custom skills are converging on repeatable patterns: thin SKILL.md entrypoints, YAML frontmatter for invocation control, supporting files for heavy context, and composition through subagents/plugins."

**Research Strategy:**
- **Use SKILL.md as baseline** — don't reinvent the wheel
- **External research supplements gaps** — what SKILL.md lacks for general convention use
- **Output format:** Compare findings to SKILL.md ("SKILL.md does X, external does Y, recommendation: Z")

---

## Research Questions

**Focus:** What to add to SKILL.md pattern for general convention use?

### Q1: Meta-Conventions (How do projects define conventions?)

**Focus:** Do established projects have explicit meta-conventions?

**Questions:**
- Do meta-conventions exist in known open-source projects? (Linux Kernel, Python PEPs, RFCs, Architectural Decision Records, Rust RFCs, IETF standards process)
- What sections are **mandatory** in convention documents? (Scope, Rules, Examples, Anti-patterns, Changelog, Rationale, Enforcement)
- What formats do they use? (Markdown with YAML frontmatter, plain text, reStructuredText, custom templating)
- Do conventions have explicit owners/maintainers declared?

**Expected output:**
- List of projects with meta-conventions (with links to meta-convention documents)
- Common structural elements (core sections that appear across multiple projects)
- Differences (what's optional vs mandatory, format variations)
- Ownership models (who writes, who approves, who maintains conventions)

**Evidence threshold:** Official project docs, convention templates, meta-RFC/PEP documents.

---

### Q2: Convention Structure (What to add to SKILL.md baseline?)

**Focus:** SKILL.md has YAML frontmatter + markdown body. What else is needed?

**Baseline (SKILL.md):**
- YAML frontmatter: name, description, behavior flags
- Markdown body: instructions
- NO versioning field
- NO changelog
- NO prerequisites/dependencies

**Questions:**
- Do conventions have versioning? (Semantic versioning? Date-based? Status-based like "Draft/Active/Deprecated"?)
- Do conventions have changelog? (What format? What to track: version, date, changes, rationale, migration notes?)
- Do conventions declare prerequisites or dependencies? (References to other conventions, assumed knowledge, required tooling)
- What sections beyond SKILL.md? (Scope, Audience, Anti-patterns, Examples — which are mandatory vs optional?)

**Expected output:**
- Versioning strategies (compare to SKILL.md lack of versioning — pros/cons)
- Changelog formats (what to add to SKILL.md pattern)
- Dependency declaration patterns (cross-convention references)
- Section structure recommendations (building on SKILL.md baseline)

**Evidence threshold:** Convention examples from major projects, style guides, template repos.

---

### Q3: Enforcement (Beyond SKILL.md allowed-tools?)

**Focus:** SKILL.md has `allowed-tools` (behavior control). What else is needed for general conventions?

**Baseline (SKILL.md):**
- `allowed-tools` — enforces which tools skill can use
- `disable-model-invocation` — manual vs auto-invokable
- `context: fork` — execution isolation
- **Limitation:** Only enforces skill behavior, not convention violations

**Questions:**
- How do projects enforce conventions beyond tool restrictions? (Review checklist, linters/static analysis, CI gates, automated checks, human review)
- Do convention documents contain review checklists? (Embedded in convention? Separate tool? PR template?)
- How do projects handle violations? (Reject outright, warning, accept with justification, "convention debt" tracking)
- Conflict resolution — what if 2 conventions contradict? (Precedence rules, escalation paths)

**Expected output:**
- Enforcement strategies from real projects (compare to SKILL.md allowed-tools — what's missing?)
- Review checklist best practices (format, granularity, when to use)
- Violation handling patterns (strictness vs pragmatism)
- Conflict resolution patterns (how projects handle contradictory conventions)

**Evidence threshold:** CI/CD configs, linter rules, PR templates, contribution guides, documented review processes.

---

### Q4: Template & Anti-patterns (Making conventions learnable)

**Focus:** How to teach conventions effectively.

**Questions:**
- Do conventions include templates? (Blank starting point that follows the convention? Annotated example?)
- Do conventions list anti-patterns? (Explicit "don't do this" sections with rationale?)
- How are anti-patterns presented? (Format: anti-pattern → why bad → correct alternative? Comparative examples? Common mistakes section?)
- Do conventions include real-world examples? (Before/after, good/bad, minimal/comprehensive)

**Expected output:**
- Template formats from real projects (various styles and levels of detail)
- Anti-pattern documentation best practices (how to make them actionable, not just prescriptive)
- Do's and Don'ts presentation styles (comparative tables, annotated examples, FAQ format)
- Example quality patterns (what makes a good teaching example in a convention)

**Evidence threshold:** Convention documents with templates, style guides with examples, project contribution docs.

---

### Q5: Audience & Scope (Who uses conventions and when?)

**Focus:** Making conventions contextually appropriate.

**Questions:**
- Do conventions declare their audience? (Who should follow this: devs, architects, testers, docs writers, all contributors?)
- Do conventions declare their scope? (What's covered, what's explicitly out of scope, when this convention applies)
- How do conventions handle edge cases? (Exception clauses, references to other conventions for special cases, "escape hatches")
- Do conventions have expiry or review dates? (Automatic review triggers, deprecation paths, sunset clauses)

**Expected output:**
- Audience declaration patterns (how projects make clear who conventions apply to)
- Scope definition best practices (positive scope — what's in, negative scope — what's out)
- Edge case handling strategies (how conventions stay useful without becoming exhaustive rule books)
- Lifecycle management examples (how conventions evolve, retire, or get replaced)

**Evidence threshold:** Convention metadata, scope sections, deprecation notices, review processes.

---

### Q6: Lightweight Conventions (Agility-First)

**Focus:** Fast evolution without heavyweight process burden.

**Baseline (SKILL.md):**
- Lightweight by design (thin entry, heavy in supporting files)
- No formal approval process (plugin author owns)
- Iteration encouraged (no version constraints)
- **Works for:** Skills (single-author, plugin-scoped)
- **Gaps for:** Project-wide conventions (multi-role, cross-cutting)

**Questions:**
- How do agile projects handle conventions? (Lean docs, gradual adoption, escape hatches)
- Breaking changes — how to evolve conventions without halting work? (Deprecation paths, backward compat windows)
- Approval timelines — how fast can conventions change? (Compare PEP/RFC heavyweight vs SKILL.md lightweight)

**Expected output:**
- Lightweight convention patterns (compare to heavyweight PEPs/RFCs)
- Breaking change strategies (evolution without disruption)
- Approval speed patterns (fast iteration vs stability trade-offs)

**Evidence threshold:** Agile project docs, startup engineering handbooks, convention evolution examples.

---

### Q7: Convention as Data (Machine-Readable)

**Focus:** Conventions parseable by tools, not just readable by humans.

**Baseline (SKILL.md):**
- ✓ YAML frontmatter (machine-readable metadata)
- ✓ Parseable by Claude Code engine
- **Works for:** Runtime behavior (allowed-tools enforcement, context isolation)
- **Gaps for:** Convention validation, DB storage, cross-convention analysis

**Questions:**
- How do projects make conventions machine-readable? (JSON Schema, YAML validation, structured formats)
- Validation — how to check convention compliance automatically? (Schemas, linters, CI checks)
- Beyond SKILL.md scope — what metadata needed for convention registry? (Status, dependencies, conflicts, ownership)

**Expected output:**
- Machine-readable formats (YAML, JSON Schema, custom DSLs)
- Validation strategies (schemas, linters, automated checks)
- Metadata patterns beyond SKILL.md (convention registry requirements)

**Evidence threshold:** Schema examples, validation tools, convention registries in other projects.

---

### Q8: Ownership & Contribution (Multi-Role)

**Focus:** Who owns conventions, who can contribute, how to collaborate.

**Baseline (SKILL.md):**
- Ownership = plugin author (clear, single-owner)
- Contribution = PR to plugin repo
- **Works for:** Skills (scoped to plugin)
- **Gaps for:** Project-wide conventions (cross-role, shared ownership)

**Questions:**
- Who owns project-wide conventions? (Single role, committee, rotating ownership)
- Cross-role contributions — how do non-owners contribute? (PR, suggestion, review-only)
- Approval process — who approves convention changes? (Owner-only, consensus, majority vote)

**Expected output:**
- Ownership models (single owner vs committee vs distributed)
- Contribution patterns (PR, RFC, suggestion-based)
- Approval processes (owner-only vs consensus vs voting)

**Evidence threshold:** Project governance docs, contribution guides, convention ownership examples.

---

## Search Strategy Hints

### Phase 1 (Official/Established Ecosystems — 50% time)

**High-signal project sources:**
- **Python PEPs:** python.org/dev/peps/ — look for PEP 1 (PEP Purpose and Guidelines), PEP 8 (Style Guide), meta-PEPs
- **Rust RFCs:** rust-lang/rfcs repo — RFC 0001 (meta-RFC), contribution guide, template
- **IETF RFCs:** ietf.org — RFC 2026 (Internet Standards Process), RFC style guide
- **Linux Kernel:** kernel.org/doc/ — coding style, process documentation, submitting patches guide
- **ADR (Architectural Decision Records):** github.com/joelparkerhenderson/architecture-decision-record — templates, examples, meta-discussion
- **ISO/IEEE standards:** Look for meta-standards (how to write standards) if accessible
- **W3C specs:** w3.org/standards — process documents, spec writing guidelines

**What to look for:**
- Meta-documents (convention about conventions, process documents, style guide guides)
- Templates and examples (official templates for new conventions)
- Enforcement tooling (linters, CI checks, review checklists referenced in docs)

---

### Phase 2 (Community/Experimental Ecosystems — 50% time)

**Context switch:** Now looking for how teams build convention systems, not just follow established ones.

**Community sources:**
- **GitHub:** Search for:
  - `"meta convention" OR "convention template" OR "style guide template"`
  - `"ADR template" OR "RFC template" OR "design doc template"`
  - `awesome-* lists` for documentation, architecture, style guides
  - Company engineering handbooks (Airbnb, Google, Uber style guides — meta-sections)
- **Blog posts & case studies:**
  - "How we built our documentation system"
  - "Engineering handbook at [Company]"
  - "Scaling code review with conventions"
- **Reddit / HackerNews:**
  - r/ExperiencedDevs, r/softwarearchitecture
  - "Ask HN: How do you enforce coding standards?"
  - Discussions on convention fatigue, convention compliance
- **Academic:**
  - Papers on "software conventions", "coding standard adoption", "documentation practices"

**What to look for:**
- Convention systems (how companies manage multiple conventions)
- Real-world enforcement stories (what works, what fails)
- Anti-patterns and lessons learned (convention overhead, compliance resistance)
- Tooling experiments (automated convention checking, custom linters)

---

### Explicit searches (ensure these are covered)

- **Python PEP 1** — meta-PEP about PEPs
- **Rust RFC 0001** — meta-RFC about RFCs
- **IETF RFC 2026** — Internet Standards Process
- **Linux Kernel coding style** + submitting patches guide
- **ADR templates** (Joel Parker Henderson repo, others)
- **"Engineering handbook" OR "engineering standards" site:github.com**
- **Semantic versioning spec** (as example of well-structured convention)
- **Google Style Guides** (Python, C++, etc.) — structure and enforcement patterns
- **Airbnb style guides** (JavaScript, Ruby, etc.) — community adoption signals

---

## Output Contract

**Lokalizacja wyników:**
```
documents/architect/research_results_meta_convention.md
```

**CRITICAL:** Write results to the path above. Architect will read results from there.

---

**Struktura wyników (MUST FOLLOW):**

```markdown
# Research Results: META_CONVENTION

**Date:** YYYY-MM-DD
**Researcher:** [Agent ID or "External Agent"]

---

## TL;DR (3-5 Key Findings)

1. [Most important discovery — headline + 1 sentence context]
2. [Second discovery]
3. [Third discovery]
4. [Fourth discovery — optional]
5. [Fifth discovery — optional]

**Baseline Context:** SKILL.md pattern (YAML frontmatter + markdown body) provides foundation. External research fills gaps (versioning, enforcement, ownership).

---

## Question 1: Meta-Conventions

### Findings
[Report what you found: projects with meta-conventions, common sections, format patterns, ownership models]

### Comparison to SKILL.md
**SKILL.md does:** [What SKILL.md already provides]
**External practices do:** [What other projects add beyond SKILL.md]
**Recommendation for META_CONVENTION:** [What to adopt from external practices]

### Evidence Strength
**[Strong | Moderate | Exploratory]** — [justify: why this rating?]

### Sources
- [Source 1 with URL]
- [Source 2 with URL]
- [...]

---

## Question 2: Convention Structure

### Findings
[Report: structure patterns, versioning strategies, changelog formats, dependency declaration]

### Comparison to SKILL.md
**SKILL.md has:** YAML frontmatter (name, description, flags) + markdown body, NO versioning, NO changelog
**External practices add:** [What versioning/changelog/dependency patterns exist]
**Recommendation for META_CONVENTION:** [What to add to SKILL.md baseline]

### Evidence Strength
**[Strong | Moderate | Exploratory]**

### Sources
- [...]

---

## Question 3: Enforcement

### Findings
[Report: enforcement strategies, review checklists, violation handling, compliance tracking]

### Evidence Strength
**[Strong | Moderate | Exploratory]**

### Sources
- [...]

---

## Question 4: Template & Anti-patterns

### Findings
[Report: template formats, anti-pattern docs, presentation styles, example quality]

### Evidence Strength
**[Strong | Moderate | Exploratory]**

### Sources
- [...]

---

## Question 5: Audience & Scope

### Findings
[Report: audience declaration, scope definition, edge case handling, lifecycle management]

### Evidence Strength
**[Strong | Moderate | Exploratory]**

### Sources
- [...]

---

## Open Questions

1. [What couldn't be answered with available evidence?]
2. [What needs deeper investigation?]
3. [What patterns appeared but couldn't be verified?]
4. [What would require interviewing project maintainers?]

---

## Sources (Consolidated)

[Full list of all sources consulted, grouped by category if helpful]

**Official/Established Projects:**
- [Python PEPs: link]
- [Rust RFCs: link]
- [...]

**Community/Experimental:**
- [GitHub repos: links]
- [Blog posts: links]
- [...]
```

---

## Critical Reminders

1. **SKILL.md baseline first:** Every finding should compare to SKILL.md pattern. Format: "SKILL.md does X, external does Y, gap/supplement: Z"

2. **50/50 discipline:** Equal time on Phase 1 (established projects) and Phase 2 (community experiments). Don't overweight official sources.

3. **No Mrowisko evaluation:** Report what exists. Do NOT analyze "would this work for Mrowisko?" That's Architect's job after research.

4. **Evidence strength labels:** Mark every finding as strong/moderate/exploratory. Helps Architect weigh evidence during decision-making.

5. **Explicit "not found":** If you search for specific project (e.g., "ISO meta-standard") but don't find it → report "searched for X, not found." Don't skip silently.

6. **Trade-offs visible:** When projects make different choices (e.g., semantic versioning vs date-based), report both + pros/cons if documented.

7. **Anti-patterns matter:** If projects explicitly warn against certain convention patterns, that's high-value signal. Report prominently.

8. **Lightweight bias:** When comparing heavyweight (PEPs, RFCs) vs lightweight (SKILL.md, agile practices), note agility trade-offs prominently.

---

## Timeline Context

**Target:** 1-2 days for research execution (by external agent or claude-code-guide agent)

**Next steps (after research):**
1. Architect reads results
2. Architect drafts META_CONVENTION (applies findings to Mrowisko context)
3. Prompt Engineer reviews META_CONVENTION (parseable? clear?)
4. Convention Registry implementation begins

**This research is foundational** — quality here determines quality of all future conventions in Mrowisko.

---

## Success Criteria

Research is successful if Architect can answer:
- "What to add to SKILL.md pattern for general conventions?" (from all questions)
- "How should we version conventions?" (Q2 — SKILL.md lacks this)
- "How to enforce conventions beyond allowed-tools?" (Q3 — SKILL.md gap)
- "What template for new conventions?" (Q4 — building on SKILL.md)
- "How to handle multi-role ownership?" (Q8 — SKILL.md is single-owner)
- "How to stay lightweight while adding structure?" (Q6 — agility vs completeness)

**Key deliverable:** Comparison table (SKILL.md vs external practices → recommendation for META_CONVENTION)

If research provides strong/moderate evidence for these questions → mission accomplished.

---

**End of research prompt. External agent can now execute based on EXPLORATORY_BASE_PROMPT.md + this specific prompt.**
