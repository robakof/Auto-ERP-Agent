# Research Results: Claude Code Extensions & Practices

Date: 2026-03-24

Scope note: this pass optimizes for breadth over proof. It includes official Claude Code docs, Claude plugin marketplace pages, GitHub repos/issues, and public community pages. Where evidence is thin, second-hand, or mostly testimonial, it is marked as exploratory.

## TL;DR — 5 High-Signal Directions
- Claude Code is no longer just a terminal editor loop: it now has hooks, checkpointing, subagents, experimental agent teams, plugins, remote control, scheduled/background workflows, browser automation, IDE integrations, telemetry, and cloud/web execution paths.
- The extension surface has widened from “MCP servers” to a broader plugin model: skills, agents, hooks, MCP servers, and LSP servers can all ship together inside a plugin.
- The MCP/plugin ecosystem is large enough to matter operationally: there is an Anthropic-managed plugin directory, a high-volume marketplace, a large reference MCP repo, and multiple community registries/awesome-lists.
- Custom skills are converging on repeatable patterns: thin `SKILL.md` entrypoints, YAML frontmatter for invocation control, supporting files for heavy context, and composition through subagents/plugins instead of giant monolithic prompts.
- A parallel ecosystem is forming around orchestration and wrappers: Ralph, wshobson/agents, Claude Orchestrator, Claude MPM, Codex-delegation MCP servers, and OpenClaw-adjacent setups all point to multi-agent, multi-session, and cross-tool coordination as a major community frontier.

---

## Q1: Core Features — Beyond Obvious

### Hooks system
- **Hooks are a first-class lifecycle automation system**, not just shell callbacks. Official docs describe hooks as user-defined **shell commands, HTTP endpoints, or LLM prompts** that run at specific lifecycle points. The reference also documents **agent hooks**, **async hooks**, and **MCP tool hooks**. This is materially broader than the typical “pre-commit style” mental model.
- **Lifecycle coverage is wide.** Official hook events include `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`, `Notification`, `SubagentStart`, `SubagentStop`, `Stop`, `StopFailure`, `InstructionsLoaded`, `ConfigChange`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Elicitation`, `ElicitationResult`, and `SessionEnd`. Agent-team-specific events like `TeammateIdle` and `TaskCompleted` are also documented.
- **Hook use cases go beyond policy checks.** Obvious cases include blocking destructive shell commands, but official docs also point to async post-edit test runs, prompt-based decision hooks, permission mediation, worktree substitution, and MCP elicitation handling.
- **Hook footgun:** lifecycle complexity is high. The existence of dedicated hook troubleshooting sections and multiple GitHub bug reports suggests hooks are powerful but still easy to misconfigure.

### Slash commands and built-in utilities
- **Built-in slash commands now act as a control plane.** Official commands include `/agents`, `/chrome`, `/config`, `/context`, `/doctor`, `/hooks`, `/insights`, `/mcp`, `/memory`, `/permissions`, `/plugin`, `/remote-control`, `/schedule`, `/security-review`, `/statusline`, `/tasks`, `/voice`, `/btw`, `/pr-comments`, and `/rewind`.
- **Bundled skills appear alongside built-in commands.** Official docs explicitly note bundled skills such as `/simplify`, `/batch`, and `/debug`, which means the slash-command surface already mixes core commands and skill-distributed behaviors.
- **MCP prompts can surface as slash-like entries.** Built-in commands docs note `/mcp__<server>__<prompt>` for server-defined prompts, which effectively turns MCP servers into custom command surfaces.

### Memory system
- **Claude Code has two persistent memory layers:** `CLAUDE.md` instructions written by the user and **auto memory** notes written by Claude itself.
- **Auto memory is relatively recent and on by default.** Official docs state auto memory requires Claude Code **v2.1.59+**, is enabled by default, and can be toggled in `/memory` or disabled via `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
- **Memory has structure and loading rules.** `CLAUDE.md` files load at session start; subdirectory `CLAUDE.md` files can be lazily loaded; auto memory stores `MEMORY.md` plus topic files; only the first chunk of memory is eagerly loaded and topic files are pulled on demand.
- **Important nuance:** official docs say `CLAUDE.md` is delivered as a **user message**, not as the system prompt. That makes it persistent context, not hard enforcement. This is an important architectural detail and a recurring source of user confusion.
- **Best-practice signal from official docs:** concise, specific, structured instructions outperform broad “style guide” prose. Large memory files directly compete with conversation context.

### Settings & configuration power-user options
- **Settings are hierarchical and policy-capable.** Official scopes are `managed`, `user`, `project`, and `local`, with managed settings explicitly positioned for organization-wide enforcement.
- **Plugin governance is deeper than a single install command.** Settings docs expose `extraKnownMarketplaces` and `strictKnownMarketplaces`, letting admins whitelist or pre-register plugin marketplaces.
- **CLI flags expose many non-obvious modes.** The CLI reference documents advanced flags such as:
  - `--agents` for dynamic subagents via JSON
  - `--bare` to skip auto-discovery of hooks/skills/plugins/MCP/auto-memory/CLAUDE.md for faster scripted calls
  - `--channels` and `--dangerously-load-development-channels` for research-preview channel flows
  - `--chrome` for browser automation
  - `--fork-session` for branching session history
  - `--json-schema` for structured output in print mode
  - `--max-budget-usd` and `--max-turns` for non-interactive control
  - `--mcp-config` and `--strict-mcp-config`
  - `--remote`, `--remote-control`, and `--teleport` for cloud/web and local handoff flows
  - `--worktree` and `--teammate-mode` for isolation and agent-team display
- **Programmatic usage is not a hack anymore.** Anthropic’s Agent SDK docs explicitly present `claude -p` and SDK usage as supported paths.

### Integration modes
- **Official IDE support is substantial.** Claude Code has an official VS Code extension and JetBrains plugin. VS Code docs describe inline diffs, file @-mentions, plan review, multiple conversations, background-process monitoring, MCP connectivity, and a built-in IDE MCP server. JetBrains docs describe diff viewing, selection context sharing, diagnostics sharing, and `/ide` connectivity.
- **Remote session modes are now plural:**
  - **Remote Control:** keep the session on your machine but control it from browser/mobile.
  - **Claude Code on the web:** research-preview cloud execution on Anthropic-hosted infrastructure.
  - **Desktop/Cowork messaging in product docs/search snippets:** points to a local-vs-cloud split for interactive vs background work.
- **Browser integration is real, not conceptual.** The Chrome integration docs describe visible browser automation, DOM/console inspection, authenticated browsing through the user’s existing login state, and cross-use from CLI or VS Code.

### Other built-in capabilities that are easy to miss
- **Checkpointing is a serious session-state feature.** Official docs say Claude Code tracks edits before each change, persists checkpoints across resumed sessions, supports targeted rewind and summarize operations, and can restore code and conversation independently.
- **Checkpointing limitation:** bash-made file changes and external edits are not reliably tracked.
- **Monitoring/observability is official.** Claude Code supports OpenTelemetry metrics and logs export for usage, cost, and tool activity monitoring.
- **Code Review exists as a separate official mode/surface.** Anthropic documents multi-agent code review in research preview, with GitHub integration.
- **Channels exist in research preview.** Official docs describe a way for MCP servers to push events into a running session, effectively turning Claude Code into an event-driven runtime.

**Evidence strength:** strong for hooks/memory/settings/CLI/integrations; moderate for some newer preview surfaces; exploratory for product-search-only details around Cowork/background agents.

---

## Q2: MCP Servers — Catalog & Use Cases

### Landscape summary
The Claude Code extension surface now overlaps three related but distinct things:
1. **MCP servers** (tool/provider connections)
2. **Plugins** (packaged bundles that can include MCP, skills, agents, hooks, and LSP)
3. **Marketplaces/directories** that distribute either plugins or MCP-capable integrations

There does **not** appear to be one universally canonical registry for “all Claude Code MCP servers.” Instead, discovery is fragmented across Anthropic’s plugin marketplace, Anthropic’s official plugin GitHub directory, the `modelcontextprotocol/servers` reference repo, community awesome-lists, and project-specific repos.

### A. Official / reference / curated sources

#### 1) Anthropic plugin marketplace
- **What it is:** Anthropic-hosted marketplace for Claude plugins used by Claude Code and Cowork.
- **Capabilities surfaced:** external systems like GitHub, Slack, Linear, Stripe, Sentry, GitLab, Vercel, PostHog, Postman, Zapier, Neon, Sanity, and more.
- **Adoption signals from marketplace pages:**
  - **Context7**: ~189k installs
  - **GitHub**: ~141k installs
  - **Slack**: ~29.6k installs
  - **Vercel**: ~27.3k installs
  - **Linear**: ~24.3k installs
  - **Sentry**: ~19.4k installs
  - **GitLab**: ~18.5k installs
  - **Stripe**: ~18.4k installs
  - **Firecrawl**: ~11.4k installs
  - **PostHog**: ~5.6k installs
  - **Postman**: ~2.9k installs
  - Lower-signal but notable long-tail plugins include Zapier, Sanity, Stagehand, and Neon.
- **Maintenance signal:** marketplace-hosted and installable today; individual maintenance varies by vendor/plugin.

#### 2) `anthropics/claude-plugins-official`
- **What it is:** Anthropic-managed GitHub directory of “high quality Claude Code Plugins.”
- **Adoption signal:** ~14.3k GitHub stars.
- **Why it matters:** this is a curated distribution layer, not just a doc page, and it strongly suggests Anthropic is formalizing plugin packaging beyond raw MCP configs.

#### 3) `modelcontextprotocol/servers`
- **What it is:** large reference repository for MCP servers.
- **Adoption signal:** ~81.9k GitHub stars.
- **Important nuance:** registry-like in practice, but official search snippets and docs frame it as an **examples/reference** repo rather than a fully managed marketplace.
- **Use cases covered in examples/reference material:** filesystem, git, GitHub, Postgres, Docker, Notion, Grafana, and many others.

#### 4) `punkpeye/awesome-mcp-servers`
- **What it is:** community-maintained registry-style awesome-list.
- **Adoption signal:** ~83.9k GitHub stars.
- **Why it matters:** currently one of the broadest public maps of the MCP ecosystem.

### B. Common server categories and example capabilities

#### Developer workflow / source control
- **GitHub** — repo access, PR/review workflows, issue handling, automation. High adoption in Anthropic marketplace.
- **GitLab** — CI/CD and repo workflows. Listed in Anthropic marketplace with meaningful install volume.
- **Git / filesystem** — common in reference MCP repos for local/project operations.
- **Docker** — operational control over containers; appears in reference/community registries.

#### Docs / knowledge / project coordination
- **Context7** — version-specific docs retrieval; very high install count in Anthropic marketplace.
- **Slack** — read/send/search collaboration context; major install signal.
- **Linear / Jira / Notion** — project and ticket context. Anthropic docs/search snippets explicitly mention Jira and other SaaS MCP options; marketplace and community lists add Linear and Notion.

#### Observability / product / support
- **Sentry** — error triage and incident follow-up; strong install signal.
- **PostHog** — analytics and product telemetry; mid-tier install signal.
- **Grafana** — observability/monitoring surfaced in community/reference MCP lists.

#### Databases / backend / infra
- **Postgres** — common reference MCP example and practical server type.
- **Neon** — cloud Postgres workflow; appears in marketplace and reference/community lists.
- **AWS Labs MCP servers** — awslabs-maintained MCP set, strong GitHub signal (~8.5k stars).

#### Web / browser / testing / scraping
- **Firecrawl** — crawling/search extraction; meaningful marketplace installs.
- **Stagehand** — browser/task automation; still low-volume in marketplace but noteworthy.
- **ScreenshotMCP / Search1API / Semgrep-related servers** — found in community lists; useful as niche examples rather than broadly proven standards.

#### Integration hubs / broad connectors
- **Zapier** — many-app integration surface, but comparatively lower install count in the observed marketplace snapshot.
- **Rube** — community-listed “500+ apps” style connector surface; broad but more exploratory.

### C. Experimental / niche servers worth knowing about
- **`junyjeon/claude-codex-orchestrator`** — MCP server that lets Claude Code delegate narrow, self-contained tasks to Codex while Claude keeps architectural control. Interesting as a “model-to-model delegation” pattern.
- **`mcpskill`** (seen in community search results) — wrapper idea to expose skills through MCP, reducing repeated tool-definition loading. Evidence is exploratory.
- **Channels-enabled plugins/servers** — not a server category by business domain, but potentially a new runtime pattern: MCP servers pushing events into a live session instead of only serving pull-style tools.

### D. Adoption and maintenance signals
- **Strongest signals:** Anthropic marketplace install counts; GitHub stars on `modelcontextprotocol/servers`, `awesome-mcp-servers`, and Anthropic’s official plugin directory.
- **Medium signals:** active release pages, GitHub Actions activity, recent commits, visible usage docs.
- **Weak/exploratory signals:** single gists, marketplace mirrors, one-off blog posts, or testimonial-heavy landing pages.

**Evidence strength:** strong for marketplace/directories/reference repos; moderate for category mapping; exploratory for some niche servers and cross-model delegation setups.

---

## Q3: Custom Skills — Patterns & Examples

### Official skill structure
- Official docs standardize skills around a **directory containing `SKILL.md`**.
- Skills can live in:
  - `~/.claude/skills/<name>/SKILL.md` (personal)
  - `.claude/skills/<name>/SKILL.md` (project)
  - `<plugin>/skills/<name>/SKILL.md` (plugin-provided)
- Official docs say old `.claude/commands/` still works, but skills are the newer, richer abstraction.

### Frontmatter and control patterns
Official docs show skills using YAML frontmatter for behavior control, including:
- `name`
- `description`
- `disable-model-invocation` (for manual-only task skills)
- `allowed-tools`
- `context: fork` (run in forked/subagent-style context)

This points to a pattern: **skills are not just prompts; they are lightweight runnable units with routing and execution policy.**

### Common skill types seen in docs and public repos
- **Commit helpers / release helpers / deployment tasks**
- **Test runners / quality gates / debugging assistants**
- **Code reviewers / explainers / refactorers**
- **Scaffolders / feature generators**
- **Browser / Playwright / web-testing helpers**
- **Cross-functional workflows** in community repos: product, marketing, compliance, advisory, and content tasks

### Composition patterns
- **Thin skill, heavy supporting files.** Official docs recommend keeping `SKILL.md` focused and placing heavy references/examples/scripts beside it.
- **Argument-driven invocation.** Official docs expose `$ARGUMENTS`, `$ARGUMENTS[N]`, and session/path substitutions like `${CLAUDE_SESSION_ID}` and `${CLAUDE_SKILL_DIR}`.
- **Subagent-backed skills.** Official docs show `context: fork`, and subagent docs explicitly position subagents as isolation/context-management tools. Community practice increasingly uses skills as dispatchers into specialized agents.
- **Plugin-packaged skills.** Plugins can bundle skills, agents, hooks, MCP, and LSP together, which means teams can ship a full operating model instead of loose markdown snippets.

### Where people share skills
- **`alirezarezvani/claude-skills`** — large multi-domain repository (~6.6k stars) with 190+ skills/plugins and explicit compatibility claims beyond Claude Code.
- **`travisvn/awesome-claude-skills`** — community directory (~9.6k stars per search/opened result set).
- **`wshobson/commands`** — ~2.2k stars; 57 production-ready slash commands, including workflow-style orchestration patterns.
- **`jezweb/claude-skills`** — ~643 stars; practical dev-focused skills.
- **`honnibal/claude-skills`** — smaller experimental repo (~196 stars), useful because it exposes how advanced users structure skills defensively.
- **Awesome lists and Reddit threads** are active distribution channels, often surfacing repos faster than official docs.

### Conventions emerging from the ecosystem
- Keep the entry skill short; push bulky content into reference files.
- Separate “auto-invokable helper skills” from “manual task skills” with `disable-model-invocation`.
- Use subagents for context isolation instead of bloating the main skill.
- Namespace reusable team logic through plugins rather than copying `.claude` folders across repos.

**Evidence strength:** strong for official structure and frontmatter; moderate for composition patterns; moderate-to-exploratory for community conventions outside official docs.

---

## Q4: Advanced Workflows — Multi-Agent, Automation, CI/CD

### Official multi-agent surfaces
- **Subagents** are official and stable enough to document deeply. They run in separate context windows with their own system prompts, tool access, permissions, and model choices.
- **Agent teams** are official but explicitly **experimental**. Docs describe a lead session plus teammates, shared tasks, direct inter-agent messaging, and centralized coordination. This is much closer to a real orchestration runtime than “spawn a helper.”
- **Agent teams have meaningful caveats:** docs call out limitations around resumption, task coordination, and shutdown behavior.

### Official automation / scripting paths
- **`claude -p` print mode and the Agent SDK** provide supported programmatic invocation.
- **GitHub Actions** has official docs and an official action path (`anthropics/claude-code-action@v1` in docs/search materials), including PR review/creation and skill-aware behavior through repository `CLAUDE.md`.
- **GitLab CI/CD** appears in official product/docs surfaces as beta.
- **Scheduled/background work** appears via `/schedule`, tasks tooling, and product/community chatter around scheduled tasks. This is supported enough to mention, though some of the detailed community excitement around it is newer than the deepest docs.
- **Channels** enable event-driven session orchestration in research preview.

### Community multi-agent/orchestration projects

#### Ralph
- **`mikeyobrien/ralph-orchestrator`** is a real, active project, not just a meme reference to the “Ralph Wiggum technique.”
- Repo/docs/search signals show:
  - Claude Code support, plus support for other coding agents/tools
  - task/memory concepts
  - MCP server mode
  - Telegram-based human-in-the-loop (“RObot”) patterns
  - ~2.3k GitHub stars and recent releases
- Interpretation: Ralph is one of the clearest examples of an independent orchestration layer around Claude Code rather than a simple plugin pack.

#### wshobson/agents
- One of the strongest community signals for **workflow orchestration as a plugin ecosystem**.
- Public materials point to large numbers of focused plugins/agents/tools, explicit orchestration patterns, and even an experimental **Agent Teams plugin**.
- Search results and marketplace mirrors suggest very high adoption, though exact star counts varied across surfaced pages; still clearly high-signal.

#### Claude Orchestrator
- **`reshashi/claude-orchestrator`** positions itself as an **automated delivery pipeline**: spawn multiple Claude sessions in parallel, isolate workers in worktrees/branches, create PRs, monitor CI, apply quality gates, and merge.
- Strong example of “Claude Code as CI/CD worker fleet,” not just a local pair programmer.

#### Claude MPM
- **`bobmatnyc/claude-mpm`** frames itself as a **Multi-Agent Project Manager** for Claude Code, with orchestration, skills, MCP integration, session management, and semantic code search.
- This is a useful example of the ecosystem drifting toward “platform around Claude Code.”

#### Cross-model delegation
- **`junyjeon/claude-codex-orchestrator`** is notable because it turns Claude Code into an orchestrator over Codex via MCP.
- This suggests a community pattern where Claude Code becomes the control plane and other models become specialist workers.

### OpenClaw and adjacent systems
- **OpenClaw was explicitly searched and found.**
- What was found:
  - `openclaw/openclaw` GitHub repo
  - OpenClaw site and org pages
  - testimonial-heavy claims around persistent memory, background tasks, cron/reminders, and remote control of coding sessions
- **How to position it:** OpenClaw is not a Claude Code extension in the narrow sense; it is a broader personal-agent platform. But community pages/testimonials explicitly describe using it to manage Claude Code/Codex sessions, run background workflows, and bridge communication channels to agent runtimes.
- **Evidence quality:** mixed. The existence and popularity are real; many specific Claude Code integration claims are testimonial or community-post level rather than official, reproducible docs.

### Patterns showing up repeatedly
- **Role separation:** planner/reviewer/implementer/tester/security-auditor splits
- **Worktree isolation:** each agent/session gets an isolated git branch or worktree
- **Message passing through files, MCP, or chat transports:** Telegram, Discord, internal task files, or plugins
- **Human-in-the-loop checkpoints:** Telegram review, PR review, explicit quality gates
- **Long-running loops:** background tasks, cron/scheduling, CI monitoring, retry after failure

**Evidence strength:** strong for subagents, agent teams, Agent SDK, GitHub Actions; moderate for community orchestrators with active repos; exploratory-to-moderate for OpenClaw-based Claude Code control patterns.

---

## Q5: Extensions & Integrations — IDE, Terminal, External Tools

### Official editor extensions
- **VS Code extension** is clearly first-party and heavily adopted.
  - Marketplace page showed **~7.6M installs** at retrieval time.
  - Official docs highlight inline diffs, selection-aware prompts, @-mentions with line ranges, plan review, multi-conversation tabs, background-process monitoring, and MCP integration.
- **JetBrains plugin** is also first-party/beta.
  - Official docs list IntelliJ IDEA, PyCharm, Android Studio, WebStorm, PhpStorm, and GoLand support.
  - Features include interactive diffs, shared selection context, diagnostics sharing, and `/ide` connectivity from an external terminal.

### Browser / terminal / remote surfaces
- **Chrome integration** is an official beta, not just community browser automation. It supports visible browser actions, login-state reuse, DOM/console inspection, and data extraction.
- **Remote Control** turns any local session into something controllable from browser/mobile while keeping execution local.
- **Claude Code on the web** adds a cloud-run surface for asynchronous or parallel tasks.
- **Statusline / terminal setup / remote teleportation** show that the terminal UX itself is now extensible and configurable.

### Project-management / business-tool integrations
Through plugins/MCP/marketplace entries, Claude Code can be extended into:
- **Linear**
- **Jira**
- **Slack**
- **Notion**
- **GitHub / GitLab**
- **Stripe**
- **Sentry**
- **Vercel**
- **PostHog**
- **Postman**

This is enough breadth that Claude Code can function as a control plane over product, incident, support, and deployment workflows.

### Observability and analytics
- **Official OpenTelemetry support** provides metrics/log/event export.
- Community tooling is emerging around **hook-based observability** and **session logging**. Search results surfaced repos like `claude-code-hooks-multi-agent-observability`, but evidence is still more repo-driven than widely documented.

### Community orchestrators, wrappers, and enhancers
- **Ralph Orchestrator** — autonomous orchestration layer with multi-tool support.
- **wshobson/agents** — workflow/plugin ecosystem with multi-agent orchestration patterns.
- **Claude Orchestrator** — automated PR/CI/merge flow.
- **Claude MPM** — session/memory/orchestration wrapper-platform.
- **OpenClaw** — personal-agent shell around Claude Code/Codex-style sessions.
- **WSL/notification/audio hook repos** — small but practical terminal-quality-of-life layer.

### What was explicitly searched for
- **Open Claw / OpenClaw:** found.
- **Ralph:** found, and specifically found as `ralph-orchestrator` rather than only social-post lore.
- **Independent MCP servers:** found in large numbers through marketplace pages, `modelcontextprotocol/servers`, and `awesome-mcp-servers`.
- **Community orchestrators:** found repeatedly across GitHub repos, awesome-lists, and setup guides/gists.

**Evidence strength:** strong for official IDE/browser/remote surfaces and plugin integrations; moderate for orchestrators/wrappers; exploratory for some small terminal enhancer repos and gist-based workflows.

---

## Q6: Anti-Patterns & Footguns — What Breaks, What’s Hard

### Context and performance problems
- Multiple GitHub issues report **context-limit mismatches**, where `/context` shows substantial free space but Claude Code blocks further progress with context-limit errors.
- Other issues report **terminal lag and near-unusability as context grows**, especially in long sessions.
- Community workaround signal: some users are experimenting with hooks/routing patterns to reduce context pressure by deferring or filtering context injection.

### Hook and memory edge cases
- GitHub issues report **“Prompt is too long”** failures caused by oversized `SessionStart` hooks or overly aggressive hook-injected context.
- Another issue reports **`InstructionsLoaded` not firing after compaction**, which matters because many users rely on hooks to confirm instruction state.
- Official docs themselves warn that `CLAUDE.md` is **not strict enforcement**, which becomes a practical footgun when teams assume it behaves like a locked system prompt.

### Checkpointing misconceptions
- Checkpointing sounds like full undo, but official docs say it **does not track bash-made file changes** and **does not reliably track external edits**. Users treating it like version control are likely to be surprised.

### Experimental-feature instability
- **Agent teams** are explicitly experimental and disabled by default. Official docs mention limitations in resumption, task coordination, and shutdown.
- **Channels** and **web/cloud execution** are still preview/research-preview surfaces.
- **Chrome integration** adds context overhead when enabled by default.

### Integration and auth limitations
- Official Remote Control docs note incompatibilities with some third-party-provider or API-key-based setups. The feature depends on Anthropic account auth and certain platform conditions.
- Plugins and third-party MCP servers introduce a large trust surface. Anthropic docs and marketplace/directory materials repeatedly warn about the risk of installing untrusted extensions.

### Unmet needs seen in issues and community threads
- Better handling for huge repos / long-running sessions
- Stronger guarantees around instruction persistence after compaction or resume
- Better visibility into what hooks/plugins/memory are active at any given moment
- Safer discovery and vetting of third-party MCP servers/plugins
- Richer orchestration primitives without requiring experimental agent teams or heavy wrappers

**Evidence strength:** strong for official caveats and GitHub issue categories; moderate for community complaints/workarounds; exploratory for some Reddit-derived fixes and “90% token savings” claims.

---

## Open Questions
- Is Anthropic converging on **plugins** as the main abstraction, with raw MCP config becoming lower-level plumbing, or will both remain first-class long term?
- How much of the community orchestration layer will remain outside Claude Code versus getting absorbed into official agent teams, channels, and scheduled/background workflows?
- Is there a future canonical registry for Claude Code-compatible MCP/plugin integrations, or will discovery stay fragmented across marketplace + GitHub + awesome-lists?
- OpenClaw clearly exists and is popular, but the precise boundary between “OpenClaw uses Claude Code” and “Claude Code is one option inside a larger OpenClaw runtime” needs a deeper pass.
- Some community claims around background autonomy, observability wrappers, and cross-model orchestration are promising but not yet backed by enough reproducible case studies.

---

## Sources

### Official Claude Code / Anthropic docs
- Claude Code Docs home: https://code.claude.com/docs/en
- Hooks reference: https://code.claude.com/docs/en/hooks
- Built-in commands: https://code.claude.com/docs/en/commands
- CLI reference: https://code.claude.com/docs/en/cli-reference
- Settings: https://code.claude.com/docs/en/settings
- Memory: https://code.claude.com/docs/en/memory
- Skills: https://code.claude.com/docs/en/skills
- Subagents: https://code.claude.com/docs/en/sub-agents
- Agent teams: https://code.claude.com/docs/en/agent-teams
- Checkpointing: https://code.claude.com/docs/en/checkpointing
- Plugins reference: https://code.claude.com/docs/en/plugins-reference
- Remote Control: https://code.claude.com/docs/en/remote-control
- Claude Code on the web: https://code.claude.com/docs/en/claude-code-on-the-web
- VS Code docs: https://code.claude.com/docs/en/vs-code
- JetBrains docs: https://code.claude.com/docs/en/jetbrains
- Chrome integration docs: https://code.claude.com/docs/en/chrome
- Code Review docs: https://code.claude.com/docs/en/code-review
- Channels docs: https://code.claude.com/docs/en/channels
- Monitoring / OpenTelemetry: https://code.claude.com/docs/en/monitoring-usage
- GitHub Actions docs: https://code.claude.com/docs/en/github-actions
- Agent SDK overview: https://platform.claude.com/docs/en/agent-sdk/overview

### Anthropic marketplace / official distribution
- Plugins for Claude Code and Cowork: https://claude.com/plugins
- Context7 plugin page: https://claude.com/plugins/context7
- Anthropic official plugin directory repo: https://github.com/anthropics/claude-plugins-official
- VS Code Marketplace listing: https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code
- JetBrains Marketplace listing: https://plugins.jetbrains.com/plugin/27310-claude-code-beta-

### MCP ecosystem / registries
- MCP reference servers repo: https://github.com/modelcontextprotocol/servers
- Awesome MCP servers: https://github.com/punkpeye/awesome-mcp-servers
- MCP Inspector: https://github.com/modelcontextprotocol/inspector
- AWS Labs MCP collection: https://github.com/awslabs/mcp

### Community skills / commands / orchestration
- Awesome Claude Code: https://github.com/hesreallyhim/awesome-claude-code
- Awesome Claude Skills: https://github.com/travisvn/awesome-claude-skills
- alirezarezvani/claude-skills: https://github.com/alirezarezvani/claude-skills
- wshobson/commands: https://github.com/wshobson/commands
- wshobson/agents: https://github.com/wshobson/agents
- jezweb/claude-skills: https://github.com/jezweb/claude-skills
- honnibal/claude-skills: https://github.com/honnibal/claude-skills
- ShakaCode claude-code-templates: https://github.com/shakacode/claude-code-templates

### Community orchestrators / wrappers / experimental integrations
- Ralph Orchestrator: https://github.com/mikeyobrien/ralph-orchestrator
- Claude Orchestrator: https://github.com/reshashi/claude-orchestrator
- Claude MPM: https://github.com/bobmatnyc/claude-mpm
- Claude MPM agent templates: https://github.com/bobmatnyc/claude-mpm-agents
- Claude Codex Orchestrator: https://github.com/junyjeon/claude-codex-orchestrator
- OpenClaw site: https://openclaw.ai/
- OpenClaw repo: https://github.com/openclaw/openclaw
- OpenClaw org repositories: https://github.com/orgs/openclaw/repositories

### GitHub issues / limitations / complaints
- Context limit reached prematurely: https://github.com/anthropics/claude-code/issues/20455
- Prompt too long from SessionStart hooks: https://github.com/anthropics/claude-code/issues/15554
- Context growth makes terminal unusable: https://github.com/anthropics/claude-code/issues/12222
- InstructionsLoaded hook does not fire after compaction: https://github.com/anthropics/claude-code/issues/30973
- Related duplicate/context-limit reports: https://github.com/anthropics/claude-code/issues/19478
- Related context-limit report after compact: https://github.com/anthropics/claude-code/issues/18159

### Supplemental public signals
- Reuters on OpenClaw popularity in China: https://www.reuters.com/technology/openclaw-enthusiasm-grips-china-schoolkids-retirees-alike-raise-lobsters-2026-03-19/
- TechRadar on malicious ads impersonating Claude Code/OpenClaw: https://www.techradar.com/pro/security/infostealers-are-being-disguised-as-claude-code-openclaw-and-other-ai-developer-tools
