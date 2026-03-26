# Research Results: Claude Code Extensions & Practices

Date: 2026-03-22

Scope note: this pass optimizes for breadth over proof. It includes official docs, vendor docs, Anthropic marketplace pages, GitHub repos/issues, and public community threads. Where evidence is thin, it is marked as such.

## TL;DR — 3-5 High-Signal Directions
- Claude Code has evolved from “CLI that edits files” into an extensible platform: plugins can package skills, agents, hooks, MCP servers, and LSP servers, and Anthropic now runs a public plugin marketplace with visible install counts.
- The MCP ecosystem is already broad and skewing toward hosted OAuth-style remote servers: Notion, Stripe, Sentry, Linear, Slack, Atlassian, Vercel, Chrome DevTools, Firebase, Pinecone, PostHog, Firecrawl, and others appear either in vendor docs or the Anthropic marketplace.
- Custom skills are no longer just ad-hoc slash commands: they have a documented file structure, YAML frontmatter, tool restrictions, forked execution contexts, and plugin distribution paths. Community sharing has expanded into marketplaces, awesome-lists, and large skill/subagent collections.
- Advanced workflows now span subagents, experimental agent teams, background loops, worktrees, remote control, web/cloud sessions, and CI/CD via GitHub Actions and the Agent SDK. Public community threads show users composing multi-agent systems around worktrees and repo boundaries.
- The main footguns cluster around scale and integration overhead: large skill collections can inflate memory, MCP server/tool definitions can consume a lot of context, some hooks are reported as unreliable in edge cases, and non-official editor support still depends heavily on community tooling.

---

## Q1: Core Features — Beyond Obvious

- **Hooks system** — Claude Code supports lifecycle hooks that can run as shell commands, HTTP endpoints, prompt-based hooks, or agent hooks.
  - **Capability:** intercept session and tool lifecycle events, inject context, deny/allow/ask for tool actions, notify on idle/auth prompts, react to failures, and customize worktree creation.
  - **Examples:**
    - `PreToolUse` can allow/deny/ask and even modify tool input before execution.
    - `PostToolUseFailure` can inject extra debugging context after tool failures.
    - `Notification` hooks can react specifically to `permission_prompt` and `idle_prompt`.
    - `WorktreeCreate` can provision a custom directory instead of a normal git worktree.
    - Matchers can target MCP tools with regex such as `mcp__memory__.*`.
  - **Evidence:** official hooks docs (`https://code.claude.com/docs/en/hooks`); Anthropic Plugin Developer Toolkit / hook-development skill in `anthropics/skills`.

- **Slash commands and built-in utilities** — Claude Code exposes a larger built-in command surface than the obvious `/help`-style interactions.
  - **Capability:** inspect context/cost/stats, manage MCP and plugins, access remote control, review diffs, rewind, manage memory, switch effort mode, use vim/voice modes, open IDE bridges, review PR comments, and list tasks.
  - **Examples:** `/mcp`, `/plugin`, `/skills`, `/memory`, `/context`, `/cost`, `/stats`, `/rewind`, `/remote-control`, `/pr-comments`, `/sandbox`, `/statusline`, `/vim`, `/voice`, `/tasks`.
  - **Evidence:** built-in commands reference in Claude Code docs (`https://code.claude.com/docs/en/slash-commands`).

- **Skills system (custom commands re-framed as reusable capability packs)**
  - **Capability:** old `.claude/commands/*.md` commands still work, but the documented path is now skills. Skills can be triggered manually with slash commands or auto-invoked by the model based on their descriptions.
  - **Examples:** deploy, project setup, review, doc work, commit helpers, codegen, plugin/tooling helpers.
  - **Evidence:** official skills docs (`https://code.claude.com/docs/en/skills`); `anthropics/skills` repo (`https://github.com/anthropics/skills`).

- **Memory system with multiple layers**
  - **Capability:** Claude Code starts fresh each session but can carry state via `CLAUDE.md`, auto memory, and scoped rule files.
  - **Examples:**
    - project-level instructions in `CLAUDE.md`
    - auto memory generated from previous work
    - `.claude/rules/` for file-type or scope-specific instructions
    - subagents maintaining their own auto memory
  - **Notable detail:** docs recommend keeping `CLAUDE.md` concise (around 200 lines is suggested rather than enforced).
  - **Evidence:** official memory docs (`https://code.claude.com/docs/en/memory`).

- **Settings/config scopes and power-user controls**
  - **Capability:** settings exist at managed, user, project, and local levels with documented precedence.
  - **Examples of non-obvious options:**
    - managed allow/deny lists for MCP servers and marketplaces
    - per-scope environment variables
    - `outputStyle`
    - `agent` selection to run the main thread as a named subagent
    - deny-rules for sensitive files in permissions config
    - auto-enabling remote control from config
  - **Evidence:** official settings docs (`https://code.claude.com/docs/en/settings`).

- **CLI flags beyond the obvious**
  - **Capability:** Claude Code can be run as an interactive assistant, a headless script target, a remote-control server, or a subagent orchestrator.
  - **Examples of less-obvious flags:** `--add-dir`, `--agent`, `--agents`, `--allowedTools`, `--disallowedTools`, `--append-system-prompt`, `--permission-mode`, `--permission-prompt-tool`, `--output-format`, `--channels`, `--bare`, `--debug`, `--fallback-model`, `--effort`, `--remote-control`, `--dangerously-skip-permissions`.
  - **Notable detail:** `--bare` skips auto-discovery for hooks, skills, plugins, MCP, auto memory, and `CLAUDE.md`, which makes Claude Code behave more like a minimal programmable primitive.
  - **Evidence:** CLI reference (`https://code.claude.com/docs/en/cli-reference`).

- **Integration modes / surfaces**
  - **Capability:** the same engine now spans terminal, VS Code, Cursor, JetBrains, browser, desktop app, Slack, Chrome beta, Remote Control, and cloud-backed web sessions.
  - **Examples:**
    - VS Code: inline diffs, @mentions, plan review, conversation tabs, IDE MCP server.
    - JetBrains: diff review and selection-context sharing.
    - Remote Control: continue a local terminal session from browser or phone.
    - Web/Desktop: cloud sessions, scheduled tasks, parallel sessions, visual diffs.
    - Slack: message `@Claude` and route coding work into a Claude Code session that can return progress and PRs.
  - **Evidence:** official overview, VS Code, JetBrains, Remote Control, Web/Desktop, and Slack docs.

- **Subagents and experimental agent teams**
  - **Capability:** Claude Code can delegate to subagents with their own prompts, tool access, and permissions; newer experimental “agent teams” add multiple peer Claude Code sessions with a team lead and direct teammate-to-teammate communication.
  - **Examples:** built-in Explore / Plan style roles, team research, parallel debugging, cross-layer refactors.
  - **Evidence:** official sub-agents docs (`https://code.claude.com/docs/en/sub-agents`) and agent teams docs (`https://code.claude.com/docs/en/agent-teams`).

**Evidence strength:** **strong** for hooks, memory, settings, CLI, and official surfaces; **moderate** for day-to-day usage patterns of those features.

---

## Q2: MCP Servers — Catalog & Use Cases

Note: the Claude Code ecosystem often packages MCP servers inside **plugins**, alongside skills/hooks/LSP helpers. So “server” and “plugin” frequently blur together in practice.

### A. Anthropic / official infrastructure around MCP

- **Claude Code built-in IDE MCP server**
  - **Capability:** bridges editor context into Claude Code inside official IDE integrations.
  - **Adoption signal:** bundled in official VS Code integration; no separate public install count surfaced.
  - **Link:** `https://code.claude.com/docs/en/ide-integrations`

- **Claude Code as an MCP server**
  - **Capability:** official docs expose a “Use Claude Code as an MCP server” path, implying Claude Code itself can be mounted as a capability provider.
  - **Adoption signal:** official documentation surface exists, but public third-party usage examples were sparse in this pass.
  - **Link:** `https://code.claude.com/docs/en/mcp`
  - **Signal quality:** low signal on real-world adoption.

- **GitHub MCP Registry**
  - **Capability:** discovery layer for MCP packages/servers.
  - **Adoption signal:** official registry surface on GitHub; useful more as an index than a server itself.
  - **Link:** `https://github.com/mcp`

- **`modelcontextprotocol/servers` reference repo**
  - **Capability:** example/reference implementations for common servers.
  - **Adoption signal:** very high GitHub visibility (81k+ stars at time of search), but the repo explicitly frames itself as reference/educational rather than production-ready.
  - **Link:** `https://github.com/modelcontextprotocol/servers`

### B. Vendor-operated / official remote MCP servers

- **Notion MCP**
  - **Capability:** access Notion content via remote OAuth MCP; Notion also documents a richer Claude Code plugin bundling the server with prebuilt skills/slash commands.
  - **Adoption signal:** first-party docs and dedicated Claude Code instructions.
  - **Link:** `https://developers.notion.com/guides/mcp/get-started-with-mcp`

- **Stripe MCP**
  - **Capability:** hosted remote MCP at `https://mcp.stripe.com`; local `@stripe/mcp` also exists.
  - **Use cases:** account/product/billing operations through OAuth or restricted keys.
  - **Adoption signal:** first-party docs and GitHub MCP registry entry.
  - **Links:** `https://docs.stripe.com/mcp`, `https://github.com/mcp/com.stripe/mcp`

- **Sentry MCP**
  - **Capability:** query issues, errors, projects, and Seer analysis directly from coding assistants.
  - **Use cases:** debugging production issues from inside Claude Code.
  - **Adoption signal:** first-party docs say production release, but also explicitly warn that MCP itself is still evolving and bugs should be expected.
  - **Link:** `https://docs.sentry.io/ai/mcp/`

- **Linear MCP**
  - **Capability:** find/create/update issues, projects, and comments through a remote authenticated server.
  - **Use cases:** project management workflows from Claude Code.
  - **Adoption signal:** first-party docs with direct Claude Code setup path.
  - **Link:** `https://linear.app/docs/mcp`

### C. High-signal marketplace integrations (many are plugin bundles with MCP inside)

Marketplace install counts below are snapshots from Anthropic’s marketplace page on 2026-03-22.

- **Figma** — design-file access, component extraction, token reading, design-to-code bridge.
  - **Adoption signal:** 69,853 installs.
  - **Link:** `https://claude.com/plugins`

- **Serena** — semantic code analysis and navigation via language-server style semantics.
  - **Adoption signal:** 61,435 installs.
  - **Link:** `https://claude.com/plugins`

- **PR Review Toolkit** — review-oriented agents and automation.
  - **Adoption signal:** 58,610 installs; Anthropic verified.
  - **Link:** `https://claude.com/plugins`

- **Atlassian** — Jira and Confluence access.
  - **Adoption signal:** 42,011 installs.
  - **Link:** `https://claude.com/plugins`

- **Slack official MCP server** — workspace data and messaging workflows.
  - **Adoption signal:** 29,652 installs.
  - **Link:** `https://claude.com/plugins`

- **Vercel** — deployment and platform workflows.
  - **Adoption signal:** 27,277 installs.
  - **Link:** `https://claude.com/plugins`

- **Linear** — issue/project workflows.
  - **Adoption signal:** 24,310 installs in marketplace, plus separate first-party Linear docs.
  - **Link:** `https://claude.com/plugins`

- **Sentry** — debugging and error triage.
  - **Adoption signal:** 19,427 installs.
  - **Link:** `https://claude.com/plugins`

- **GitLab** — GitLab workflows from Claude Code.
  - **Adoption signal:** 18,529 installs.
  - **Link:** `https://claude.com/plugins`

- **Stripe** — payment/platform workflows.
  - **Adoption signal:** 18,406 installs.
  - **Link:** `https://claude.com/plugins`

- **Firebase** — app/backend workflows.
  - **Adoption signal:** 13,185 installs.
  - **Link:** `https://claude.com/plugins`

- **Firecrawl** — web crawl/search style workflows.
  - **Adoption signal:** 11,363 installs.
  - **Link:** `https://claude.com/plugins`

- **Pinecone** — vector database workflows.
  - **Adoption signal:** 5,587 installs.
  - **Link:** `https://claude.com/plugins`

- **PostHog** — product analytics / observability workflows.
  - **Adoption signal:** 5,586 installs.
  - **Link:** `https://claude.com/plugins`

- **Chrome DevTools** — live browser debugging.
  - **Adoption signal:** 5,326 installs.
  - **Link:** `https://claude.com/plugins`

- **Postman** — API workflow integration.
  - **Adoption signal:** 2,924 installs.
  - **Link:** `https://claude.com/plugins`

- **Sourcegraph** — code search / code intelligence workflow.
  - **Adoption signal:** 987 installs.
  - **Link:** `https://claude.com/plugins`

- **PagerDuty Pre-Commit Risk Score** — narrow DevOps/risk workflow example.
  - **Adoption signal:** 816 installs.
  - **Link:** `https://claude.com/plugins`

### D. Domain-specific / niche examples

- **Life sciences plugin marketplace**
  - **Capability:** Anthropic has a dedicated marketplace page for life sciences plugins with domain-specific servers/skills (examples surfaced in search included PubMed, BioRender, Synapse-related tooling).
  - **Adoption signal:** official Anthropic marketplace presence.
  - **Link:** `https://www.anthropic.com/claude-code-life-sciences-marketplace`
  - **Signal quality:** exploratory in this pass; individual server maturity was not deeply audited.

### E. Churn and ecosystem notes worth knowing

- Several MCP capabilities are in motion rather than settled:
  - Anthropic docs now recommend **HTTP** transport and note **SSE is deprecated**.
  - Some reference-repo servers have moved or been archived over time (for example, public search surfaced Slack and Postgres changes in `modelcontextprotocol/servers`).
  - Some servers expose real production value, but safety/isolation issues still appear in issue trackers.

**Evidence strength:** **moderate** overall. Strong for vendor-documented servers and marketplace visibility; exploratory for long-tail community servers and true production adoption.

---

## Q3: Custom Skills — Patterns & Examples

- **Documented skill structure**
  - **Structure:** a skill is a directory with `SKILL.md`; optional supporting files can include scripts, references, examples, or templates.
  - **Conventions:** `SKILL.md` carries the behavior; docs suggest keeping it relatively small and pushing large helper assets into side files.
  - **Evidence:** official skills docs (`https://code.claude.com/docs/en/skills`).

- **YAML frontmatter makes skills programmable**
  - **Common fields:** `name`, `description`, `disable-model-invocation`, `allowed-tools`, `context`.
  - **Useful patterns:**
    - `disable-model-invocation: true` turns a skill into an explicitly-invoked slash command.
    - `allowed-tools` limits the skill’s execution surface.
    - `context: fork` runs the skill in an isolated subagent rather than inline.
  - **Evidence:** official skills docs.

- **Where skills live / who can use them**
  - **Scopes:** personal (`~/.claude/skills`), project (`.claude/skills`), plugin-bundled skills, and enterprise/managed skills.
  - **Non-obvious detail:** old `.claude/commands` compatibility still exists, but skills take precedence when names conflict.
  - **Evidence:** official skills docs.

- **Common skill types observed in official docs and public repos**
  - **Project setup / automation:** setup analyzers, repo bootstrap, environment prep.
  - **Commit and review helpers:** commit-message generation, PR review, review comments.
  - **Test/build runners:** run suites, format, lint, and verify outputs.
  - **Code reviewers / architectural explainers:** review code against local conventions or output explanatory commentary.
  - **Scaffolders / doc writers:** generate endpoints, templates, docs, release notes.
  - **Evidence:** official `anthropics/skills`; Anthropic marketplace entries such as Claude Code Setup, PR Review Toolkit, Explanatory Output Style, Plugin Developer Toolkit.

- **Composition and chaining patterns**
  - **Observed pattern:** a skill can act as a reusable prompt capsule, then fork into a subagent, which can itself call tools under restricted permissions.
  - **Observed mechanism:** official docs show `context: fork`; skills can also be installed via plugins, which means skills, hooks, subagents, and MCP can travel together as one package.
  - **Emerging pattern:** community plugin/skill packs increasingly bundle “meta-skills” for building more skills.
  - **Evidence:** official skills docs; `anthropics/skills` skill-creator; `jlaswell/claude-community-marketplace` skill-builder plugin.

- **Where people share skills**
  - **Official:** `anthropics/skills`.
  - **Curated community lists:** `hesreallyhim/awesome-claude-code`, `ComposioHQ/awesome-claude-skills`, `travisvn/awesome-claude-skills`, `VoltAgent/awesome-agent-skills`.
  - **Community marketplaces:** `jlaswell/claude-community-marketplace`, `ananddtyagi/cc-marketplace`, `jimmc414/claude-code-plugin-marketplace`, plus newer meta-lists such as `Chat2AnyLLM/awesome-claude-plugins`.
  - **Signal note:** community counts are noisy, but discovery layers are multiplying fast.

- **Subagent collections are starting to look like a parallel ecosystem to skills**
  - **Example:** `VoltAgent/awesome-claude-code-subagents` describes 100+ specialized subagents, installable manually or as Claude Code plugins.
  - **Use cases:** language specialists, infra/devops agents, orchestration/meta agents, role-specific engineering agents.
  - **Evidence:** GitHub repo + install instructions.

**Evidence strength:** **moderate**. Official structure is strong; the ecosystem and composition patterns are partly exploratory because many examples come from community repos/marketplaces.

---

## Q4: Advanced Workflows — Multi-Agent, Automation, CI/CD

- **Subagents as lightweight role separation**
  - **Capability:** specialized assistants with custom prompts, scoped tools, and independent permissions.
  - **Observed roles:** code reviewer, debugger, data-oriented analyst, database query validator, Explore-style search agent, Plan-style planner.
  - **Evidence:** official sub-agents docs.

- **Agent teams as heavier multi-session orchestration**
  - **Capability:** one lead Claude Code session coordinates multiple teammate sessions; teammates have separate context windows and can communicate directly with one another.
  - **Version context:** agent teams require Claude Code v2.1.32+ and are explicitly presented as experimental.
  - **Use cases named by Anthropic:** research/review, parallel feature ownership, competing debugging hypotheses, cross-layer changes.
  - **Evidence:** official agent teams docs.

- **Parallel worktree workflows**
  - **Capability:** Claude Code’s ecosystem is explicitly worktree-aware.
  - **Examples:**
    - hooks include `WorktreeCreate`/`WorktreeRemove`
    - `/batch` reportedly decomposes large codebase changes into multiple isolated work units with background agents and worktrees
    - desktop/web experiences emphasize multiple parallel sessions
  - **Evidence:** official hooks docs; official workflow docs; community multi-agent threads.

- **Autonomous / recurring loops**
  - **Capability:** `/loop` runs recurring prompts inside a session; desktop and web surfaces add longer-lived scheduled or cloud-backed tasks; channels can push events into live sessions instead of polling.
  - **Version context:** Channels are documented as a research preview and require specific auth/admin conditions.
  - **Evidence:** official channels docs, overview, desktop/web docs.

- **Remote and cross-surface handoff workflows**
  - **Capability:** a task can start in terminal, move to browser/mobile/desktop, and come back.
  - **Examples:** Remote Control, `/teleport`, browser/mobile continuation, cloud sessions, Slack → Claude Code → PR flows.
  - **Evidence:** official overview, Remote Control, web, and Slack docs.

- **CI/CD integration**
  - **Capability:** Claude Code can run inside GitHub Actions and GitLab CI/CD, or be used through the Agent SDK and headless CLI.
  - **Examples:** PR review, issue triage, implementation from issue/PR comments, custom automations.
  - **Evidence:** official GitHub Actions docs; `anthropics/claude-code-action` repo.

- **Programmatic orchestration / scripting**
  - **Capability:** `claude -p` exposes the same agent loop/tooling model in non-interactive form; Anthropic also documents the Agent SDK in CLI, Python, and TypeScript.
  - **Use cases:** scripts, CI jobs, wrappers, custom orchestrators, external task runners.
  - **Evidence:** official overview, CLI docs, SDK docs, GitHub Action repo.

- **Community multi-agent patterns (thin-to-moderate evidence, but rich for idea generation)**
  - **Pattern: repo partitioning / no-go zones** — one Reddit thread described 5–6 agents in parallel, each bounded by directory or feature, with explicit rules such as “don’t fix files you didn’t touch.”
  - **Pattern: one worktree = one owner = one PR** — repeated in multi-agent community discussions.
  - **Pattern: lead agent turns plan into tasks, then delegates** — visible both in Anthropic’s team docs and in community “multi-clauding” threads.
  - **Pattern: external orchestrators** — threads around Gastown and similar wrappers suggest people are building message-bus/worktree shells around multiple Claude Code instances, though reliability reports are mixed.
  - **Evidence:** Reddit threads in `r/ClaudeCode`.

**Evidence strength:** **moderate** for official multi-agent/CI capabilities; **exploratory** for community orchestration stacks and wrappers.

---

## Q5: Extensions & Integrations — IDE, Terminal, External Tools

- **Official VS Code / Cursor extension**
  - **Capability:** inline diffs, @mentions, plan review, context sharing, conversation tabs, IDE MCP bridge, background process visibility.
  - **Evidence:** official VS Code docs (`https://code.claude.com/docs/en/ide-integrations`).

- **Official JetBrains plugin**
  - **Capability:** interactive diff viewing and selection-context sharing inside IntelliJ-family IDEs.
  - **Evidence:** official JetBrains docs (`https://code.claude.com/docs/en/jetbrains`).

- **Official Chrome extension (beta)**
  - **Capability:** browser automation / debugging with a visible Chrome window and shared browser login state.
  - **Evidence:** official Chrome docs (`https://code.claude.com/docs/en/chrome`).

- **Claude desktop / web / remote sessions**
  - **Capability:** local, remote, SSH, cloud sessions, visual diffs, recurring tasks, multiple sessions, connectors, plugin install flows.
  - **Evidence:** official overview and desktop/web docs.

- **Slack bridge**
  - **Capability:** route coding work from chat into Claude Code sessions; progress and PR creation can happen from Slack-driven flows.
  - **Evidence:** official Slack docs.

- **Community Neovim integrations**
  - **Examples:**
    - `greggh/claude-code.nvim` — terminal toggle, file reload, real-time buffer updates, project-root behavior.
    - additional community variants surfaced in search: `sivchari/claude-code.nvim`, `nandoolle/claude-code.nvim`, `rsmdt/claude-code.nvim`.
  - **Adoption signal:** `greggh/claude-code.nvim` is one of the more visible repos in search and is widely cited in community lists.
  - **Evidence:** GitHub repos and awesome lists.

- **Community Emacs integrations**
  - **Examples:** `stevemolitor/claude-code.el`, `claude-code-ide.el`, `cpoile/claudemacs`, `yuya373/claude-code-emacs`, `monet` (Claude Code IDE protocol in Emacs).
  - **Evidence:** GitHub repos and awesome lists.

- **Official gap + community workaround**
  - **Observed state:** Anthropic issue discussion indicates other IDEs are feasible if an editor can speak the relevant WebSocket / MCP-style protocol, but non-official editors are not first-class in the same way VS Code/JetBrains are.
  - **Evidence:** `anthropics/claude-code` issue #1234 and community repos.

- **Terminal enhancers / output post-processing**
  - **Examples:**
    - `ariel-frischer/claude-clean` — parses Claude Code streaming JSON into a cleaner terminal UI.
    - output-style libraries and community wrappers that focus on formatting or terminal ergonomics.
  - **Signal quality:** exploratory; these exist, but no single dominant standard emerged in this pass.

- **Project-management and observability extensions**
  - **PM / knowledge tools surfaced in docs/marketplace:** Notion, Linear, Atlassian/Jira/Confluence, Slack, GitHub, GitLab, Asana.
  - **Observability / analytics surfaced:** Sentry, PostHog, Datadog AI Agents Console (organization-level telemetry, spend, latency, errors, repo-level activity), plus community session-history/replay tools.
  - **Evidence:** vendor docs, Anthropic plugin marketplace, Datadog blog, community posts.

**Evidence strength:** **moderate**. Strong for official editor/web/chat surfaces and marketplace integrations; exploratory for terminal polish and non-official editor ecosystems.

---

## Q6: Anti-Patterns & Footguns — What Breaks, What’s Hard

- **Large skill collections can become a scaling problem**
  - **Reported issue:** a public GitHub issue describes active sessions growing to 18–23GB RAM in a project with 1,071 skills/commands and hooks.
  - **Interpretation:** very large local extension catalogs may be a real stressor.
  - **Evidence:** `anthropics/claude-code` issue #22427.

- **Instruction / memory drift is still a practical complaint**
  - **Reported issue:** users have filed bugs that `CLAUDE.md` and persistent memory instructions are not consistently followed.
  - **Interpretation:** the memory system exists and is documented, but operational reliability can diverge from the mental model users expect.
  - **Evidence:** `anthropics/claude-code` issue #33603.

- **Hooks can be powerful but brittle at the edges**
  - **Reported issue:** a public issue claims `PreToolUse` hooks can fail silently or be bypassed in some circumstances.
  - **Interpretation:** hooks are a control surface, but users treating them as a hard security boundary should be cautious.
  - **Evidence:** `anthropics/claude-code` issue #31250.

- **MCP context tax is a recurring complaint**
  - **Reported issues:** users request lazy-loading of MCP tool definitions and report that even disabled MCP servers may still load tool definitions into context.
  - **Interpretation:** external-tool abundance can erode useful working context inside the model.
  - **Evidence:** `anthropics/claude-code` issues #11364 and #11370; Notion docs explicitly point users to `/context` to inspect per-server token usage.

- **Marketplace / plugin UX is still maturing**
  - **Reported issue:** marketplace load/validation failures have been reported (for example on Windows).
  - **Interpretation:** plugin packaging is powerful but not yet frictionless everywhere.
  - **Evidence:** `anthropics/claude-code` issue #33068.

- **Large repos still have familiar AI-agent performance problems**
  - **Official troubleshooting advice:** high CPU/memory in large repos is acknowledged; guidance includes compacting context, restarting, and excluding build/generated directories.
  - **Interpretation:** Claude Code inherits the classic “too much repo noise” problem.
  - **Evidence:** official troubleshooting docs.

- **Editor ecosystem is uneven**
  - **Observed tension:** official support is concentrated in VS Code/JetBrains, while Neovim/Emacs users rely on community integrations.
  - **Interpretation:** power users can extend into other editors, but first-party ergonomics and support are asymmetric.
  - **Evidence:** official issue #1234 plus community repos.

- **Server/tool ecosystem churn creates operational uncertainty**
  - **Observed patterns:** some public MCP servers in reference repos have moved, been archived, or changed maintainership; Slack naming limits and git-server path isolation issues have appeared in public issues.
  - **Interpretation:** the MCP ecosystem is productive but still unstable enough that “works today” does not guarantee “stable next quarter.”
  - **Evidence:** `modelcontextprotocol/servers` issues; vendor docs that warn MCP is still developing.

- **Security boundaries need scrutiny**
  - **Example:** a `modelcontextprotocol/servers` issue reported `mcp-server-git` ignoring its `--repository` restriction under one execution path, effectively widening file access.
  - **Interpretation:** treat third-party or reference MCP servers as software that requires normal security review, not as intrinsically safe glue.
  - **Evidence:** `modelcontextprotocol/servers` issue #604.

**Evidence strength:** **exploratory to moderate**. Many of the strongest footgun signals come from issue trackers and user reports rather than stable official guarantees.

---

## Open Questions
- How much real production usage exists for **Claude Code as an MCP server**? Official documentation exists, but public examples were sparse in this pass.
- The boundary between **plugin**, **MCP server**, **skill pack**, **subagent pack**, and **LSP bundle** is getting blurry. A future pass should map packaging formats more systematically.
- There is no obvious single official directory for **community skills/subagents/plugins**. Discovery is fragmented across GitHub, Anthropic marketplace, community marketplaces, and awesome-lists.
- Discord/community-chat evidence remains under-sampled here; public web indexing makes it much harder to verify Discord-native experiments than GitHub or Reddit.
- Adoption signals are uneven: Anthropic marketplace provides install counts, GitHub provides stars/forks, Reddit provides anecdotes, but these are not directly comparable.
- Some features (Channels, agent teams, Chrome beta, plugin beta-era surfaces) are changing quickly enough that any map of capabilities will age fast.

---

## Sources

### Official Claude / Anthropic docs and pages
- Claude Code overview — https://code.claude.com/docs
- Settings — https://code.claude.com/docs/en/settings
- Memory — https://code.claude.com/docs/en/memory
- CLI reference — https://code.claude.com/docs/en/cli-reference
- MCP — https://code.claude.com/docs/en/mcp
- IDE integrations (VS Code / Cursor) — https://code.claude.com/docs/en/ide-integrations
- JetBrains — https://code.claude.com/docs/en/jetbrains
- Remote Control — https://code.claude.com/docs/en/remote-control
- Claude Code on the web — https://code.claude.com/docs/en/web
- Chrome extension (beta) — https://code.claude.com/docs/en/chrome
- Slack — https://code.claude.com/docs/en/slack
- Sub-agents — https://code.claude.com/docs/en/sub-agents
- Agent teams — https://code.claude.com/docs/en/agent-teams
- Skills — https://code.claude.com/docs/en/skills
- Hooks — https://code.claude.com/docs/en/hooks
- Slash commands — https://code.claude.com/docs/en/slash-commands
- GitHub Actions — https://code.claude.com/docs/en/github-actions
- Channels — https://code.claude.com/docs/en/channels
- Troubleshooting — https://code.claude.com/docs/en/troubleshooting
- Plugins marketplace — https://claude.com/plugins
- Blog: Customize Claude Code with plugins — https://claude.com/blog/claude-code-plugins

### Official / primary repos from Anthropic
- `anthropics/claude-code` marketplace manifest — https://github.com/anthropics/claude-code/blob/main/.claude-plugin/marketplace.json
- `anthropics/skills` — https://github.com/anthropics/skills
- `anthropics/skills` skill-creator — https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md
- `anthropics/claude-code-action` — https://github.com/anthropics/claude-code-action

### MCP ecosystem / registries / vendor docs
- GitHub MCP org / registry surface — https://github.com/mcp
- `modelcontextprotocol/servers` — https://github.com/modelcontextprotocol/servers
- Notion MCP docs — https://developers.notion.com/guides/mcp/get-started-with-mcp
- Stripe MCP docs — https://docs.stripe.com/mcp
- Stripe MCP registry entry — https://github.com/mcp/com.stripe/mcp
- Sentry MCP docs — https://docs.sentry.io/ai/mcp/
- Linear MCP docs — https://linear.app/docs/mcp
- Anthropic life sciences marketplace — https://www.anthropic.com/claude-code-life-sciences-marketplace

### Community marketplaces / curated discovery layers
- `jlaswell/claude-community-marketplace` — https://github.com/jlaswell/claude-community-marketplace
- `ananddtyagi/cc-marketplace` — https://github.com/ananddtyagi/cc-marketplace
- `jimmc414/claude-code-plugin-marketplace` — https://github.com/jimmc414/claude-code-plugin-marketplace
- `hesreallyhim/awesome-claude-code` — https://github.com/hesreallyhim/awesome-claude-code
- `ComposioHQ/awesome-claude-skills` — https://github.com/ComposioHQ/awesome-claude-skills
- `travisvn/awesome-claude-skills` — https://github.com/travisvn/awesome-claude-skills
- `VoltAgent/awesome-agent-skills` — https://github.com/VoltAgent/awesome-agent-skills
- `VoltAgent/awesome-claude-code-subagents` — https://github.com/VoltAgent/awesome-claude-code-subagents
- `Chat2AnyLLM/awesome-claude-plugins` — https://github.com/Chat2AnyLLM/awesome-claude-plugins

### Community editor / tooling repos
- `greggh/claude-code.nvim` — https://github.com/greggh/claude-code.nvim
- `stevemolitor/claude-code.el` — https://github.com/stevemolitor/claude-code.el
- `ariel-frischer/claude-clean` — https://github.com/ariel-frischer/claude-clean

### Community threads / anecdotal practice
- Reddit: How I run 5-6 Claude Code agents in parallel without them breaking each other’s work — https://www.reddit.com/r/ClaudeCode/comments/1ru3i4q/how_i_run_56_claude_code_agents_in_parallel/
- Reddit: Spent 2 weeks running multiple claude code agents in parallel with gastown. here’s the honest take — https://www.reddit.com/r/ClaudeCode/comments/1qur3qq/spent_2_weeks_running_multiple_claude_code_agents/
- Reddit: Multi-Agent workflows (aka Multi-Clauding) — https://www.reddit.com/r/ClaudeCode/comments/1qlf38z/multiagent_workflows_aka_multiclauding/

### Issues / limitation signals
- Memory leak in active sessions with many skills — https://github.com/anthropics/claude-code/issues/22427
- CLAUDE.md / persistent memory instructions ignored — https://github.com/anthropics/claude-code/issues/33603
- PreToolUse hooks fail silently — https://github.com/anthropics/claude-code/issues/31250
- Lazy-load MCP tool definitions — https://github.com/anthropics/claude-code/issues/11364
- Disabled MCP servers still load tool definitions — https://github.com/anthropics/claude-code/issues/11370
- Plugin marketplace validation/load error — https://github.com/anthropics/claude-code/issues/33068
- Support for other IDEs (Neovim/Emacs) — https://github.com/anthropics/claude-code/issues/1234
- `mcp-server-git` repository restriction issue — https://github.com/modelcontextprotocol/servers/issues/604
- Slack MCP tool-name length issue — https://github.com/modelcontextprotocol/servers/issues/3258

### Observability / analytics
- Datadog: Monitor Claude Code adoption in your organization with AI Agents Console — https://www.datadoghq.com/blog/claude-code-monitoring/
