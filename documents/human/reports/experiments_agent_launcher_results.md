# Wyniki eksperymentów: Agent Launcher

*Data: 2026-03-26*
*Wykonawca: Developer (sesja f99e2d360558)*
*Plan: `documents/human/plans/EXPERIMENTS_agent_launcher.md`*
*PRD: `documents/human/plans/PRD_agent_launcher.md`*
*Status: ZAKONCZONE*

---

## Executive Summary

| Eksperyment | Status | Wynik kluczowy |
|---|---|---|
| **E-01: Spawn interaktywny** | DONE | Wariant A (`--append-system-prompt`) = rekomendowany. `-p` = NIE interaktywne. |
| **E-04: Terminal API** | DONE | `TerminalLocation.Editor` dziala. sendText OK. Brak odczytu outputu (hooks = jedyny kanal). |
| **E-03: Lifecycle hooks** | DONE | 23 typow hookow. Stop + SessionEnd pokrywaja lifecycle. Brak idle detection. |
| **E-02: Multi-window** | DONE | Hipoteza potwierdzona: terminals per-window, wspoldzielony stan = mrowisko.db. |

**Kluczowe odkrycie:** Claude Code ma 23 typow hookow (nie 4), w tym `SessionStart`, `SessionEnd`, `SubagentStart`, `SubagentStop` -- znacznie wiecej niz zakladal PRD.

---

## E-01: Interaktywna sesja z wstrzyknietym kontekstem

### Metoda
Analiza `claude --help` + dokumentacja Claude Code (hooks reference, CLI reference, permission modes).

### Wyniki per wariant

| # | Komenda | Interaktywne? | CLAUDE.md? | Hooki? | Uwagi |
|---|---------|:---:|:---:|:---:|---|
| **A** | `claude --append-system-prompt "..."` | **TAK** | TAK | TAK | **REKOMENDOWANY.** Dodaje do default system prompt bez zastepowania. |
| **B** | `claude -p "..."` | **NIE** | TAK | TAK | `-p` = "Print response and exit". Nie daje interaktywnosci. |
| **C** | `claude` (baseline) | TAK | TAK | TAK | Normalna sesja interaktywna — pelne CLI. |
| **D** | `claude --system-prompt "..."` | **TAK** | TAK | TAK | Zastepuje default system prompt, ale CLAUDE.md laduje sie niezaleznie. |
| **E** | `claude --resume <session_id>` | **TAK** | TAK | TAK | Mozna wznowic w innym terminalu. Akceptuje session_id lub name. |

### Dodatkowe flagi przydatne dla Agent Launcher

| Flaga | Zastosowanie |
|---|---|
| `--session-id <uuid>` | Ustawia UUID nowej sesji — **idealny do registry tracking** (znamy ID przed spawnem). |
| `--name <name>` | Nazwa wyswietlana w `/resume` i terminal title. Mozna tez wznowic po nazwie. |
| `--permission-mode <mode>` | Kontrola poziomu autonomii spawned agenta. |
| `--fork-session` | Przy `--resume` — tworzy nowa sesje zamiast kontynuowac stara. |
| `--bare` | Pomija hooki, CLAUDE.md, LSP — **NIE uzywac** w normalnym trybie. |

### Kombinacja flag — rekomendacja dla Agent Launcher

```bash
claude --append-system-prompt "[TRYB AUTONOMICZNY] Rola: developer. Task: sprawdz backlog" \
       --session-id "550e8400-e29b-41d4-a716-446655440000" \
       --name "Agent: developer" \
       --permission-mode default
```

Dlaczego:
- `--append-system-prompt` — nie nadpisuje, dodaje kontekst
- `--session-id` — launcher zna ID przed spawnem, moze zapisac do registry
- `--name` — czytelna nazwa w UI i resume picker
- `--permission-mode` — jawna kontrola autonomii

### Weryfikacja manualna (wymaga potwierdzenia czlowieka)

- [ ] Wariant A: slash commands (`/help`, `/resume`) dzialaja normalnie
- [ ] Wariant A: status line wyswietla sie poprawnie
- [ ] Wariant A: session_init z CLAUDE.md odpala sie automatycznie
- [ ] Wariant D: czy brak default system prompt powoduje problemy z zachowaniem agenta
- [ ] Wariant E: resume w innym terminalu zachowuje pelny kontekst

---

## E-04: Terminal API capabilities

### Metoda
Research VS Code Extension API documentation + analiza istniejacego PoC (`extensions/mrowisko-terminal-control/src/extension.ts`).

### Wyniki per test

| # | Test | Wynik | Szczegoly |
|---|------|:---:|---|
| **A** | `sendText()` do Claude | **TAK** | Wysyla tekst do input stream terminala. Parametr `addNewLine` (default: true). Symuluje wpisanie tekstu — Claude otrzyma go jak input od uzytkownika. |
| **B** | Nazewnictwo terminala | **TAK** | `createTerminal({name: "Agent: developer"})` — nazwa widoczna w tab. Mozna tez ustawic ikone: `iconPath: new vscode.ThemeIcon("terminal")`. |
| **C** | Terminal w editor area | **TAK** | `TerminalLocation.Editor` istnieje i dziala. Mozna tez okreslic kolumne: `location: {viewColumn: vscode.ViewColumn.Two}`. |
| **D** | `exitStatus` | **TAK** | Po zamknieciu: `{code: number, reason: TerminalExitReason}`. Reason: `Unknown`, `Shutdown`, `Process`, `User`. |
| **E** | `onDidCloseTerminal` | **TAK** | Event fires z obiektem Terminal. Mozna odczytac exitStatus w handlerze. |
| **F** | Limit terminali | **WARUNKOWO** | Brak hard limit. Performance skaluje sie z iloscia terminali + scrollback buffer. Default scrollback: 1000 linii (konfigurowalne do 50000). |

### Dodatkowe eventy Terminal API

| Event | Istnieje? | Co daje |
|---|:---:|---|
| `onDidOpenTerminal` | TAK | Fires gdy terminal tworzony — dostajemy obiekt Terminal |
| `onDidCloseTerminal` | TAK | Fires gdy terminal zamykany — mamy exitStatus |
| `onDidChangeActiveTerminal` | TAK | Fires gdy user przelacza active terminal |

### Capability matrix

| Mozliwosc | Status | Uwagi |
|---|:---:|---|
| Tworzenie terminala | TAK | Pelne opcje: name, icon, env, cwd, location |
| Wysylanie tekstu | TAK | `sendText(text, addNewLine?)` |
| Odczyt outputu | **NIE** | Brak public API. Workaround: Pseudoterminal (Extension Terminal) ale nie pasuje do naszego use case. |
| Exit detection | TAK | `onDidCloseTerminal` + `exitStatus` |
| Terminal w editor area | TAK | `TerminalLocation.Editor` |
| Split terminali | TAK | `TerminalSplitLocationOptions` z `parentTerminal` |
| Ukryty terminal | TAK | `hideFromUser: true` |
| Transient terminal | TAK | `isTransient: true` — auto-close |

### Wazne ograniczenie

**Nie mozna odczytac outputu terminala.** To potwierdza decyzje z PRD: lifecycle detection musi isc przez hooki Claude Code, nie przez parsowanie terminala.

---

## E-03: Lifecycle detection przez hooki

### Metoda
Analiza istniejacego hooka `on_stop.py` + debug payload (`tmp/hook_stop_debug.json`) + dokumentacja Claude Code.

### Odkrycie: 23 typy hookow

Claude Code wspiera **23 typow hookow**, nie 4. Pelna lista:

**Blokujace (moga kontrolowac flow):**
| Hook | Opis |
|---|---|
| `PreToolUse` | Przed wywolaniem narzedzia |
| `PostToolUse` | Po udanym uzyciu narzedzia |
| `PostToolUseFailure` | Po nieudanym uzyciu narzedzia |
| `UserPromptSubmit` | Przed przetworzeniem promptu |
| `PermissionRequest` | Dialog permisji |
| `Stop` | Claude konczy odpowiedz |
| `SubagentStop` | Subagent konczy |
| `TaskCompleted` | Task oznaczony jako completed |
| `ConfigChange` | Zmiana pliku konfiguracyjnego |
| `TeammateIdle` | Teammate blisko idle |
| `Elicitation` | MCP server prosi o input |
| `ElicitationResult` | User odpowiada na elicitation |
| `WorktreeCreate` | Tworzenie worktree |

**Observability-only (bez blokowania):**
| Hook | Opis |
|---|---|
| `SessionStart` | Start sesji |
| `SessionEnd` | Koniec sesji (cleanup) |
| `InstructionsLoaded` | CLAUDE.md zaladowany |
| `PostCompact` | Po kompresji kontekstu |
| `PreCompact` | Przed kompresja kontekstu |
| `StopFailure` | Blad przy stop |
| `CwdChanged` | Zmiana working directory |
| `FileChanged` | Zmiana pliku |
| `WorktreeRemove` | Usuniecie worktree |
| `SubagentStart` | Subagent startuje |
| `Notification` | Notyfikacja wyslana |

### Wyniki per test

| # | Test | Wynik | Szczegoly |
|---|------|:---:|---|
| **A** | Stop hook payload | **TAK** | Otrzymuje: `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`, `stop_hook_active`, `last_assistant_message` |
| **B** | Stop vs SessionEnd | **TAK** | **Stop** = Claude konczy odpowiedz (blokujacy, mozna wymusic kontynuacje). **SessionEnd** = sesja sie konczy (observability-only, brak blokowania). Rozne zdarzenia. |
| **C** | Reliability hookow | **WARUNKOWO** | Stop fires na normalne zakonczenie. SessionEnd ma matchery: `clear\|resume\|logout\|prompt_input_exit\|bypass_permissions_disabled\|other`. Wymaga manualnego testu dla `/exit` i wyczerpania turns. |
| **D** | Idle detection | **NIE** | Brak natywnego sygnalu "agent czeka na input". Brak heartbeat API. |
| **E** | Round-trip test | **TAK** | Istniejacy `on_stop.py` juz zapisuje do mrowisko.db. Wtyczka moze pollowac DB. |

### Brakujace pole: exit_reason

Stop hook **nie** otrzymuje `exit_reason` ani `stop_reason`. `stopReason` pojawia sie tylko w output hooka (gdy blokuje):
```json
{"decision": "block", "reason": "Kontynuuj prace"}
```

### Mapa lifecycle dla Agent Launcher

```
[Spawn terminal]
    |
    v
SessionStart hook → zapis do registry (live_agents table)
    |
    v
[Agent pracuje] — brak sygnalu idle (!)
    |
    v
Stop hook → update registry (last_message, transcript_path)
    |
    ├── decision: "block" → agent kontynuuje (petla)
    └── decision: "allow" → agent konczy odpowiedz
         |
         v
    [User pisze lub /exit]
         |
         v
SessionEnd hook → cleanup registry (agent dead)
    |
    v
onDidCloseTerminal → cleanup terminal reference
```

### Rekomendacja hookow dla Agent Launcher

| Hook | Akcja | Implementacja |
|---|---|---|
| `SessionStart` | Zarejestruj agenta w `live_agents` | Nowy hook: `on_session_start.py` |
| `Stop` | Update `last_activity`, `last_message` | Rozszerz istniejacy `on_stop.py` |
| `SessionEnd` | Oznacz agenta jako dead w registry | Nowy hook: `on_session_end.py` |
| `SubagentStart` | Rejestruj subagenta | Nowy hook (Faza 2) |
| `SubagentStop` | Cleanup subagenta | Nowy hook (Faza 2) |

### Idle detection — workaround

Natywny idle detection nie istnieje. Proponowane obejscia:

1. **Timestamp-based**: `Stop` hook zapisuje timestamp. Brak nowego `Stop` przez N sekund = prawdopodobnie idle.
2. **Transcript polling**: Wtyczka parsuje `.jsonl` transcript (jesli unlocked) i sprawdza ostatnia aktywnosc.
3. **Custom heartbeat**: Hook `PostToolUse` zapisuje timestamp — brak nowych tool calls = agent czeka lub idle.

Zaden z tych sposobow nie jest 100% wiarygodny. Rekomendacja: **nie implementowac idle detection w Fazie 1.**

---

## E-02: Multi-window terminal control

### Metoda
Research VS Code Extension API documentation.

### Wyniki per test

| # | Test | Wynik | Szczegoly |
|---|------|:---:|---|
| **A** | Widocznosc terminali cross-window | **NIE** | `vscode.window.terminals` jest **per-window**. Kazde okno VS Code to osobny Extension Host. |
| **B** | Gdzie leci spawned terminal | **Window A** | Terminal tworzony przez wtyczke pojawia sie w tym samym oknie co Extension Host. |
| **C** | Wspoldzielony stan przez DB | **TAK** | Oba okna moga czytac/pisac do mrowisko.db. SQLite z WAL mode wspiera concurrent readers. |

### Hipoteza: POTWIERDZONA

> VS Code Extension API jest per-window. Terminale jednego okna nie sa widoczne z drugiego. Wspoldzielony stan = mrowisko.db.

### Implikacje architektoniczne

1. **Kazde okno VS Code = niezalezny pilot.** Widzi tylko swoje terminale.
2. **Registry (mrowisko.db) = jedyne zrodlo prawdy** o zywych agentach cross-window.
3. **Wtyczka w kazdym oknie** musi:
   - Pollowac registry (mrowisko.db) po stan globalny
   - Zarzadzac tylko lokalnymi terminalami
   - Synchronizowac registry przy spawn/close terminala
4. **Brak potrzeby IPC miedzy oknami** — wystarczy DB jako mediator.

Architektura:
```
[Window A]                    [Window B]
  |-- Extension A               |-- Extension B
  |   |-- terminals[]           |   |-- terminals[]
  |   |-- poll registry         |   |-- poll registry
  |   |-- spawn local           |   |-- spawn local
  |                             |
  +-------- mrowisko.db --------+
            (live_agents)
            (invocations)
```

---

## Podsumowanie odkryc

### Kluczowe decyzje architektoniczne umozliwione przez eksperymenty

| # | Decyzja | Uzasadnienie |
|---|---------|-------------|
| 1 | **`--append-system-prompt` do wstrzykniecia kontekstu** | Nie nadpisuje, CLAUDE.md laduje sie normalnie, hooki dzialaja |
| 2 | **`--session-id` do pre-registration w registry** | Znamy UUID przed spawnem — mozemy zapisac do DB zanim sesja wystartuje |
| 3 | **`TerminalLocation.Editor` do layoutu** | Terminale w editor area = wizja "agenci obok siebie" |
| 4 | **Hooki (SessionStart/Stop/SessionEnd) do lifecycle** | 3 hooki pokrywaja pelny cykl zycia agenta |
| 5 | **mrowisko.db jako mediator cross-window** | Jedyne zrodlo prawdy, brak potrzeby IPC |
| 6 | **Bez idle detection w Fazie 1** | Brak natywnego sygnalu, workaroundy zawodne |

### Nowe hooki do zaimplementowania (Faza 1)

| Hook | Plik | Funkcja |
|---|---|---|
| `SessionStart` | `tools/hooks/on_session_start.py` | Rejestracja agenta w `live_agents` |
| `SessionEnd` | `tools/hooks/on_session_end.py` | Oznaczenie agenta jako dead |

Istniejacy `on_stop.py` wymaga rozszerzenia o update `last_activity` w registry.

### Nowa tabela w mrowisko.db (propozycja)

```sql
CREATE TABLE live_agents (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL,
    task TEXT,
    terminal_name TEXT,
    window_id TEXT,
    status TEXT DEFAULT 'starting',  -- starting, active, idle, stopped
    spawned_by TEXT,                  -- 'human' lub session_id rodzica
    created_at TEXT DEFAULT (datetime('now')),
    last_activity TEXT,
    stopped_at TEXT,
    transcript_path TEXT
);
```

### Otwarte pytania (do Architekta)

1. Czy `--session-id` z wlasnym UUID jest stabilny? (edge case: co jesli UUID koliduje z istniejaca sesja?)
2. Czy registry powinien byc w `live_agents` (osobna tabela) czy rozszerzenie istniejacego modelu `sessions`?
3. Idle detection — czy potrzebny w Fazie 1 czy odroczony?
4. Permission mode dla spawned agentow — jaki default? (`default` wymaga human approval, `acceptEdits` daje wiecej autonomii)
