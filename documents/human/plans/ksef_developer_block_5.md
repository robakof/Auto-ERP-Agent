# Developer Block 5 — KSeF M3 Certificate Enrollment + Token Generation

Data: 2026-04-16
Autor: Architect
Dotyczy planu: `documents/human/plans/ksef_api_automation.md` (§5 M3)
Dla roli: Developer
Status: Ready to start
Prerequisites: Block 1 ✓ (API client + auth), Block 4 ✓ (SendInvoice e2e, Demo ACCEPTED)

---

## Cel bloku

Interaktywny skrypt enrollment: generuje CSR → rejestruje certyfikat w KSeF →
pobiera wydany certyfikat → generuje długoterminowy KSeF token → zapisuje do `.env`.

Po ukończeniu: `py tools/ksef_enroll.py` przeprowadza operatora krok po kroku
przez cały enrollment na Demo/Prod. Wynik: KSEF_TOKEN w .env, gotowy do użycia
przez runtime auth flow (Block 1 KSefAuth).

**Constraint:** Enrollment to operacja jednorazowa, interaktywna (nie daemon).
Skrypt prowadzi operatora — wypisuje co robi, czeka na potwierdzenie, raportuje status.

---

## Co już istnieje (z Block 1-4)

| Komponent | Lokalizacja | Status |
|---|---|---|
| KSeFApiClient (12 runtime endpointów) | `core/ksef/adapters/ksef_api.py` | ✓ Block 1 |
| KSeFAuth (runtime auth: challenge→token→redeem) | `core/ksef/adapters/ksef_auth.py` | ✓ Block 1 |
| KSefHttp (retry, logging, error mapping) | `core/ksef/adapters/http.py` | ✓ Block 1 |
| config.py (KSEF_ENV, KSEF_BASE_URL, KSEF_NIP, KSEF_TOKEN) | `core/ksef/config.py` | ✓ Block 1 |
| rsa_oaep_encrypt (shared) | `core/ksef/adapters/encryption.py` | ✓ Block 4 |
| Exception hierarchy | `core/ksef/exceptions.py` | ✓ Block 1+2 |

**Co brakuje (scope Block 5):**
1. Enrollment API endpoints w `ksef_api.py` (E1-E4 + token generation)
2. CSR generation helper
3. Enrollment orchestrator (use case)
4. CLI `tools/ksef_enroll.py` (interaktywny)
5. Testy: unit + contract

---

## Odpowiedź na pytanie Developera

> Czy enrollment endpointy wymagają osobnych metod w ksef_api.py,
> czy osobny moduł ksef_enrollment.py?

**Rekomendacja: endpointy w `ksef_api.py`, orchestracja w `usecases/enroll_certificate.py`.**

Uzasadnienie:
- `ksef_api.py` = "one method per KSeF endpoint" — enrollment endpoints to nadal KSeF REST endpoints, ten sam HTTP client, te same response patterns. Rozdzielenie na osobny moduł API złamałoby spójność.
- Orchestracja (CSR gen → submit → poll → retrieve → token gen) to use case, analogiczny do `SendInvoiceUseCase`. Osobny moduł w `usecases/`.
- Pattern zachowany: API client = transport, use case = flow.

---

## Scope — co dokładnie powstaje

### 1. Nowe metody w `core/ksef/adapters/ksef_api.py`

Dodaj 5 metod (enrollment sekcja):

```python
# ---- Certificate enrollment ----------------------------------

def get_enrollment_data(self, *, access_token: str) -> EnrollmentData:
    """GET /certificates/enrollments/data — dane do wniosku CSR."""

def submit_enrollment(
    self,
    *,
    access_token: str,
    certificate_name: str,
    certificate_type: str,    # "Authentication"
    csr_b64: str,
    valid_from: datetime,
) -> EnrollmentSubmitResult:
    """POST /certificates/enrollments — złożenie wniosku. 202 Accepted."""

def enrollment_status(
    self, reference_number: str, *, access_token: str,
) -> EnrollmentStatus:
    """GET /certificates/enrollments/{ref} — polling statusu."""

def retrieve_certificates(
    self,
    *,
    access_token: str,
    serial_numbers: list[str],
) -> list[Certificate]:
    """POST /certificates/retrieve — pobranie wydanych certyfikatów."""

def generate_token(
    self,
    *,
    access_token: str,
    # payload do ustalenia — patrz Q1
) -> GeneratedToken:
    """POST /tokens — wygenerowanie KSeF tokena."""
```

**Uwaga:** Wszystkie enrollment endpointy wymagają `access_token` (Bearer). Operator musi się najpierw uwierzytelnić istniejącym tokenem, by wywołać enrollment nowego certyfikatu.

### 2. Nowe modele w `core/ksef/models.py`

```python
@dataclass(frozen=True)
class EnrollmentData:
    """Response from GET /certificates/enrollments/data."""
    common_name: str
    country_name: str
    serial_number: str
    unique_identifier: str
    organization_name: str
    organization_identifier: str


@dataclass(frozen=True)
class EnrollmentSubmitResult:
    """Response from POST /certificates/enrollments."""
    reference_number: str
    timestamp: datetime


@dataclass(frozen=True)
class EnrollmentStatus:
    """Response from GET /certificates/enrollments/{ref}."""
    request_date: datetime
    status_code: int
    status_description: str

    @property
    def ready(self) -> bool:
        return self.status_code == 200

    @property
    def in_progress(self) -> bool:
        return self.status_code == 100

    @property
    def failed(self) -> bool:
        return self.status_code >= 400


@dataclass(frozen=True)
class Certificate:
    """One entry from POST /certificates/retrieve."""
    certificate_b64: str
    certificate_name: str
    serial_number: str
    certificate_type: str


@dataclass(frozen=True)
class GeneratedToken:
    """Response from POST /tokens."""
    token: str
    valid_until: datetime | None   # jeśli API zwraca TTL
```

### 3. Helper: `core/ksef/adapters/csr.py` (NOWY, ~40 linii)

Generacja klucza RSA + CSR (PKCS#10) na podstawie enrollment data:

```python
@dataclass(frozen=True)
class CsrResult:
    """Generated CSR + private key."""
    csr_pem: str              # PEM-encoded CSR
    csr_der_b64: str          # DER-encoded, Base64 — do API
    private_key_pem: str      # PEM-encoded private key — do bezpiecznego storage


def generate_csr(enrollment_data: EnrollmentData) -> CsrResult:
    """Generate RSA-2048 key + CSR using subject from enrollment_data."""
```

Używa `cryptography` (już w dependencies). RSA-2048 (minimum wg spec KSeF).

**WAŻNE:** Private key NIGDY na dysk automatycznie. CLI pyta operatora gdzie zapisać i ostrzega.

### 4. Use case: `core/ksef/usecases/enroll_certificate.py` (NOWY)

```python
@dataclass(frozen=True)
class EnrollResult:
    """Wynik pełnego enrollment flow."""
    certificate_b64: str
    certificate_name: str
    serial_number: str
    token: str
    private_key_pem: str      # do zapisu przez CLI


class EnrollCertificateUseCase:
    def __init__(
        self,
        api: KSeFApiClient,
        auth: KSefAuth,
        *,
        poll_interval_s: float = 5.0,
        poll_timeout_s: float = 300.0,
        sleep: Callable[[float], None] = time.sleep,
        on_status: Callable[[str], None] = print,   # callback dla CLI
    ) -> None: ...

    def execute(self) -> EnrollResult:
        """
        Flow:
        1. Auth (auth.ensure_valid) — potrzebny access_token
        2. GET enrollment data (E1)
        3. Generate CSR locally (RSA-2048 + subject z enrollment data)
        4. Submit enrollment (E2) → reference_number
        5. Poll enrollment status (E3) aż ready
        6. Retrieve certificate (E4)
        7. Generate KSeF token (E5)
        8. Return EnrollResult

        on_status callback: use case informuje CLI co robi (dla operatora).
        """
```

**Kontrakt:**
- `on_status` callback — use case wywołuje np. `on_status("E2: Wniosek złożony, ref=ABC123")`. CLI wypisuje to operatorowi. Pozwala na testowanie bez print().
- Polling E3: exponential backoff 5s → 10s → 20s (cap 60s), timeout 300s (enrollment może trwać)
- Error w dowolnym kroku → typed exception, CLI obsługuje

### 5. CLI: `tools/ksef_enroll.py` (NOWY, ~100 linii)

```
py tools/ksef_enroll.py
py tools/ksef_enroll.py --env demo
py tools/ksef_enroll.py --key-out secrets/ksef_private.pem --token-out .env
```

**Flow interaktywny:**
```
=== KSeF Certificate Enrollment ===
Środowisko: demo (api-demo.ksef.mf.gov.pl)
NIP: 7871003063

[1/7] Uwierzytelnianie... OK
[2/7] Pobieranie danych enrollment... OK
  Subject: CN=..., O=..., C=PL
[3/7] Generowanie klucza RSA-2048 + CSR... OK
[4/7] Składanie wniosku o certyfikat...
  Reference: ABC-123-DEF
[5/7] Oczekiwanie na wydanie certyfikatu...
  Status: przetwarzanie... (5s)
  Status: przetwarzanie... (15s)
  Status: gotowy!
[6/7] Pobieranie certyfikatu... OK
  Serial: 123456789
[7/7] Generowanie tokena KSeF... OK

=== WYNIK ===
Certyfikat: zapisany do secrets/ksef_cert.pem
Klucz prywatny: zapisany do secrets/ksef_private.pem
Token KSeF: zapisany do .env (KSEF_TOKEN=...)

UWAGA: Klucz prywatny przechowuj bezpiecznie! Nie commituj do repo.
```

**Parametry:**
- `--env` — override KSEF_ENV (default z .env)
- `--key-out` — ścieżka do zapisu klucza prywatnego (default: `secrets/ksef_private.pem`)
- `--cert-out` — ścieżka do zapisu certyfikatu (default: `secrets/ksef_cert.pem`)
- `--token-out` — plik do dopisania KSEF_TOKEN (default: `.env`)
- `--dry-run` — pokaż co by zrobił, nie kontaktuj się z API

**Bezpieczeństwo:**
- Sprawdź `.gitignore` zawiera `secrets/` i `.env`
- Ostrzeż jeśli nie zawiera
- Private key: file permissions 600 (Unix) lub warning (Windows)
- Nie wypisuj pełnego tokena w logach (ostatnie 4 znaki OK)

### 6. Testy

#### Unit: `tests/ksef/test_csr.py` (NOWY)

```
test_generate_csr_produces_valid_pem()
test_generate_csr_subject_matches_enrollment_data()
test_generate_csr_key_is_rsa_2048()
test_generate_csr_der_b64_roundtrips()
```
Minimum: **≥4 unit**

#### Contract: `tests/ksef/test_enroll_uc.py` (NOWY)

Use case z full mock — weryfikuje orchestrację:

```
test_enroll_happy_path_returns_token()
test_enroll_polls_until_ready()
test_enroll_timeout_raises_error()
test_enroll_api_error_propagates()
test_enroll_on_status_callback_called()
test_enroll_auth_failure_raises()
```
Minimum: **≥6 contract**

#### API methods: `tests/ksef/test_ksef_api_enrollment.py` (NOWY)

Testy mapowania response → typed dataclass (jak istniejące testy api):

```
test_get_enrollment_data_maps_response()
test_submit_enrollment_returns_ref()
test_enrollment_status_maps_codes()
test_retrieve_certificates_maps_array()
test_generate_token_maps_response()
```
Minimum: **≥5 unit**

#### Minimum testów

- CSR: ≥4 unit
- Enrollment use case: ≥6 contract
- API methods: ≥5 unit
- **Total nowych: ≥15 + zachowane 149 z Block 1-4 = ≥164 PASS**

---

## Pytania do Architekta (rozstrzygnięte w planie)

### Q1: POST /tokens — jaki payload?

OpenAPI spec (`openapiksef.json`) nie zawiera jasnej definicji POST /tokens body.
**Decyzja:** Developer weryfikuje na Demo. Jeśli endpoint wymaga dodatkowych pól
(np. certificate serial, scope, permissions) — dodaj do `generate_token()`.
Jeśli endpoint nie istnieje lub wymaga innej ścieżki — flag do Architekta.

### Q2: Enrollment wymaga istniejącego tokena — chicken-and-egg?

Tak. Enrollment endpoints wymagają Bearer access_token. Oznacza to:
- Operator musi mieć **wstępny** KSeF token (uzyskany ręcznie przez portal KSeF)
- Enrollment generuje **nowy** certyfikat + token (potencjalnie z innymi uprawnieniami)
- Runtime auth flow (Block 1) używa tokena z .env — bez znaczenia czy "ręczny" czy "enrolled"

**Implikacja:** Skrypt enrollment to narzędzie do **rotacji/formalizacji** credentiali,
nie do bootstrap od zera. Pierwszy token zawsze pochodzi z portalu KSeF.
Udokumentuj to w CLI help i docstringu.

### Q3: Gdzie `secrets/` w strukturze projektu?

Nowy katalog `secrets/` w root. Dodaj do `.gitignore` jeśli nie ma.
Cel: bezpieczne przechowywanie klucza prywatnego i certyfikatu.
Nie mieszaj z `data/` (ksef.db) ani `output/` (XML).

---

## Decyzje zatwierdzone

| Decyzja | Wybór | Uzasadnienie |
|---|---|---|
| Enrollment methods w ksef_api.py | TAK | Spójność: one method per endpoint |
| Orchestracja w usecases/ | TAK | Pattern: API = transport, UC = flow |
| CSR helper osobny moduł | TAK (csr.py) | Izolowalne, testowalne niezależnie |
| RSA-2048 | TAK | Minimum wg spec KSeF |
| Private key NIE na dysk automatycznie | TAK | Security — CLI pyta operatora |
| on_status callback | TAK | Testowalność bez side effects |
| `secrets/` katalog | TAK | Separacja od data/output |

---

## Out of scope (świadomie)

- **XAdES signature auth** — inna ścieżka auth (podpis XML), nie używamy (ADR-KSEF-002)
- **Certificate revocation** — osobna operacja, nie w M3 scope
- **Token rotation daemon** — automatyczna rotacja, docelowo M6
- **OS keyring / vault** — docelowy secure storage, na razie .env (ADR-KSEF-005)
- **Prod enrollment** — Block 5 weryfikuje na Demo; Prod = osobny run z `--env prod`

---

## Ryzyka

| Ryzyko | Mitygacja |
|---|---|
| POST /tokens payload nieznany z OpenAPI spec | Developer weryfikuje na Demo, flag jeśli problem |
| Enrollment processing delay (certyfikat nie gotowy od razu) | Poll z backoff do 300s, CLI informuje operatora |
| CSR subject fields nie zgadzają się z KSeF expectations | Pobieramy exact fields z E1, używamy 1:1 |
| Private key wyciek | Ostrzeżenia w CLI, .gitignore check, file permissions |
| Enrollment niedostępny na Demo | `@pytest.mark.integration` skip, contract testy z mock |

---

## Kolejność pracy (rekomendacja)

1. **csr.py** + unit testy — izolowany moduł, zero zależności od API
2. **Nowe modele** w models.py (EnrollmentData, EnrollmentStatus, Certificate, GeneratedToken)
3. **Nowe metody** w ksef_api.py + unit testy mapowania
4. **enroll_certificate.py** (use case) + contract testy z full mock
5. **ksef_enroll.py** (CLI) — interaktywny wrapper
6. Verify na Demo: `py tools/ksef_enroll.py --env demo` (manual)

---

## Workflow i handoff

Developer realizuje przez `workflow_developer_tool`.

Po ukończeniu — handoff do Architekta na `workflow_code_review`:

```
py tools/agent_bus_cli.py handoff \
  --from developer --to architect \
  --phase "ksef_block_5_review" --status PASS \
  --summary "Block 5: enrollment cert + token generation. Demo verified. 164+ tests PASS." \
  --next-action "Code review — core/ksef/adapters/csr.py, core/ksef/usecases/enroll_certificate.py, tools/ksef_enroll.py"
```

Po PASS → M5 daemon (ScanErp + batch) — decyzja człowieka.
