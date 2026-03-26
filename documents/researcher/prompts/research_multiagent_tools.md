# Research Prompt: Narzędzia do pracy wieloagentowej (GUI-first)

## Kontekst

Użytkownik prowadzi projekt z wieloma autonomicznymi agentami LLM (Claude Code).
Obecne środowisko: VS Code + terminale. Problem: brak widoczności statusu agentów,
brak orkiestracji, praca czysto terminalowa jest niewygodna przy skali 3+ agentów.

Cel researchu: znaleźć narzędzia i platformy zaprojektowane z myślą o pracy
z wieloma agentami LLM jednocześnie — ze szczególnym uwzględnieniem rozwiązań GUI,
nie CLI/terminal-first.

## Pytania badawcze

### P1: Google Antigravity
Co to jest Google Antigravity? Czy istnieje produkt o tej nazwie?
Sprawdź: oficjalna strona, GitHub, dokumentacja, artykuły techniczne, Product Hunt.
Jeśli istnieje — opisz: czym jest, jak działa multi-agent management, dostępność (beta/GA),
czy działa na Windows, koszt, połączenie z Claude/Gemini/OpenAI.
Jeśli nie istnieje lub nie możesz potwierdzić — napisz wprost.

### P2: IDE i edytory "agent-first" (2024-2025)
Które edytory/IDE zostały zaprojektowane lub znacząco rozbudowane z myślą o pracy z agentami AI?
Sprawdź: Cursor, Windsurf (Codeium), Zed, GitHub Copilot Workspace, Google Project IDX,
JetBrains AI, Replit Agent, Devin (Cognition), SWE-agent GUI, OpenHands (OpenDevin).
Dla każdego: czy obsługuje wiele agentów równolegle? Czy ma widok statusu? Integracja z Claude?

### P3: Dedykowane platformy orkiestracji agentów LLM
Czy istnieją platformy zaprojektowane specjalnie do orkiestracji wielu agentów LLM
z interfejsem graficznym (nie tylko API)?
Sprawdź: LangGraph Studio, CrewAI UI, AutoGen Studio, AgentOps, Langfuse, Helicone,
AgentBench, inne dashboardy monitorujące agenty.
Kryteria: widok statusu agentów live, możliwość interwencji, integracja z Claude Code.

### P4: Wzorce wieloagentowe w 2025 — co faktycznie używają deweloperzy
Jakie środowiska i wzorce pracy z wieloma agentami są najpopularniejsze w 2025?
Sprawdź: ankiety, wpisy na HN, Reddit r/ClaudeAI, r/LocalLLaMA, X/Twitter wątki od
praktyków (nie marketerów). Co faktycznie działa przy 5-10 równoległych agentach?

### P5: Claude Code — oficjalne wzorce multi-agent (Anthropic)
Co Anthropic oficjalnie rekomenduje dla pracy z wieloma agentami Claude Code?
Sprawdź: dokumentacja claude.ai/docs, blogi Anthropic, GitHub anthropics/claude-code.
Czy istnieje oficjalny GUI do zarządzania agentami? Czy Claude Code ma roadmapę w tym kierunku?

## Output contract

Wyniki zapisz do: `documents/dev/research_results_multiagent_tools.md`

Struktura:
```
## TL;DR — top rekomendacje (max 5, z uzasadnieniem)

## P1: Google Antigravity — weryfikacja

## P2: IDE agent-first — porównanie

## P3: Platformy orkiestracji z GUI

## P4: Wzorce wieloagentowe 2025 — co faktycznie działa

## P5: Anthropic — oficjalne podejście multi-agent

## Otwarte pytania
```

Dla każdego narzędzia: nazwa, URL, krótki opis, siła dowodów (wysoka/średnia/niska),
czy działa na Windows, integracja z Claude. Bez oceny dopasowania do konkretnego projektu.
