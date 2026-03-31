# Mrowisko Terminal Control - Eksperyment E4

Minimalna wtyczka VS Code testująca możliwość kontroli terminali przez agenta.

## Cel eksperymentu

Sprawdzić czy agent może:
1. ✓ Utworzyć nowy terminal w VS Code programmatically
2. ✓ Uruchomić komendę `claude` w terminalu
3. ✓ Zostawić terminal interaktywny dla człowieka

## Instalacja i test

### Krok 1: Instalacja zależności

```bash
cd extensions/mrowisko-terminal-control
npm install
```

### Krok 2: Kompilacja

```bash
npm run compile
```

To stworzy `out/extension.js` z skompilowanego TypeScript.

### Krok 3: Instalacja wtyczki w VS Code

**Opcja A: Tryb development (F5)**
1. Otwórz folder `extensions/mrowisko-terminal-control` w VS Code
2. Naciśnij `F5` (uruchomi Extension Development Host)
3. W nowym oknie VS Code otwórz Command Palette (`Ctrl+Shift+P`)
4. Wpisz: `Mrowisko: Test Terminal Control`

**Opcja B: Instalacja przez .vsix**
```bash
# 1. Zainstaluj vsce (VS Code Extension CLI)
npm install -g @vscode/vsce

# 2. Spakuj wtyczkę
vsce package

# 3. Zainstaluj lokalnie
code --install-extension mrowisko-terminal-control-0.1.0.vsix
```

### Krok 4: Uruchom test

**Test 1: Prosty terminal**
1. Command Palette (`Ctrl+Shift+P`)
2. Wpisz: `Mrowisko: Test Terminal Control`
3. **Weryfikacja:** Czy widzisz nowy terminal z "Mrowisko Test" i output echo?

**Test 2: Spawn agent**
1. Command Palette (`Ctrl+Shift+P`)
2. Wpisz: `Mrowisko: Spawn Agent`
3. Wybierz rolę (np. `developer`)
4. Wpisz task (np. `Wypisz zawartość katalogu tools/ narzędziem Glob`)
5. **Weryfikacja:**
   - Czy widzisz nowy terminal "Agent: developer"?
   - Czy Claude Code uruchomił się w tym terminalu?
   - Czy agent wykonuje task?
   - Czy możesz pisać w terminalu (interaktywność)?

## Komendy wtyczki

| Komenda | Opis |
|---------|------|
| `Mrowisko: Test Terminal Control` | Test podstawowy - echo w nowym terminalu |
| `Mrowisko: Spawn Agent` | Uruchom agenta w nowym terminalu (wybór roli + task) |

## Co sprawdzamy?

| Pytanie | Test |
|---------|------|
| Czy mogę utworzyć terminal? | Test 1 - podstawowy terminal |
| Czy mogę wysłać komendę? | Test 1 - sendText('echo ...') |
| Czy mogę uruchomić Claude? | Test 2 - claude -p developer |
| Czy terminal jest interaktywny? | Test 2 - spróbuj pisać w terminalu ręcznie |
| Czy human może dołączyć? | Test 2 - agent działa, Ty piszesz wiadomość |

## Struktura kodu

```typescript
// Utworzenie terminala
const terminal = vscode.window.createTerminal('Nazwa');

// Wyświetlenie terminala
terminal.show();

// Wysłanie komendy
terminal.sendText('claude -p "developer" ...');

// Terminal pozostaje interaktywny - human może pisać!
```

## Wynik eksperymentu

### Sukces oznacza:
- ✓ Terminal utworzony w VS Code
- ✓ Komenda `claude` uruchomiona
- ✓ Agent wykonuje task autonomicznie
- ✓ Human może pisać w terminalu (dołączyć do sesji)

### Jeśli działa → implikacje:

**Agent może:**
1. Spawnować innych agentów w osobnych terminalach
2. Człowiek widzi wszystkie sesje (split view w VS Code)
3. Człowiek może dołączyć do dowolnej sesji (pisze w terminalu)
4. Rozwiązuje problem "runner bez interaktywności"

**mrowisko_runner.py v2 może być wtyczką VS Code** zamiast CLI.

### Jeśli nie działa → alternatywy:

- Windows Terminal integration (split panes przez `wt.exe`)
- tmux/screen (wymaga WSL na Windows)
- Własny renderer (bez shared terminal)

## Troubleshooting

**Błąd: "Cannot find module 'vscode'"**
→ Uruchom: `npm install`

**Błąd kompilacji TypeScript**
→ Sprawdź czy TypeScript zainstalowany: `npm install -g typescript`
→ Uruchom: `npm run compile`

**Wtyczka nie pojawia się w Command Palette**
→ Sprawdź czy Extension Development Host uruchomiony (F5)
→ Sprawdź Output → Extension Host (czy są błędy)

**Terminal nie uruchamia Claude**
→ Sprawdź czy `claude` dostępny w PATH: `where claude`
→ Może wymagać `claude.cmd` na Windows

## Następne kroki (jeśli sukces)

1. Rozbudowa wtyczki: parametry (max-turns, budget, tools)
2. Integracja z agent_bus (czytanie backlog → spawn)
3. Multi-agent view (split terminals dla wielu agentów)
4. Monitoring (status agentów, heartbeat)
5. Zamiana mrowisko_runner.py → wtyczka VS Code

