# Eksperyment E4: Test wtyczki VS Code Terminal Control

**Cel:** Sprawdzić czy agent może kontrolować terminale VS Code (tworzyć, uruchamiać komendy, zachować interaktywność).

**Status wtyczki:** ✓ Skompilowana i gotowa do testu

---

## Jak przetestować (2 opcje)

### Opcja A: Tryb Development (ZALECANE - najszybsze)

1. **Otwórz folder wtyczki w NOWYM oknie VS Code:**
   ```
   File → Open Folder → extensions/mrowisko-terminal-control
   ```

2. **Uruchom Extension Development Host:**
   - Naciśnij `F5`
   - LUB `Run → Start Debugging`
   - Otworzy się **nowe okno VS Code** z napisem "[Extension Development Host]"

3. **W nowym oknie testowym:**
   - Otwórz Command Palette: `Ctrl+Shift+P`
   - Wpisz: `Mrowisko`
   - Zobaczysz 2 komendy:
     - `Mrowisko: Test Terminal Control`
     - `Mrowisko: Spawn Agent`

4. **Test 1 - Prosty terminal:**
   - Wybierz: `Mrowisko: Test Terminal Control`
   - **Sprawdź:**
     - ✓ Czy pojawił się nowy terminal "Mrowisko Test"?
     - ✓ Czy widzisz output: "Mrowisko Terminal Control - test OK"?
   - **Wynik:** Jeśli TAK → wtyczka ma kontrolę nad terminalami ✓

5. **Test 2 - Spawn agent:**
   - Wybierz: `Mrowisko: Spawn Agent`
   - Wybierz rolę: `developer`
   - Wpisz task: `Wypisz zawartość tools/ narzędziem Glob (pattern: tools/*.py)`
   - **Sprawdź:**
     - ✓ Czy pojawił się terminal "Agent: developer"?
     - ✓ Czy Claude Code uruchomił się?
     - ✓ Czy agent wykonuje task (Glob tools/*.py)?
     - ✓ **CZY MOŻESZ PISAĆ W TERMINALU?** (wpisz coś ręcznie)
   - **Wynik:** Jeśli możesz pisać → interaktywność działa ✓

---

### Opcja B: Instalacja przez .vsix (jeśli F5 nie działa)

1. **Zainstaluj narzędzie do pakowania:**
   ```bash
   npm install -g @vscode/vsce
   ```

2. **Spakuj wtyczkę:**
   ```bash
   cd extensions/mrowisko-terminal-control
   vsce package
   ```
   To stworzy plik: `mrowisko-terminal-control-0.1.0.vsix`

3. **Zainstaluj w VS Code:**
   ```bash
   code --install-extension mrowisko-terminal-control-0.1.0.vsix
   ```
   LUB przez GUI:
   - Extensions (Ctrl+Shift+X)
   - Menu `...` → Install from VSIX
   - Wybierz `mrowisko-terminal-control-0.1.0.vsix`

4. **Reload VS Code** (może wymagać)

5. **Testuj** (jak w Opcji A, punkty 3-5)

---

## Co sprawdzamy?

| Test | Pytanie | Sukces = |
|------|---------|----------|
| Test 1 | Czy mogę utworzyć terminal? | Terminal "Mrowisko Test" pojawił się |
| Test 1 | Czy mogę wysłać komendę? | Widzisz output "test OK" |
| Test 2 | Czy mogę uruchomić Claude? | Terminal "Agent: developer" z sesją Claude |
| Test 2 | Czy agent wykonuje task? | Glob tools/*.py wyświetlone |
| Test 2 | **Czy terminal interaktywny?** | **Możesz pisać wiadomości do agenta** |

---

## Wyniki eksperymentu

### Jeśli WSZYSTKO działa (wszystkie ✓):

**Implikacje:**
- ✓ Agent może spawnować innych agentów w osobnych terminalach VS Code
- ✓ Człowiek widzi wszystkie sesje (split view)
- ✓ Człowiek może dołączyć do dowolnej sesji w dowolnym momencie
- ✓ **Rozwiązuje problem runner bez interaktywności**

**Następny krok:**
- Rozbudowa wtyczki (integracja z agent_bus, backlog, multi-agent view)
- **mrowisko_runner.py v2 = wtyczka VS Code** (nie CLI)

---

### Jeśli NIE działa:

**Możliwe problemy:**

1. **Terminal się nie tworzy** → błąd w kodzie wtyczki, sprawdź Output → Extension Host
2. **Claude nie uruchamia się** → sprawdź czy `claude` w PATH: `where claude`
3. **Agent uruchamia się ale nie możesz pisać** → problem z VS Code Terminal API (limitation)

**Alternatywy:**
- Windows Terminal integration (`wt.exe` split-pane)
- tmux/screen (wymaga WSL)
- Subprocess bez interaktywności (obecny mrowisko_runner.py)

---

## Raportowanie wyników

Po testach powiedz mi:

1. **Test 1 (prosty terminal):** Działa / Nie działa
2. **Test 2 (spawn agent):**
   - Agent uruchomił się: TAK / NIE
   - Agent wykonał task: TAK / NIE
   - **Możesz pisać w terminalu: TAK / NIE** ← KLUCZOWE

3. **Screenshot** (opcjonalnie) - pokaż terminal z agentem

---

## Troubleshooting

**F5 nie działa / brak Extension Development Host:**
→ Upewnij się że otworzyłeś folder `extensions/mrowisko-terminal-control` (nie główny folder Mrowisko)

**Błąd: "Cannot find module 'vscode'":**
→ Uruchom w folderze wtyczki: `npm install`

**Komenda nie pojawia się w Command Palette:**
→ Sprawdź Output → Extension Host (Ctrl+Shift+U) - czy są błędy?

**Terminal uruchamia się ale Claude nie:**
→ Zmień w extension.ts linię 51 na: `claude.cmd` (Windows wymaga .cmd)

---

## Lokalizacja plików

- Wtyczka: `extensions/mrowisko-terminal-control/`
- Kod źródłowy: `src/extension.ts`
- Skompilowany: `out/extension.js`
- README z instrukcjami: `README.md`

---

**Powodzenia! Zgłoś wyniki — jeśli działa, to game changer dla runnera.**

