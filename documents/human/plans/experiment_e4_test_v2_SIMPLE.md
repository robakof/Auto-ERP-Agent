# Eksperyment E4 v2: Test wtyczki - UPROSZCZONY

**Fix:** Naprawiono błędy komendy (`claude.cmd`, escapowanie cudzysłowów)
**Cel:** Sprawdzić czy agent może kontrolować terminale VS Code

---

## WAŻNE: Otwórz NOWE okno VS Code (nie zastępuj obecnego)

**Przed testem:**
1. Zapisz obecną pracę (ta sesja)
2. **File → New Window** (lub `Ctrl+Shift+N`) — otworzy się puste okno VS Code
3. W nowym oknie: **File → Open Folder** → `extensions/mrowisko-terminal-control`

Teraz masz:
- **Okno 1:** Główny projekt (ta sesja z agentem) — NIE ZAMYKAJ
- **Okno 2:** Folder wtyczki (do testów) — testuj tutaj

---

## Test 1: Prosty terminal (5 sekund, zero ryzyka)

**W oknie 2 (folder wtyczki):**

1. Naciśnij `F5` (uruchomi Extension Development Host)
   - Jeśli pyta o konfigurację → wybierz "VS Code Extension Development"
   - Otworzy się **nowe okno 3** z napisem "[Extension Development Host]"

2. **W oknie 3 (testowym):**
   - `Ctrl+Shift+P` (Command Palette)
   - Wpisz: `Mrowisko: Test Terminal Control`
   - Naciśnij Enter

3. **Sprawdź:**
   - ✓ Czy pojawił się terminal "Mrowisko Test" (u dołu okna)?
   - ✓ Czy widzisz 3 linie outputu:
     ```
     Mrowisko Terminal Control - test OK
     Czy widzisz ten output?
     Jesli TAK - wtyczka ma kontrole nad terminalami!
     ```

**Jeśli widzisz → SUKCES** ✓ Wtyczka ma kontrolę nad terminalami!

---

## Test 2: Spawn Agent (tylko jeśli Test 1 działa)

**W oknie 3 (testowym):**

1. `Ctrl+Shift+P`
2. Wpisz: `Mrowisko: Spawn Agent`
3. Wybierz rolę: `developer`
4. Wpisz task: `Wypisz 'test' i zakoncz`

5. **Sprawdź:**
   - ✓ Czy terminal "Agent: developer" się pojawił?
   - ✓ Czy Claude uruchomił się? (widzisz sesję Claude Code)
   - ✓ **Czy możesz pisać w terminalu?** (spróbuj wpisać coś ręcznie)

**Jeśli możesz pisać → PEŁNY SUKCES** ✓✓

---

## Co raportować?

**Test 1:**
- [ ] Terminal "Mrowisko Test" pojawił się
- [ ] Widzę 3 linie echo

**Test 2:**
- [ ] Terminal "Agent: developer" pojawił się
- [ ] Claude uruchomił się
- [ ] **Mogę pisać w terminalu** ← KLUCZOWE

---

## Troubleshooting (jeśli coś nie działa)

**F5 nie uruchamia Extension Development Host:**
→ Sprawdź czy jesteś w folderze `extensions/mrowisko-terminal-control` (nie w głównym Mrowisko)

**Komenda nie pojawia się w Command Palette:**
→ Sprawdź Output panel → Extension Host (Ctrl+Shift+U) - szukaj błędów

**Terminal pojawia się ale puste (brak echo):**
→ To może być problem z PowerShell - ale wtyczka DZIAŁA (tworzy terminale)

**"Zapętlenie komend" jak poprzednio:**
→ Przeładuj wtyczkę: w oknie 2 naciśnij `Ctrl+R` (reload Extension Development Host)

---

## Co zmieniono od v1?

1. **Fix:** `claude` → `claude.cmd` (Windows wymaga .cmd)
2. **Fix:** Escapowanie cudzysłowów w systemPrompt
3. **Uproszczenie:** Test 1 tylko echo (zero ryzyka błędu)
4. **Instrukcje:** Otwórz nowe okno (nie zamykaj głównego)

---

**Jeśli Test 1 działa** → wtyczka może tworzyć terminale ✓
**Jeśli Test 2 działa** → wtyczka może uruchamiać Claude interaktywnie ✓✓
**Jeśli możesz pisać** → GAME CHANGER dla runnera ✓✓✓

Raportuj wyniki!

