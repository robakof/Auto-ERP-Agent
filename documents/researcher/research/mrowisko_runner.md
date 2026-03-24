# Research: Mrowisko Runner — weryfikacja podejścia

Źródło wymagań: `research_prompt_mrowisko_runner.md`.

Data weryfikacji: 2026-03-17

---

## TL;DR

**Rekomendacja:** podejście **CLI subprocess jest sensowne jako v1 runnera**, jeśli priorytetem są:
- live output w terminalu,
- reużycie istniejącego kontekstu projektu (`CLAUDE.md`, `.claude/settings.json`, skills, MCP),
- prostota wdrożenia.

Ale są trzy ważne zastrzeżenia:

1. **Nie opierałbym runnera na `claude --print < tmp/runner_prompt.md` jako głównym interfejsie promptu.** Oficjalnie udokumentowane wzorce to `claude -p "query"` oraz `cat file | claude -p "query"`. Nie znalazłem oficjalnego przykładu ani gwarancji, że „goły stdin redirect bez pozycyjnego promptu” jest wspieranym kontraktem API CLI. Lepiej przekazywać prompt jawnie jako argument (`-p "..."`) albo przejść na Agent SDK.

2. **Do live streamingu najlepszy jest `--output-format stream-json` + `--verbose` + `--include-partial-messages`.** `text` jest najprostszy dla człowieka, ale nie daje najlepszego kontraktu dla runnera.

3. **Jeśli runner ma dostać bardziej zaawansowane sterowanie** (callbacki uprawnień, przerywanie, pełna kontrola nad sesją, strukturalne eventy, lepsza obsługa długich promptów), to **Anthropic Agent SDK** jest mocniejszym wyborem niż goły subprocess CLI.

Moja praktyczna rekomendacja:
- **v1 / POC:** CLI subprocess, ale na `claude -p ... --output-format stream-json`.
- **v2 / production-ish orchestrator:** Agent SDK (Python/TS), z jawnie ustawionym ładowaniem projektowego kontekstu.
- **Nie stawiałbym dziś produkcji na built-in Agent Teams**, bo są **eksperymentalne** i dokumentacja sama mówi o ograniczeniach.

---

## 1. Claude Code CLI — subprocess invocation

### 1.1 Czy `claude --print < plik` poprawnie inicjalizuje projekt (CLAUDE.md, hooks)?

### Wniosek
**Częściowo tak, ale proponowana forma wywołania jest ryzykowna.**

- Oficjalna dokumentacja mówi, że `-p` / `--print` uruchamia Claude Code „programmatically”, a **„all CLI options work the same way”** jak w zwykłym CLI. To jest mocny sygnał, że print mode korzysta z tego samego agent loop, toolingu i context management.
  - Docs: https://code.claude.com/docs/en/headless
  - Docs: https://platform.claude.com/docs/en/agent-sdk/overview

- Claude Code w katalogu projektu ma dostęp do:
  - plików projektu,
  - `CLAUDE.md`,
  - skills, MCP, subagentów itd.
  - Docs: https://code.claude.com/docs/en/how-claude-code-works

- `CLAUDE.md` jest ładowany **na starcie każdej sesji**; hooks reference ma nawet osobny event `InstructionsLoaded`, który odpala się, gdy `CLAUDE.md` jest ładowany do kontekstu, w tym z `load_reason: "session_start"`.
  - Docs: https://code.claude.com/docs/en/best-practices
  - Docs: https://code.claude.com/docs/en/hooks

- `SessionStart` hooks również odpalają się na starcie sesji (`source: startup`).
  - Docs: https://code.claude.com/docs/en/hooks

**Natomiast:** istnieje też specjalny mechanizm `--init` / `--init-only`, opisany jako **„Run initialization hooks”**. To sugeruje, że jeśli przez „inicjalizuje projekt” rozumiecie **specjalne initialization hooks**, to one **nie są częścią zwykłego `-p` startupu**.
- Docs: https://code.claude.com/docs/en/cli-reference

### Praktyczna interpretacja
- **Tak:** normalny projektowy kontekst (`CLAUDE.md`, settings, zwykłe session hooks) powinien działać w `-p`.
- **Nie zakładałbym:** że `claude --print < file` to wspierany sposób przekazania *głównego promptu*.
- **Nie mieszałbym:** zwykłego session startup z `--init` / initialization hooks.

### Zalecenie
Zamiast:

```bash
claude --print --output-format text < tmp/runner_prompt.md
```

użyłbym jednego z dwóch wzorców:

1. **Udokumentowany CLI pattern**
```bash
cat tmp/context.md | claude -p "Wykonaj zadanie opisane w stdin" --output-format stream-json --verbose --include-partial-messages
```

2. **Runner czyta plik i przekazuje prompt jawnie**
```python
subprocess.Popen([
    "claude",
    "-p",
    prompt_text,
    "--output-format", "stream-json",
    "--verbose",
    "--include-partial-messages",
])
```

Drugi wariant daje czytelniejszy kontrakt niż poleganie na shell redirection jako „prompt API”.

---

### 1.2 Czy subprocess otrzymuje dostęp do ustawień projektu (`.claude/settings.json`)?

### Wniosek
**Tak, w CLI to jest domyślny model pracy projektu.**

Claude Code ma hierarchiczne scope’y konfiguracji:
- user: `~/.claude/settings.json`
- project: `.claude/settings.json`
- local: `.claude/settings.local.json`

Dokumentacja wprost mówi, że project settings są przechowywane w `.claude/settings.json` i dotyczą repozytorium, a `CLAUDE.md` oraz hooks/settings należą do scope’u projektu.
- Docs: https://code.claude.com/docs/en/settings
- Docs: https://code.claude.com/docs/en/vs-code

Dodatkowo CLI ma flagę:
- `--setting-sources user,project,local`
- `--settings <path-or-json>`

czyli można sterować tym jawnie.
- Docs: https://code.claude.com/docs/en/cli-reference

### Ważny niuans
To dotyczy **CLI**. W **Agent SDK** jest odwrotnie: jeśli `setting_sources` nie ustawisz, to **SDK domyślnie nie ładuje żadnych filesystem settings**, a żeby załadować `CLAUDE.md`, trzeba uwzględnić `"project"`.
- Docs: https://platform.claude.com/docs/en/agent-sdk/python

To jest bardzo ważny argument „za CLI” na starcie: CLI z definicji lepiej reużywa projektową konfigurację niż SDK ustawione naiwnie.

---

### 1.3 Czy istnieje flaga `--session-id` lub `--parent-session` do śledzenia łańcuchów wywołań?

### Wniosek
- **`--session-id`: tak, istnieje.**
- **`--parent-session`: nie znalazłem.**
- Są też: `--resume`, `--continue`, `--fork-session`, `--name`.

CLI reference:
- `--session-id` — użycie konkretnego UUID sesji
- `--resume` / `--continue` — wznowienie sesji
- `--fork-session` — utworzenie nowej sesji z zachowaniem historii
- `--name` — nazwa sesji widoczna w `/resume`
- Docs: https://code.claude.com/docs/en/cli-reference

### Rekomendacja dla runnera
Jeśli chcecie śledzić drzewo A→B→A:
- **nie liczcie na `--parent-session`**, bo oficjalnie go nie widzę,
- trzymajcie **własny `parent_session_id` / `invocation_id` / `trace_id` w SQLite**,
- sesję Claude’a traktujcie jako *leaf execution context*, nie jako jedyne źródło prawdy o relacjach parent/child.

Dobry wzorzec:
- runner generuje własny `trace_id`
- nadaje childowi `--session-id` albo przechowuje session ID zwrócone przez CLI (`--output-format json`)
- mapuje parent/child we własnej bazie

---

### 1.4 `--output-format text` vs `json` — który daje lepszy live streaming?

### Wniosek
**Najlepszy streaming daje `stream-json`, nie `text` ani zwykły `json`.**

Oficjalnie:
- `text` — plain text
- `json` — pełny strukturalny wynik po zakończeniu / pełny log rozmowy
- `stream-json` — newline-delimited JSON, eventy w czasie rzeczywistym
- `--include-partial-messages` — partial streaming events
- Docs: https://code.claude.com/docs/en/headless
- Docs: https://code.claude.com/docs/en/common-workflows
- Docs: https://code.claude.com/docs/en/cli-reference

Anthropic wręcz podaje wzorzec do token-level streamingu:
```bash
claude -p "Write a poem" --output-format stream-json --verbose --include-partial-messages | \
  jq -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") | .event.delta.text'
```

### Rekomendacja
Dla runnera:
- **UI/UX dla człowieka:** można renderować plain text z eventów,
- **kontrakt integracyjny:** trzymajcie się `stream-json`.

`text` jest wygodny do prostych skryptów, ale nie daje tak dobrego modelu sterowania i parsowania.

---

### 1.5 Czy jest mechanizm `--max-turns` lub `--budget-tokens` do ograniczenia kosztów?

### Wniosek
- **`--max-turns`: tak**
- **`--max-budget-usd`: tak**
- **`--budget-tokens`: nie znalazłem jako flagi CLI**

CLI reference:
- `--max-turns` — limit agentic turns
- `--max-budget-usd` — limit dolarowy dla print mode
- Docs: https://code.claude.com/docs/en/cli-reference

`budget_tokens` istnieje w dokumentacji API/extended thinking, ale to nie jest opisane jako flaga Claude Code CLI.
- Docs: https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking

### Rekomendacja
Minimalny zestaw bezpieczników dla child process:
- `--max-turns`
- `--max-budget-usd`
- zewnętrzny timeout procesu w runnerze
- licznik restartów / retries w SQLite

---

## 2. Live streaming output

### 2.1 Czy subprocess Popen z Claude Code CLI streamuje output line-by-line czy buforuje?

### Wniosek
**Oficjalnie wspierany kontrakt streamingowy to newline-delimited JSON event stream.**

Docs mówią, że `stream-json` zwraca „series of JSON objects in real-time”, a z `--include-partial-messages` można dostać partiale/tokendelta podczas generacji.
- Docs: https://code.claude.com/docs/en/headless
- Docs: https://code.claude.com/docs/en/common-workflows
- Docs: https://code.claude.com/docs/en/cli-reference

To oznacza, że **po stronie runnera najbezpieczniej założyć odczyt liniowy po newline** dla `stream-json`.

### Czego nie udało się potwierdzić wprost
Nie znalazłem w oficjalnych docs gwarancji typu:
- „`text` streamuje line-by-line bez buforowania”
- „CLI ma tryb całkowicie unbuffered na stdout”

Czyli:
- dla `stream-json` mamy **oficjalny real-time protocol**,
- dla `text` nie widzę równie mocnego kontraktu.

---

### 2.2 Czy istnieje flaga wymuszająca unbuffered output?

### Wniosek
**Nie znalazłem oficjalnej flagi „unbuffered output”.**

Najbliższe wspierane mechanizmy to:
- `--output-format stream-json`
- `--verbose`
- `--include-partial-messages`
- Docs: https://code.claude.com/docs/en/headless
- Docs: https://code.claude.com/docs/en/cli-reference

### Rekomendacja
Jeśli chcecie przewidywalny live output:
- nie walczcie z `text` + nieudokumentowanym buforowaniem,
- użyjcie `stream-json` jako protokołu,
- po stronie runnera renderujcie eventy do konsoli.

---

## 3. Multi-agent orchestration best practices

### 3.1 Jakie są znane pułapki przy orchestracji agentów przez subprocess?

Najważniejsze pułapki, które wynikają bezpośrednio z dokumentacji Claude Code:

1. **Równoległe używanie tej samej sesji powoduje interleaving historii.**
   Dokumentacja wprost mówi, że jeśli tę samą sesję wznowisz w wielu terminalach, wiadomości będą się przeplatać.
   - Docs: https://code.claude.com/docs/en/how-claude-code-works

2. **Sesje są związane z katalogiem.**
   Równoległość powinna być rozdzielana katalogami / worktree, a nie tylko branchami w jednym katalogu.
   - Docs: https://code.claude.com/docs/en/how-claude-code-works

3. **Parallel work ma sens tylko przy realnej niezależności zadań.**
   Anthropic podkreśla, że dla zadań sekwencyjnych, same-file edits albo pracy z dużą liczbą zależności lepsza jest jedna sesja lub subagenci, nie pełny team.
   - Docs: https://code.claude.com/docs/en/agent-teams

4. **Token cost skaluje się z liczbą agentów.**
   Każdy agent/team mate ma własne okno kontekstu.
   - Docs: https://code.claude.com/docs/en/agent-teams
   - Docs: https://code.claude.com/docs/en/costs

5. **Zbyt duży `CLAUDE.md` lub zbyt grube prompty zwiększają koszt i szum.**
   Anthropic rekomenduje trzymać `CLAUDE.md` zwięzły i przenosić workflow-specific instrukcje do skills.
   - Docs: https://code.claude.com/docs/en/best-practices
   - Docs: https://code.claude.com/docs/en/costs

6. **Permissions przy `resume` nie wracają automatycznie.**
   Historia wraca, ale session-scoped permissions nie.
   - Docs: https://code.claude.com/docs/en/how-claude-code-works

---

### 3.2 Jak inne projekty rozwiązują problem pętli wywołań (A→B→A)?

Nie znalazłem w docs Claude Code jednego „loop breaker” dla własnych subprocess runnerów, ale z dokumentacji wynikają dobre praktyki:

- **Używaj świeżych child sessions zamiast współdzielenia tej samej sesji.**
- **Przechowuj parent/child relation poza Claude Code** (np. SQLite), bo CLI nie daje `--parent-session`.
- **Rozdziel typy delegacji:**
  - *subagents* — gdy worker ma wykonać skupione zadanie i zwrócić wynik,
  - *agent teams* — gdy workerzy mają rozmawiać między sobą.
- **Model task graph, nie free-form call graph.** Dokumentacja agent teams pokazuje shared task list + dependencies zamiast dowolnych recursive summons.
  - Docs: https://code.claude.com/docs/en/agent-teams
  - Docs: https://code.claude.com/docs/en/sub-agents

### Moja rekomendacja architektoniczna
Własny runner powinien mieć twarde reguły:
- `max_depth`
- `max_children_per_task`
- zakaz bezpośredniego „call parent” bez pośrednictwa mailbox/inbox
- status tasków typu `pending / running / done / blocked / failed`
- edge’y DAG zamiast dowolnych rekurencyjnych wywołań

Czyli: **modelujcie koordynację jak workflow, nie jak otwartą konwersację agentów bez granic.**

---

### 3.3 Czy są lepsze wzorce niż plik tymczasowy do przekazania kontekstu agentowi?

### Tak — i są lepsze z kilku powodów.

1. **Stały kontekst projektu przenieść do `CLAUDE.md` / skills / hooks**
   - `CLAUDE.md` dla reguł globalnych,
   - skills dla workflow-specific instrukcji ładowanych on-demand,
   - hooks dla deterministycznych akcji.
   - Docs: https://code.claude.com/docs/en/best-practices
   - Docs: https://code.claude.com/docs/en/skills
   - Docs: https://code.claude.com/docs/en/hooks-guide

2. **Task-specific prompt przekazywać jawnie jako prompt sesji**
   - CLI: `claude -p "..."`
   - SDK: `prompt="..."` jako string lub stream
   - Docs: https://code.claude.com/docs/en/headless
   - Docs: https://platform.claude.com/docs/en/agent-sdk/python

3. **Duże dane wejściowe przesyłać przez stdin jako payload pomocniczy, nie jako jedyny prompt contract**
   Oficjalny wzorzec to `cat file | claude -p "query"`.
   - Docs: https://code.claude.com/docs/en/cli-reference

4. **Bardzo duży / dynamiczny kontekst streszczać przed wejściem do modelu**
   Anthropic wprost rekomenduje „offload processing to hooks and skills”, żeby nie wrzucać surowych dużych payloadów do kontekstu.
   - Docs: https://code.claude.com/docs/en/costs

### W praktyce dla Mrowiska
Najlepszy podział:
- **projektowe zasady:** `CLAUDE.md`
- **procedury runnera / role agentów:** skills lub predefiniowane agenty
- **pojedyncze zadanie:** prompt string
- **duże payloady / logi / artefakty:** stdin albo pliki robocze, ale jako *dane*, nie jako główna semantyka promptu

---

### 3.4 Jak zarządzać równoległymi wywołaniami?

### Rekomendacja
1. **Izolacja przez katalog / git worktree**
   Claude Code samo rekomenduje worktree do równoległych sesji.
   - Docs: https://code.claude.com/docs/en/how-claude-code-works
   - Docs: https://code.claude.com/docs/en/cli-reference
   - Docs: https://code.claude.com/docs/en/vs-code

2. **Nie współdzielić session ID między workerami**
   Jeśli chcesz wspólny punkt startu, użyj `--fork-session`, nie `--resume` w kilku procesach.
   - Docs: https://code.claude.com/docs/en/how-claude-code-works

3. **Równoległość tylko dla zadań z małą liczbą zależności i bez wspólnych plików**
   - Docs: https://code.claude.com/docs/en/agent-teams

4. **Na start ogranicz liczbę workerów**
   Anthropic dla agent teams sugeruje zwykle 3–5 teammates; dla własnego runnera to też rozsądny punkt wyjścia.
   - Docs: https://code.claude.com/docs/en/agent-teams

5. **Zadbaj o ownership plików**
   Dwa agenty dotykające tego samego pliku to proszenie się o conflict/overwrite.
   - Docs: https://code.claude.com/docs/en/agent-teams

---

## 4. Bezpieczeństwo i kontrola

### 4.1 Jak ograniczyć co agent może zrobić w subprocess (uprawnienia, scope)?

### Najmocniejsze warstwy kontroli w Claude Code

1. **Restrict tools na wejściu sesji**
- `--tools` — ogranicza listę dostępnych wbudowanych tooli
- `--disallowedTools` — usuwa wybrane toole z kontekstu
- `--allowedTools` — auto-approves wybrane toole / reguły
- Docs: https://code.claude.com/docs/en/cli-reference

2. **Permission rules w settings**
- `permissions.allow`
- `permissions.deny`
- matcher syntax typu `Bash(npm run *)`, `Read(./.env)` itd.
- Docs: https://code.claude.com/docs/en/permissions
- Docs: https://code.claude.com/docs/en/settings

3. **Permission modes**
- `default`
- `acceptEdits`
- `plan`
- `dontAsk`
- `bypassPermissions`
- Docs: https://code.claude.com/docs/en/permissions

4. **Sandboxing (OS-level)**
- sandbox filesystem boundaries,
- `allowWrite`, `denyWrite`, `denyRead`,
- network restrictions,
- możliwość wyłączenia escape hatch przez `allowUnsandboxedCommands: false`
- Docs: https://code.claude.com/docs/en/sandboxing

5. **Hooks jako policy enforcement**
- `PreToolUse` może `allow` / `deny` / `ask`
- `PermissionRequest` może zatwierdzić lub zablokować w imieniu użytkownika
- można walidować komendy, URL-e, tool inputs
- Docs: https://code.claude.com/docs/en/hooks
- Docs: https://code.claude.com/docs/en/hooks-guide

### Moja rekomendacja minimalna dla runnera
Dla child subprocess uruchamianych autonomicznie:
- `--tools "Read,Grep,Glob"` dla agentów badawczych
- `--permission-mode plan` dla analizatorów
- sandbox włączony dla agentów, którzy mają wykonywać Bash
- twarde deny na sekrety (`Read(./.env)`, `Read(./secrets/**)`) w `.claude/settings.json`
- `PreToolUse` hook blokujący destrukcyjne komendy i nieautoryzowane wyjścia sieciowe

---

### 4.2 Czy Claude Code ma wbudowany mechanizm `--allow-tools` do whitelistowania narzędzi?

### Wniosek
**Tak, ale nazwa flagi to `--allowedTools`, nie `--allow-tools`.**

Dodatkowo:
- jeśli chcesz **ograniczyć, jakie toole w ogóle są dostępne**, użyj `--tools`
- jeśli chcesz auto-approve tylko niektóre użycia, użyj `--allowedTools`

Docs:
- https://code.claude.com/docs/en/cli-reference
- https://code.claude.com/docs/en/headless

To ważne rozróżnienie:
- `--tools` = *capability boundary*
- `--allowedTools` = *approval shortcut*

Dla bezpieczeństwa runnera ważniejsze jest zwykle **`--tools` + sandbox + deny rules**, a nie samo `--allowedTools`.

---

### 4.3 Jak wykrywać i przerywać runaway agents (nieskończona pętla, nadmierne koszty)?

### W praktyce trzeba połączyć kilka mechanizmów

1. **Budżety w CLI**
- `--max-turns`
- `--max-budget-usd`
- Docs: https://code.claude.com/docs/en/cli-reference

2. **Wall-clock timeout w runnerze**
- subprocess timeout
- SIGTERM / kill po przekroczeniu czasu
- to nie jest funkcja Claude Code, tylko waszego supervisora

3. **Monitoring kosztu i czasu**
- `/cost`
- status line z polami kosztu i duration
- OpenTelemetry / monitoring usage
- Docs: https://code.claude.com/docs/en/costs
- Docs: https://code.claude.com/docs/en/statusline
- Docs: https://code.claude.com/docs/en/monitoring-usage

4. **Detekcja strukturalna po stronie runnera**
- max depth
- max retries
- max children
- loop detection po `(task_type, payload_hash, ancestor_set)`

5. **Hooks / policy**
- `PreToolUse` i `PermissionRequest` jako guardrails
- Docs: https://code.claude.com/docs/en/hooks

### Jeśli przejdziecie na Agent SDK
SDK daje dodatkowo:
- `interrupt()`
- callback `can_use_tool`
- streaming message objects
- własne hooki i kontrolę nad sandboxem
- Docs: https://platform.claude.com/docs/en/agent-sdk/python

To jest jeden z najmocniejszych argumentów za SDK w kolejnej fazie.

---

## 5. Alternatywy do rozważenia

### 5.1 Czy Anthropic Agent SDK jest lepszym wyborem niż CLI subprocess dla tego przypadku?

### Krótka odpowiedź
**Dziś: niekoniecznie na start. Docelowo: bardzo możliwe, że tak.**

### Kiedy CLI subprocess wygrywa
CLI jest lepsze, jeśli zależy wam przede wszystkim na:
- prostocie,
- terminal-first UX,
- maksymalnym podobieństwie do „jak pracuje człowiek w Claude Code”,
- reużyciu projektowego kontekstu bez dodatkowego kodu.

CLI/print mode jest oficjalnie wspierane jako programmatic usage / headless mode.
- Docs: https://code.claude.com/docs/en/headless

### Kiedy Agent SDK wygrywa
SDK wygrywa, jeśli potrzebujecie:
- pełnego streamingu jako obiektów wiadomości,
- callbacków uprawnień (`can_use_tool`),
- `interrupt()` / lepszego lifecycle control,
- własnego transportu,
- natywnego API dla sesji i wiadomości,
- bardziej przewidywalnego kontraktu niż parsowanie stdout procesu.

Docs:
- https://platform.claude.com/docs/en/agent-sdk/overview
- https://platform.claude.com/docs/en/agent-sdk/python

### Krytyczny niuans SDK
Żeby SDK zachowywało się „jak Claude Code”, trzeba uważać:
- `setting_sources` domyślnie = **brak filesystem settings**
- trzeba dodać `"project"`, żeby ładować `CLAUDE.md`
- warto użyć preset system prompt `claude_code`
- Docs: https://platform.claude.com/docs/en/agent-sdk/python

### Finalna rekomendacja
- **Jeśli celem jest szybkie uruchomienie runnera:** zaczynajcie od CLI subprocess.
- **Jeśli celem jest trwały orchestrator z kontrolą i audytem:** planujcie migrację do SDK wcześniej, niż później.

---

### 5.2 Czy istnieją gotowe orchestration frameworks warte rozważenia vs własna implementacja?

### LangGraph
Najmocniejsze strony wg oficjalnych docs:
- durable execution,
- streaming,
- human-in-the-loop,
- persistence,
- production-ready deployment.
- Docs: https://docs.langchain.com/oss/python/langgraph/overview
- Docs: https://docs.langchain.com/oss/python/langchain/human-in-the-loop

**Kiedy warto:**
- gdy chcecie workflow engine / state machine,
- gdy potrzebujecie wznawiania po awarii,
- gdy ważne są checkpointy, approval gates, trwały stan.

### CrewAI
Oficjalnie pozycjonuje się jako framework do:
- collaborative agents,
- crews + flows,
- guardrails,
- memory,
- knowledge,
- observability.
- Docs: https://docs.crewai.com/

**Kiedy warto:**
- gdy chcecie wyższy poziom abstrakcji i szybkie składanie multi-agent workflow,
- gdy mniej zależy wam na natywnym „Claude Code project UX”, a bardziej na frameworkowym runtime.

### Moja ocena dla Mrowiska
Na dziś:
- **LangGraph** jest najbardziej sensowną „poważną alternatywą” dla własnego orchestration layer, jeśli potrzebujecie trwałego workflow runtime.
- **CrewAI** wygląda sensownie, ale to już większy frameworkowy skok i słabiej odpowiada na wasz priorytet „reuse existing Claude Code project config”.
- **Własny runner + Claude Code CLI/SDK** nadal wydaje się najbardziej spójny z waszymi celami.

---

## Co oficjalnie już istnieje w Claude Code i może zmienić decyzję

### 1. Subagents
Claude Code ma wbudowane subagenty z osobnym context window, własnymi tool restrictions i niezależnymi permissions.
- Docs: https://code.claude.com/docs/en/sub-agents

To oznacza, że część przypadków „spawn child agent” może dać się zrobić **bez osobnego subprocess orchestration**.

### 2. Agent Teams
Claude Code ma też **Agent Teams**, ale:
- są **experimental**,
- są **disabled by default**,
- mają znane ograniczenia dot. session resumption, coordination i shutdown behavior.
- Docs: https://code.claude.com/docs/en/agent-teams

**Wniosek:** traktowałbym je jako inspirację / benchmark architektoniczny, nie jako fundament produkcyjnego systemu.

### 3. Worktrees
Claude Code wspiera `--worktree`, co jest bardzo dobrym wzorcem dla bezpiecznej równoległości.
- Docs: https://code.claude.com/docs/en/cli-reference
- Docs: https://code.claude.com/docs/en/how-claude-code-works

---

## Lista pułapek, których warto unikać

1. **Nie używaj tej samej sesji równolegle w wielu subprocessach.**
   Grozi interleavingiem historii.

2. **Nie opieraj publicznego kontraktu runnera na `claude -p < file` bez pozycyjnego promptu.**
   To nie jest wzorzec pokazany w docs.

3. **Nie dawaj agentom równoległej edycji tych samych plików.**
   Rozdziel ownership plików albo użyj worktree.

4. **Nie polegaj wyłącznie na `--allowedTools`.**
   To nie zastępuje `--tools`, deny rules i sandboxa.

5. **Nie zakładaj, że resume przywróci permissions.**
   Historia wraca, permissions nie.

6. **Nie pakuj wszystkiego do `CLAUDE.md`.**
   Trzymaj go krótko, a specjalistyczne workflow przenoś do skills.

7. **Nie używaj built-in Agent Teams jako jedynego planu na produkcję.**
   Są eksperymentalne.

8. **Nie próbuj robić „nieskończonej autonomii” bez twardych limitów.**
   Max turns, max budget, wall-clock timeout, max depth, loop detection są obowiązkowe.

---

## Rekomendowana architektura dla Mrowiska

### Etap 1 — pragmatyczny start
**Wybór: Claude Code CLI subprocess**

- runner uruchamia child process per task
- każdy child ma osobny `session_id`
- prompt przekazywany jawnie (nie przez gołe `< file`)
- output: `stream-json`
- budżety: `--max-turns`, `--max-budget-usd`
- narzędzia ograniczone przez `--tools` / project settings / sandbox
- task lineage, retries, loop detection trzymane w SQLite

### Sugerowany kontrakt procesu
```bash
claude -p "$TASK_PROMPT" \
  --output-format stream-json \
  --verbose \
  --include-partial-messages \
  --max-turns 8 \
  --max-budget-usd 1.50 \
  --setting-sources user,project \
  --tools "Read,Grep,Glob,Bash" \
  --allowedTools "Read,Grep,Glob"
```

Dla agentów stricte analitycznych:
```bash
claude -p "$TASK_PROMPT" \
  --output-format stream-json \
  --verbose \
  --include-partial-messages \
  --permission-mode plan \
  --tools "Read,Grep,Glob"
```

### Etap 2 — gdy zacznie boleć sterowanie
**Migracja do Agent SDK**

Powody migracji:
- lepszy streaming API,
- możliwość `interrupt()`,
- callbacki uprawnień,
- dokładniejsza kontrola sesji,
- mniej hackowania wokół stdout/stderr subprocessa.

### Etap 3 — tylko jeśli naprawdę będzie potrzebne
**LangGraph lub inny workflow runtime**

Dopiero kiedy potrzebujecie:
- trwałego stanu kroków,
- checkpointów,
- human approval gates,
- wznowienia po awarii na poziomie workflow, nie tylko pojedynczego child process.

---

## Finalna odpowiedź na pytanie „czy coś nam umyka?”

### Tak — trzy rzeczy są łatwe do przeoczenia

1. **`claude -p` jest wspierane, ale wasz konkretny sposób z `< tmp/runner_prompt.md` nie jest dobrze udokumentowany.**
   To najważniejsza rzecz do poprawy od razu.

2. **Claude Code ma już własne mechanizmy delegacji (subagents, agent teams, worktrees).**
   Nawet jeśli nie chcecie ich używać bezpośrednio, warto projektować runner tak, by nie walczył z tymi natywnymi modelami.

3. **Agent SDK jest dużo bliżej „production orchestrator substrate”, niż może się wydawać.**
   CLI jest świetne na start, ale gdy tylko zaczniecie potrzebować callbacków, approval flow i porządnego sterowania sesjami, SDK prawdopodobnie okaże się naturalnym kolejnym krokiem.

---

## Ostateczna rekomendacja

**Tak — CLI subprocess to właściwe podejście na start.**

Ale w wersji skorygowanej:
- **nie**: `claude --print < tmp/runner_prompt.md`
- **tak**: `claude -p "$prompt" --output-format stream-json ...`
- **tak**: limity kosztu/turnów + sandbox + tool restrictions + hooks
- **tak**: osobne sesje per child, własny tracing parent/child w SQLite
- **tak**: worktree dla równoległych agentów piszących kod

**A czego bym nie zrobił:**
- nie budowałbym od razu dużej własnej warstwy multi-agent conversation routing bez twardego DAG/task modelu,
- nie opierałbym production strategy na experimental Agent Teams,
- nie odkładałbym planu migracji do SDK, jeśli runner ma szybko zyskać bardziej zaawansowaną autonomię.

---

## Linki do kluczowej dokumentacji

### Anthropic / Claude Code
- Programmatic usage / headless: https://code.claude.com/docs/en/headless
- CLI reference: https://code.claude.com/docs/en/cli-reference
- Settings: https://code.claude.com/docs/en/settings
- How Claude Code works: https://code.claude.com/docs/en/how-claude-code-works
- Best practices: https://code.claude.com/docs/en/best-practices
- Hooks guide: https://code.claude.com/docs/en/hooks-guide
- Hooks reference: https://code.claude.com/docs/en/hooks
- Permissions: https://code.claude.com/docs/en/permissions
- Sandboxing: https://code.claude.com/docs/en/sandboxing
- Subagents: https://code.claude.com/docs/en/sub-agents
- Agent teams: https://code.claude.com/docs/en/agent-teams
- Costs: https://code.claude.com/docs/en/costs
- Monitoring / OTel: https://code.claude.com/docs/en/monitoring-usage
- Status line: https://code.claude.com/docs/en/statusline

### Anthropic Agent SDK
- Overview: https://platform.claude.com/docs/en/agent-sdk/overview
- Python reference: https://platform.claude.com/docs/en/agent-sdk/python

### Frameworks alternatywne
- LangGraph overview: https://docs.langchain.com/oss/python/langgraph/overview
- LangChain overview (positioning vs LangGraph): https://docs.langchain.com/oss/python/langchain/overview
- LangChain Human-in-the-loop: https://docs.langchain.com/oss/python/langchain/human-in-the-loop
- CrewAI docs: https://docs.crewai.com/
