# Co zepsuliśmy i jak to naprawiamy — live_agents tracking

**Data:** 2026-03-29
**Autor:** Architect

---

## Problem w jednym zdaniu

Agenci nie wiedzą kim są. System myli ich tożsamości — heartbeat jednego agenta ożywia martwego innego, a Dashboard pokazuje fałszywy obraz.

---

## Jak do tego doszło

### Krok 1: Jeden agent, jeden plik — działało

Na początku był jeden agent na raz. `session_init` pisał swoje ID do pliku `tmp/session_id.txt`. Heartbeat czytał ten plik i aktualizował odpowiedni record w bazie. Proste, działało.

### Krok 2: Wielu agentów, jeden plik — zepsute

Gdy uruchomiliśmy kilku agentów jednocześnie (Developer, Analyst, Dispatcher), każdy `session_init` nadpisywał ten sam plik. Efekt: plik wskazywał na OSTATNIEGO agenta który się zainicjalizował. Heartbeat wszystkich agentów aktualizował record tego ostatniego. Dashboard: jeden agent "żyje", reszta wygląda na martwą.

### Krok 3: Łatka #1 — claude_uuid w heartbeat

Naprawiliśmy heartbeat żeby matchował po `claude_uuid` (unikalny identyfikator Claude Code) zamiast po pliku. Ale żeby to działało, trzeba było jakoś połączyć `claude_uuid` z naszym `session_id`. Wprowadziliśmy plik `pending_claude_uuid.txt` jako "most" między hookiem (który zna claude_uuid) a session_init (który zna session_id).

### Krok 4: Łatka #2 — uuid_bridge w bazie

Plik `pending_claude_uuid.txt` miał ten sam problem co `session_id.txt` — jeden plik, wielu agentów. Przenieśliśmy "most" do bazy danych (`uuid_bridge` table). Session_init miał brać najnowszy unclaimed UUID z bazy.

### Krok 5: uuid_bridge nie wie kto jest kto

Developer uruchamia session_init → bierze najnowszy UUID z bridge → ale to jest UUID Analityka który wystartował sekundę wcześniej. Developer przejmuje tożsamość Analityka. Heartbeat Developera ożywia martwego Analityka. Dashboard: Analityk "żyje" (fałsz), Developer "umarł" (fałsz).

**Wniosek: każda łatka przenosiła problem zamiast go rozwiązywać.** Shared state (plik lub tablica bridge) w multi-session to fundamentalnie zły pattern.

---

## Dlaczego łatki nie działają

Cały czas próbowaliśmy odpowiedzieć na pytanie: **"Który record w bazie jest mój?"**

Odpowiedzi które próbowaliśmy:
- "Ten wskazany przez plik" → plik jest shared, wskazuje na kogoś innego
- "Ten z moim claude_uuid" → nie wiem jaki jest mój claude_uuid (dostaję go w hooku, nie w session_init)
- "Najnowszy unclaimed w bridge" → najnowszy może być cudzym UUID

**Problem: dwa procesy (hook i session_init) wiedzą różne rzeczy i nie mają niezawodnego kanału komunikacji.**

| Proces | Wie | Nie wie |
|---|---|---|
| on_session_start (hook) | claude_uuid (z Claude Code) | mrowisko session_id (jeszcze nie istnieje) |
| session_init (skrypt) | mrowisko session_id (sam generuje) | claude_uuid (nie ma do niego dostępu) |

Most między nimi (plik lub bridge) jest zawsze shared i zawodny w multi-session.

---

## Rozwiązanie: env var w terminalu

**Zamiast mostu — odpowiedź wbudowana w terminal od momentu stworzenia.**

VS Code pozwala ustawić zmienne środowiskowe przy tworzeniu terminala:

```typescript
const terminal = vscode.window.createTerminal({
    name: "Developer-abc123",
    env: { MROWISKO_SESSION_ID: "abc123" }  // ← to jest klucz
});
```

Każdy proces uruchomiony w tym terminalu (Claude Code, hooki, session_init) automatycznie dziedziczy tę zmienną. Nie trzeba pliku. Nie trzeba bridge. Nie trzeba zgadywać.

### Jak to wygląda w praktyce

```
SPAWN (Extension tworzy terminal):
  "Tworzę terminal dla Developera. Jego session_id to abc123."
  → Zapisuje do bazy: {session_id: abc123, role: developer, status: starting}
  → Tworzy terminal z env: MROWISKO_SESSION_ID=abc123

CLAUDE CODE STARTUJE (hook on_session_start):
  "Jestem w terminalu. Moje MROWISKO_SESSION_ID to abc123. Mój claude_uuid to xyz789."
  → Zapisuje do bazy: UPDATE ... SET claude_uuid=xyz789 WHERE session_id=abc123
  → Gotowe. Link ustanowiony. Zero zgadywania.

SESSION_INIT (agent uruchamia):
  "Moje MROWISKO_SESSION_ID to abc123. Szukam w bazie..."
  → Znajduje swój record. Wie kim jest. Ładuje kontekst.

HEARTBEAT (każdy prompt):
  "Moje MROWISKO_SESSION_ID to abc123."
  → UPDATE last_activity WHERE session_id=abc123
  → Aktualizuje SWÓJ record. Nigdy cudzego.
```

### Dlaczego to nie ma race condition

Każdy terminal ma WŁASNĄ zmienną środowiskową ustawioną przy tworzeniu. Terminal Developera ma `MROWISKO_SESSION_ID=abc123`. Terminal Analityka ma `MROWISKO_SESSION_ID=def456`. Nie mogą się pomylić — to nie jest shared plik, to jest per-process environment.

Nawet jeśli 10 agentów startuje w tej samej sekundzie — każdy czyta SWOJĄ zmienną, nie wspólny plik.

---

## Co usuwamy

| Artefakt | Dlaczego | Zastąpiony przez |
|---|---|---|
| `tmp/session_id.txt` | Shared plik nadpisywany przez każdego agenta | env var `MROWISKO_SESSION_ID` |
| `tmp/session_data.json` | Shared plik z rolą — złą w multi-session | DB lookup po session_id z env |
| `tmp/pending_claude_uuid.txt` | Shared plik — przejmowanie cudzej tożsamości | env var → on_session_start wie session_id |
| `uuid_bridge` table | Heurystyczne matchowanie — race conditions | Nie potrzebna — env var = deterministyczny link |

---

## Co zyskujemy

1. **Dashboard pokazuje prawdę.** Heartbeat aktualizuje właściwy record → display_status jest wiarygodny.
2. **Dispatcher może koordynować.** Widzi kto naprawdę żyje, kto stoi, kto umarł.
3. **Poke trafia do właściwego agenta.** Session_id w env → lookup terminal_name → sendText do właściwego terminala.
4. **Resume działa.** claude_uuid w bazie matchuje z Claude Code → reuse session_id.
5. **Spawn jest niezawodny.** Extension ustawia env → link spawn→session gwarantowany.

---

## Lekcja

**Shared mutable state nie skaluje się do wielu agentów.** Pliki w `tmp/` były OK dla jednego agenta. Przy dwóch — race condition. Przy trzech — chaos tożsamości.

Rozwiązanie to nie "lepszy shared state" (bridge, lock file, atomic write) — tylko **eliminacja shared state**. Każdy agent musi mieć swoją tożsamość wbudowaną w process environment, nie czytaną z pliku dzielonego z innymi.

Ta sama zasada obowiązuje dla przyszłych mechanizmów: jeśli wielu agentów musi wiedzieć "kim jestem", odpowiedź musi być per-process (env var, process argument), nie per-directory (plik).
