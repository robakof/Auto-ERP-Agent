# Code Review: Extension Rewrite Faza 1

Date: 2026-03-30
Commit: 46daad6
ADR: ADR-005

## Summary

**Overall assessment:** PASS
**Code maturity level:** L3 Senior — fundamentalna zmiana jakosci vs poprzedni kod (L1).
CWD contract spelniony, better-sqlite3 direct, LogOutputChannel, esbuild, fail-fast activation.

## Extension-Specific Checklist (nowa!)

| Wymiar | Status | Uwagi |
|--------|--------|-------|
| Async I/O (brak execFileSync) | PASS | better-sqlite3 sync ale ~1ms, zero Python subprocess |
| CWD determinism | PASS | resolveWorkspaceRoot fail-fast, absolutne sciezki |
| LogOutputChannel | PASS | createOutputChannel("Mrowisko", { log: true }) |
| .vscodeignore kompletny | PASS | whitelist model, node_modules excluded except better-sqlite3 |
| Bundler | PASS | esbuild, dist/extension.js |
| Activation event | PASS | workspaceContains:mrowisko.db (lazy) |
| Disposables | PASS | context.subscriptions z reverse teardown order |
| Testy | N/A | Faza 3 — akceptowalne dla Fazy 1 |

## Findings

### Critical Issues

Brak.

### Warnings (should fix)

**W1: Approver nadal uzywa Python proxy**
extension.ts:48 — `new Approver(dbPath, spawner)` — Approver dostaje dbPath (string)
i wewnetrznie wola execFileSync. To jest swiadome (komentarz "Faza 1 — will be rewritten
in Faza 2") ale Approver nadal crashuje z tego samego powodu co wczesniej (CWD).

**Rekomendacja:** Jesli Approver jest w Fazie 2, rozważ wyłączenie go w Fazie 1
(nie startuj pollingu). Lepiej nic niz crashujacy poll co 5s.

**W2: Resume path w URI handler — stary kod**
extension.ts:159-193 — Resume flow nadal uzywa `existing.sendText("/resume")`.
EXTENSION_KNOWN_ISSUES W4 mowi: resume do istniejacego terminala NIE dziala
(shell martwy po exit Claude Code). Ten kod jest z przed rewrite.

**Rekomendacja:** Zostaw na Faze 2, ale dodaj komentarz `// BUG: see EXTENSION_KNOWN_ISSUES W4`.

### Suggestions

**S1: db.ts:49 — busy_timeout jako parametr**
Hardcoded 3000ms. Rozważ parametr konstruktora z defaultem. Nie bloker.

**S2: package.json dependencies — better-sqlite3 version mismatch**
package.json ma `"better-sqlite3": "^11.0.0"`, package-lock.json referencuje `^12.8.0`.
Nie krytyczne (lock wins) ale warto zsynchronizowac.

**S3: Registry wrapper — dobre podejscie przejsciowe**
Registry jako thin wrapper nad MrowiskoDB to czysty transition pattern.
Spawner/Watcher/Commands nie musza sie zmieniac w Fazie 1. W Fazie 2 usunac
Registry i uzyc MrowiskoDB bezposrednio.

## Porownanie z inspekcja (8 problemow)

| Problem | Status po Fazie 1 |
|---------|-------------------|
| P1: CWD niezdefiniowany | NAPRAWIONY — resolveWorkspaceRoot fail-fast |
| P2: Approver nie dziala | CZESCIOWY — czeka Faza 2 |
| P3: Brak bundlera | NAPRAWIONY — esbuild |
| P4: .vscodeignore dziurawy | NAPRAWIONY — whitelist model |
| P5: Zero testow | CZEKA — Faza 3 |
| P6: Brak Output Channel | NAPRAWIONY — LogOutputChannel |
| P7: execFileSync | NAPRAWIONY — better-sqlite3 direct (Approver czeka F2) |
| P8: Python proxy | NAPRAWIONY — MrowiskoDB (Approver czeka F2) |

6/8 naprawionych w Fazie 1. Pozostale 2 (Approver + testy) w Fazie 2-3.

## Recommended Actions

- [W1] Rozważ wyłączenie Approver polling w Fazie 1 (crashuje jak przed rewrite)
- [W2] Dodaj komentarz BUG przy resume sendText("/resume")
- [S2] Zsynchronizuj better-sqlite3 version w package.json
