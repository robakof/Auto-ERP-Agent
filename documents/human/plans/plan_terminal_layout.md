# Plan: Terminal Layout — 1 rola = 1 grupa, instancje = karty

## Cel
Każda rola ma osobną grupę edytora (ViewColumn). Wiele instancji tej samej roli = karty w jednej grupie. Dispatcher może przełączać aktywną kartę (karuzela).

## Mechanizm VS Code API
`vscode.window.createTerminal({ location: { viewColumn: ViewColumn.Two } })` — tworzy terminal w konkretnej grupie edytora. Drugi terminal z tym samym viewColumn = nowa karta w tej grupie.

## Zmiany

### 1. Nowy plik: `src/layout.ts` — RoleLayout
- `roleColumns: Map<string, ViewColumn>` — rola → przypisana kolumna
- `roleTerminals: Map<string, Terminal[]>` — rola → lista terminali
- `carouselIndex: number` — globalny indeks karuzeli
- Metody:
  - `getViewColumn(role)` → przypisuje i zwraca ViewColumn
  - `addTerminal(role, terminal)` — rejestruje terminal
  - `removeTerminal(terminal)` — wyrejestrowuje (watcher wywołuje)
  - `focusRole(role)` — aktywuje pierwszy terminal roli
  - `rotateNext()` — karuzela: następny terminal globalnie
  - `getAllTerminals()` — flat lista aktywnych terminali

### 2. Modyfikacja: `src/spawner.ts`
- Konstruktor przyjmuje `RoleLayout`
- `spawn()`: zamiast `TerminalLocation.Editor` → `{ viewColumn: layout.getViewColumn(role) }`
- Po stworzeniu: `layout.addTerminal(role, terminal)`

### 3. Modyfikacja: `src/extension.ts`
- Inicjalizacja `RoleLayout` w `activate()`
- Przekazanie do `Spawner`
- Nowe URI handlers: `focusAgent` (param: `role`), `rotateTab` (brak param)
- `resumeAgent`: używa `layout.getViewColumn(role)` zamiast hardcoded location

### 4. Modyfikacja: `src/watcher.ts`
- Konstruktor przyjmuje `RoleLayout`
- Na `onDidCloseTerminal`: `layout.removeTerminal(terminal)`

### 5. Modyfikacja: `src/commands.ts`
- `mrowisko.focusAgent` — quick pick roli, fokus na grupę
- `mrowisko.rotateTab` — karuzela (bez dialogu, instant)

### 6. Modyfikacja: `package.json`
- Rejestracja nowych komend + keybinding dla rotateTab

### 7. Modyfikacja: `tools/vscode_uri.py`
- `focusAgent --role <role>` — URI command
- `rotateTab` — URI command

## Zachowanie edge case
- Lokalizacja "panel" — ignoruje layout (panel nie ma ViewColumn), fallback na dotychczasowe zachowanie
- Role pojawiają się dynamicznie — kolumny 1,2,3... w kolejności pierwszego spawnu
- Terminal zamknięty gdy jest ostatni w roli → kolumna zwolniona (recycle w przyszłości)

## Kolejność implementacji
1. layout.ts (nowy)
2. spawner.ts (viewColumn)
3. watcher.ts (removeTerminal)
4. extension.ts (init + URI handlers)
5. commands.ts (nowe komendy)
6. package.json (rejestracja)
7. vscode_uri.py (CLI support)
8. Build + test
