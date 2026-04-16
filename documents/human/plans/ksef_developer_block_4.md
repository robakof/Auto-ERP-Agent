# Developer Block 4 — KSeF M4 SendInvoice (encryption + use case + CLI)

Data: 2026-04-16
Autor: Architect
Dotyczy planu: `documents/human/plans/ksef_api_automation.md` (§5 M4)
Dla roli: Developer
Status: Ready to start
Prerequisites: Block 1 ✓ (API client + auth), Block 2 ✓ (Shadow DB), Block 3 ✓ (domain + XML builder)

---

## Cel bloku

Pierwszy end-to-end send invoice na KSeF Demo: XML → encrypt → session → send → poll → UPO → close.
Po ukończeniu: `py tools/ksef_send.py FS-59.xml` wysyła realną fakturę na api-demo.ksef.mf.gov.pl,
odbiera numer KSeF i UPO.

**Constraint:** Zero logiki biznesowej XML (istnieje w Block 3). Block 4 = transport + encryption + orchestracja.

---

## Co już istnieje (z Block 1-3)

| Komponent | Lokalizacja | Status |
|---|---|---|
| KSeFApiClient (12 endpointów: auth, sessions, invoices, UPO) | `core/ksef/adapters/ksef_api.py` | ✓ Block 1 |
| KSeFAuth (auth orchestration, token refresh, polling) | `core/ksef/adapters/ksef_auth.py` | ✓ Block 1 |
| KSeFHttp (retry, logging, error mapping) | `core/ksef/adapters/http.py` | ✓ Block 1 |
| Typed models (OnlineSession, SendInvoiceAck, InvoiceStatus, Upo) | `core/ksef/models.py` | ✓ Block 1 |
| ShipmentRepository (CRUD, state machine, audit trail) | `core/ksef/adapters/repo.py` | ✓ Block 2 |
| Wysylka domain + state machine | `core/ksef/domain/shipment.py` | ✓ Block 2 |
| Exception hierarchy (KSefError, KSefApiError, KSefAuthError, KSefRepoError) | `core/ksef/exceptions.py` | ✓ Block 1+2 |
| Faktura/Korekta domain + XmlBuilder | `core/ksef/domain/`, `core/ksef/adapters/xml_builder.py` | ✓ Block 3 |
| RSA-OAEP encrypt (dla auth token) | `core/ksef/adapters/ksef_auth.py:_rsa_oaep_encrypt` | ✓ Block 1 |

**Co brakuje (scope Block 4):**
1. Encryption moduł (AES-256-CBC + RSA-OAEP dla klucza symetrycznego sesji)
2. Use case SendInvoice (orchestracja pełnego flow)
3. CLI `tools/ksef_send.py`
4. Testy: unit + contract + integration (Demo)

---

## Scope — co dokładnie powstaje

### 1. Moduł: `core/ksef/adapters/encryption.py` (NOWY)

KSeF online session wymaga szyfrowania symetrycznego (AES-256-CBC) z kluczem zaszyfrowanym
asymetrycznie (RSA-OAEP SHA-256) certyfikatem SymmetricKeyEncryption z KSeF.

```python
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class SessionEncryption:
    """Gotowy payload encryption do open_online_session."""
    symmetric_key: bytes          # 32 bytes AES-256 key (przechowywany w pamięci na czas sesji)
    iv: bytes                     # 16 bytes IV
    encrypted_key_b64: str        # RSA-OAEP(symmetric_key) → Base64
    iv_b64: str                   # Base64(iv)

@dataclass(frozen=True)
class EncryptedInvoice:
    """Gotowy payload do send_invoice."""
    encrypted_content_b64: str    # AES-256-CBC(XML) → Base64
    encrypted_hash_b64: str       # SHA-256(encrypted_bytes) → Base64
    encrypted_size: int           # len(encrypted_bytes)
    plain_hash_b64: str           # SHA-256(xml_bytes) → Base64
    plain_size: int               # len(xml_bytes)


class KSeFEncryption:
    """Szyfrowanie sesji i faktur dla KSeF online."""

    def __init__(self, sym_cert_b64: str) -> None:
        """sym_cert_b64 — certyfikat SymmetricKeyEncryption z /security/public-key-certificates."""

    def prepare_session(self) -> SessionEncryption:
        """Generuj nowy AES key + IV, zaszyfruj key certyfikatem."""

    def encrypt_invoice(self, xml_bytes: bytes, session: SessionEncryption) -> EncryptedInvoice:
        """AES-256-CBC encrypt + SHA-256 hashes + sizes."""
```

**Kontrakt:**
- `prepare_session()` generuje **losowy** 32-byte key + 16-byte IV per sesja (nie reuse!)
- AES-256-CBC z **PKCS#7 padding** (wymagane przez KSeF spec)
- RSA-OAEP z SHA-256 (jak w ksef_auth.py — wyciągnij `_rsa_oaep_encrypt` do shared)
- SHA-256 hash: `hashlib.sha256(content).digest()` → Base64
- Klucz symetryczny żyje w pamięci na czas sesji, NIE zapisywany na dysk

**Refaktor:** Przenieś `_rsa_oaep_encrypt` z `ksef_auth.py` do `encryption.py` (shared).
`ksef_auth.py` importuje z `encryption.py` — kierunek zależności zachowany.

### 2. Moduł: `core/ksef/usecases/send_invoice.py` (NOWY)

Use case orchestruje pełny flow wysyłki jednego dokumentu.

```python
@dataclass(frozen=True)
class SendResult:
    """Wynik wysyłki — wszystko co caller potrzebuje."""
    wysylka_id: int
    ksef_number: str | None         # None jeśli rejected
    upo_path: Path | None           # None jeśli rejected/error
    status: ShipmentStatus          # ACCEPTED | REJECTED | ERROR


class SendInvoiceUseCase:
    def __init__(
        self,
        api: KSeFApiClient,
        auth: KSeFAuth,
        repo: ShipmentRepository,
        encryption: KSeFEncryption,
        *,
        poll_interval_s: float = 2.0,
        poll_timeout_s: float = 60.0,
        upo_dir: Path = Path("output/ksef/upo"),
    ) -> None: ...

    def execute(
        self,
        xml_path: Path,
        gid: int,
        rodzaj: str,               # "FS" | "FSK"
        nr_faktury: str,
        data_wystawienia: date,
    ) -> SendResult:
        """
        Flow:
        1. Check idempotency (repo.has_pending_or_sent → skip/error)
        2. Create DRAFT (repo.create)
        3. Transition DRAFT → QUEUED
        4. Auth (auth.ensure_valid)
        5. Transition QUEUED → AUTH_PENDING
        6. Read XML from path
        7. Prepare session encryption
        8. Open online session (api.open_online_session)
        9. Encrypt XML
        10. Send invoice (api.send_invoice)
        11. Transition AUTH_PENDING → SENT + save session/invoice refs
        12. Poll invoice status (api.invoice_status) until terminal
        13. If ACCEPTED: fetch UPO, save to file, transition → ACCEPTED
        14. If REJECTED: transition → REJECTED
        15. Close session (api.close_online_session)
        16. Return SendResult

        Error handling:
        - Any KSefError → transition → ERROR + save error_msg
        - Auth retry: auth.ensure_valid handles refresh/re-auth
        - Session close: always in finally (best effort)
        """
```

**Kontrakt:**
- **Idempotency:** Nie wysyła jeśli `has_pending_or_sent(gid, rodzaj)` → zwraca status existing
- **State transitions:** każdy krok = transition w repo (audit trail)
- **Session per document:** 1 dokument = 1 sesja (decyzja z planu: "pojedyncza sesja per dokument")
- **UPO save:** `output/ksef/upo/{ksef_number}.xml` (path w Wysylka.upo_path)
- **Error recovery:** błąd w dowolnym kroku → transition to ERROR z error_msg, close session (best effort)
- **No retry logic:** caller (CLI/daemon) decyduje o retry. Use case = 1 attempt

### 3. Aktualizacja: `core/ksef/adapters/ksef_api.py`

`send_invoice()` przyjmuje teraz `payload: dict` — OK, ale warto dodać typed helper:

```python
def send_invoice_encrypted(
    self,
    *,
    access_token: str,
    session_ref: str,
    encrypted: EncryptedInvoice,
) -> SendInvoiceAck:
    """Convenience wrapper that builds the payload from EncryptedInvoice."""
    payload = {
        "invoiceHash": encrypted.plain_hash_b64,
        "invoiceSize": encrypted.plain_size,
        "encryptedInvoiceHash": encrypted.encrypted_hash_b64,
        "encryptedInvoiceSize": encrypted.encrypted_size,
        "encryptedInvoiceContent": encrypted.encrypted_content_b64,
    }
    return self.send_invoice(
        access_token=access_token,
        session_ref=session_ref,
        payload=payload,
    )
```

Alternatywa: builder w use case. **Decyzja Developera** — oba podejścia OK.

### 4. CLI: `tools/ksef_send.py` (NOWY)

```
py tools/ksef_send.py output/ksef/ksef_FS-59_04_26_SPKR_2026-04-14.xml
py tools/ksef_send.py output/ksef/ksef_kor_FSK-1_04_26_SPKRK_2026-04-14.xml
py tools/ksef_send.py --gid 59                    # generuj + wyślij (ErpReader + XmlBuilder + send)
py tools/ksef_send.py --dry-run output/ksef/*.xml  # pokaż co by wysłał bez wysyłki
```

**Parametry z .env:**
- `KSEF_ENV` — `demo` | `prod` (base URL)
- `KSEF_TOKEN` — długoterminowy token KSeF
- `KSEF_NIP` — NIP podmiotu

**Struktura ~80 linii:**
```python
def main() -> int:
    args = _parse_args()
    xml_path = Path(args.xml_file)
    gid, rodzaj = _extract_metadata(xml_path)  # parsuj z filename lub XML root

    api = _build_api_client()
    auth = _build_auth(api)
    repo = _build_repo()
    enc = _build_encryption(api)

    uc = SendInvoiceUseCase(api=api, auth=auth, repo=repo, encryption=enc)
    result = uc.execute(xml_path, gid, rodzaj, nr_faktury, data_wystawienia)

    _print_result(result)
    return 0 if result.status == ShipmentStatus.ACCEPTED else 1
```

**Metadata extraction z XML file:**
- Parse XML root → `<Fa>` → `<P_2>` (numer faktury), `<P_1>` (data wystawienia)
- GID z filename (pattern `*_FS-{gid}_*`) lub z dodatkowego argumentu `--gid`
- `rodzaj` z filename: `ksef_FS-*` = "FS", `ksef_kor_FSK-*` = "FSK"

### 5. Testy

#### Unit: `tests/ksef/test_encryption.py` (NOWY)

```
test_prepare_session_key_is_32_bytes()
test_prepare_session_iv_is_16_bytes()
test_prepare_session_key_is_random()             # dwie wywołania != ten sam key
test_encrypt_invoice_aes_cbc_round_trip()         # decrypt z tym samym key+IV = oryginał
test_encrypt_invoice_pkcs7_padding_correct()       # len(encrypted) % 16 == 0
test_encrypt_invoice_hashes_match()               # SHA-256 plain + encrypted
test_encrypt_invoice_sizes_match()
test_rsa_oaep_encrypt_with_mock_cert()
```
Minimum: **≥8 unit**

#### Contract: `tests/ksef/test_send_invoice_uc.py` (NOWY)

Use case z **full mock** (api, repo, encryption) — weryfikuje orchestrację:

```
test_send_happy_path_transitions_to_accepted()
test_send_idempotent_skip_when_already_sent()
test_send_rejected_transitions_to_rejected()
test_send_api_error_transitions_to_error()
test_send_auth_failure_transitions_to_error()
test_send_closes_session_on_success()
test_send_closes_session_on_error()               # finally block
test_send_saves_upo_on_accepted()
test_send_records_ksef_number()
```
Minimum: **≥9 contract**

#### Integration: `tests/ksef/test_send_integration.py` (NOWY)

Real API call na Demo (skip jeśli brak KSEF_TOKEN):

```python
@pytest.mark.integration
def test_send_real_invoice_to_demo():
    """Send FS-59 XML to api-demo.ksef.mf.gov.pl, verify ACCEPTED + UPO."""
```
Minimum: **≥1 integration** (manual trigger, nie w CI)

#### Minimum testów

- Encryption: ≥8 unit
- Use case: ≥9 contract
- Integration: ≥1
- **Total nowych: ≥18 + zachowane 126 z Block 1-3 = ≥144 PASS**

---

## Decyzje zatwierdzone

| Decyzja | Wybór | Uzasadnienie |
|---|---|---|
| 1 sesja per dokument | TAK | Upraszcza recovery, decyzja z planu architektonicznego |
| Symmetric key per sesja | TAK (losowy) | KSeF wymaga, reuse klucza = security risk |
| UPO storage | `output/ksef/upo/{ksef_number}.xml` | Osobny katalog, nie miesza się z wygenerowanymi XML |
| Shadow DB integration | TAK — pełny cykl DRAFT→ACCEPTED | Block 2 repo gotowe, use case łączy wszystko |
| Encryption cert cache | Per instancja KSeFEncryption (in-memory) | Jak auth cert w Block 1 |

## Pytania do Architekta (do rozstrzygnięcia przed kodem)

### Q1: `_rsa_oaep_encrypt` — shared czy duplikacja?

`ksef_auth.py:177-189` ma `_rsa_oaep_encrypt()` (prywatna, module-level). `encryption.py` potrzebuje
tego samego. Opcje:
- A: Przenieś do `encryption.py`, ksef_auth importuje stamtąd
- B: Wyciągnij do `core/ksef/crypto_utils.py` (osobny moduł)
- C: Duplikuj (DRY violation, ale zero coupling)

**Rekomendacja:** A — encryption.py jest naturalnym domem dla crypto operations.

### Q2: Metadata extraction z XML — parsować XML czy filename?

CLI musi znać GID, rodzaj, numer faktury, datę wystawienia. Opcje:
- A: Parse filename (`ksef_FS-59_04_26_SPKR_2026-04-14.xml` → GID=59, rodzaj=FS, data=2026-04-14)
- B: Parse XML root (`<P_2>` = numer, `<P_1>` = data, `<RodzajFaktury>` = rodzaj)
- C: Wymagaj explicit `--gid 59 --rodzaj FS` w CLI

**Rekomendacja:** B + C fallback — XML parsing jest authoritative, filename jest convenience. `--gid` override na wypadek custom filenames.

### Q3: Poll timeout dla invoice status — jaki?

Auth polling to 30s (Block 1). Invoice status na Demo może trwać dłużej.
- Rekomendacja: 120s default, konfigurowalny w use case constructor
- Jeśli timeout → transition ERROR, nie retry

---

## Acceptance criteria

- [ ] `core/ksef/adapters/encryption.py` — AES-256-CBC + RSA-OAEP + SHA-256, frozen dataclasses
- [ ] `core/ksef/usecases/send_invoice.py` — pełen flow auth→session→encrypt→send→poll→UPO→close
- [ ] `tools/ksef_send.py` — CLI z exit codes, metadata extraction
- [ ] State machine integration: DRAFT→QUEUED→AUTH_PENDING→SENT→ACCEPTED (full path)
- [ ] Idempotency: skip when has_pending_or_sent
- [ ] Session close in finally (best effort, nawet przy error)
- [ ] UPO saved to `output/ksef/upo/`
- [ ] `_rsa_oaep_encrypt` shared (nie duplikacja)
- [ ] Tests: ≥18 nowych, suite ≥144 PASS
- [ ] Integration test na Demo: ≥1 FS wysłany, ACCEPTED, UPO odebrany

### Jakość kodu (L3 Senior — kontynuacja Block 1-3)

- Frozen dataclasses dla SessionEncryption, EncryptedInvoice, SendResult
- DI w use case (api, auth, repo, encryption — testowalne bez live API)
- Error handling: typed exceptions, transitions in repo, never silent
- No secrets on disk (symmetric key = in-memory only)
- Typed throughout, PEP 604
- `from __future__ import annotations`

---

## Out of scope (świadomie)

- **Batch send** (wiele faktur w jednej sesji) — M5 daemon
- **ScanErp** (auto-detect nowych faktur z ERP) — M5 daemon
- **Korekta techniczna** (hashOfCorrectedInvoice w payload) — wymaga lookup oryginalnej faktury w KSeF, osobny M
- **Offline mode** — pole `offlineMode: false` hardcoded (domyślne KSeF)
- **Enrollment** (E1-E5) — operacja jednorazowa, manualna, inna ścieżka (M3 enrollment scope)
- **Token refresh w trakcie sesji** — KSeFAuth.ensure_valid() obsługuje, ale use case nie testuje explicit

---

## Ryzyka

| Ryzyko | Mitygacja |
|---|---|
| Demo API niestabilne / offline | Integration test z `@pytest.mark.integration`, skip w CI |
| AES padding niezgodny z KSeF (PKCS#5 vs #7) | PKCS#7 explicit, test round-trip, verification na Demo |
| Invoice rejected przez KSeF (format error) | Snapshot testy z Block 3 gwarantują poprawny XML; first send = smoke test |
| UPO nie dostępne od razu (polling delay) | Poll z backoff do 120s, timeout → ERROR + retry przez usera |
| KSeF cert SymmetricKeyEncryption niedostępny na Demo | Fallback: sprawdź `/security/public-key-certificates` usage field |
| Shadow DB concurrent access (dwa CLI jednocześnie) | SQLite WAL mode z Block 2 + has_pending_or_sent check |

---

## Kolejność pracy (rekomendacja)

1. **encryption.py** + unit testy — izolowany moduł, zero zależności od API
2. Refaktor `_rsa_oaep_encrypt` do encryption.py (shared)
3. **send_invoice.py** (use case) + contract testy z full mock
4. **ksef_send.py** (CLI) — thin wrapper
5. Integration test na Demo (manual trigger z `KSEF_TOKEN`)
6. Verify: `py tools/ksef_send.py output/ksef/ksef_FS-59_04_26_SPKR_2026-04-14.xml` → ACCEPTED

---

## Workflow i handoff

Developer realizuje przez `workflow_developer_tool`.

Po ukończeniu — handoff do Architekta na `workflow_code_review`:

```
py tools/agent_bus_cli.py handoff \
  --from developer --to architect \
  --phase "ksef_block_4_review" --status PASS \
  --summary "Block 4: encryption + SendInvoice use case + CLI. Demo ACCEPTED. 144+ tests PASS." \
  --next-action "Code review — core/ksef/adapters/encryption.py, core/ksef/usecases/send_invoice.py, tools/ksef_send.py, tests/ksef/test_{encryption,send_invoice_uc,send_integration}.py"
```

Po PASS → M5 daemon (ScanErp + batch) lub M3 enrollment — decyzja człowieka.
