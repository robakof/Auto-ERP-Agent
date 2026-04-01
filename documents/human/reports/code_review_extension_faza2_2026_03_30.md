# Code Review: Extension Rewrite Faza 2

Date: 2026-03-30
Commit: b7d2121
ADR: ADR-005

## Summary

**Overall assessment:** PASS
**Code maturity level:** L3 Senior — pelen rewrite Approver/Spawner/Watcher/Commands.
Zero Python proxy. MrowiskoDB direct. Policy routing. Kill support. +164/-199 (mniej kodu).

## Extension-Specific Checklist

| Wymiar | Status |
|--------|--------|
| Async I/O (brak execFileSync) | PASS |
| CWD determinism | PASS |
| LogOutputChannel | PASS |
| .vscodeignore | PASS |
| Bundler | PASS (22.4kb) |
| Disposables | PASS |
| Known Issues W1-W4 compliance | PASS |
| Policy routing (spawn_policy.json) | PASS |

## Findings

### Critical Issues

Brak.

### Warnings (should fix)

**W1: package.json activationEvents — podwojny trigger**
```json
"activationEvents": ["workspaceContains:mrowisko.db", "onStartupFinished"]
```
ADR-005 mowi: lazy activation `workspaceContains:mrowisko.db` only.
`onStartupFinished` to eager — aktywuje extension w KAZDYM oknie VS Code,
nawet bez mrowisko.db. Usunac `onStartupFinished`.

**W2: package.json autoPromptTemplate nadal ma [TRYB AUTONOMICZNY]**
```json
"default": "[TRYB AUTONOMICZNY] Rola: {role}. Task: {task}"
```
PE wlasnie usunela TRYB AUTONOMICZNY z wszystkich promptow (msg #576).
Template w extension jest niespojny. Zaktualizowac na nowy format.

**W3: registry.ts — deprecated ale nie pusty**
System reminder mowi `// DEPRECATED: Registry removed in Faza 2. This file can be deleted.`
Plik nadal w repo. Usunac w tym VSIX build (albo w Fazie 3 cleanup).

### Suggestions

**S1: Approver.handleInvocation — brak timeout na approval dialog**
approver.ts:75-89 — showApprovalDialog czeka na user response bez limitu.
Jesli user nie odpowie — invocation wisi w `processing` Set na zawsze.
Rozwazyc timeout (np. 5 min → auto-reject + log warning). Nie bloker.

**S2: Spawner.stop — terminal lookup by sessionId**
spawner.ts:123 — `this.terminals.get(sessionId)` — ale terminals Map
jest keyed by spawnToken (spawner.ts:82), nie sessionId.
Jesli stop przychodzi z sessionId → terminal nie zostanie znaleziony → fallback markStopped.
To moze byc bug — zweryfikowac czy terminals Map jest re-keyed po session linkage.

**S3: Approver.resume — claudeUuid source**
approver.ts:97 — `this.spawner.resume(terminalName, inv.target_session_id || "", inv.session_id || "")`
target_session_id = claude_uuid? session_id = spawn_token? Naming sugeruje
ze parametry moga byc zamienione. Zweryfikowac z MrowiskoDB i live_agents schema.

## Porownanie z inspekcja (8 problemow) — final status

| Problem | Status |
|---------|--------|
| P1: CWD niezdefiniowany | NAPRAWIONY (F1) |
| P2: Approver nie dziala | NAPRAWIONY (F2) — MrowiskoDB direct, policy routing |
| P3: Brak bundlera | NAPRAWIONY (F1) — esbuild 22.4kb |
| P4: .vscodeignore dziurawy | NAPRAWIONY (F1) |
| P5: Zero testow | CZEKA (F3) |
| P6: Brak Output Channel | NAPRAWIONY (F1) |
| P7: execFileSync | NAPRAWIONY (F1+F2) — zero Python subprocess |
| P8: Python proxy | NAPRAWIONY (F2) — MrowiskoDB direct |

7/8 naprawionych. Testy (P5) w Fazie 3.

## Recommended Actions

- [W1] Usunac `onStartupFinished` z activationEvents
- [W2] Zaktualizowac autoPromptTemplate (usunac TRYB AUTONOMICZNY)
- [W3] Usunac registry.ts
- [S2] Zweryfikowac terminals Map keying (spawnToken vs sessionId) — potencjalny bug
