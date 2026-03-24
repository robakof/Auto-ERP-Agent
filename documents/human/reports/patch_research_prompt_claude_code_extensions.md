# Patch Analysis: Research Prompt — Claude Code Extensions

**Date:** 2026-03-24
**Agent:** Prompt Engineer
**Problem type:** `conflicting_instructions` + `missing_checkpoint`

---

## Problem Diagnosis

**User observation:**
> Research nie zawiera wzmianki o Open Claw, Ralph itp. — najpopularniejsze rzeczy o których wiem się nie pojawiły. Researcher za bardzo się zawęża do potwierdzonego zamiast eksperymentalnego.

**Root cause found:**

Prompt zawiera **conflicting instructions**:

1. Line 12: "Accept weak evidence: GitHub issues, Reddit threads, **experimental repos**"
2. Line 149: "GitHub: `repo:anthropics/claude-code`" — zawęża do 1 oficjalnego repo

**Result:**
- ✓ Official ecosystem pokryty (Anthropic marketplace, vendor docs, official MCP servers)
- ✗ Community experiments pominięte (Open Claw, Ralph, independent orchestrators)
- r/ClaudeCode **pojawił się w results** mimo braku w search hints (researcher znalazł mimo promptu)

**Hypothesis:**
Researcher agent (claude-code-guide) ma bias towards official sources (jego mission to "answer questions about Claude Code features"). Search hints wzmacniają bias zamiast go niwelować.

---

## Solution

**Approach:** Explicit two-phase structure (50% official, 50% community) + rozszerzenie search hints.

### Changes Implemented

#### 1. Research Structure — Two Phases (after line 14)

**ADDED:**
```markdown
## Research Structure — Two Phases

### Phase 1: Official Ecosystem (50% time)
- Anthropic docs, marketplace, official repos
- Vendor-documented integrations (Notion, Stripe, Linear)
- High confidence sources

**Goal:** Map what's supported, documented, production-ready.

### Phase 2: Community Ecosystem (50% time)
- GitHub broad search (not just anthropics/ org)
- Reddit (r/ClaudeCode especially), HN, Twitter
- Independent projects (Open Claw, Ralph, orchestrators)
- Experimental, low-confidence, "I built this" posts

**Goal:** Map what's possible, what people are trying, edge experiments.

**Critical:** After Phase 1, SWITCH CONTEXT. Don't filter Phase 2 by "is this official?"
You're now looking for experiments, not endorsements.
```

**Why:**
- Explicit context switch eliminuje bias
- Equal weight (50/50) — community coverage równa official
- "SWITCH CONTEXT" — strong signal że Phase 2 = różne reguły

---

#### 2. Search Strategy Hints — Phase Separation (line 147-155)

**OLD:**
```markdown
- GitHub: `repo:anthropics/claude-code` + issues, discussions, wiki
- Reddit: r/ClaudeAI, r/Anthropic
- Discord: Claude/Anthropic servers
```

**NEW:**
```markdown
**Phase 1 (Official Ecosystem):**
- GitHub: `repo:anthropics/claude-code`
- Official docs: claude.ai docs, Anthropic API docs
- Anthropic marketplace: claude.com/plugins
- Vendor docs: Notion, Stripe, Linear, Sentry MCP
- MCP registry: github.com/mcp, modelcontextprotocol/servers

**Phase 2 (Community Ecosystem):**
- GitHub:
  - Broad search: "Claude Code" (not limited to anthropics/ org)
  - Specific projects: "Open Claw", "Ralph", orchestrators, wrappers
  - Awesome-lists: awesome-claude-code, awesome-claude-skills
- Reddit: r/ClaudeCode, r/ClaudeAI, r/Anthropic, r/LocalLLaMA
- Twitter/X, HackerNews: community launches, independent projects
- Discord: Anthropic + community servers
- Blogs: Dev.to, Medium, personal "I built..." posts
```

**Why:**
- Phase 1 = focused (official sources only)
- Phase 2 = broad (community GitHub, r/ClaudeCode, Twitter, HN)
- Explicit mention: "Open Claw", "Ralph" — researcher będzie szukał nazwami

---

#### 3. Q5 — Community Orchestrators (after line 74)

**ADDED:**
```markdown
- Community orchestrators & wrappers:
  - Multi-agent orchestration frameworks
  - CLI wrappers and enhancements
  - Experimental integrations (Open Claw, Ralph, etc.)
  - Independent MCP servers outside official marketplace

**Evidence threshold:** GitHub repos, HackerNews, Twitter, Reddit experiments.
```

**Why:**
- Explicit callout = researcher wie że to jest w scope
- "Open Claw, Ralph" — nazwane = searched
- Evidence threshold rozszerzony (Twitter, HN)

---

#### 4. Time Cap — Prioritize Coverage (line 157)

**OLD:**
```markdown
if a question yields <3 sources after 15 min → mark as "low signal" and move on.
```

**NEW:**
```markdown
if a question yields <3 sources after 15 min → mark as "low signal, needs deeper pass" and continue.
Don't skip categories — surface coverage matters more than proof depth.
```

**Why:**
- "Continue" zamiast "move on" — nie pomijaj kategorii
- "Surface coverage > proof depth" — breadth over perfection

---

## Expected Effect

**Researcher behavior change:**

Before patch:
- Search `repo:anthropics/claude-code` → official ecosystem only
- r/ClaudeAI, r/Anthropic → miss r/ClaudeCode community threads
- Skip community projects (not in search hints)

After patch:
- Phase 1: Official ecosystem (50% time) — mapped jak wcześniej
- **Phase 2: Community ecosystem (50% time):**
  - Szukaj "Open Claw", "Ralph" nazwami
  - Broad GitHub search (nie tylko anthropics/ org)
  - r/ClaudeCode, Twitter, HN — community buzz
  - Awesome-lists, independent projects

**Results quality:**
- ✓ Official coverage preserved (marketplace, vendor docs)
- ✓ Community experiments surfaced (Open Claw, Ralph, orchestrators)
- ✓ Balanced view (50/50 split explicit)

---

## Test Plan

1. Uruchom research ponownie:
   ```
   claude --agent=claude-code-guide --thoroughness="very thorough" \
     --prompt-file=documents/prompt_engineer/research_prompt_claude_code_extensions.md
   ```

2. Sprawdź results coverage:
   - ✓ Phase 1 results: official marketplace, vendor docs (jak wcześniej)
   - ✓ Phase 2 results: **Open Claw, Ralph, community orchestrators**
   - ✓ r/ClaudeCode threads (powinna być explicit sekcja, nie incidental)

3. Jeśli Open Claw/Ralph **nadal brak:**
   - Sprawdź czy nazwy poprawne ("OpenClaw"? "Ralph AI"? "ralph-claude"?)
   - Sprawdź czy public repos (może private/closed beta)
   - Researcher powinien reportować: "searched for X, not found"

4. Jeśli noise za wysoki:
   - Rozważ zwiększenie evidence threshold dla Phase 2
   - Lub zmniejsz Phase 2 time allocation (40% zamiast 50%)

---

## Risks

1. **Noise increase:**
   - Phase 2 = lower evidence threshold → więcej low-quality results
   - Mitigacja: "prioritize breadth" + Phase structure filtruje naturally

2. **Time cost:**
   - 50/50 split → researcher może spędzić więcej czasu
   - Mitigacja: "15 min per question" cap preserved

3. **Open Claw/Ralph may not exist publicly:**
   - User zna nazwy, ale mogą być private repos lub closed beta
   - Researcher powinien reportować "searched, not found" (nie silent skip)

---

## Meta-Observation

**Pattern discovered:** Research prompts mogą zawierać **implicit bias through search hints**.

Prompt mówi "accept weak evidence" (broad mission), ale search hints zawężają do official sources (narrow execution).

**Transferable rule:**
Gdy research prompt ma broad mission ("map landscape", "show what's possible"), search hints powinny być **equally broad**. Jeśli chcesz zawęzić — zmień mission, nie tylko hints.

**Solution pattern:**
Explicit phase structure (official vs community) eliminuje bias i daje researcher jasny context switch.

---

## Files Changed

1. `documents/prompt_engineer/research_prompt_claude_code_extensions.md` (4 patches)

## Commits

Pending — czekam na user approval przed commitem.

---

## Next Steps

User decision:
1. Uruchomić research ponownie z patchowanym promptem?
2. Commit zmian teraz, research później?
3. Zweryfikować nazwy (Open Claw, Ralph) przed researchem?
