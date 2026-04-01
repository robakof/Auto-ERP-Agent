# ADR-005: Extension Architecture — Rewrite mrowisko-terminal-control

Date: 2026-03-30
Status: Accepted

## Context

### Problem

Extension mrowisko-terminal-control crashuje przy activation. Root cause: CWD
niezdefiniowany — `path.dirname("mrowisko.db")` zwraca pusty string gdy workspace
nie otwarty. 27 commitow fixow na tym samym problemie. Approver nigdy nie dzialal
(polyka errory cicho). Code maturity: L1 Junior.

Inspekcja: `documents/human/reports/extension_inspection_2026_03_30.md`
Research: `documents/researcher/research/research_results_vscode_extension_lifecycle.md`

### 8 problemow zidentyfikowanych w inspekcji

| # | Problem | Severity |
|---|---------|----------|
| P1 | CWD niezdefiniowany, niedeterministyczny | Critical |
| P2 | Approver nigdy nie dzialal (polyka errory) | Critical |
| P3 | Brak bundlera (tsc-only) | High |
| P4 | .vscodeignore dziurawy (pakuje node_modules, DB) | High |
| P5 | Zero testow TypeScript | High |
| P6 | Brak Output Channel (debugging slepy) | Medium |
| P7 | execFileSync blokuje host thread | Medium |
| P8 | Python proxy zamiast direct DB | Low |

### Istniejaca architektura

```
extension.ts → Registry (DB via Python subprocess)
             → Spawner (terminal creation)
             → Watcher (terminal close → markStopped)
             → Approver (poll pending invocations → dialog → spawn)
             → Commands (QuickPick UI)
             → Layout (ViewColumn management)
             → URI Handler (CLI → extension bridge)
```

Komunikacja z DB: extension → execFileSync("py", ["agent_launcher_db.py", ...]) → stdout JSON.
Kazda operacja = nowy proces Python = ~200-500ms + sync block.

## Decision

### Rewrite, nie patch

27 commitow fixow na tych samych problemach = debt zbyt gleboki na patch.
Rewrite z zachowaniem: types.ts, layout.ts (ok). Przepisanie: registry, approver,
extension, spawner, watcher.

### DB Access: better-sqlite3 direct (nie Python proxy)

**Opcje rozwazone:**

| Opcja | Pro | Con |
|-------|-----|-----|
| Python subprocess (obecne) | Reuse agent_launcher_db.py | 200-500ms/call, sync block, CWD dependent |
| better-sqlite3 direct | ~1ms/call, async-friendly, zero CWD | Duplikacja SQL, schema drift risk |
| LSP server | Clean protocol, async | Overengineered dla naszego use case |

**Decyzja: better-sqlite3 direct.**
- Juz w node_modules (dependency istnieje)
- Eliminuje caly Python proxy layer + CWD problem
- ~100x szybsze niz subprocess
- Schema drift mitigation: shared SQL constants lub migration versioning

### Bundler: esbuild

Research potwierdza: esbuild to oficjalny default 2026, najkrotsza konfiguracja,
najszybszy build. tsc-only zostawia wiele plikow + node_modules w VSIX.

### Development workflow: F5 + local workspace extension

- **F5 (Extension Development Host)** — codzienny development, breakpoints, reload
- **Local workspace extension** (`.vscode/extensions/`) — testowanie w kontekscie Mrowisko
- **VSIX** — tylko finalna walidacja paczki

### Logging: LogOutputChannel

```typescript
const log = vscode.window.createOutputChannel("Mrowisko", { log: true });
log.info("Extension activated", { dbPath, workspaceFolder });
log.error("Approver poll failed", { error, cwd });
```

Structured logging z poziomami. Kazdy subprocess call logowany z: command, cwd, duration, exitCode.

## Architecture (nowa)

### Workspace Contract

```typescript
function resolveWorkspaceRoot(): string {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders || folders.length === 0) {
    throw new Error("Mrowisko requires an open workspace folder.");
  }
  return folders[0].uri.fsPath;
}
```

**Regula:** Extension NIE aktywuje sie bez otwartego workspace.
Fail-fast, nie fail-silent. Activation event: `workspaceContains:mrowisko.db`.

### DB Layer: MrowiskoDB

```typescript
import Database from "better-sqlite3";

export class MrowiskoDB {
  private db: Database.Database;

  constructor(dbPath: string) {
    // dbPath MUSI byc absolutny
    if (!path.isAbsolute(dbPath)) {
      throw new Error(`dbPath must be absolute, got: ${dbPath}`);
    }
    this.db = new Database(dbPath, { readonly: false });
    this.db.pragma("busy_timeout = 3000");
    this.db.pragma("journal_mode = WAL");
  }

  getActiveAgents(): LiveAgent[] {
    return this.db.prepare(
      "SELECT * FROM live_agents WHERE status IN ('starting', 'active')"
    ).all() as LiveAgent[];
  }

  getPendingInvocations(): PendingInvocation[] {
    return this.db.prepare(
      "SELECT * FROM invocations WHERE status = 'pending' ORDER BY created_at"
    ).all() as PendingInvocation[];
  }

  approveInvocation(id: number): void {
    this.db.prepare("UPDATE invocations SET status = 'approved' WHERE id = ?").run(id);
  }

  rejectInvocation(id: number): void {
    this.db.prepare("UPDATE invocations SET status = 'rejected' WHERE id = ?").run(id);
  }

  insertAgent(spawnToken: string, role: string, task: string, terminalName: string): void {
    this.db.prepare(
      `INSERT INTO live_agents (spawn_token, role, task, terminal_name, status, created_at)
       VALUES (?, ?, ?, ?, 'starting', datetime('now'))`
    ).run(spawnToken, role, task, terminalName);
  }

  markStopped(sessionId: string): void {
    this.db.prepare(
      "UPDATE live_agents SET status = 'stopped', stopped_at = datetime('now') WHERE session_id = ?"
    ).run(sessionId);
  }

  cleanup(thresholdMinutes: number = 60): void {
    this.db.prepare(
      `UPDATE live_agents SET status = 'stopped', stopped_at = datetime('now')
       WHERE status IN ('starting', 'active')
       AND last_activity < datetime('now', '-' || ? || ' minutes')`
    ).run(thresholdMinutes);
  }

  readSpawnPolicy(): Record<string, string> {
    // Policy z config/spawn_policy.json — czytane przez extension, nie DB
    // Ale extension moze tez czytac z DB jesli policy overrides tam trafia (v2)
    return {};
  }

  dispose(): void {
    this.db.close();
  }
}
```

**Kluczowe:** Zero Python dependency. Zero CWD dependency. Absolutne sciezki only.
better-sqlite3 jest synchroniczny ale ~1ms per query — nie blokuje UI.

### Approver v2

```typescript
export class Approver {
  private timer: ReturnType<typeof setInterval> | undefined;
  private processing = new Set<number>();

  constructor(
    private db: MrowiskoDB,
    private spawner: Spawner,
    private log: vscode.LogOutputChannel,
    private policyFile: string
  ) {}

  start(intervalMs: number): void {
    this.timer = setInterval(() => this.poll(), intervalMs);
  }

  private readPolicy(): Record<string, string> {
    try {
      return JSON.parse(fs.readFileSync(this.policyFile, "utf-8"));
    } catch {
      this.log.warn("spawn_policy.json not found, defaulting to approval");
      return {};
    }
  }

  private poll(): void {
    try {
      const pending = this.db.getPendingInvocations();
      for (const inv of pending) {
        if (this.processing.has(inv.id)) continue;
        this.processing.add(inv.id);
        this.handleInvocation(inv);
      }
    } catch (e) {
      this.log.error("Approver poll error", e);
      // NIE polykaj cicho — loguj
    }
  }

  private async handleInvocation(inv: PendingInvocation): Promise<void> {
    const action = inv.action || "spawn";
    const policy = this.readPolicy();
    const mode = policy[action] || "approval";

    try {
      if (mode === "auto" || this.isTrustedPair(inv.invoker_id, inv.target_role)) {
        this.autoApprove(inv, action);
      } else {
        await this.showApprovalDialog(inv, action);
      }
    } finally {
      this.processing.delete(inv.id);
    }
  }

  private autoApprove(inv: PendingInvocation, action: string): void {
    this.db.approveInvocation(inv.id);
    this.log.info(`Auto-approved: ${action} ${inv.target_role} by ${inv.invoker_id}`);
    this.executeAction(inv, action);
  }

  private async showApprovalDialog(inv: PendingInvocation, action: string): Promise<void> {
    const choice = await vscode.window.showWarningMessage(
      `${inv.invoker_id} wants to ${action} ${inv.target_role}: "${inv.task}"`,
      "Approve", "Reject"
    );
    if (choice === "Approve") {
      this.db.approveInvocation(inv.id);
      this.executeAction(inv, action);
    } else {
      this.db.rejectInvocation(inv.id);
      this.log.info(`Rejected: ${action} ${inv.target_role}`);
    }
  }

  private executeAction(inv: PendingInvocation, action: string): void {
    if (action === "spawn") {
      this.spawner.spawn({ role: inv.target_role, task: inv.task });
    } else if (action === "resume") {
      // Resume logic — find terminal, dispose stale, create fresh with --resume
      this.spawner.resume(inv.target_session_id);
    } else if (action === "stop") {
      this.spawner.stop(inv.target_session_id);
    }
    // kill handled as stop + force dispose
  }

  dispose(): void {
    if (this.timer) clearInterval(this.timer);
  }
}
```

**Kluczowe zmiany vs obecny:**
- Obsluguje spawn + stop + resume + kill (nie tylko spawn)
- Czyta spawn_policy.json (auto/approval routing)
- Loguje do LogOutputChannel (nie polyka errorow)
- Direct DB (nie Python subprocess)

### Activation Flow

```typescript
export function activate(context: vscode.ExtensionContext): void {
  const log = vscode.window.createOutputChannel("Mrowisko", { log: true });

  // 1. Resolve workspace — fail-fast
  let workspaceRoot: string;
  try {
    workspaceRoot = resolveWorkspaceRoot();
  } catch (e) {
    log.error("No workspace folder open. Extension inactive.");
    vscode.window.showErrorMessage("Mrowisko: otwórz folder projektu.");
    return;
  }

  // 2. Resolve DB — absolute path
  const dbPath = path.join(workspaceRoot, "mrowisko.db");
  if (!fs.existsSync(dbPath)) {
    log.warn(`mrowisko.db not found at ${dbPath}. Extension inactive.`);
    return;
  }

  // 3. Initialize components
  const db = new MrowiskoDB(dbPath);
  const policyFile = path.join(workspaceRoot, "config", "spawn_policy.json");
  const layout = new RoleLayout();
  const terminals: TerminalMap = new Map();
  const spawner = new Spawner(db, terminals, layout, log);
  const approver = new Approver(db, spawner, log, policyFile);
  const watcher = new Watcher(db, terminals, layout, log);

  // 4. Activate
  watcher.activate();
  registerCommands(context, db, spawner, terminals, layout);
  approver.start(5000);

  // 5. Cleanup orphans
  db.cleanup();
  log.info("Extension activated", { workspaceRoot, dbPath });

  // 6. Register disposables
  context.subscriptions.push(
    { dispose: () => approver.dispose() },
    { dispose: () => watcher.dispose() },
    { dispose: () => db.dispose() },
    log
  );
}
```

**Kluczowe:**
- Fail-fast jesli workspace nie otwarty
- Absolutne sciezki ZAWSZE
- LogOutputChannel od pierwszej linii
- Disposables zarejestrowane w context.subscriptions

### .vscodeignore (nowy)

```
.vscode/**
.vscode-test/**
src/**
test-fixtures/**
node_modules/**
!node_modules/better-sqlite3/**
!node_modules/better-sqlite3/build/**
.gitignore
tsconfig.json
tsconfig.test.json
esbuild.js
*.map
*.vsix
*.md
!README.md
```

Whitelist model: exclude all, include only runtime needs.
better-sqlite3 musi zostac (native binary) — ale TYLKO build output.

### package.json scripts (nowy)

```json
{
  "scripts": {
    "vscode:prepublish": "npm run build",
    "build": "esbuild src/extension.ts --bundle --outfile=dist/extension.js --external:vscode --external:better-sqlite3 --platform=node --format=cjs",
    "watch": "npm run build -- --watch --sourcemap",
    "compile": "tsc -p ./",
    "typecheck": "tsc --noEmit",
    "test": "npm run typecheck && node src/test/runTest.js",
    "package": "vsce package"
  }
}
```

### Activation Event

```json
{
  "activationEvents": ["workspaceContains:mrowisko.db"]
}
```

Lazy activation — extension laduje sie TYLKO gdy workspace zawiera mrowisko.db.
Nie `onStartupFinished` (eager, niepotrzebny overhead w kazdym oknie VS Code).

## Migration Path

### Faza 1: Fundaments (1-2 sesje Dev)
- MrowiskoDB class (better-sqlite3 direct)
- LogOutputChannel
- resolveWorkspaceRoot (fail-fast)
- Activation event: workspaceContains:mrowisko.db
- esbuild config
- .vscodeignore fix

### Faza 2: Rewrite core (2-3 sesje Dev)
- Registry → MrowiskoDB (juz w Fazie 1)
- Approver v2 (spawn + stop + resume + policy routing)
- Spawner (zachowaj logike, inject log + db)
- Watcher (zachowaj logike, inject log + db)

### Faza 3: Tests + polish (1-2 sesje Dev)
- Unit tests: MrowiskoDB, policy reader, CWD resolution
- Integration tests: activation, spawn, approver poll
- F5 launch.json verification
- VSIX smoke test

### Cleanup
- Usun agent_launcher_db.py (nie uzywany po rewrite)
- Usun agent_launcher_db references z agent_bus_cli.py (jesli sa)

## Consequences

### Gains
- Extension dziala (nie crashuje na CWD)
- Approver dziala (approval gate zywy)
- ~100x szybsze DB queries (1ms vs 200-500ms)
- Debugging mozliwy (Output Channel)
- Testy istnieja (regressions wykrywane)
- Mniejszy VSIX (esbuild bundle, proper ignore)
- Lazy activation (nie spowalnia kazdego okna VS Code)

### Costs
- Rewrite = 4-7 sesji Dev (vs patch = 1-2 sesji ale nie rozwiaze fundamentow)
- SQL duplikacja (TypeScript + Python maja podobne queries)
- better-sqlite3 native binary w VSIX (~5MB)

### Risks
- **Schema drift:** Python CLI i TypeScript extension czytaja ta sama DB.
  Mitigation: shared schema version check, migration w obu jezykach.
- **better-sqlite3 cross-platform:** Native binary musi byc buildowany per platform.
  Mitigation: prebuild-install (juz w dependencies), testowac na Windows.
- **Rewrite scope creep:** Pokusa dodania nowych features podczas rewrite.
  Mitigation: ADR scope = parity z obecna funkcjonalnoscia. Zero nowych features.

## Resolved Questions

### Q1: agent_launcher_db.py — usunac po rewrite

Jedyni konsumenci: registry.ts:49 i approver.ts:26 (extension subprocess calls).
Zero referencji z Python. Po rewrite na better-sqlite3 direct — usunac w Fazie 3 cleanup.

### Q2: better-sqlite3 na Windows ARM — nieaktualne

Projekt dziala na Windows 11 x64. better-sqlite3 ma prebuildy dla win32-x64.
Windows ARM nie jest target platform. Jesli kiedys — rozwiazemy wtedy.

### Q3: kill = osobna akcja, nie stop --force

| | stop | kill |
|---|---|---|
| Mechanizm | `/exit` → agent cleanup → terminal closes | `terminal.dispose()` → natychmiastowe zamkniecie |
| on_session_end | Odpala sie (graceful) | Moze nie zdazyc |
| DB status | Updated przez hook | Wymaga recznego markStopped |
| Kiedy | Agent zyje, chcemy zakonczyc | Agent zamrozony, nie reaguje na /exit |
| Policy | `"stop": "auto"` (szybkosc) | `"kill": "approval"` (destruktywne) |

Kill to osobna akcja w Approver (`executeAction` switch). Osobna komenda CLI (`cmd_kill`).
Uzasadnienie: inna semantyka, inna policy, inna implementacja.
