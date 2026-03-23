# Research Prompt: Claude Code — Extensions, Patterns & Practices

**Agent type:** claude-code-guide
**Thoroughness:** very thorough
**Character:** Eksploracyjny — priorytet: szerokość, nie głębokość dowodów

---

## Mission

Map the landscape of Claude Code capabilities, extensions, and community practices. Show what's possible — not what's proven. We want to see options we don't know exist.

Accept weak evidence: GitHub issues, Reddit threads, Discord mentions, blog posts, experimental repos. If it's been tried, report it.

---

## Research Questions

### Q1: Core features — beyond obvious
What built-in Claude Code features exist beyond basic file editing?
- Hooks system (types, triggers, example use cases)
- Slash commands (custom skills, built-in utilities)
- Memory system (structure, persistence, best practices)
- Settings & configuration (non-obvious flags, power-user options)
- Integration modes (IDE extensions, CLI features, remote sessions)

**Evidence threshold:** Official docs, GitHub repo mentions, confirmed user reports.

---

### Q2: MCP Servers — catalog & use cases
What MCP servers exist and what capabilities do they enable?
- Official Anthropic servers
- Community-maintained servers
- Domain-specific servers (databases, APIs, dev tools, file systems, web search)
- Experimental/niche servers worth knowing about

For each category: name, capability, signal of adoption (stars, mentions, maintenance status).

**Evidence threshold:** Public repos, MCP directory if exists, user testimonials.

---

### Q3: Custom skills — patterns & examples
How do teams build custom skills for Claude Code?
- Skill structure (files, metadata, conventions)
- Common skill types (commit helpers, test runners, code reviewers, project scaffolders)
- Skill composition (calling other skills, chaining workflows)
- Where people share skills (repos, gists, templates)

**Evidence threshold:** Code examples, how-to posts, skill repos.

---

### Q4: Advanced workflows — multi-agent, automation, CI/CD
What do power users do with Claude Code beyond single-session coding?
- Multi-agent setups (role separation, handoffs, message buses)
- Autonomous task loops (background agents, retries, error recovery)
- Integration with CI/CD (pre-commit hooks, test automation, PR bots)
- Scripting & orchestration (calling Claude Code programmatically)

**Evidence threshold:** Blog posts, project case studies, experimental repos, Discord/Reddit threads.

---

### Q5: Extensions & integrations — IDE, terminal, external tools
What extends Claude Code in editors, terminals, and external systems?
- VS Code extensions (if any)
- Vim/Neovai/Emacs modes
- Terminal enhancers (prompt styling, output parsing)
- Integration with project management tools (Linear, Jira, Notion)
- Integration with observability/logging (session replay, analytics)

**Evidence threshold:** Extension marketplaces, GitHub repos, setup guides.

---

### Q6: Anti-patterns & footguns — what breaks, what's hard
What do users struggle with or report as limitations?
- Common misconfigurations
- Performance bottlenecks (large repos, slow tools, context limits)
- Hook/skill bugs or edge cases
- Unmet needs (feature requests, workarounds)

**Evidence threshold:** GitHub issues, Reddit complaints, Discord help threads.

---

## Output Contract

**Deliverable:** `documents/prompt_engineer/research_results_claude_code_extensions.md`

**Structure:**

```markdown
# Research Results: Claude Code Extensions & Practices

## TL;DR — 3-5 High-Signal Directions
- [Short headline 1: capability/pattern/opportunity]
- [Short headline 2: ...]
- [...]

---

## Q1: Core Features — Beyond Obvious
[Findings structured as bullet list. For each feature: name, capability, example, evidence source.]

**Evidence strength:** [strong | moderate | exploratory]

---

## Q2: MCP Servers — Catalog & Use Cases
[Grouped by category. For each server: name, capability, adoption signal, link.]

**Evidence strength:** [...]

---

[Repeat for Q3-Q6]

---

## Open Questions
- [What couldn't be answered with available evidence?]
- [What needs deeper investigation?]
- [What might exist but wasn't found?]

---

## Sources
[List all sources: docs, repos, threads, posts. Include URLs.]
```

**Do NOT:**
- Evaluate fit for Mrowisko project (no "this would work for..." commentary)
- Rank or recommend (no "best practice" or "we should use X")
- Filter by maturity (report experimental stuff too)

**DO:**
- Cast a wide net (search GitHub, Reddit, Discord, blogs, official docs, MCP registries)
- Include version/date context where relevant (features change fast)
- Note when evidence is thin ("mentioned in 1 Discord thread, unverified")
- Prioritize breadth over depth

---

## Search Strategy Hints

- GitHub: `repo:anthropics/claude-code` + issues, discussions, wiki
- Reddit: r/ClaudeAI, r/Anthropic
- Discord: Claude/Anthropic servers (if you have access via web search proxies)
- Blogs: Dev.to, Medium, personal tech blogs mentioning "Claude Code"
- MCP: Search for "Model Context Protocol" servers, registries, awesome-lists
- Official docs: Check claude.ai docs, Anthropic API docs for Claude Code sections

---

**Time cap:** Thorough search, but if a question yields <3 sources after 15 min → mark as "low signal" and move on. We value coverage over perfection.
