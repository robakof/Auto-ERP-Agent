# Inspekcja: mrowisko-terminal-control extension

**Data:** 2026-03-30
**Trigger:** Msg #566 od developera — extension crashuje, approver martwy, 4 sesje petli
**Scope:** Pelna inspekcja kodu (8 plikow TypeScript) + git history (27 commitow) + architektura

---

## TL;DR — zjebane od gory do dolu

Czlowiek mial racje. Extension ma fundamentalne problemy na kazdym poziomie:
architektura, CWD handling, deployment, testy, debugging, wiedza kumulowana.
27 commitow — wiekszosc to fixy tego samego problemu (CWD, crash, workaroundy).
Devowie petla sie bo nie maja fundamentow — brak researchu, brak architektury,
brak narzedzi debugowania.

---

## Problemy (severity order)

### P1: CRITICAL — CWD jest niezdefiniowany i niedeterministyczny

**Registry.ts:43-49:**
```typescript
this.cwd = path.dirname(dbPath) || process.cwd();
if (path.basename(dbPath) === "mrowisko.db") {
  this.cwd = path.dirname(dbPath);
}
```

Problem: `dbPath` pochodzi z `resolveDbPath()` w extension.ts. Jesli workspace
nie jest otwarty → dbPath = "mrowisko.db" (relative) → `path.dirname("mrowisko.db")` = `""` → `this.cwd = ""`.
`execFileSync` z pustym cwd dziedziczy process.cwd() = VS Code install dir.

To jest ROOT CAUSE crashy. Naprawiane 4+ razy (commity 42d82ef, 72ecb5d, 5646e71)
ale nigdy fundamentalnie — tylko try/catch wokol symptomu.

**Fix:** `resolveDbPath()` MUSI zwracac absolutna sciezke ZAWSZE. Jesli workspace
nie otwarty → extension NIE aktywuje sie (fail-fast, nie fail-silent).

### P2: CRITICAL — Approver nigdy nie dzialal poprawnie

**Approver.ts:51-73** — `poll()` wola `this.run(["pending-invocations"])` co 5s.
Ale `this.run()` uzywa `execFileSync` z tym samym zepsutym CWD.
Kazdy poll crashuje cicho (catch na linii 71 polyka error).

**Konsekwencja:** Caly approval gate (bezpiecznik #219, spawn_policy.json) jest martwy.
Invocations sa tworzone w DB ale nikt ich nie przetwarza.

**Approver.ts:76-86** — `autoApprove` i `showApprovalDialog` obsuguja TYLKO spawn.
Brak obslogi stop-request i resume-request (dodane dzisiaj w agent_bus_cli.py).

### P3: HIGH — Brak bundlera (esbuild/webpack)

**package.json:91-95:**
```json
"scripts": {
  "vscode:prepublish": "npm run compile",
  "compile": "tsc -p ./"
}
```

`tsc` produkuje wiele osobnych .js plikow w `out/`. Brak bundlera = wolne ladowanie,
brak tree-shaking, VSIX zawiera node_modules z better-sqlite3 (native module, 192KB+ binary).

To nie jest bug — to brak fundamentow. Kazda powazna extension uzywa esbuild/webpack.

### P4: HIGH — .vscodeignore jest dziurawy

```
.vscode/**
.vscode-test/**
src/**
.gitignore
tsconfig.json
*.map
*.vsix
```

**Brakuje:**
- `node_modules/**` — VSIX pakuje cale node_modules (w tym better-sqlite3 z native binary!)
- `mrowisko.db` — runtime DB nie powinna byc w VSIX
- `documents/**` — jesli workspace = repo root
- `tests/**`, `*.test.js`

### P5: HIGH — Zero testow

Brak jakichkolwiek testow TypeScript. Kazda zmiana = manual test.
Git history to potwierdza: 27 commitow, wiele "fix" w tytule, powtarzajace sie problemy.

### P6: MEDIUM — Brak Output Channel

Extension loguje do `console.log` (Extension Host log). Uzytkownik nie widzi nic.
Debugging wymaga szukania w `AppData/Roaming/Code/logs/` po nested folders.

Kazda powazna extension ma dedykowany Output Channel:
```typescript
const log = vscode.window.createOutputChannel("Mrowisko");
log.appendLine("Extension activated");
```

### P7: MEDIUM — execFileSync (synchroniczny!) w extension host

**Registry.ts:52-57, Approver.ts:29-34:**
Uzycie `execFileSync` blokuje Extension Host thread. Przy timeoucie 10s
VS Code moze oznaczac extension jako "unresponsive".

Powinno byc `execFile` (async) z callbackiem lub promisem.

### P8: LOW — agent_launcher_db.py = oddzielny skrypt proxy

Extension komunikuje sie z DB przez oddzielny Python skrypt (`tools/agent_launcher_db.py`).
Kazda operacja DB = spawn nowego procesu Python = ~200-500ms overhead.

Alternatywa: better-sqlite3 (juz w node_modules!) — direct DB access z TypeScript.
Zero Python dependency, zero process spawn overhead.

---

## Pattern: Dlaczego devowie sie petla

Git history ujawnia cykl:
1. Extension crashuje → dev dodaje try/catch
2. Try/catch maskuje problem → nastepna feature crashuje w tym samym miejscu
3. Dev dodaje kolejny try/catch → itd.

**Root cause petli:** Brak diagnozy fundamentalnej przyczyny (CWD).
Zamiast naprawiac `resolveDbPath()` naprawiali symptomy w 4+ commitach.

**Brak feedback loop:** Bez Output Channel i bez testow dev nie wie CZY fix pomogl
dopoki nie zbuduje VSIX, nie zainstaluje, nie zrestartuje VS Code i nie spawnie agenta.
To jest 5-minutowy feedback loop na kazda zmiane.

**Brak architektury:** Nie ma dokumentu ktory mowilby "tak extension powinna dzialac".
Devowie nie maja punktu zaczepienia — kazdy idzie po omacku.

---

## Co powinno istniec a nie istnieje

1. **`architecture/ADR-005-extension-architecture.md`** — jak extension powinna dzialac,
   CWD contract, activation flow, Approver lifecycle, communication z DB
2. **Output Channel** — "Mrowisko" w VS Code Output panel
3. **Testy** — vscode-test lub przynajmniej unit testy logiki (CWD resolution, policy routing)
4. **Bundler** — esbuild w scripts
5. **Development mode** — F5 launch.json (istnieje `.vscode/launch.json` w extension dir)
6. **Poprawny .vscodeignore**

---

## Rekomendacja

### Krok 1: STOP developmentu nowych features w extension

Nic nie dziala. Dodawanie nowych features na zepsutych fundamentach to marnowanie tokenow.

### Krok 2: Poczekaj na research od PE

Research (#569) pokrywa: development workflow, deployment, testing, debugging, CWD.
Daje fundamenty zanim cokolwiek naprawimy.

### Krok 3: ADR-005 Extension Architecture

Po researchu — Architect pisze ADR z kontraktem:
- CWD resolution contract (absolutne sciezki ZAWSZE)
- Activation flow (fail-fast jesli workspace nie otwarty)
- Approver lifecycle (jakie invocations obsluguje, jak)
- DB access strategy (agent_launcher_db.py vs better-sqlite3 direct)
- Logging contract (Output Channel)
- Test strategy

### Krok 4: Rewrite zamiast fix

27 commitow fixow na tych samych problemach = code debt zbyt gleboki na patch.
Rewrite z ADR-005 jako spec. Zachowac: types.ts, layout.ts (ok). Przepisac: registry, approver, extension, spawner.

### Interim: CLI approval

Do czasu az extension dziala — dispatcher robi approval reczny:
```
py tools/agent_bus_cli.py approve --id <invocation_id>
```
(Jesli approve command nie istnieje — Dev dodaje w 15 min.)

---

## Code Maturity: L1 Junior

- Synchroniczny I/O blokujacy host thread
- Polykanie errorow (catch {})
- CWD niezdefiniowany (niedeterministic behavior)
- Zero testow
- Zero logging
- Zero bundler
- Powtarzajace sie fixy tego samego problemu (27 commitow, pattern: try/catch instead of root cause)

Standard projektu: L3 Senior. Extension wymaga fundamentalnej przebudowy.
