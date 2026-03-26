# Research Results: META_CONVENTION

**Date:** 2026-03-24  
**Researcher:** GPT-5.4 Thinking

---

## TL;DR (5 Key Findings)

1. Successful convention systems almost always split **metadata/process** from **explanatory body content**. PEPs, RFCs, ADRs, and standards processes all use structured headers or templates plus a narrative body. SKILL.md already has this core shape; the main external additions are status, ownership, dependencies, and lifecycle metadata.
2. Mature ecosystems prefer **status-based lifecycle control** over pure document versioning for individual conventions. PEPs, Rust/Electron/Amundsen RFCs, ADRs, and W3C/IETF process documents all emphasize statuses like Draft, Active, Accepted, Rejected, Deprecated, or Superseded.
3. Enforcement is rarely “document-only.” Proven projects combine **human review + automation + exception handling**: linters/formatters/checkers, CI or pre-submit checks, and reviewer or maintainer judgment. SKILL.md’s `allowed-tools` is narrower than these broader enforcement systems.
4. The best teaching-oriented convention templates consistently include **motivation/context, examples, alternatives, drawbacks, and migration or consequences**. Anti-patterns are usually taught via explicit bad/good examples and rationale, not by rules alone.
5. Lightweight systems stay lightweight by keeping the entry document thin, using templates, allowing staged adoption, and reserving heavyweight review only for substantial changes. Amaranth explicitly simplified Rust’s RFC process for a smaller community; Conventional Commits and MADR show how far machine-readability and automation can go with very small documents.

**Baseline Context:** SKILL.md pattern (YAML frontmatter + markdown body) provides foundation. External research fills gaps (status/lifecycle, versioning, changeloging, ownership, dependencies, supersession, review, validation, and conflict handling).

---

## Comparison Snapshot: SKILL.md vs External Practice

- **SKILL.md already has:** machine-readable header, human-readable body, lightweight entrypoint, behavior control.
- **External practice commonly adds:** document status, author/owner/approver fields, dependency links, changelog or release notes, supersedes/superseded-by links, review/approval workflow, validation tooling, examples/anti-examples, and explicit audience/scope.
- **Common pattern across proven systems:** small structured metadata block + standardized body sections + external validation/review + lifecycle states.

---

## Question 1: Meta-Conventions

### Findings

Meta-conventions are common in successful ecosystems.

- **Python PEPs** have an explicit meta-convention. PEP 1 defines what a PEP is, who it is for, what types exist, and how the workflow operates. It explicitly treats meta-PEPs as Process PEPs.
- **Rust RFCs** have an explicit meta-convention. RFC 0002 defines when the RFC process is required, what “substantial” means, and how an RFC moves from proposal to active.
- **IETF / RFC Series** separates process from editorial convention. RFC 2026 defines the standards process; RFC 7322 and the RFC Editor style guide define structure, style, editorial philosophy, dispute handling, and update paths.
- **W3C** likewise separates process rules from style guidance. The W3C Process Document is the operative governance/process layer, while the Manual of Style is a companion best-practice guide for editors.
- **ADR ecosystems** function as lighter-weight meta-convention systems. Michael Nygard ADRs, the ADR GitHub organization, and MADR all provide canonical templates, naming guidance, statuses, and examples.
- **ISO/IEC** has drafting directives and official templates, which indicates that formal standards bodies also use explicit meta-conventions for document structure and drafting. Publicly accessible evidence was stronger on templates and high-level drafting guidance than on detailed ownership/process internals.

Common structural elements across these meta-conventions:

- structured metadata/header;
- required body sections (summary/abstract, motivation/context, specification/decision, consequences/drawbacks);
- explicit lifecycle or status markers;
- references/dependencies/supersession links;
- named editorial or approval roles;
- template-backed authoring.

Ownership models vary:

- **Python:** authors + optional sponsor + PEP-Delegate + PEP editors + Steering Council.
- **Rust:** author + relevant sub-team assignee/reviewers; significant changes require sub-team handling and final comment period.
- **IETF/W3C:** editors/authors work within formal approval bodies.
- **ADR/MADR:** usually team- or repo-owned, often without heavy central governance.
- **Smaller RFC systems (Amundsen, Amaranth):** maintainer, subsystem maintainer, or RFC champion ownership is explicit.

### Comparison to SKILL.md

**SKILL.md does:** provide structured metadata and a markdown body in a compact format.

**External practices do:** add explicit governance/process around the document itself: who writes it, who reviews it, who approves it, what status it is in, and how it evolves or is superseded.

**Recommendation for META_CONVENTION:** keep SKILL.md’s frontmatter+body pattern, but add explicit meta-fields for lifecycle, ownership, and relationships between conventions.

### Evidence Strength

**Strong** — multiple official process documents from Python, Rust, IETF, W3C, plus widely used ADR templates, converge on the same broad pattern.

### Sources

- Python PEP 1 — https://peps.python.org/pep-0001/
- Python PEP 12 — https://peps.python.org/pep-0012/
- Rust RFC 0002 — https://rust-lang.github.io/rfcs/0002-rfc-process.html
- Rust RFC repository README — https://github.com/rust-lang/rfcs
- RFC 2026 — https://datatracker.ietf.org/doc/html/rfc2026
- RFC 7322 — https://www.rfc-editor.org/rfc/rfc7322.html
- RFC Editor Style Guide site — https://www.rfc-editor.org/styleguide/
- W3C Process Document — https://www.w3.org/policies/process/
- W3C Manual of Style — https://www.w3.org/guide/manual-of-style/
- ADR repository — https://github.com/joelparkerhenderson/architecture-decision-record
- MADR — https://adr.github.io/madr/
- ISO Templates — https://www.iso.org/iso-templates.html
- ISO/IEC Directives, Part 2 (located) — https://www.iso.org/sites/directives/current/part2/index.xhtml

---

## Question 2: Convention Structure

### Findings

### 1) Structure is usually standardized more than prose style alone

Across PEPs, RFCs, and ADRs, structure is not left to author preference. Templates define both metadata and required narrative sections.

Common body sections across systems:

- **Abstract/Summary**
- **Motivation / Context / Problem statement**
- **Specification / Decision / Reference-level details**
- **Rationale / Alternatives / Prior art**
- **Drawbacks / Consequences**
- **Examples / Guide-level explanation**
- **Backwards compatibility / Migration / Future possibilities / Unresolved questions**
- **References / More information**

### 2) Lifecycle status is more common than semantic document versioning

For individual convention documents, the most common control mechanism is not SemVer but status:

- **PEPs:** Draft, Active, Accepted, Provisional, Deferred, Rejected, Withdrawn, Final, Superseded.
- **ADRs:** proposed, accepted, rejected, deprecated, superseded.
- **RFC-style systems:** Proposed/Pending/Active/Landed/Rejected or similar.

This suggests a distinction between:

- **document lifecycle status** for a single convention entry, and
- **versioning of the convention system/template itself** (where SemVer is more common, e.g. MADR, Conventional Commits, SemVer spec itself).

### 3) Dependencies and supersession are common, explicit, and valuable

- PEPs support `Requires`, `Replaces`, and `Superseded-By`.
- ADR tools and ADR practice support “supersede” relationships between decision records.
- RFC ecosystems often encode related issues, PRs, or reference implementations in the header.

This is one of the clearest gaps versus SKILL.md.

### 4) Changeloging appears in two places

Two patterns recur:

- **embedded history fields** inside the convention document (e.g. PEP `Post-History`, discussion/resolution links);
- **project-level changelog files** for the convention template/system itself (e.g. MADR follows SemVer and Keep a Changelog).

For changelogs, strong recurring principles are:

- entries per version/release,
- chronological order,
- release date,
- grouped categories,
- linkable versions,
- human-readable summaries.

### 5) Metadata often grows when conventions become machine-queried

Examples:

- PEPs expose JSON metadata via the PEPs API.
- IETF uses RFCXML plus Relax NG schemas.
- MADR supports YAML front matter for status/date/decision-makers.

### Comparison to SKILL.md

**SKILL.md has:** YAML frontmatter (`name`, `description`, control flags) + markdown body, NO explicit status/version/dependency/change history model.

**External practices add:**

- status/lifecycle fields;
- authorship/ownership metadata;
- dependency and supersession links;
- richer required body sections;
- changelog or change-history conventions;
- references to implementations/issues/discussions.

**Recommendation for META_CONVENTION:** keep the frontmatter+body structure, but extend the frontmatter with status, owner(s), dependencies, supersedes/superseded-by, and review metadata; and standardize body sections for context, rule, examples, anti-patterns, and consequences.

### Evidence Strength

**Strong** — official templates and template-backed ecosystems consistently show these patterns.

### Sources

- Python PEP 12 — https://peps.python.org/pep-0012/
- Python PEPs API — https://peps.python.org/api/
- Rust RFC template — https://github.com/rust-lang/rfcs/blob/master/0000-template.md
- Electron RFC template — https://github.com/electron/rfcs/blob/main/0000-template.md
- Michael Nygard ADR template — https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md
- MADR template — https://adr.github.io/madr/decisions/adr-template.html
- MADR repo — https://github.com/adr/madr
- SemVer — https://semver.org/
- Keep a Changelog — https://keepachangelog.com/en/1.1.0/
- Conventional Commits — https://www.conventionalcommits.org/en/v1.0.0/

---

## Question 3: Enforcement

### Findings

### 1) Enforcement is layered

Real projects rarely rely on one mechanism. They use some combination of:

- **templates** to reduce variance before review;
- **linters/formatters/checkers** for mechanical rules;
- **reviewer/maintainer approval** for semantic correctness;
- **gates or staged review periods** for major changes;
- **exception policies** where automation is advisory, not absolute.

### 2) Automation is common for low-level rules

- **Linux kernel**: `checkpatch.pl` is expected before submission; violations can trigger rejection, but the checker is explicitly “a guide, not a replacement for human judgment.” Error/Warning/Check levels make strictness visible.
- **Google style guides**: explicitly require tools such as `pylint`; warnings may be suppressed with explanation.
- **Commit conventions**: Conventional Commits is designed for automation; commitlint exists specifically to enforce commit-message conventions and supports shareable configs.
- **MADR**: uses markdownlint and distributes templates and config files.

### 3) Human review remains decisive for semantic conventions

- **PEPs**: editors check structure/formatting, but acceptance is a governance decision.
- **Rust RFCs**: major proposals go through team assignment and final comment period.
- **Amundsen**: uses RFC champions, maintainer approval, and if needed an explicit vote threshold.
- **IETF/RFC Editor**: editing for readability happens, but semantic disputes escalate through a defined dispute-resolution path.

### 4) Review checklists are often implicit inside templates

Instead of separate checklists, many systems bake the checklist into section requirements:

- Have you explained motivation?
- Have you shown examples?
- Have you documented drawbacks and alternatives?
- Have you handled backwards compatibility and migration?
- Have you named dependencies and stakeholders?

Electron and Rust RFC templates are good examples of “template as checklist.”

### 5) Violation handling is usually pragmatic, not absolutist

Common pattern:

- mechanical violations: fix automatically or block until fixed;
- judgment calls: allow with reviewer justification;
- semantic disagreement: escalate to owner/maintainer/body;
- contradicting or outdated conventions: supersede explicitly rather than silently overwrite.

### 6) Conflict resolution patterns are explicit in mature systems

Observed mechanisms:

- **Governance escalation**: Steering Council (Python), RFC Series Editor / stream-approving body (RFC Editor), maintainers or subsystem maintainers (Amaranth/Amundsen).
- **Supersession links**: `Superseded-By` in PEPs; ADR supersede workflows; status changes on replaced records.
- **Active operative document rule**: W3C explicitly follows the most recent operative Process Document.

### Comparison to SKILL.md

**SKILL.md has:** `allowed-tools`, `disable-model-invocation`, `context`, which constrain runtime behavior of a skill.

**External practices add:** validation of document structure, human approval workflows, staged review, linter/CI enforcement, exception handling, and explicit dispute/supersession rules.

**Recommendation for META_CONVENTION:** extend beyond runtime controls into convention validation, review workflow, and conflict-resolution metadata/process.

### Evidence Strength

**Strong** — enforcement patterns are documented directly in official contribution and process material, with strong convergence on automation for low-level rules and humans for semantic judgment.

### Sources

- Linux kernel submitting patches — https://docs.kernel.org/process/submitting-patches.html
- Linux kernel coding style — https://docs.kernel.org/process/coding-style.html
- Google Python Style Guide — https://google.github.io/styleguide/pyguide.html
- Google Style Guides — https://google.github.io/styleguide/
- Conventional Commits — https://www.conventionalcommits.org/en/v1.0.0/
- commitlint — https://commitlint.js.org/
- commitlint repo — https://github.com/conventional-changelog/commitlint
- Python PEP 1 — https://peps.python.org/pep-0001/
- Rust Forge: proposals and stabilization — https://forge.rust-lang.org/compiler/proposals-and-stabilization.html
- Rust RFC merge procedure — https://forge.rust-lang.org/lang/rfc-merge-procedure.html
- RFC 7322 — https://www.rfc-editor.org/rfc/rfc7322.html
- W3C Process Document — https://www.w3.org/policies/process/
- Amundsen RFCs — https://github.com/amundsen-io/rfcs
- Amaranth RFCs — https://github.com/amaranth-lang/rfcs

---

## Question 4: Template & Anti-patterns

### Findings

### 1) Good convention systems nearly always supply templates

Template patterns observed:

- **full annotated template** (Rust RFC, Electron RFC, MADR, PEP 12);
- **minimal template** (MADR minimal template);
- **bare template** for experienced users (IETF bare RFCXML template; MADR bare templates);
- **multiple templates for different convention types** (Amundsen feature vs deprecation RFC templates).

This is a recurring pattern: mature systems support both learnability and speed by shipping more than one authoring mode.

### 2) The best templates teach by explanation, not just placeholders

Strong templates explain what each section is for, what quality looks like, and what kinds of evidence belong there.

Examples:

- Electron and Rust templates explain what each section should accomplish.
- PEP 12 is explicitly designed to prevent automatic rejection for form errors.
- IETF provides annotated and bare templates plus schemas.

### 3) Anti-patterns are often expressed as bad/good examples with rationale

This is especially strong in coding style guides:

- **Airbnb** repeatedly uses bad/good examples and “Why?” rationale.
- **Linux kernel** uses explicit “Don’t do X” examples.
- **Google** uses rule → pros/cons/decision → suppression guidance.

This teaching style is stronger than bare rules because it explains trade-offs and exceptions.

### 4) Comparative examples make conventions learnable

High-quality example styles observed:

- bad / good / best examples;
- minimal vs expanded examples;
- guide-level vs reference-level explanation;
- concrete migration examples;
- examples of corner cases and unresolved areas.

### 5) Anti-patterns are more actionable when they include three parts

Observed effective structure:

1. anti-pattern or bad example,  
2. why it is problematic,  
3. correct alternative (often with code or document snippet).

### Comparison to SKILL.md

**SKILL.md does:** support a simple reusable shape and encourages thin entry documents.

**External practices do:** provide richer templates, multiple template variants, explicit instructional text, and anti-pattern teaching through examples and rationale.

**Recommendation for META_CONVENTION:** provide at least two templates (annotated + bare/minimal), and make anti-patterns first-class with bad/good examples and rationale.

### Evidence Strength

**Moderate** — evidence is broad and consistent, but much of it comes from templates and style guides rather than single explicit “meta-convention best practice” documents.

### Sources

- Python PEP 12 — https://peps.python.org/pep-0012/
- Rust RFC template — https://github.com/rust-lang/rfcs/blob/master/0000-template.md
- Electron RFC template — https://github.com/electron/rfcs/blob/main/0000-template.md
- IETF templates and schemas — https://authors.ietf.org/templates-and-schemas
- MADR template — https://adr.github.io/madr/decisions/adr-template.html
- MADR repo — https://github.com/adr/madr
- Airbnb JavaScript Style Guide — https://github.com/airbnb/javascript
- Linux kernel coding style — https://docs.kernel.org/process/coding-style.html
- Google Python Style Guide — https://google.github.io/styleguide/pyguide.html
- Amundsen RFCs — https://github.com/amundsen-io/rfcs

---

## Question 5: Audience & Scope

### Findings

### 1) Explicit audience declarations are common in strong systems

- PEP 1 has an explicit “PEP Audience” section.
- National Archives’ handbook explicitly lists its intended audiences.
- Many engineering handbooks describe who they are for (staff, collaborators, external partners, new joiners, etc.).

### 2) Scope is often stated both positively and negatively

Mature systems usually define:

- what the convention/process covers;
- what kinds of changes trigger it;
- what does **not** require it.

Good examples:

- Rust RFC process lists what counts as “substantial” and what does not need an RFC.
- Amaranth explicitly limits RFC scope to named subsystems and says other repos are currently outside the process.
- National Archives handbook says what its guidance is intended to cover.

### 3) Edge cases are handled by exceptions, not exhaustive rulebooks

Common strategies:

- allow suppressions with explanation (Google/pylint);
- allow justified style violations (Linux `checkpatch.pl` guidance);
- defer or supersede unresolved or outdated proposals (PEPs, ADRs);
- separate stable requirements from less formal recommendations (RFC Style Guide + web supplement).

### 4) Lifecycle management is explicit, but hard expiry dates are rare

Common lifecycle tools:

- status transitions;
- superseded/replaces links;
- changelog or history;
- “latest operative document” rule;
- “living document” framing in engineering handbooks.

What was **not strongly found**: widespread mandatory review dates or automatic sunset clauses for conventions. Some systems mention periodic revision, but explicit expiry metadata was uncommon in the evidence gathered.

### Comparison to SKILL.md

**SKILL.md does:** imply scope through naming/description and tool restrictions, but does not usually declare audience, positive scope, negative scope, or lifecycle review rules.

**External practices do:** name the intended audience, define when the convention applies, list exceptions or out-of-scope cases, and mark replacement/deprecation clearly.

**Recommendation for META_CONVENTION:** add explicit audience and scope sections plus lifecycle/supersession handling; treat review dates as optional rather than universal because evidence for them was weaker.

### Evidence Strength

**Moderate** — audience and scope are well-supported; explicit expiry/review-date practices were not strongly supported.

### Sources

- Python PEP 1 — https://peps.python.org/pep-0001/
- Rust RFC 0002 — https://rust-lang.github.io/rfcs/0002-rfc-process.html
- Amaranth RFCs — https://github.com/amaranth-lang/rfcs
- National Archives Engineering Handbook — https://nationalarchives.github.io/engineering-handbook/
- ChainSafe Engineering Handbook — https://github.com/ChainSafe/engineering-handbook
- IPA Data Science, Engineering, and Technology Handbook — https://github.com/PovertyAction/ipa-data-tech-handbook
- RFC 7322 — https://www.rfc-editor.org/rfc/rfc7322.html
- W3C Process Document — https://www.w3.org/policies/process/

---

## Question 6: Lightweight Conventions (Agility-First)

### Findings

### 1) Lightweight systems minimize process for small changes

- Rust explicitly says many changes can go through normal PR flow; only substantial changes require RFCs.
- Amaranth inherits Rust’s shape but explicitly simplifies it for a smaller community.
- Conventional Commits is intentionally lightweight: a tiny syntax, high tool leverage.
- MADR is explicitly streamlined and supports minimal templates.

### 2) Heavyweight and lightweight paths often coexist

Successful systems do not use one process for everything. They tier effort:

- **lightweight path:** PR + linter + code review;
- **heavyweight path:** proposal/RFC/decision record + explicit stakeholder review.

### 3) Breaking-change handling tends to favor transition markers over big-bang replacement

Common patterns:

- `deprecated` / `superseded` statuses;
- migration guidance in guide-level sections;
- follow-up PRs to keep accepted documents in sync;
- changelog entries and semantic version bumps for the template/system itself.

### 4) “Living document” language is common in handbook-style convention systems

Handbooks from National Archives, ChainSafe, and IPA all frame themselves as evolving documents that improve through contribution rather than as frozen standards texts.

### Comparison to SKILL.md

**SKILL.md does:** stay light, permit local ownership, and avoid heavyweight approval.

**External practices do:** keep lightweight paths for ordinary changes, but add a heavier path only for cross-cutting or high-impact conventions. They also formalize deprecation/supersession more than SKILL.md does.

**Recommendation for META_CONVENTION:** preserve a lightweight default path and reserve heavier governance for shared, cross-role, or high-risk conventions.

### Evidence Strength

**Moderate** — strong examples exist, but “agility-first convention systems” are less canonized than standards processes.

### Sources

- Rust RFC 0002 — https://rust-lang.github.io/rfcs/0002-rfc-process.html
- Rust RFC repo README — https://github.com/rust-lang/rfcs
- Amaranth RFCs — https://github.com/amaranth-lang/rfcs
- Conventional Commits — https://www.conventionalcommits.org/en/v1.0.0/
- MADR — https://adr.github.io/madr/
- National Archives Engineering Handbook — https://nationalarchives.github.io/engineering-handbook/
- ChainSafe Engineering Handbook — https://github.com/ChainSafe/engineering-handbook
- IPA Data Science, Engineering, and Technology Handbook — https://github.com/PovertyAction/ipa-data-tech-handbook

---

## Question 7: Convention as Data (Machine-Readable)

### Findings

### 1) Machine-readable convention metadata is a proven pattern

Strong examples:

- **SKILL.md baseline:** YAML frontmatter.
- **PEPs:** structured headers + public JSON API.
- **IETF:** RFCXML templates + schemas for validation.
- **MADR:** YAML front matter for metadata.
- **Conventional Commits:** fixed message grammar designed for tools.

### 2) Validation usually depends on a schema or grammar

Observed validation mechanisms:

- Relax NG schema for RFCXML;
- JSON document shape for PEP metadata publication;
- YAML front matter conventions for ADR tools/docs sites;
- grammar-based linting for Conventional Commits;
- markdownlint / checkpatch / pylint for partial validation of conformance.

### 3) Machine-readable metadata commonly includes more than title and description

Frequently useful fields:

- status,
- authors/owners/decision-makers,
- dates,
- dependencies/requires,
- replaces/superseded-by,
- discussion links,
- implementation/reference links,
- scope/topic/type.

### 4) Human-readable and machine-readable forms are usually combined, not separated

The dominant pattern is not “store rules only as code” or “store rules only as prose.” It is:

- structured metadata for tools,
- narrative markdown/XML/reST for humans,
- external validators/checkers for compliance.

### Comparison to SKILL.md

**SKILL.md does:** establish the right foundational pattern: parseable frontmatter plus prose body.

**External practices do:** widen the metadata vocabulary and back it with schemas, APIs, or linting.

**Recommendation for META_CONVENTION:** extend the SKILL.md frontmatter model rather than replacing it; use explicit fields for lifecycle, ownership, dependencies, conflicts/supersession, and validation hooks.

### Evidence Strength

**Strong** — multiple major ecosystems use structured metadata plus tooling.

### Sources

- Python PEPs API — https://peps.python.org/api/
- Python PEP 12 — https://peps.python.org/pep-0012/
- IETF templates and schemas — https://authors.ietf.org/templates-and-schemas
- RFC Style Guide — https://www.rfc-editor.org/rfc/rfc7322.html
- MADR metadata ADR — https://adr.github.io/madr/decisions/0013-use-yaml-front-matter-for-meta-data.html
- MADR repo — https://github.com/adr/madr
- Conventional Commits — https://www.conventionalcommits.org/en/v1.0.0/
- commitlint — https://commitlint.js.org/

---

## Question 8: Ownership & Contribution (Multi-Role)

### Findings

### 1) Mature systems make ownership explicit

Patterns found:

- **central editorial/governance model**: PEP editors + Steering Council; RFC Editor + stream-approving body; W3C process bodies;
- **subsystem ownership model**: Rust sub-teams, Amaranth subsystem maintainers;
- **champion model**: Amundsen RFC Champion acts as maintainer-side owner;
- **distributed/living-document model**: engineering handbooks with broad contribution permission and lightweight issue/PR-based change proposals.

### 2) Contribution is usually open, approval is not

This is a highly repeated pattern:

- many people can draft, suggest, or PR changes;
- a smaller set of editors/maintainers/approvers decides status transitions.

### 3) Consensus is preferred, but escalation exists

Observed approval styles:

- editor/approver review plus council decision (Python);
- consensus building plus FCP (Rust);
- maintainer approval, then vote if needed (Amundsen);
- subsystem maintainer disposition (Amaranth);
- issue/PR discussion for handbook updates (ChainSafe).

### 4) Explicitly naming non-author roles helps multi-role collaboration

Especially useful roles seen in the wild:

- sponsor,
- delegate/approver,
- editor,
- champion,
- decision-makers,
- consulted,
- informed.

These roles are largely absent from the SKILL.md baseline.

### Comparison to SKILL.md

**SKILL.md does:** fit a single-owner, plugin-scoped model well.

**External practices do:** separate authorship from sponsorship, review, approval, and maintenance, which is important once a convention spans teams or roles.

**Recommendation for META_CONVENTION:** add multi-role metadata and workflow concepts rather than assuming “author = owner = approver.”

### Evidence Strength

**Moderate** — ownership patterns are clear, but they vary significantly by project size and governance maturity.

### Sources

- Python PEP 1 — https://peps.python.org/pep-0001/
- Python PEP 12 — https://peps.python.org/pep-0012/
- Rust RFC repo README — https://github.com/rust-lang/rfcs
- Rust Forge — https://forge.rust-lang.org/compiler/proposals-and-stabilization.html
- Amundsen RFCs — https://github.com/amundsen-io/rfcs
- Amaranth RFCs — https://github.com/amaranth-lang/rfcs
- W3C Process Document — https://www.w3.org/policies/process/
- ChainSafe Engineering Handbook — https://github.com/ChainSafe/engineering-handbook
- MADR metadata ADR — https://adr.github.io/madr/decisions/0013-use-yaml-front-matter-for-meta-data.html

---

## Open Questions

1. **Expiry/review-date practice:** I did not find strong evidence that mainstream convention systems commonly require explicit expiry dates or mandatory review-by dates on each convention document.
2. **Conflict fields vs supersession fields:** Supersession is common; explicit machine-readable `conflicts_with` metadata was much less visible in the surveyed systems.
3. **ISO/IEEE internals:** I located official drafting directives/templates, but public, easily accessible detail on day-to-day ownership/approval patterns for internal drafting conventions was thinner than for PEP/RFC/W3C ecosystems.
4. **Convention debt tracking:** Projects clearly allow exceptions and supersession, but explicit “convention debt” registries or debt accounting systems were not strongly evidenced in the materials surveyed.
5. **Cross-role contribution at large scale:** Smaller and mid-size open-source systems document champion/maintainer/editor roles well; large-company private convention systems likely have richer practice than what public documentation exposes.

---

## Sources (Consolidated)

**Official / Established Projects**

- Python PEP 1 — https://peps.python.org/pep-0001/
- Python PEP 12 — https://peps.python.org/pep-0012/
- Python PEPs API — https://peps.python.org/api/
- Rust RFC 0002 — https://rust-lang.github.io/rfcs/0002-rfc-process.html
- Rust RFC template — https://github.com/rust-lang/rfcs/blob/master/0000-template.md
- Rust RFC repo README — https://github.com/rust-lang/rfcs
- Rust Forge: proposals and stabilization — https://forge.rust-lang.org/compiler/proposals-and-stabilization.html
- Rust Forge: RFC merge procedure — https://forge.rust-lang.org/lang/rfc-merge-procedure.html
- RFC 2026 — https://datatracker.ietf.org/doc/html/rfc2026
- RFC 7322 — https://www.rfc-editor.org/rfc/rfc7322.html
- RFC Editor Style Guide — https://www.rfc-editor.org/styleguide/
- RFC Editor web style guide supplement — https://www.rfc-editor.org/styleguide/part2/
- IETF templates and schemas — https://authors.ietf.org/templates-and-schemas
- W3C Process Document — https://www.w3.org/policies/process/
- W3C Manual of Style — https://www.w3.org/guide/manual-of-style/
- ISO/IEC Directives, Part 2 (located) — https://www.iso.org/sites/directives/current/part2/index.xhtml
- ISO Templates — https://www.iso.org/iso-templates.html
- SemVer — https://semver.org/
- Linux kernel coding style — https://docs.kernel.org/process/coding-style.html
- Linux kernel submitting patches — https://docs.kernel.org/process/submitting-patches.html
- Google Style Guides — https://google.github.io/styleguide/
- Google Python Style Guide — https://google.github.io/styleguide/pyguide.html

**Community / Experimental / Template Ecosystems**

- ADR repository — https://github.com/joelparkerhenderson/architecture-decision-record
- Michael Nygard ADR template — https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md
- ADR GitHub organization — https://adr.github.io/
- MADR — https://adr.github.io/madr/
- MADR template — https://adr.github.io/madr/decisions/adr-template.html
- MADR metadata ADR — https://adr.github.io/madr/decisions/0013-use-yaml-front-matter-for-meta-data.html
- MADR repo — https://github.com/adr/madr
- Conventional Commits — https://www.conventionalcommits.org/en/v1.0.0/
- commitlint — https://commitlint.js.org/
- commitlint repo — https://github.com/conventional-changelog/commitlint
- Airbnb JavaScript Style Guide — https://github.com/airbnb/javascript
- Electron RFC template — https://github.com/electron/rfcs/blob/main/0000-template.md
- Amundsen RFCs — https://github.com/amundsen-io/rfcs
- Amaranth RFCs — https://github.com/amaranth-lang/rfcs
- ChainSafe Engineering Handbook — https://github.com/ChainSafe/engineering-handbook
- National Archives Engineering Handbook — https://nationalarchives.github.io/engineering-handbook/
- IPA Data Science, Engineering, and Technology Handbook — https://github.com/PovertyAction/ipa-data-tech-handbook
- Sourcegraph engineering principles and practices — https://github.com/sourcegraph/handbook/blob/main/content/departments/engineering/dev/process/principles-and-practices.md
- Keep a Changelog — https://keepachangelog.com/en/1.1.0/

---

## Direct Answer to the Core Research Goal

What to add to the **SKILL.md** pattern for general convention use, based on proven external practice:

1. **Lifecycle metadata** — `status`, `created`, `updated`, optional `effective_from`, optional `deprecated_from`.
2. **Ownership metadata** — `author`, `owner`, `approver`, optional `sponsor`, optional `consulted`, optional `informed`.
3. **Relationship metadata** — `requires`, `replaces`, `superseded_by`, optional `related`.
4. **Standard body sections** — Summary, Scope/Audience, Context/Motivation, Rules/Decision, Examples, Anti-patterns, Exceptions, Consequences/Migration, References.
5. **Validation hooks** — schema/linter/checklist references, plus whether exceptions require justification.
6. **Supersession and conflict handling** — explicit replacement path instead of silent edits.
7. **Template variants** — annotated, minimal, and bare.
8. **Change-history strategy** — either embedded change history or separate changelog for the convention system/template.

This is the most consistent supplement to the SKILL.md baseline observed across PEPs, RFCs, ADRs, standards processes, and living engineering handbooks.
