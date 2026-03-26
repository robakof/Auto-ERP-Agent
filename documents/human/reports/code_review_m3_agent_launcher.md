# Code Review: Agent Launcher M3

Date: 2026-03-26
Commits: `3c7995a`, `7f978ce`, `bd09b76`

## Summary

**Overall assessment:** PASS
**Code maturity level:** L3 (Senior) — M3 zamyka fundamentalną mechanikę agent-to-agent. Dobre rozwiązania: trusted pairs z config, startup delay zamiast naiwnego sendText, loadRoles z pliku config, sendText URI command. Transcript reader w tmp/ to PoC — do przeniesienia do tools/ w przyszłości.

## Findings

### Critical Issues (must fix)

*Brak.*

### Warnings (should fix)

- **spawner.ts:7,68-70** — `STARTUP_DELAY_MS = 4000` hardcoded. setTimeout to heurystyka — Claude Code może startować wolniej (cold start, duży CLAUDE.md) lub szybciej. Nie ma sygnału "gotowy na input". Na razie działa, ale to kruche rozwiązanie. Rozważ: konfigurowalne z default 4000, lub retry pattern (sprawdź transcript czy sesja wystartowała).

- **extension.ts:49-57** — URI `sendText` pozwala dowolnemu procesowi pisać do terminala agenta po session_id. Brak walidacji kto wysyła. Na razie OK (single user, local), ale przy skali to security concern. Faza 3+ powinna dodać auth (np. token w URI).

- **approver.ts:43-48** — Trusted pairs format `"developer>erp_specialist"`. Separator `>` jest nieoczywisty. Lepszy format: `"developer→erp_specialist"` lub obiekt `{"from": "developer", "to": "erp_specialist"}`. Ale zmiana formatu to breaking config — zostawiam jako suggestion.

- **tmp/read_transcript.py:8** — Hardcoded ścieżka projektu `C--Users-cypro-OneDrive-Pulpit-Mrowisko`. Nie zadziała na innej maszynie/projekcie. Do przeniesienia do `tools/` z dynamicznym wykrywaniem project path.

### Suggestions (nice to have)

- **commands.ts:8-27** — `loadRoles()` czyta config synchronicznie przy każdym QuickPick. Przy dużym pliku config może być lag. Cache z invalidacją na file change byłby czystszy. Nie blokuje.

- **extension.ts:58-59** — URI `reload` wykonuje `reloadWindow`. Przydatne do development, ale potencjalnie destruktywne (zamyka wszystkie terminale agentów). Rozważ: usunięcie z produkcji lub dodanie confirmation.

- **spawner.ts:50** — `[TRYB AUTONOMICZNY]` hardcoded w spawner. Jeśli prompty się zmienią (np. PE zredefiniuje tryb autonomiczny) — trzeba edytować TS. Rozważ: konfigurowalny template system prompt.

## Architecture Compliance M3

| Task | Status | Zgodny z planem? |
|---|---|---|
| M3.1 Auto-approve trusted pairs | ✓ | ✓ — z config, clean implementation |
| M3.2 sendText timing fix | ✓ | ✓ — setTimeout 4s, pragmatyczne |
| M3.3 Debug cleanup | ✓ | ✓ — console.log usunięte z approver |
| M3.4 Stress test | Deferred | N/A — per decyzja architekta |
| M3.5 ROLES z config | ✓ | ✓ — loadRoles() z session_init_config.json |
| sendText via URI | ✓ (bonus) | Nie w planie — dobra inicjatywa |
| read_transcript | ✓ (bonus) | Nie w planie — PoC w tmp/ |
| reload via URI | ✓ (bonus) | Nie w planie — dev utility |

## Nowe komendy URI (z M3)

| Command | Bezpieczeństwo | Uwagi |
|---|---|---|
| `sendText` | Warning — brak auth | OK na teraz, auth w przyszłości |
| `reload` | Warning — destruktywne | Dev utility, rozważ usunięcie z prod |

## Recommended Actions

- [ ] **W1:** `STARTUP_DELAY_MS` → konfigurowalne w settings (default 4000)
- [ ] **W2:** `read_transcript.py` → przenieś z tmp/ do tools/ z dynamicznym project path
- [ ] **W3:** `[TRYB AUTONOMICZNY]` → konfigurowalny template
- [ ] **W4:** W przyszłości: auth dla sendText URI (token/secret)

## Overall M1-M3 Assessment

**Agent Launcher v1.0 jest funkcjonalny.** Mechanika spawn → communicate → read działa end-to-end. Architektura czysta (Spawner/Registry/Watcher/Approver/Commands), Python bridge pragmatyczny, URI handler elegancki. Code maturity L3 konsekwentnie przez wszystkie milestones.

Następny krok architektoniczny: rola orkiestratora (prompt + workflow) i stabilizacja przed produkcyjnym użyciem.
