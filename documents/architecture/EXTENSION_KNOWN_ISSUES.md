# Extension Known Issues — Claude Code terminal workarounds

**Data:** 2026-03-30
**Cel:** Dokumentacja workaroundow odkrytych podczas rozwoju extension.
Dev MUSI przeczytac ten plik przed rewrite — te problemy wrocą.

---

## W1: "/" artifact po starcie Claude Code (CRITICAL)

**Problem:** Claude Code 2.1.83+ wstrzykuje znak "/" do input terminala po starcie.
Jesli extension wyśle tekst zanim "/" zostanie wyczyszczony — Claude Code interpretuje
go jako slash command i blokuje sesje.

**Workaround:**
```typescript
// 1. Wyslij pusty Enter — czyści "/" artifact
terminal.sendText("", true);
// 2. Poczekaj 300-500ms
setTimeout(() => {
  // 3. Dopiero teraz wyslij prawdziwy tekst
  terminal.sendText(actualMessage);
}, 500);
```

**Dotyczy:** Kazde sendText do terminala Claude Code — spawn, poke, resume.
**Zrodlo:** Commit fffd89b, spawner.ts:72-76, extension.ts:104-107.
**Status:** Aktywny workaround. Bug w Claude Code — nie w naszym kodzie.

---

## W2: Startup delay — Claude Code potrzebuje czasu na init (CRITICAL)

**Problem:** Po uruchomieniu `claude` w terminalu, Claude Code laduje CLAUDE.md,
session_init, prompty rol. Trwa to 4-15s w zaleznosci od rozmiaru projektu.
Tekst wyslany przed zakonczeniem initu jest tracony lub interpretowany blednie.

**Workaround:**
```typescript
const STARTUP_DELAY_MS = 12000; // 12s — safe for large projects
setTimeout(() => {
  // Dopiero teraz wyslij pierwszy message
  terminal.sendText("", true);  // clear "/" (W1)
  setTimeout(() => terminal.sendText(task), 500);
}, STARTUP_DELAY_MS);
```

**Historia:** Bylo 4s (commit 8c80e77) → za malo → zwiekszone do 12s (commit e630944).
**Konfigurowalnosc:** `mrowisko.startupDelayMs` w settings (default 12000).
**Status:** Heurystyka. Brak sygnalu "ready" od Claude Code. Retry pattern bylby lepszy
ale wymaga sposobu detekcji gotowosci (np. monitorowanie transcript).

---

## W3: Terminal nie zamyka sie po /exit (MEDIUM)

**Problem:** Po wyslaniu `/exit` do Claude Code, proces Claude konczy sie ale
terminal shell (bash/powershell) zostaje otwarty. Uzytkownik widzi martwy terminal.

**Workaround:**
```typescript
terminal.sendText("/exit");
setTimeout(() => terminal.dispose(), 3000);  // 3s na graceful exit
```

**Zrodlo:** Commit fd562b4.
**Trade-off:** 3s timeout — jesli Claude Code jest wolniejszy, dispose moze przerwac cleanup.
Jesli szybszy — uzytkownik widzi martwy terminal przez 3s.

---

## W4: Resume wymaga nowego terminala (MEDIUM)

**Problem:** Po zakonczeniu sesji Claude Code (exit lub crash), shell w terminalu
jest martwy. `sendText("/resume")` do istniejacego terminala nie dziala — shell
nie ma procesu ktory przyjmie input.

**Workaround:**
```typescript
// 1. Dispose stary terminal
const existing = vscode.window.terminals.find(t => t.name === terminalName);
if (existing) existing.dispose();

// 2. Stworz nowy terminal z tym samym name
const newTerminal = vscode.window.createTerminal({
  name: terminalName,
  env: { MROWISKO_SPAWN_TOKEN: spawnToken }
});

// 3. Uruchom claude --resume
newTerminal.sendText(`claude --resume "${claudeUuid}"`);
```

**Zrodlo:** Commit d2be1a2.
**Wazne:** claude_uuid musi byc znany (z live_agents DB). Bez uuid → resume
bez kontekstu (Claude Code pyta uzytkownika ktora sesje wznowic).

---

## W5: Poke — ten sam "/" problem (LOW)

**Problem:** Poke (wysylanie tekstu do zywego agenta) ma ten sam "/" artifact
problem co spawn (W1). Agent moze miec "/" w input buffer.

**Workaround:** Ten sam co W1 — empty sendText + delay + actual message.

**Zrodlo:** Commit 1952999, extension.ts:104-107.

---

## Ogolne zasady sendText do Claude Code

1. **NIGDY nie wysylaj tekstu bez uprzedniego empty Enter** (chyba ze 100% pewny
   ze agent nie ma "/" w buforze)
2. **ZAWSZE delay po empty Enter** (300-500ms minimum)
3. **ZAWSZE startup delay przed pierwszym sendText** (12s default, konfigurowalny)
4. **Resume = nowy terminal** (nie sendText do starego)
5. **Stop = /exit + dispose po timeout** (nie samo /exit)
6. **Wszystkie delaye sa heurystyczne** — brak mechanizmu "ready" od Claude Code

---

## Wersja Claude Code

Workaroundy testowane na Claude Code 2.1.83.
Nowsze wersje MOGA naprawic "/" artifact — ale zakladaj ze nie naprawily
dopoki nie przetestujesz. Nie usuwaj workaroundow bez weryfikacji.
