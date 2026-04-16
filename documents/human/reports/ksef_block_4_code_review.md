# Code Review: KSeF Block 4 — SendInvoice e2e (encryption + use case + CLI)

Date: 2026-04-16
Reviewer: Architect
Branch: main (commits 5ed29c4, 91acc8f, c38146d)
Plan: `documents/human/plans/ksef_developer_block_4.md`
Handoff: msg #92 (developer → architect), detale: `tmp/handoff_block_4_review.md`

## Summary

**Overall assessment: PASS**
**Code maturity level: L3 Senior (strong)** — frozen dataclasses, DI throughout (api, auth, repo, encryption, sleep, clock), state machine audit trail, clean error handling (KSefError catch → ERROR transition), structured JSON logging, session close in finally. Idempotency guard. Demo integration ACCEPTED.

**Tests:** 149/149 PASS (22 nowych + 127 z Block 1-3). Integration: FS-59 → Demo ACCEPTED (7871003063-20260416-2F7840C00000-05).

**Acceptance criteria vs deliverable:**

| Criterium | Status |
|---|---|
| encryption.py — AES-256-CBC + RSA-OAEP + SHA-256 | ✓ 107 L, frozen dataclasses |
| send_invoice.py — full flow auth→session→encrypt→send→poll→UPO→close | ✓ 218 L, state machine integration |
| ksef_send.py — CLI z exit codes, metadata extraction | ✓ 145 L, --dry-run, --gid/--rodzaj override |
| State machine: DRAFT→QUEUED→AUTH_PENDING→SENT→ACCEPTED | ✓ full path w contract tests |
| Idempotency: skip when has_pending_or_sent | ✓ tested |
| Session close in finally | ✓ best-effort, tested on success + error |
| UPO saved to output/ksef/upo/ | ✓ tested |
| `_rsa_oaep_encrypt` shared (nie duplikacja) | ✓ → `rsa_oaep_encrypt` w encryption.py, ksef_auth importuje |
| Tests ≥18 nowych, suite ≥144 | ✓ 22 nowych, suite 149 |
| Integration: ≥1 FS Demo ACCEPTED | ✓ KSeF number assigned |
| W1 XSD regression tests (Block 3 backlog) | ✓ 2 testy (FS + FSK) |
| W2 type annotations _build_fa_header | ✓ fixed |

## Decyzje Q1-Q3

### Q1: Shared RSA-OAEP → **Opcja A — APPROVE**
`rsa_oaep_encrypt` przeniesiony do `encryption.py` (module-level function, nie klasa). `ksef_auth.py:23` importuje stamtąd. Kierunek zależności poprawny: auth → encryption (nie odwrotnie). Zero duplikacji.

### Q2: Metadata extraction → **Opcja B+C — APPROVE**
CLI parsuje XML (`P_1`, `P_2` z namespace discovery) + filename regex fallback. `--gid`/`--rodzaj` override dostępne. Authoritative source = XML, convenience = filename. Dobrze.

### Q3: Poll timeout 120s + --poll-timeout → **APPROVE**
`_DEFAULT_POLL_TIMEOUT_S = 120.0` w use case. CLI arg `--poll-timeout`. Exponential backoff: 2s → 4s → 8s (cap). Timeout → `KSefError` → ERROR transition. Dobrze.

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

**W1: Dead code — line 112-113 w send_invoice.py**

```python
self._repo.transition(
    wid, ShipmentStatus.AUTH_PENDING,  # no-op transition — already AUTH_PENDING
) if False else None  # placeholder — session_ref saved below
```

Ten kod nigdy się nie wykonuje (`if False`). Prawdopodobnie pozostałość z refaktoru gdzie developer chciał zapisać `session_ref` do repo po otwarciu sesji, ale nie ma pola w `transition()` na to (session_ref jest przekazywany dopiero w `SENT` transition na linii 131). Usunąć te 3 linie.

**W2: `_extract_gid_rodzaj` — duplikat warunku (linie 90 i 100)**

```python
# line 90
if gid_override and rodzaj_override:
    return gid_override, rodzaj_override

# ... filename parsing ...

# line 100 — identyczny warunek, nigdy osiągnięty
if gid_override and rodzaj_override:
    return gid_override, rodzaj_override
```

Drugie sprawdzenie (linia 100) jest nieosiągalne — pierwszy `if` na linii 90 zawsze wcześniej zwróci. Usunąć linie 100-101.

**W3: `_poll_invoice` brak return type annotation**

```python
# current
def _poll_invoice(
    self, access_token: str, session_ref: str, invoice_ref: str,
):

# fix
def _poll_invoice(
    self, access_token: str, session_ref: str, invoice_ref: str,
) -> InvoiceStatus:
```

Reszta use case jest typed. Inconsistency — minor.

### Suggestions (nice to have)

**S1: `_send_one` brak type annotations na parametrach i return**
`ksef_send.py:57` — `def _send_one(xml_path, gid, rodzaj, nr, data_wyst, poll_timeout)`. Reszta CLI ma typy. Minor — CLI to thin wrapper.

**S2: `_FORM_CODE` hardcoded w use case**
`send_invoice.py:25` — `{"systemCode": "FA (3)", "schemaVersion": "1-0E", "value": "FA"}`. Akceptowalne na obecnym etapie (wszystkie faktury to FA(3)). Jeśli pojawi się wsparcie dla innych schematów, wyciągnij jako parametr. Na razie OK.

**S3: Batch-aware log w CLI**
`ksef_send.py` obsługuje wiele plików XML (nargs="+"), ale przy wielu plikach tworzy osobne instancje api/auth/repo per plik (`_send_one`). Oznacza to N auth flow dla N plików. Dla Block 4 (pojedynczy dokument) to OK. Batch optimization to M5 scope — świadomie out of scope.

## Architecture Assessment

### Module boundaries

```
tools/ksef_send.py (thin CLI ~145L)
    ↓ late import
core/ksef/usecases/send_invoice.py (orchestration ~218L)
    ↓ DI
core/ksef/adapters/encryption.py (crypto ~107L)
core/ksef/adapters/ksef_api.py (HTTP calls)
core/ksef/adapters/ksef_auth.py (auth flow)
core/ksef/adapters/repo.py (Shadow DB)
core/ksef/domain/shipment.py (state machine)
```

Czyste warstwy. Use case importuje adaptery. CLI importuje use case + adaptery dla wiring. Domain ma zero importów z wyższych warstw. **Dependency direction correct.**

### Pattern compliance

| Pattern | Status |
|---|---|
| Validation at Boundary → Trust Internally | ✓ XML parsed at CLI boundary, use case trusts typed params |
| Repository (Persistence Separation) | ✓ Use case → repo, nie SQL |
| DI for Testability | ✓ api, auth, repo, encryption, sleep — full mock in contract tests |
| State Machine Audit Trail | ✓ Każdy krok = repo.transition |
| Error → Typed Exception → Transition | ✓ KSefError → ERROR, structured log |
| Session Close in Finally | ✓ best-effort, both paths tested |

### Anti-pattern check

| Anti-pattern | Status |
|---|---|
| Defensive Programming Hell | ✓ Clean — validate at CLI boundary only |
| Mixed Dimensions | ✓ Clean — encryption/auth/orchestration/persistence separated |
| Silent Failure | ✓ Clean — UPO fetch failure logged as warning, session close failure logged |
| Retry Sprawl | ✓ Avoided — "No retry logic: caller decides" per plan |
| Simpler solution exists? | No — use case orchestration is justified by state machine + audit trail |

## Test Coverage Analysis

| File | Tests | Plan min | Status |
|---|---|---|---|
| test_encryption.py | 11 | ≥8 | ✓ |
| test_send_invoice_uc.py | 10 | ≥9 | ✓ |
| test_send_integration.py | 1 | ≥1 | ✓ (Demo ACCEPTED) |
| **Total new** | **22** | **≥18** | ✓ |
| + Block 1-3 | 127 | 126+1 | ✓ |
| **Suite total** | **149** | **≥144** | ✓ |

**Contract tests quality:** Full mock z realistic fixtures. Weryfikują orchestrację (transition sequence), idempotency, error handling, session close on both paths, UPO save. Dobrze osadzone.

**Encryption tests quality:** Round-trip decrypt, PKCS#7 padding, hash verification, size verification, randomness, frozen dataclass. Self-signed cert fixture. Solidne.

## Block 3 Backlog Resolution

| Item | Status |
|---|---|
| W1: XSD regression tests (FS + FSK) | ✓ Done (test_xsd_validator.py:54-75) |
| W2: `_build_fa_header` type annotations | ✓ Done (xml_builder.py:119-121) |

## Recommended Actions

### Before commit (must):
- [ ] W1: Usuń dead code `send_invoice.py:112-113` (if False placeholder)
- [ ] W2: Usuń nieosiągalny duplikat warunku `ksef_send.py:100-101`

### Nice-to-have (non-blocking):
- [ ] W3: Dodaj `-> InvoiceStatus` return type do `_poll_invoice`
- [ ] S1: Type annotations na `_send_one` w CLI

## Verdict

**PASS.** Block 4 to kompletny e2e send invoice: encryption (AES-256-CBC + RSA-OAEP), use case z pełnym state machine audit trail, CLI z metadata extraction, 22 nowych testów, Demo integration ACCEPTED. Shared `rsa_oaep_encrypt` (Q1-A) bez duplikacji. Idempotency + session close in finally. Dwa Warnings (W1: dead code, W2: unreachable code) — oba kosmetyczne, usunięcie ~5 linii łącznie.

Developer może commitować `feat(ksef): block 4` po W1+W2 fix.
