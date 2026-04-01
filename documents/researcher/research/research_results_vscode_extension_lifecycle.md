# Research: VS Code Extension Development Lifecycle

Data: 2026-03-30

Legenda siły dowodów:
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, cookbook, działające repo
- **spekulacja** — inferencja, hipoteza, rekomendacja nieprzetestowana

## TL;DR — 7 najważniejszych kierunków

1. **Domyślny workflow deweloperski dla VS Code extension to F5 / Extension Development Host, nie ręczna instalacja do katalogu użytkownika.** F5 daje breakpoints, source maps i szybki cykl edycja → reload; instalacja VSIX jest potrzebna głównie do walidacji paczki, testów „jak u użytkownika”, testów remote/Codespaces i prywatnego udostępniania. — siła dowodów: **praktyczne**
2. **Oficjalnie wspierany sposób „uruchom z kodu źródłowego” to `--extensionDevelopmentPath`; symlink do `~/.vscode/extensions/` nie jest pokazany jako główny workflow.** Od 2024 dochodzi też opcja local workspace extensions w `.vscode/extensions`, czyli instalacja unpacked extension tylko dla jednego workspace. — siła dowodów: **praktyczne**
3. **„Hot reload” jest ograniczony.** Dla kodu extension standardem nadal jest `Developer: Reload Window`; od VS Code 1.88 można restartować zaktualizowane extensions bez pełnego reloadu okna, ale nie w scenariuszach remote. Zmiany w `package.json`/`contributes` zwykle nadal wymagają reloadu. — siła dowodów: **praktyczne**
4. **Testy powinny być warstwowe:** szybkie unit testy poza hostem + integration tests w osobnym Extension Development Host przez `@vscode/test-electron` albo nowszy VS Code Test CLI. To jest oficjalny model; testy extension uruchamiają się w specjalnym host process, a nie w zwykłym Node runtime. — siła dowodów: **praktyczne**
5. **Packaging i deploy warto oprzeć o `vsce`, ale z własnym CI wokół niego.** `vsce package` daje artefakt `.vsix`, `vsce publish` publikuje, a `vscode:prepublish` jest naturalnym hakiem buildowym. Paczka powinna być jawnie czyszczona przez `.vscodeignore` albo whitelistę `files`. — siła dowodów: **praktyczne**
6. **Dla debuggingu i supportu lepszy jest `LogOutputChannel` niż `console.log`.** Dedykowany kanał w Output, log levels (`trace/debug/info/warn/error`) i opcjonalne pliki pod `context.logUri` dają workflow bliższy dojrzałym extensions. Do diagnozy hosta używa się `Developer: Show Logs...`, Output → `Log (Extension Host)` / `Log (Remote Extension Host)` i `Developer: Show Running Extensions`. — siła dowodów: **praktyczne**
7. **Nie należy polegać na implicit CWD.** Dla `child_process` defaultem jest `process.cwd()`, a nie „aktywny workspace folder”. Dlatego `cwd` i ścieżki do executable powinny być ustawiane jawnie. Dla architektury: subprocess jest naturalnym wyborem dla orkiestracji CLI; LSP opłaca się dopiero, gdy narzędzie staje się długowiecznym, cięższym serwisem z funkcjami „language-like”. — siła dowodów: **praktyczne** (architektura: częściowo **spekulacja**)

## Wyniki per obszar badawczy

## A. Development workflow

### A1. F5 debug mode vs VSIX install

**Wniosek:** F5 / Extension Development Host powinien być podstawowym trybem codziennego developmentu. — siła dowodów: **praktyczne**

Dlaczego:
- oficjalny tutorial prowadzi przez `F5`, który kompiluje i uruchamia extension w nowym **Extension Development Host**;
- ten tryb naturalnie wspiera breakpoints, Debug Console, source maps i szybkie iterowanie;
- przy zmianach kodu standardowy flow to edycja → `Developer: Reload Window` w oknie development host.

**Wniosek:** Instalacja z VSIX jest potrzebna do walidacji artefaktu i zachowania „jak u użytkownika”, a nie do codziennej edycji. — siła dowodów: **praktyczne**

Kiedy VSIX ma sens:
- sprawdzenie, co naprawdę trafia do paczki;
- test ścieżki instalacji/upgrade;
- test extension w środowisku remote, Codespaces albo na innej maszynie;
- prywatne udostępnienie extension bez Marketplace.

Trade-off:
- **F5**: najszybsze iterowanie, najlepszy debugging, ale nie weryfikuje realnej zawartości `.vsix`.
- **VSIX**: najbliżej produkcji, ale wolniejsze iterowanie; dodatkowo extensions instalowane z VSIX mają domyślnie wyłączony auto-update.

### A2. Symlink development / praca z extension w workspace

**Wniosek:** Oficjalny mechanizm „uruchamiaj extension z kodu źródłowego” to `--extensionDevelopmentPath` (bez kopiowania do `~/.vscode/extensions/`). — siła dowodów: **praktyczne**

To jest ważne rozróżnienie: VS Code ma osobny tryb **Development** (`ExtensionMode.Development`) uruchamiany z `--extensionDevelopmentPath`. To dokładnie robi launch configuration typu `extensionHost` i przycisk F5.

**Wniosek:** Symlink do katalogu użytkownika jest możliwy technicznie, ale nie jest pokazany przez oficjalne docs jako preferowany workflow. — siła dowodów: **praktyczne** + **spekulacja**

Interpretacja:
- oficjalne źródła prowadzą przez F5 / `--extensionDevelopmentPath`;
- dla izolacji środowiska instalacji VS Code wspiera `--extensions-dir` i `--user-data-dir`;
- od 2024 jest też **local workspace extension**: unpacked extension w `.vscode/extensions` danego repo/workspace, instalowany tylko dla tego workspace.

To oznacza, że w praktyce są dziś trzy różne modele:
1. **F5 / development path** — najlepszy do authoringu i debugowania.
2. **Local workspace extension** — dobre, gdy extension ma być częścią konkretnego repo/workspace.
3. **VSIX / normal install** — dobre do finalnej walidacji i dystrybucji.

### A3. Hot reload

**Wniosek:** Pełny „hot reload bez restartu okna” nie jest oficjalnie oferowany jako podstawowy workflow dla klasycznych Node-based extensions. — siła dowodów: **praktyczne**

Co jest potwierdzone:
- tutorial nadal każe używać `Developer: Reload Window` po zmianach;
- od VS Code 1.88 zaktualizowane extensions można **restartować** bez pełnego reloadu okna;
- ale w scenariuszach remote nadal trzeba reloadować okno.

**Wniosek:** Dla zmian kodu wykonawczego można liczyć na szybki reload, ale nie na prawdziwy HMR. Dla zmian manifestu (`package.json`, `contributes`, activation model) trzeba zakładać reload. — siła dowodów: **praktyczne** + **spekulacja**

Praktyczna granica:
- kod w `activate()` / zarejestrowane komendy → zazwyczaj wystarczy reload development host;
- statyczne contribution points (`commands`, `menus`, `views`, `configuration`, itp.) są deklaracjami manifestu i powinny być traktowane jako reload-sensitive;
- `globalState` / `workspaceState` są trwałym storage, więc sam reload okna nie jest równoznaczny z „czystym startem stanu”.

### A4. Recommended project structure

**Wniosek:** Wzorcowa struktura katalogów jest bardzo mała, ale w praktyce warto od razu rozdzielić kod runtime, testy i artefakty buildu. — siła dowodów: **praktyczne**

Minimalny canonical scaffold z docs:
- `.vscode/launch.json`
- `.vscode/tasks.json`
- `src/extension.ts`
- `package.json`
- `tsconfig.json`
- artefakt runtime wskazany przez `main` (tradycyjnie `out/extension.js`)

Struktura, która dobrze skaluje się do MVP → produkcja:

```text
.vscode/
  launch.json
  tasks.json
src/
  extension.ts
  ... moduły runtime
src/test/
  runTest.ts
  suite/
    index.ts
    *.test.ts
test-fixtures/
  single-root/
  multi-root.code-workspace
out/            # przy tsc-only
dist/           # przy bundlingu
package.json
tsconfig.json
tsconfig.test.json   # opcjonalnie
esbuild.js / webpack.config.js   # opcjonalnie
README.md
CHANGELOG.md
.vscodeignore
```

Uwaga:
- **`out/`** to klasyczny scaffold TypeScript bez bundlera;
- **`dist/`** częściej pojawia się przy bundlingu;
- dla tests warto mieć osobne fixtures z workspace’ami single-root i multi-root.

## B. Deployment i packaging

### B1. `.vscodeignore`

**Wniosek:** Paczka VSIX powinna być czyszczona jawnie przez `.vscodeignore` albo whitelistę `files`; nie warto liczyć na „przypadkowo małą” paczkę. — siła dowodów: **praktyczne**

Oficjalna dokumentacja mówi wprost, że `.vscodeignore` służy do wykluczania plików niepotrzebnych w runtime.

Typowo do wykluczenia:
- `src/**` jeśli runtime korzysta z `out/` lub `dist/`;
- `test/**`, `src/test/**`, `test-fixtures/**`;
- `.github/**`, CI configi;
- coverage, cache, `.nyc_output`, `.eslintcache`;
- lokalne ustawienia i edytorowe artefakty;
- `tsconfig*.json`, configi lint/format jeśli nie są potrzebne w runtime;
- duże docs/assets niepotrzebne użytkownikowi w paczce.

Potencjalne wyjątki:
- `README.md`, `CHANGELOG.md`, ikony i screenshoty potrzebne Marketplace’owi;
- source maps tylko wtedy, gdy świadomie chcesz je wysyłać;
- jeśli paczka ma narzędzia CLI albo helper binaries, nie wolno ich odfiltrować.

**Wniosek:** W praktyce bezpieczniejszy jest model „whitelist / allow-list” (`files`) niż długa deny-lista. — siła dowodów: **praktyczne** + **spekulacja**

Powód:
- `vsce` od 2024 ostrzega, gdy nie używasz ani `.vscodeignore`, ani `files`;
- allow-list daje mniejszą szansę, że przez przypadek do `.vsix` trafią test fixtures, raw sources albo śmieci z repo.

### B2. VSIX build pipeline i wersjonowanie

**Wniosek:** `vsce` powinno zostać narzędziem bazowym, a „custom pipeline” powinien je otaczać, nie zastępować. — siła dowodów: **praktyczne**

Rola narzędzi:
- `vsce package` — buduje artefakt `.vsix`;
- `vsce publish` — publikuje do Marketplace;
- `vscode:prepublish` — hook odpalany przed package/publish, dobry do buildu bundla.

**Wniosek:** Najczytelniejszy pipeline to: lint/typecheck → testy → bundle/compile → `vsce package` → artefakt → opcjonalnie `vsce publish`. — siła dowodów: **praktyczne**

Wersjonowanie:
- semver w `package.json`;
- osobny tor **pre-release** ma sens, bo `vsce` wspiera pre-release packaging/publishing;
- warto pakować artefakt na każdym releasowym tagu, a nie budować go dopiero „na żywo” przy publikacji.

Uwaga praktyczna:
- jeśli paczka zawiera zależności z executable bits w `node_modules`, bezpieczniej budować `.vsix` na Linux/macOS niż na Windows, bo publishing z Windows może zgubić POSIX executable bit.

### B3. Bundling: esbuild vs webpack vs rollup vs samo `tsc`

**Wniosek:** Bundling jest oficjalnie rekomendowany, a dla web extensions bywa wymagany. — siła dowodów: **praktyczne**

Dokumentacja argumentuje to prosto:
- wiele małych plików i całe `node_modules` pogarszają instalację i start;
- jeden bundle zwykle ładuje się szybciej;
- dla targetu web bundling jest praktycznie standardem.

**Wniosek:** Dla większości desktop-first extensions z logiką Node/CLI najlepszym defaultem w 2026 jest **esbuild**. — siła dowodów: **praktyczne**

Dlaczego:
- oficjalny guide ma pełny przykład dla esbuild;
- od maja 2024 `yo code` potrafi scaffoldować projekt z esbuildem;
- konfiguracja jest krótka;
- build jest szybki.

Ograniczenie:
- esbuild nie robi pełnego type-checkingu, więc i tak trzeba odpalić osobny `tsc --noEmit`.

**Wniosek:** **webpack** ma sens, gdy potrzebujesz bardziej złożonej kontroli nad assetami, targetem web/desktop i kompatybilnością loaderów. — siła dowodów: **praktyczne**

Plusy webpacka:
- bogatszy ekosystem loaderów i pluginów;
- dobra kontrola nad asset graph;
- w oficjalnym guide pokazany target `webworker` dla wsparcia desktop + web.

**Wniosek:** `tsc` bez bundlera nadal jest realną opcją dla małego, desktop-only MVP, ale koszt to większa paczka i gorsze właściwości dystrybucyjne. — siła dowodów: **praktyczne**

**Wniosek:** **rollup** jest opcją wykonalną, ale ma słabsze first-party guidance niż esbuild/webpack. — siła dowodów: **praktyczne**

### B4. Extension dependencies: bundle all-in-one vs shipping `node_modules`

**Wniosek:** Dla extension orkiestrującego zewnętrzne CLI zwykle najlepszy jest model „bundle własny kod + minimalizuj runtime deps”, zamiast wysyłać całe `node_modules`. — siła dowodów: **praktyczne** + **spekulacja**

Rozsądny podział:
- **bundle**: własny kod, małe helpery JS/TS;
- **external**: `vscode` (zawsze), ewentualnie moduły/narzędzia, które muszą pozostać oddzielne;
- **nie bundle’ować w ciemno**: binariów, natywnych addonów i narzędzi CLI, które mają własny lifecycle.

Trade-off:
- **bundle all-in-one**: mniejszy VSIX, mniej problemów z packagingiem, szybszy startup;
- **shipping `node_modules`**: prostszy build i łatwiejsza inspekcja, ale większa paczka i więcej edge-case’ów.

## C. Testing

### C1. `@vscode/test-electron` / VS Code Test CLI

**Wniosek:** Oficjalny model testowania extension to uruchamianie testów wewnątrz specjalnego hosta VS Code, nie „gołego” procesu Node. — siła dowodów: **praktyczne**

Dokumentacja opisuje testy extension jako **integration tests**, uruchamiane w specjalnym **Extension Development Host**. Historycznie robi się to przez `@vscode/test-electron` (`runTests`), a nowszy docs-driven flow promuje też **VS Code Test CLI**, który używa Mocha pod spodem.

Co framework daje:
- pobranie konkretnej wersji VS Code do testów;
- otwarcie wskazanego workspace/folderu;
- przekazanie `--extensionDevelopmentPath` i `--extensionTestsPath`;
- dodatkowe CLI args (`--disable-extensions`, itp.);
- możliwość instalacji innych extensions/VSIX w setupie.

### C2. Setup / teardown / workspace fixtures

**Wniosek:** Workspace fixtures powinny być traktowane jako część pierwszorzędna harnessu testowego. — siła dowodów: **praktyczne**

W extension testach realne są scenariusze, których nie odtworzysz sensownie samym mockingiem:
- brak otwartego workspace;
- single-root;
- multi-root;
- konkretna struktura plików i ustawień;
- scenariusze remote/path-resolution.

Praktyczny wzorzec:
- `src/test/runTest.ts` — bootstrap;
- `src/test/suite/index.ts` — runner;
- osobne fixtures:
  - `fixtures/empty-window`
  - `fixtures/single-root`
  - `fixtures/multi-root.code-workspace`

### C3. Unit tests vs integration tests

**Wniosek:** Granica jest klarowna: wszystko, co zależy od realnego hosta VS Code, terminali, command registry i lifecycle extension, powinno być integration-tested; logika czysta może być unit-tested poza hostem. — siła dowodów: **praktyczne**

Dobre kandydaty na **unit tests**:
- parsowanie konfiguracji;
- wybór folderu/workspace;
- budowanie komend CLI i argv;
- mapowanie exit code → domenowe rezultaty;
- serializacja/deserializacja stanu;
- reguły retry/timeouts/backoff.

Dobre kandydaty na **integration tests**:
- aktywacja extension;
- rejestracja komend;
- interakcja z `vscode.workspace`, `vscode.window`, `commands.executeCommand`;
- tworzenie terminali;
- czytanie settings z workspace;
- zachowanie w multi-root;
- integracja z prawdziwym procesem pomocniczym lub stub CLI.

**Wniosek:** W dojrzałym setupie integration tests powinny być mniejsze liczbowo, ale krytyczne ścieżki host/runtime muszą być nimi pokryte. — siła dowodów: **praktyczne** + **spekulacja**

### C4. Mocking VS Code API

**Wniosek:** Oficjalne docs nie promują jednej biblioteki do mockowania `vscode`; najbardziej stabilny wzorzec to własna cienka warstwa adapterów + manual mocks w Jest/Vitest. — siła dowodów: **praktyczne**

Dlaczego:
- `vscode` nie działa jak zwykły runtime dependency poza hostem;
- bezpośrednie mockowanie całego API szybko staje się kruche;
- dużo stabilniej mockować własne porty/adapters typu:
  - `showInfo()`
  - `getWorkspaceFolders()`
  - `executeCommand()`
  - `createTerminal()`

W praktyce:
- `vscode.window`, `vscode.commands`, `vscode.workspace` najlepiej mockować selektywnie;
- testy jednostkowe powinny unikać dotykania pełnego API surface;
- dla UI-level end-to-end istnieją community tools (np. ExTester), ale to osobna warstwa niż unit/integration.

### C5. CI pipeline

**Wniosek:** Testy extension da się uruchamiać w CI bez klasycznego GUI; standardem na Linuxie jest headless run z `xvfb-run`. — siła dowodów: **praktyczne**

Oficjalne docs CI pokazują ten model wprost. Sensowny pipeline:
1. install dependencies
2. lint / typecheck
3. unit tests
4. integration tests przez VS Code host
5. optional package smoke test (`vsce package`)

Dobre praktyki:
- uruchamiać integration tests z `--disable-extensions`, by ograniczyć flakiness;
- przypinać lub testować zakres wspieranych wersji VS Code;
- trzymać fixtures i stuby CLI w repo, żeby testy nie zależały od maszyny buildowej.

GitHub Actions jest tu naturalnym wyborem, ale wzorzec jest przenośny na dowolne CI.

## D. Debugging i logging

### D1. Output Channel / LogOutputChannel

**Wniosek:** Dla extension produkcyjnej lepszy jest dedykowany **`LogOutputChannel`** niż surowy `console.log`. — siła dowodów: **praktyczne**

VS Code API wspiera dwa istotne tryby:
- `createOutputChannel(name)` — zwykły output;
- `createOutputChannel(name, { log: true })` — **log output channel** z poziomami logowania.

Korzyści:
- standardowe metody `trace/debug/info/warn/error`;
- logi pojawiają się w Output jako kanał logów VS Code;
- można reagować na `logLevel` i `onDidChangeLogLevel`.

**Wniosek:** Structured logging ma sens nawet w extension bez własnego backendu. — siła dowodów: **praktyczne** + **spekulacja**

Dobrze logować pola, nie tylko stringi:
- `event`
- `command`
- `cwd`
- `workspaceFolder`
- `executable`
- `pid`
- `durationMs`
- `exitCode`
- `correlationId`
- `errorName` / `errorCode`

To daje możliwość reprodukcji błędów bez czytania przypadkowych `console.log`.

### D2. Extension Host logs: gdzie szukać

**Wniosek:** Główne trzy miejsca diagnozy to: `Developer: Show Logs...`, Output → `Log (Extension Host)` / `Log (Remote Extension Host)`, oraz `Developer: Show Running Extensions`. — siła dowodów: **praktyczne**

Praktyczne zastosowanie:
- `Show Logs...` — szybkie wejście do logów procesu;
- Output channel hosta — najlepszy do stack traces, activation failures i runtime errors;
- `Show Running Extensions` — pokazuje gdzie extension działa (local/remote), ile zużywa i czy problem wynika z niewłaściwego hosta.

To jest szczególnie ważne dla extension współpracujących z terminalem, procesami i remote development.

### D3. Activation errors

**Wniosek:** Problemy z aktywacją trzeba rozdzielać na trzy klasy: manifest, host placement, runtime exception. — siła dowodów: **praktyczne** + **spekulacja**

1. **Manifest / deklaracje**
   - `engines.vscode`
   - `main`
   - `activationEvents`
   - `contributes`
   - zgodność inferred activation events od VS Code 1.74+

2. **Host placement**
   - local vs remote;
   - `extensionKind`;
   - czy extension uruchamia się w ogóle tam, gdzie ma dostęp do potrzebnych zasobów.

3. **Runtime**
   - wyjątek w `activate()`;
   - nieobsłużone błędy w callbackach/event listenerach;
   - błędy ścieżek / CWD / missing executable.

**Wniosek:** Dla aktywacji przydatne jest rozróżnienie trybu uruchomienia (`Development`, `Production`, `Test`). — siła dowodów: **praktyczne**

To pozwala uniknąć mylenia:
- F5 z kodu źródłowego,
- instalacji `.vsix`,
- execution w harnessie testowym.

### D4. Structured logging vs `console.log`

**Wniosek:** `console.log` jest użyteczne jako lokalny, doraźny debug, ale nie powinno być główną strategią diagnostyczną. — siła dowodów: **praktyczne** + **spekulacja**

Dlaczego:
- brak poziomów logowania;
- brak stabilnego formatu;
- słabe wsparcie dla supportu użytkownika;
- trudniej filtrować i korelować zdarzenia.

Dojrzały wzorzec:
- kanał logów dla użytkownika/developera;
- opcjonalne logi plikowe pod `context.logUri`;
- event IDs / correlation IDs dla ścieżek subprocessowych;
- możliwość podniesienia verbosity bez zmiany kodu diagnostycznego.

## E. CWD i process isolation

### E1. Czy extension ma gwarantowane CWD?

**Wniosek:** Nie należy zakładać, że extension „dziedziczy sensowny workspace CWD”. Dla child process default to `process.cwd()`, jeśli `cwd` nie zostanie ustawione. — siła dowodów: **praktyczne**

To jest krytyczne:
- `child_process.spawn` / `execFile` mają opcję `cwd`;
- gdy jej nie podasz, Node użyje bieżącego CWD procesu;
- to nie jest semantycznie równoważne „aktywnemu folderowi użytkownika”.

**Wniosek:** Każdy subprocess uruchamiany przez extension powinien dostawać jawne `cwd`. — siła dowodów: **praktyczne** + **spekulacja**

Najbezpieczniejsza kolejność wyboru:
1. folder wybrany explicite przez użytkownika/konfigurację,
2. konkretny `workspaceFolder`,
3. fallback „brak workspace” obsłużony jawnie,
4. dopiero na końcu ewentualny bezpieczny default.

Uwaga:
- `createTerminal(...)` ma osobną semantykę i może domyślnie używać katalogu workspace, jeśli istnieje;
- to **nie przenosi się** automatycznie na `child_process.spawn()`.

### E2. `execFile` / `spawn`: absolutne vs relatywne ścieżki

**Wniosek:** Dla executable i ważnych input paths lepsze są ścieżki absolutne; relatywne mają sens dopiero po jawnej rezolucji względem workspace albo extension install path. — siła dowodów: **praktyczne**

Dodatkowo:
- `execFile()` uruchamia plik bez shella (bezpieczniejsze dla quoting/escaping);
- `exec()` uruchamia przez shell i powinno być używane tylko, gdy faktycznie potrzebujesz składni powłoki;
- `spawn()` i `execFile()` są dobrym defaultem dla integracji CLI.

Dla plików należących do samej extension:
- używaj ścieżek wyprowadzonych z extension context (`context.asAbsolutePath(...)`, `Uri.joinPath(...)`);
- nie zakładaj stałej lokalizacji typu `~/.vscode/extensions/...`, bo remote i różne hosty łamią takie założenia.

### E3. `workspace.workspaceFolders`: kiedy undefined

**Wniosek:** `workspace.workspaceFolders` może być `undefined`, gdy użytkownik nie ma otwartego żadnego folderu/workspace. — siła dowodów: **praktyczne**

To oznacza, że extension musi umieć żyć w co najmniej trzech stanach:
- **no-folder / empty window**
- **single-root**
- **multi-root**

Każdy kod, który wybiera CWD, config scope albo path resolution, powinien te tryby rozróżniać jawnie.

### E4. Multi-root workspaces

**Wniosek:** Multi-root nie jest edge case’em — jest pełnoprawnym modelem pracy i wpływa na CWD, settings scope, launch configs i path variables. — siła dowodów: **praktyczne**

Co zmienia multi-root:
- jedno okno ma wiele folderów projektu;
- globalne workspace settings trafiają do `.code-workspace`;
- per-folder `.vscode/settings.json` działają tylko dla ustawień resource-scoped;
- path variables mogą wymagać jawnego folder scope, np. `${workspaceFolder:Program}`;
- część extensions, które nie wspierają multi-root, działa tylko względem pierwszego folderu.

**Wniosek:** Dla extension orkiestrującej CLI „pierwszy folder” nie powinien być traktowany jako uniwersalny default semantyczny. — siła dowodów: **praktyczne** + **spekulacja**

Lepsze wzorce:
- działać na aktywnym dokumencie → wyprowadzać `workspaceFolder` od dokumentu;
- przy command-level operacjach pytać o folder;
- cachować stan per-folder, nie globalnie.

## F. Extension architecture patterns

### F1. Activation events: lazy vs eager

**Wniosek:** Lazy activation powinno być domyślne; `*` należy traktować jako wyjątek wymagający mocnego uzasadnienia. — siła dowodów: **praktyczne**

Powód jest bezpośredni: docs o Extension Host akcentują startup performance i lazy loading extensions przez activation events.

Dodatkowo od VS Code 1.74 część activation events dla contribution points może być inferowana automatycznie (np. commands, views, languages, authentication), jeżeli `engines.vscode` jest odpowiednio nowe.

W praktyce:
- `onCommand:*`, `onUri`, `workspaceContains:*`, `onLanguage:*` są zdrowym defaultem;
- `*` ma sens tylko dla rozszerzeń, które naprawdę muszą zacząć pracę przy starcie okna.

### F2. Disposable pattern

**Wniosek:** `context.subscriptions` powinno być centralnym rejestrem wszystkiego, co da się zdysponować. — siła dowodów: **praktyczne**

To obejmuje:
- command registrations,
- event listeners,
- file watchers,
- output channels,
- terminals,
- status bar items,
- timers / cancellables opakowane w disposable.

Ważny detal z API:
- elementy w `context.subscriptions` są czyszczone przy deaktywacji;
- asynchroniczny dispose **nie jest awaitowany**.

**Wniosek:** Długie, krytyczne cleanupy procesów nie powinny polegać wyłącznie na „magii deactivation”. — siła dowodów: **praktyczne** + **spekulacja**

Typowe wycieki:
- listeners bez dispose;
- child processy bez kill/timeout policy;
- terminale pozostawione po błędzie;
- watchery file systemu działające poza lifecycle komendy.

### F3. State management: `globalState` vs `workspaceState` vs pliki

**Wniosek:** `globalState` i `workspaceState` są dobre do małego key-value state, ale nie powinny być traktowane jak magazyn większych blobów i logów. — siła dowodów: **praktyczne** + **spekulacja**

Rozdział odpowiedzialności:
- `globalState` — stan niezależny od aktualnego workspace;
- `workspaceState` — stan kontekstowy dla aktualnego workspace;
- `globalStorageUri` / `storageUri` — pliki i prywatne dane większe niż prosty Memento;
- `secrets` — dane wrażliwe.

Ważna granica:
- `storageUri` jest `undefined`, gdy nie ma otwartego workspace/folderu;
- dlatego kod zapisujący pliki workspace-scoped musi umieć działać bez tego założenia.

**Wniosek:** Oficjalne docs nie podają twardych limitów pojemności dla Memento; to obszar, gdzie trzeba zachować ostrożność. — siła dowodów: **praktyczne**

### F4. Komunikacja z external tools: subprocess vs LSP vs WebSocket

**Wniosek:** Dla extension, której główną rolą jest orkiestracja zewnętrznych CLI, **subprocess** jest najniższym kosztem wejścia i najbardziej naturalnym punktem startowym. — siła dowodów: **praktyczne** + **spekulacja**

Zalety subprocess:
- niski koszt implementacji;
- łatwy mapping stdout/stderr/exit code;
- dobry fit do „wywołaj narzędzie, zbierz wynik, pokaż w VS Code”.

**Wniosek:** **LSP** staje się sensowne, gdy narzędzie jest długowieczne, CPU/memory-intensive, językowo-zorientowane albo ma być współdzielone między editorami. — siła dowodów: **praktyczne**

Oficjalny guide LSP podkreśla:
- separację procesu i kosztów wydajnościowych;
- możliwość implementacji serwera w innym języku;
- wzorzec multi-root przez osobny serwer per workspace folder;
- przewagę standardowego protokołu dla złożonych language features.

**Wniosek:** **WebSocket** ma sens głównie wtedy, gdy po drugiej stronie już istnieje daemon/service lub potrzebujesz trwałego, streamingowego połączenia z komponentem zdalnym. — siła dowodów: **spekulacja**

Trade-offy:
- **subprocess** — najprostszy lifecycle, ale trzeba samemu rozwiązać retries, streaming, concurrency;
- **LSP** — większy narzut architektoniczny, za to lepsza izolacja i standard dla language-like services;
- **WebSocket** — dobry do live sessions / remote daemons, ale wprowadza więcej problemów sieciowych, reconnectów i security surface.

## Otwarte pytania / luki w wiedzy

- **Nie udało się potwierdzić oficjalnego, twardego limitu rozmiaru dla `globalState` / `workspaceState` / Memento.** Docs opisują semantykę, ale nie publikują limitów operacyjnych.
- **Nie znaleziono oficjalnego źródła, które promowałoby jedną bibliotekę do mockowania VS Code API.** Oficjalne docs opisują test host i harness, ale nie standaryzują mocking layer.
- **Nie znaleziono oficjalnej rekomendacji „rób symlink do `~/.vscode/extensions`”.** Oficjalne wzorce to `--extensionDevelopmentPath`, izolowane `--extensions-dir` oraz od 2024 local workspace extensions. Wniosek, że symlink to workflow drugorzędny, jest interpretacją.
- **Hot reload pozostaje częściowo niejawny.** Jest jasne, że `Reload Window` działa, a `Restart extensions` istnieje dla update’ów extension, ale szczegółowe zachowanie wszystkich typów zmian (zwłaszcza manifest/contributes vs runtime state) nie jest zebrane w jednym oficjalnym miejscu.
- **Bundling vs `tsc`-only nie jest sprzecznością, tylko wyborem kontekstowym.** Oficjalne docs rekomendują bundling, ale dla małych desktop-only extensions `tsc`-only nadal jest wykonalne — brak twardej granicy „od jakiego rozmiaru trzeba bundle’ować”.
- **Dla UI automation narzędzia community istnieją, ale nie są first-party standardem.** To oznacza większe ryzyko maintenance niż w przypadku `@vscode/test-electron`.

## Źródła / odniesienia

### Oficjalne VS Code docs i API

- [Your First Extension](https://code.visualstudio.com/api/get-started/your-first-extension) — oficjalny podstawowy workflow developmentu, F5, reload okna, debugging extension.
- [Extension Anatomy](https://code.visualstudio.com/api/get-started/extension-anatomy) — canonical project structure, `package.json`, `main`, `activationEvents`, `context.subscriptions`.
- [Testing Extensions](https://code.visualstudio.com/api/working-with-extensions/testing-extension) — oficjalny harness testowy, `@vscode/test-electron`, CLI, workspace fixtures, custom runner.
- [Publishing Extensions](https://code.visualstudio.com/api/working-with-extensions/publishing-extension) — `vsce package`, `vsce publish`, `.vscodeignore`, pre-release, publishing pipeline.
- [Bundling Extensions](https://code.visualstudio.com/api/working-with-extensions/bundling-extension) — rekomendacja bundlingu, esbuild/webpack examples, wymagania dla web extensions.
- [VS Code API Reference](https://code.visualstudio.com/api/references/vscode-api) — `createOutputChannel`, `LogOutputChannel`, `globalState`, `workspaceState`, `storageUri`, `workspaceFolders`, `context.subscriptions`, `ExtensionMode`.
- [Activation Events](https://code.visualstudio.com/api/references/activation-events) — model aktywacji i lazy loading.
- [Extension Host](https://code.visualstudio.com/api/advanced-topics/extension-host) — powody dla lazy activation i kwestie performance/stability.
- [Supporting Remote Development and GitHub Codespaces](https://code.visualstudio.com/api/advanced-topics/remote-extensions) — host placement, testowanie extension w remote, storage/path considerations.
- [Language Server Extension Guide](https://code.visualstudio.com/api/language-extensions/language-server-extension-guide) — trade-offy LSP, separacja procesu, multi-root server pattern.
- [Command Line Interface](https://code.visualstudio.com/docs/configure/command-line) — `--install-extension`, `--extensions-dir`, `--user-data-dir`, CLI install z `.vsix`.
- [Multi-root Workspaces](https://code.visualstudio.com/docs/editing/workspaces/multi-root-workspaces) — semantyka multi-root, `.code-workspace`, settings scopes, path variables.

### VS Code release notes (źródła zmian 2024+)

- [March 2024 (VS Code 1.88)](https://code.visualstudio.com/updates/v1_88) — `Restart extensions`, zachowanie update flow, ograniczenia remote.
- [April 2024 (VS Code 1.89)](https://code.visualstudio.com/updates/v1_89) — general availability dla local workspace extensions (`.vscode/extensions`).
- [May 2024 (VS Code 1.90)](https://code.visualstudio.com/updates/v1_90) — generator `yo code` z opcją scaffoldingu esbuild (użyte do oceny aktualnego defaultu bundlera).

### Narzędzia i repozytoria oficjalne / quasi-oficjalne

- [@vscode/vsce repository](https://github.com/microsoft/vscode-vsce) — źródło praktycznych informacji o managerze packaging/publishing oraz aktualnych wymaganiach narzędzia.
- [vscode-test repository README](https://github.com/microsoft/vscode-test) — historyczne/narzędziowe źródło dla `runTests`, wersjonowania VS Code w testach i opcji harnessu.

### Źródła uzupełniające spoza VS Code

- [Node.js `child_process` docs](https://nodejs.org/api/child_process.html) — źródło prawdy dla `spawn`, `exec`, `execFile`, `cwd`, shell vs no-shell.
- [Jest Manual Mocks](https://jestjs.io/docs/manual-mocks) — źródło dla wzorca manual mocking przy unit testach poza hostem.
- [ExTester / vscode-extension-tester](https://github.com/redhat-developer/vscode-extension-tester) — community narzędzie do UI/E2E tests dla extensions; użyte tylko jako opcja dodatkowa, nie jako standard first-party.
