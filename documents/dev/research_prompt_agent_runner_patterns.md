# Research Prompt: Wzorce projektowe dla runnera agentów Claude Code

## Kontekst

Szukam wzorców dla systemu uruchamiania agentów AI opartych na Claude Code CLI.

System ma spełniać następujące właściwości:

1. **Człowiek jako uczestnik** — człowiek ma dostęp do wiersza poleceń tak samo jak agent.
   Może wejść do dowolnej sesji agenta, zobaczyć co robi i wziąć udział w jego pracy.
   Nie jest "operatorem z zewnątrz" — jest pełnoprawnym uczestnikiem na tym samym poziomie.

2. **Komunikacja agent-agent** — agenci mogą wysyłać sobie wiadomości i zlecać zadania.
   Agent A może wywołać agenta B z konkretnym zadaniem i czekać na wynik lub działać asynchronicznie.

3. **Multiplikacja ról** — może istnieć wielu agentów tej samej roli (np. 3x ERP Specialist).
   System musi rozróżniać konkretne instancje (nie tylko rolę) i kierować komunikację
   do właściwej instancji lub do całej grupy danej roli.

4. **Pełny podgląd** — człowiek widzi co robi każdy agent: aktualny task, status, historię.
   Niekoniecznie wszystko naraz, ale ma do tego dostęp na żądanie.

5. **CLI-native** — każdy agent to sesja Claude Code w osobnym wierszu poleceń.
   Nie szukamy rozwiązań wymagających przepisania agentów na API (headless).

## Pytania badawcze

### P1: Wzorce identyfikacji instancji agenta przy multiplikacji ról
Jak odróżnić dwa agenty o tej samej roli?
- Czy Claude Code `--session-id`, `--name` lub inne flagi CLI pozwalają na unikalną identyfikację?
- Jakie wzorce nazewnictwa instancji stosują systemy multi-agent (np. `erp_specialist_01`, `erp_specialist_az`)?
- Jak routing wiadomości działa gdy odbiorca to "dowolny wolny agent roli X" vs "konkretna instancja"?
- Wzorce: actor model (Erlang/Akka), worker pool, named pipes.

### P2: Wzorce komunikacji agent-agent przez CLI
Jak agenci uruchomieni jako osobne procesy CLI mogą komunikować się ze sobą?
- Shared file / shared DB (np. SQLite) — agent zapisuje wiadomość, drugi odczytuje przy następnym turnie
- Unix pipes / named pipes między procesami
- Message queue (Redis, RabbitMQ, SQLite-based kolejka)
- HTTP/REST między agentami (każdy agent wystawia lokalny endpoint)
- Wzorzec "inbox polling" vs "push notification" do procesu agenta
Która metoda działa najlepiej z Claude Code (który sam jest procesem CLI z interaktywnym promptem)?

### P3: Wzorzec "człowiek jako uczestnik" — human-in-the-loop na poziomie CLI
Jak zaprojektować system gdzie człowiek może wejść do sesji agenta i uczestniczyć?
- `tmux attach` / `screen -r` — dołączenie do istniejącej sesji terminala
- Claude Code `--resume <session_id>` — czy pozwala na przejęcie/podgląd sesji?
- Wzorzec "shared terminal" (np. tmate, ttyd) dla zdalnego podglądu
- Czy Claude Code ma tryb "observer" lub "co-pilot" gdzie człowiek widzi i może interweniować?
- Jak odróżnić input człowieka od inputu orchestratora w tym samym terminalu?

### P4: Wzorzec orchestratora — kto zarządza pulą agentów
Czy potrzebny jest centralny orchestrator, czy agenci są peer-to-peer?
- Orchestrator jako osobna sesja Claude Code: przydziela zadania, monitoruje statusy
- Peer-to-peer: agenci sami negocjują zadania przez shared queue
- Hybrydowy: orchestrator przydziela, agenci raportują przez wspólną magistralę
Jakie wzorce stosują istniejące systemy (AutoGen, CrewAI, LangGraph) przy CLI-based agents?
Czy Anthropic ma oficjalny wzorzec dla "agent swarm" przy użyciu Claude Code?

### P5: Widoczność i podgląd — wzorce monitorowania pracy agentów
Jak człowiek może mieć pełen podgląd do pracy wielu agentów bez zakłócania ich pracy?
- Wzorzec "structured log" — każdy agent zapisuje strukturalny log (JSON) do wspólnego miejsca
- Wzorzec "event bus" — agenci emitują zdarzenia (task_started, tool_used, task_done)
- Wzorzec "status file" — każdy agent trzyma aktualny stan w pliku (odczyt na żądanie)
- Dedykowane narzędzia: czy istnieją dashboardy zaprojektowane pod Claude Code multi-agent?
- Integracja z Claude Code hooks (`PostToolUse`, `Stop`, `Notification`) jako źródło zdarzeń

### P6: Wzorce wdrożeń w produkcji (case studies)
Czy istnieją publiczne implementacje systemu agentów Claude Code lub podobnych narzędzi
spełniających powyższe właściwości?
Sprawdź: GitHub (claude-code + multi-agent, agent swarm, agent runner),
blogi inżynieryjne (2024-2025), Anthropic cookbook, case studies firm.
Co działa w praktyce przy 5-10 równoległych agentach CLI?

## Output contract

Wyniki zapisz do: `documents/dev/research_results_agent_runner_patterns.md`

Struktura:
```
## TL;DR — 3-5 wzorców godnych prototypu (z uzasadnieniem)

## P1: Identyfikacja instancji przy multiplikacji ról

## P2: Komunikacja agent-agent przez CLI

## P3: Człowiek jako uczestnik — human-in-the-loop

## P4: Orchestrator vs peer-to-peer

## P5: Widoczność i podgląd pracy agentów

## P6: Wdrożenia produkcyjne — case studies

## Otwarte pytania
```

Dla każdego wzorca: nazwa, opis, wady/zalety, siła dowodów (wysoka/średnia/niska), źródła.
Bez oceny dopasowania do konkretnego projektu — tylko wzorce i fakty.
