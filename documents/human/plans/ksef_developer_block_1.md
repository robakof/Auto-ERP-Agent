# Developer Block 1 — KSeF API client + auth + smoke tests

Data: 2026-04-15
Autor: Architect
Dotyczy planu: `documents/human/plans/ksef_api_automation.md` (§5 M2 + M3 runtime)
Dla roli: Developer
Status: Ready to start

---

## Cel bloku

Udowodnić że umiemy rozmawiać z KSeF 2.0 Demo API — zalogować się tokenem,
otworzyć sesję, zamknąć sesję. **Zero logiki biznesowej, zero XML, zero DB, zero ERP.**
Czysty transport + auth + testy.

Po ukończeniu tego bloku mamy fundament na którym M1 (Shadow DB), M0 (konsolidacja
XML), M4 (SendInvoice pipeline) budują bez zgadywania kontraktu API.

---

## Decyzje zatwierdzone (2026-04-15)

| Decyzja | Wybór |
|---|---|
| Strategia dostarczenia tokena | Opcja B: człowiek ręcznie pobiera token z portalu MF Demo i wkleja do `.env`. **Enrollment tool `tools/ksef_enroll.py` odkładamy do późniejszego bloku.** |
| Storage sekretów (start) | `.env` w katalogu projektu, wpisany w `.gitignore`; docelowo keyring (ADR-KSEF-005 później) |
| Biblioteka HTTP | `httpx` (async-ready — przyda się do pollingu) |
| Klient API | Hand-written, nie generowany z OpenAPI (użyjemy tylko ~10 endpointów z 650 KB spec) |
| Środowisko uruchomieniowe | Windows Server (ERP XL RDP) — ten sam serwer co docelowy daemon |
| Środowisko testowe | `ksef-test.mf.gov.pl` (Demo) — base URL do potwierdzenia w `openapiksef.json` |

---

## Scope — co dokładnie powstaje

### Moduł: `core/ksef/`

Nowy pakiet. Struktura:

```
core/
  __init__.py
  ksef/
    __init__.py
    adapters/
      __init__.py
      http.py           # httpx wrapper: base_url, retry, timeouts, structured logging
      ksef_api.py       # KSeFApiClient — metody per endpoint
      ksef_auth.py      # KSefAuth — orchestracja auth flow + cache access tokena
    config.py           # ładowanie .env (KSEF_ENV, KSEF_DEMO_TOKEN, KSEF_BASE_URL)
    exceptions.py       # KSefError hierarchy: AuthError, ApiError(4xx), TransportError(5xx/timeout)
    models.py           # dataclasses odpowiedzi: AuthChallenge, AccessToken, Session, InvoiceStatus, Upo
```

### Endpointy KSeF API do zaimplementowania

Kolejność = kolejność w auth flow + operational loop:

| # | Metoda | Endpoint | Cel |
|---|---|---|---|
| 1 | POST | `/auth/challenge` | Pobierz challenge |
| 2 | POST | `/auth/ksef-token` | Autoryzacja tokenem |
| 3 | GET  | `/auth/{referenceNumber}` | Status authn |
| 4 | POST | `/auth/token/redeem` | Access token |
| 5 | POST | `/auth/token/refresh` | Refresh access token |
| 6 | POST | `/sessions` | Otwarcie sesji interaktywnej |
| 7 | POST | `/sessions/{ref}/invoices` | Wyślij fakturę (placeholder body — testujemy tylko kontrakt, nie content) |
| 8 | GET  | `/sessions/{ref}/invoices/{invoiceRef}` | Status pojedynczej faktury |
| 9 | GET  | `/sessions/{ref}/invoices/ksef/{ksefNumber}/upo` | UPO |
| 10 | DELETE | `/auth/sessions/current` | Zamknięcie sesji |

Każdy endpoint:
- Sygnatura zwraca typed dataclass (nie dict)
- 4xx → `KSefApiError(status, error_code, message, details)`
- 5xx / timeout / connection → `KSefTransportError` z retry policy (tenacity: 3x, exp backoff 1s→4s→10s)
- 429 → respektuj `Retry-After`

### Klasa `KSefAuth` — orchestracja

```
KSefAuth(api_client, token_provider)
  authenticate() -> AccessToken
    1. challenge = api.get_challenge()
    2. auth_ref = api.auth_with_token(token=token_provider.get(), challenge_ts=challenge.timestamp)
    3. polling api.auth_status(auth_ref) aż status=finished (max 30s, 1s interval)
    4. access = api.redeem_token(auth_ref)
    5. self._cache = access
    6. return access

  ensure_valid() -> AccessToken
    if cache.expires_in < 5min: self._cache = api.refresh_token(cache.refresh_token)
    return self._cache
```

Persistence cache: **nie w Block 1** — trzymaj tylko w pamięci. Disk-cache dodamy
gdy pojawi się daemon (M5).

### CLI: `tools/ksef_smoke.py`

```
py tools/ksef_smoke.py --env demo
```

Wykonuje sekwencję:
1. Wczytaj `.env` (`KSEF_ENV`, `KSEF_DEMO_TOKEN`, `KSEF_BASE_URL`)
2. `KSefAuth.authenticate()` → loguj otrzymany access token (ostatnie 4 znaki + TTL)
3. `api.open_session()` → loguj session_ref
4. `api.close_session()` → loguj success
5. Exit code: 0 = OK, 1 = auth fail, 2 = transport fail, 3 = API fail

**Brak** wysyłania faktury w smoke — to Block 2 (M4).

### `.env` — wzorzec

Plik przykładowy `.env.example` w repo (commitowany):

```
KSEF_ENV=demo
KSEF_BASE_URL=https://ksef-test.mf.gov.pl/api
KSEF_DEMO_TOKEN=  # wklej token z portalu MF Demo po rejestracji CEiM
```

`.env` (prawdziwy) → `.gitignore`.

---

## Testy

### Contract tests (mocked) — `tests/test_ksef_api_contract.py`

Biblioteka: `respx` (mocki dla httpx).

Pokrycie per endpoint (10 endpointów × scenariusze):

- **Happy path** — 200/201 → deserialize do dataclass, zero KeyError
- **4xx** — 400/401/403/404/409/422 → `KSefApiError` z poprawnym `error_code`
- **5xx** — 500/502/503 → `KSefTransportError` po wyczerpaniu retry
- **429** → respect `Retry-After`, potem sukces
- **Timeout / ConnectionError** → `KSefTransportError` po retry

Minimum: ~40-50 testów, wszystkie PASS, zero flakes.

### Auth flow tests — `tests/test_ksef_auth_flow.py`

- Happy flow: challenge → auth → polling → redeem → access token
- Polling timeout (30s bez `finished`) → `AuthTimeoutError`
- Polling failure (status=failed) → `AuthError` z kodem z API
- `ensure_valid` — bez odświeżenia (token ważny)
- `ensure_valid` — z refreshem (TTL < 5 min)
- `ensure_valid` — refresh nieudany → pełna re-authentication

Mock clock: `freezegun` albo `time_machine`.

### Integration test — `tests/integration/test_ksef_demo_smoke.py`

Jeden test, marker `@pytest.mark.integration`. Skip jeśli brak `KSEF_DEMO_TOKEN`
w env.

```python
def test_smoke_demo_auth_and_session(ksef_client):
    auth = KSefAuth(ksef_client, EnvTokenProvider())
    access = auth.authenticate()
    assert access.token
    assert access.expires_at > now()

    session = ksef_client.open_session(access.token)
    assert session.reference_number

    ksef_client.close_session(access.token, session.reference_number)
```

Uruchamiany ręcznie na serwerze RDP po wklejeniu tokena do `.env`:
```
py -m pytest tests/integration/test_ksef_demo_smoke.py -m integration -v
```

---

## Acceptance criteria (Architect → Developer)

- [ ] Wszystkie 10 endpointów z tabeli zaimplementowane jako metody `KSeFApiClient`
- [ ] Każda odpowiedź typowana (dataclass), zero `dict` przeciekających do warstwy wyższej
- [ ] Contract tests: ≥40 testów, 100% PASS
- [ ] Auth flow tests: 100% PASS (6+ scenariuszy)
- [ ] Integration smoke test przeciw Demo: auth + open_session + close_session kończy się OK
- [ ] `tools/ksef_smoke.py --env demo` exit 0 na serwerze ERP (po wklejeniu tokena)
- [ ] `.env.example` w repo, `.env` w `.gitignore`
- [ ] `tmp/` nie zawiera sekretów (check pre-commit)
- [ ] Zero zmian w `tools/ksef_generate*.py` — nie dotykamy istniejących generatorów
- [ ] Zero logiki biznesowej w `core/ksef/adapters/` — tylko transport, mapping, auth

### Jakość kodu (L3 Senior)

- Funkcje ≤15 linii (helpery mogą być dłuższe tylko przy dobrym uzasadnieniu)
- Zero `print()` — `logging` + structured JSON handler
- Typed throughout (`mypy` przechodzi bez errorów dla `core/ksef/`)
- `from __future__ import annotations` + hinty per PEP 604
- Zero magic strings — kody błędów KSeF jako enum

---

## Workflow i handoff z powrotem

Developer realizuje przez workflow `workflow_developer_tool` (nowa funkcja tooling)
albo `workflow_developer_patch` (jeśli Developer uzna scope = patch-size).
Decyzja o wyborze workflow należy do Developera po wstępnej ocenie scope.

Po ukończeniu — handoff do Architekta na code review
(`workflow_code_review`). Code review ocenia:
- Strukturę warstw (czy nie ma przecieków)
- L3 Senior w wymiarach bazowych + Python CLI stack
- Kompletność testów per acceptance
- Anti-patterny z `PATTERNS.md`

Po PASS code review → Block 2 (enrollment tool lub M1 — decyzja po review).

---

## Out of scope w Block 1 (świadomie)

- `tools/ksef_enroll.py` — enrollment cert flow (E1-E5). Opcja B: token dostajemy
  manualnie. Enrollment buildujemy później gdy potrzebna rotacja.
- Shadow DB `data/ksef.db` (M1) — robimy po API
- XML generation, domain model (M0) — robimy po API i DB
- Daemon (M5) — robimy jako ostatnie
- Retry z persist state — Block 1 retry tylko w pamięci
- Disk cache tokena — Block 1 trzyma w pamięci procesu
- Prod env — wyłącznie Demo, `KSEF_ENV=demo` jest jedyną dopuszczalną wartością w Block 1

---

## Punkty uwagi dla Developera

1. **Base URL Demo KSeF** — zweryfikuj w `documents/Wzory plików/openapiksef.json`
   (pole `servers`). Jeśli brak — zapytaj Architekta.
2. **Czas życia access tokena** — w spec KSeF jest konkretny TTL; pokryj edge cases
   (refresh w locie, re-auth gdy refresh_token też wygasł).
3. **Polling interval auth status** — start 1s, exp backoff do 5s; timeout 30s.
4. **Rate limiting** — Demo może mieć niższe limity niż Prod. 429 obowiązkowo testowany.
5. **Strefa czasu** — wszystkie timestamps z/do API w UTC, w logach pokazuj też lokalne.
6. **Security** — `.env` NIGDY nie trafia do commita. Test: `git log -p` po skończeniu nie zawiera słowa "KSEF_DEMO_TOKEN=" z wartością.
7. **Sesja operacyjna vs Auth session** — uważaj na nazewnictwo. `/auth/sessions` to
   zarządzanie sesjami auth (login); `/sessions` to sesje wysyłkowe. Nie mieszać.
8. **Daemon runtime** — kod pisany jest pod uruchomienie na Windows Server (ERP XL via RDP).
   Ścieżki `pathlib` tylko, zero hardcoded `/`.

---

## Plik do weryfikacji po skończeniu

Architect wykona code review przez `workflow_code_review`. Developer wyśle handoff:

```
py tools/agent_bus_cli.py handoff \
  --from developer --to architect \
  --phase "ksef_block_1_review" --status PASS \
  --summary "Block 1 zaimplementowany: 10 endpointów, 40+ testów, smoke OK na Demo" \
  --next-action "Code review — core/ksef/, tests/test_ksef_*, tools/ksef_smoke.py"
```

Z listą przetestowanych klas testowych w formacie:
`test_ksef_api_contract.py::TestXxx — N/N PASS`
