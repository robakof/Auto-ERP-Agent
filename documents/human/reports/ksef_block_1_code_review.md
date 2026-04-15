# Code Review: KSeF Block 1 (API client + auth + tests)

Date: 2026-04-15
Branch: main
Reviewer: Architect
Plan: `documents/human/plans/ksef_developer_block_1.md`
Handoff: msg #63 (developer → architect)

## Summary

**Overall assessment:** **NEEDS REVISION** (2 Critical: brak deps w requirements.txt, brak tests/integration/)
Po naprawie Critical issues → PASS bez kolejnej rundy.

**Code maturity level:** **L3 Senior** — czyste warstwy (http → api → auth), boundary validation (dict→dataclass w jednym miejscu w `_extract_error` / `_parse_*`), dependency injection (cert, clock, sleep, http_client), typed throughout, testy edge case'ów (refresh failure, polling timeout, brak cert). Dla L4 brakowałoby guardrails uniemożliwiających klasy błędów (np. typed router niezomijalny) i self-monitoring observability.

**Tests:** 51/51 PASS (`tests/ksef/` lokalnie zweryfikowane przez Architekta).

**Acceptance vs deliverable:**
- ✓ 10 endpointów + bonus `/security/public-key-certificates` (wymagany dla RSA-OAEP encryption KSeF tokena — dobre rozszerzenie scope, zgodne z KSeF 2.0)
- ✓ Typed dataclasses na granicy
- ✓ 41 contract tests + 10 auth flow tests = 51 PASS
- ✗ **Integration smoke test (`tests/integration/test_ksef_demo_smoke.py`) nieobecny** — Block 1 §Acceptance go wymagał (skip gdy brak `KSEF_TOKEN`)
- ✓ `tools/ksef_smoke.py` — CLI z exit codes
- ✓ `.env.example` — sekcja KSeF dodana
- ✓ Zero zmian w `tools/ksef_generate*.py`
- ✓ Zero logiki biznesowej w adapters

---

## Findings

### Critical Issues (must fix przed PASS)

- **`requirements.txt:1-9`** — brak nowych zależności: `httpx`, `tenacity`, `cryptography`, `respx`. Bez tego setup na serwerze RDP/CI rozsypie się przy `pip install -r requirements.txt`. Dodaj:
  ```
  httpx>=0.27
  tenacity>=8.2
  cryptography>=42.0
  respx>=0.21      # tylko do testów; jeśli mamy requirements-dev.txt — tam
  ```
  Sprawdź czy projekt ma podział `requirements.txt` / `requirements-dev.txt` i ulokuj poprawnie.

- **`tests/integration/` — katalog nie istnieje** — Block 1 §Testy wymagało:
  ```
  tests/integration/test_ksef_demo_smoke.py
  ```
  Z markerem `@pytest.mark.integration` i automatycznym `pytest.skip` gdy brak `KSEF_TOKEN` w env. Ten test musi istnieć w repo (nawet jeśli się skipuje), bo to forma kontraktu z prawdziwym Demo. Tools/ksef_smoke.py jest manualnym CLI — nie zastępuje automatu w pytest.

### Warnings (should fix)

- **`core/ksef/config.py:18,49`** — `nip: str | None` jako Optional, mimo że auth zawsze wymaga NIP. `tools/ksef_smoke.py:37` ratuje błąd dopiero w runtime. Albo uczyń `KSEF_NIP` wymaganym w `load_config()` (raise w startup), albo dokumentuj że jest opcjonalny tylko dla skryptów które go nie potrzebują (i wymień je). Fail-fast > fail-late.

- **`core/ksef/adapters/ksef_auth.py:163-170` vs `core/ksef/models.py:46-56`** — `AuthOperationStatus` ma properties `in_progress`/`success`/`failed`, ale `_poll_until_success` ich nie używa, tylko hard-coded `_STATUS_SUCCESS = 200`, `>= 400`, `_STATUS_IN_PROGRESS`. Logika rozróżniania kodów zduplikowana w dwóch miejscach. Albo używaj properties z modelu (`if status.success`, `if status.failed`, `if status.in_progress`), albo wywal properties z modelu jako martwy kod.

- **`.env` w `.gitignore`** — niezweryfikowane przez review. Sprawdź `git check-ignore .env` zanim ktokolwiek wklei prawdziwy KSEF_TOKEN. Dodaj entry jeśli brak.

- **`core/ksef/adapters/http.py:190-194` + retry decorator (157-163)** — przy 429 najpierw `_sleep_retry_after` (z `Retry-After` z API), potem rzucamy `KSefTransportError`, potem tenacity dodaje exp backoff (1→4→10s). Czyli sleep podwójny. Świadoma decyzja czy bug? Jeśli świadoma — komentarz "double sleep intentional: API throttle + jitter safety". Jeśli nie — dla 429 zignoruj tenacity backoff lub pomiń własne sleep.

- **`core/ksef/adapters/ksef_api.py:170-176` (`close_online_session`)** — używa `POST /sessions/online/{ref}/close`. Zweryfikowano w spec (linia 7780): poprawny endpoint, POST. OK. Ale odlogowanie sesji `/auth/sessions/current` używa `DELETE` (poprawnie, linia 155-156). Asymetria nazewnicza w API KSeF — komentarz w kodzie pomógłby (`# Note: KSeF uses POST .../close for online sessions, but DELETE for auth session`).

### Suggestions (nice to have)

- **`core/ksef/adapters/http.py:120` (`request_json`)** — return type `Any` to za luźno. W praktyce zawsze `dict[str, Any] | list[Any]`. Doprecyzuj sygnaturę.

- **`core/ksef/adapters/ksef_auth.py:127-134` (`logout`)** — `try/finally` połyka błąd z `api.logout()`. Tracimy diagnostykę. Dodaj `except Exception as exc: _LOG.warning(...)` przed `finally`.

- **`core/ksef/adapters/http.py:201-207` (`_sleep_retry_after`)** — clampuje do 60s. Jeśli KSeF zwróci 300s (długi throttle), my śpimy 60 i ponawiamy → marnujemy quota. Albo nie clampuj, albo log warn gdy clamping zachodzi.

- **`core/ksef/adapters/ksef_auth.py:158-177` (`_poll_until_success`)** — funkcja ma 20 linii, ale gęsta logika. Można rozbić na `_evaluate_status_code(status)` (zwracający enum: SUCCESS / FAILED / IN_PROGRESS / UNKNOWN) i pętlę polling. Funkcja ≤15 linii to nasz target.

- **`core/ksef/adapters/ksef_api.py:99-108` (`redeem_token`)** — duplikat parsowania `validUntil` z `refresh_token`. Helper `_parse_token(payload, cls) -> AccessToken | RefreshToken` zredukowałby DRY.

- **`tools/ksef_smoke.py:69` (`except Exception`)** — łapie wszystko jednym kodem. Mogłoby rozróżniać exit codes per typ błędu (auth=2, transport=3, api=4) — ułatwia diagnostykę z `echo $?`.

- **`core/ksef/adapters/ksef_auth.py:91`** — payload `f"{token}|{timestampMs}"`. Format hard-coded; dobrze byłoby mieć stałą `_AUTH_PAYLOAD_FORMAT` lub komentarz wskazujący sekcję spec KSeF którą realizuje.

- **`tools/ksef_smoke.py:50`** — `print` z `[c.usage for c in certs]` może drukować wartość traktowaną jako wrażliwą? Cert publiczny ze swojej natury OK, ale w trybie verbose można też zalogować `valid_to` per cert (przyda się przy debugowaniu wygaśnięcia).

---

## Recommended Actions

Developer wykonuje patch:

- [ ] **C1** Dodać `httpx>=0.27`, `tenacity>=8.2`, `cryptography>=42.0` do `requirements.txt`; `respx>=0.21` do `requirements-dev.txt` jeśli istnieje (lub do `requirements.txt` z komentarzem `# test only`).
- [ ] **C2** Utworzyć `tests/integration/__init__.py` + `tests/integration/test_ksef_demo_smoke.py` z testem oznaczonym `@pytest.mark.integration` i `pytest.skip("KSEF_TOKEN missing", allow_module_level=False)` przy braku tokena. Test wykonuje: load_config → get_public_key_certificates → authenticate → open_online_session → close_online_session → logout. Konfiguracja `pytest.ini` lub `pyproject.toml` powinna zarejestrować marker `integration` (`addopts = -m "not integration"` w default; uruchomienie: `pytest -m integration`).
- [ ] **W1** `KSEF_NIP` → wymagane w `load_config()` z jasnym komunikatem błędu.
- [ ] **W2** `_poll_until_success` używa properties z `AuthOperationStatus` (DRY).
- [ ] **W3** Zweryfikować `.env` w `.gitignore` (raport: PASS/FAIL).
- [ ] **W4** Decyzja świadoma o double-sleep przy 429 — komentarz albo refaktor.
- [ ] **Suggestions S1-S6** — opcjonalne, do oceny przez Developera. Jeśli zostawia bez zmian, niech krótko uzasadni w handoff zwrotnym.

Po wykonaniu C1-W4: handoff zwrotny do Architekta na drugie review (powinno być szybkie — tylko delta).

---

## Architektura — co zostało zrobione dobrze

Warto utrwalić jako wzorzec dla kolejnych bloków:

1. **Boundary validation** — wszystkie odpowiedzi parsowane do dataclass w `KSeFApiClient.*` przez `_parse_dt` / `_parse_auth_init`. Upper layers (auth, smoke) nie widzą surowych dictów. Zgodne z `PATTERNS.md §Validation at Boundary`.
2. **Dependency injection** — `KSefHttp(client=...)` pozwala na respx w testach; `KSefAuth(clock=..., sleep=...)` umożliwia mock clock bez biblioteki freezegun. Mniej zależności, więcej kontroli.
3. **Rozdzielenie warstw** — http (transport) / api (kontrakt endpointów) / auth (orchestracja). Każda warstwa zna tylko warstwę poniżej. Zero przecieków.
4. **Obsługa szyfrowania KSeF tokena** — Developer trafnie rozszerzył scope o `/security/public-key-certificates` + RSA-OAEP/SHA-256, co jest wymogiem spec KSeF 2.0. Test `test_authenticate_encrypts_token_payload` weryfikuje że payload faktycznie szyfrowany. Bez tego auth by nie zadziałało na Demo.
5. **Cache cert per instancja `KSefAuth`** — pobrany raz, używany do końca życia. Sensowna optymalizacja (cert nie zmienia się w trakcie sesji).
6. **`request_empty` jako osobna metoda** — nie udawać że odpowiedź 204 jest JSON. Czysta semantyka.

---

## Wnioski strategiczne

Block 1 ma fundament wysokiej jakości. Po naprawie 2 Critical mamy bazę pod:
- **Block 2:** Shadow DB (M1) + enrollment tool (`tools/ksef_enroll.py`) — można pisać równolegle
- **Block 3:** M0 (konsolidacja XML) — niezależny od KSeF API
- **Block 4:** M4 SendInvoice use case łączący wszystko

Decyzja o kolejności Block 2/3/4 — po review Block 1 fix, w osobnej rozmowie z człowiekiem.

**Pattern do wpisania w `PATTERNS.md`** (osobny task):
- "Async-Ready Sync HTTP Client" — `httpx.Client` z `KSefHttp` daje sync API, ale stack `httpx + tenacity + respx` jest gotowy na przejście na async gdy daemon zacznie obsługiwać polling wielu sesji równolegle.
- "Boundary Dataclass Parsing" — wzorzec `_parse_*` w API client jako jedyna warstwa konwersji dict↔domain. Powtarzalny dla każdego nowego adaptera.
