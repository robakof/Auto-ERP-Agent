# Plan architektoniczny: Automatyzacja KSeF API

Data: 2026-04-15
Autor: Architect
Status: Draft (do review przez człowieka)
Zakres: od obecnych 2 skryptów generujących XML → pełna automatyzacja wysyłki do KSeF API

---

## 1. Cel

Zautomatyzować wysyłkę faktur FS i korekt FSK z ERP Comarch XL bezpośrednio do
KSeF (Krajowy System e-Faktur) przez REST API. Po zatwierdzeniu dokumentu w ERP
system samodzielnie:

1. Wykryje nową fakturę/korektę,
2. Wygeneruje KSeF XML FA(3),
3. Otworzy sesję w KSeF (auth),
4. Wyśle dokument,
5. Pobierze UPO (Urzędowe Poświadczenie Odbioru),
6. Zapisze ślad w shadow DB (status, KSeF number, UPO).

Zero modyfikacji ERP XL. Wszystko co wiemy o wysyłce — w naszej DB.

---

## 2. Decyzje zatwierdzone przez człowieka (2026-04-15)

| Decyzja | Wybór | Uzasadnienie |
|---|---|---|
| Środowisko startowe | **Demo KSeF** (`ksef-test.mf.gov.pl`) | Bezpieczny start, zero ryzyka na Prod |
| Certyfikat | **CEiM** — do wyrobienia (pieczęć kwalifikowana firmy) | `msps.pl` to prywatny projekt, nie dotykamy |
| Strategia auth | **KSeF token** (enrollment przez `/certificates/enrollments` + autoryzacja przez `/auth/ksef-token`) | Prostsza ścieżka niż XAdES — brak konieczności implementacji podpisu XML |
| Feedback do ERP | **Shadow DB** — nasza baza, bez ingerencji w ERP | ERP XL nietknięty, jedno źródło danych o wysyłkach |
| Lokalizacja DB | **Osobny `data/ksef.db`** | Dedykowany backup, separacja księgowego audytu od agent bus |
| Tryb pracy | **Auto-scan daemon** | Bez udziału operatora, "wystawione w ERP → wysłane do KSeF" |
| Źródło prawdy | **ERP XL** (dokumenty ze statusem zatwierdzony) | Tylko dokumenty domknięte, brak draftów |
| Skala / polityka | **~20-30 dok/dzień, każdy wysyłany pojedynczo po zatwierdzeniu** | Brak batchy — pojedyncza sesja per dokument (upraszcza recovery) |

---

## 3. Ocena stanu obecnego

### 3.1 Kod — co istnieje

- `tools/ksef_generate.py` — FS (faktura sprzedaży) → FA(3) XML
- `tools/ksef_generate_kor.py` — FSK (korekta) → FA(3) XML z sekcją `DaneFaKorygowanej`
- `solutions/ksef/ksef_fs_draft.sql` — widok FS
- `solutions/ksef/ksef_fsk_draft.sql` — widok FSK z modelem StanPrzed/StanPo
- Ręczna walidacja XSD (`--validate`)
- Output: plik XML na dysku (`output/ksef/`)

### 3.2 Poziom dojrzałości — L2 Mid

Wymiary do poprawy (bloker dla rozbudowy):

- **DRY:** oba skrypty mają `E()`, `v()`, `fmt_decimal()`, `validate_xsd()`, `build_sql()`, `main()` niemal identyczne. Helpery skopiowane.
- **Warstwa domenowa brakuje:** dict-hell. `row["Fa_P15_KwotaNaleznosci"]` rozsiane po kodzie — zero enkapsulacji. Dodanie pola wymaga zmiany SQL + Pythona + testów w wielu miejscach.
- **Brak persystencji:** wygenerowany XML = jedyny ślad. Uruchomić drugi raz? Wygeneruje ponownie. Nie wiadomo co zostało "wysłane" (bo nic nie jest jeszcze wysyłane).
- **Brak abstrakcji warstwowej:** CLI → SQL → lxml w jednym module. Trudno testować, trudno rozszerzać o API.

Wniosek: **zanim dodamy klienta API, wymagana konsolidacja (M0).** Dobudowywanie API do obecnej struktury pogłębia dług.

---

## 4. Architektura docelowa

### 4.1 Warstwy

```
┌─────────────────────────────────────────────────────────┐
│ Daemon / CLI entrypoint                                  │  tools/ksef_daemon.py
│  - tick: co N minut skanuj ERP po nowe zatwierdzone      │  tools/ksef_send.py (one-shot)
│  - per dokument: dispatch do use case                    │
├─────────────────────────────────────────────────────────┤
│ Use Cases (orchestracja)                                 │  core/ksef/usecases/
│  - SendInvoice(gid, rodzaj)                              │    send_invoice.py
│  - PollStatus(wysylka_id)                                │    poll_status.py
│  - FetchUPO(wysylka_id)                                  │    fetch_upo.py
│  - ScanErp()  → lista nowych GID-ów                      │    scan_erp.py
├─────────────────────────────────────────────────────────┤
│ Domain                                                   │  core/ksef/domain/
│  - Faktura, Korekta, Pozycja, Podmiot (dataclasses)      │    invoice.py
│  - Wysylka (state machine)                               │    shipment.py
│  - UPO                                                   │    upo.py
├─────────────────────────────────────────────────────────┤
│ Adapters (ports & adapters)                              │  core/ksef/adapters/
│  - ErpReader      (SQL → Faktura/Korekta)                │    erp_reader.py
│  - KSeFApiClient  (REST: auth, sessions, invoices, UPO)  │    ksef_api.py
│  - ShipmentRepo   (SQLite: audit trail, idempotency)     │    repo.py
│  - XmlBuilder     (Faktura → XML string)                 │    xml_builder.py
│  - XadesSigner    (podpis XAdES wyzwania auth)           │    signer.py
└─────────────────────────────────────────────────────────┘
```

Zasada: każda warstwa zna tylko warstwę poniżej. Domain nie wie o SQL, API, XML.

### 4.2 State machine wysyłki

```
DRAFT ──► QUEUED ──► AUTH_PENDING ──► SENT ──► ACCEPTED (UPO)
   │         │            │              │            │
   └─► ERROR ◄────────────┴──────────────┴──► REJECTED (by KSeF)
```

Każdy stan ma odrębną akcję (test z heurystyki 1). Przejścia wyłącznie forward —
retry tworzy nowy wpis `wysylka` z referencją do poprzedniej próby (audit).

### 4.3 Idempotencja

Klucz: `(gid_erp, rodzaj_dokumentu)`. Przed wysyłką check: czy istnieje wysyłka
w stanie `ACCEPTED` lub `SENT` (czeka na UPO)? Jeśli tak — skip, log.

Daemon musi być restart-safe: restart w środku `AUTH_PENDING` → wznowienie (sesja
w KSeF istnieje z `referenceNumber` zapisanym w DB).

### 4.4 KSeF API — zmapowane endpointy (openapiksef.json)

**Ścieżka enrollment (jednorazowa, offline — przez operatora):**

| Krok | Endpoint | Metoda | Uwaga |
|---|---|---|---|
| E1. Dane do wniosku o cert | `/certificates/enrollments/data` | GET | Pobierz payload do wniosku |
| E2. Złożenie wniosku o cert | `/certificates/enrollments` | POST | Wniosek o wydanie cert KSeF |
| E3. Status wniosku | `/certificates/enrollments/{ref}` | GET | Polling aż gotowe |
| E4. Pobranie certyfikatu | `/certificates/retrieve` | POST | Cert do przechowania (secret) |
| E5. Wygenerowanie tokena KSeF | `/tokens` | POST | Token = długoterminowy credential |

**Ścieżka operacyjna (runtime, daemon):**

| Krok | Endpoint | Metoda |
|---|---|---|
| 1. Wyzwanie autoryzacyjne | `/auth/challenge` | POST |
| 2. Autoryzacja tokenem KSeF | `/auth/ksef-token` | POST (body: token) |
| 3. Redeem access token | `/auth/token/redeem` | POST |
| 4. Status auth | `/auth/{referenceNumber}` | GET |
| 5. Otwarcie sesji | `/sessions` | POST |
| 6. Wysłanie faktury | `/sessions/{ref}/invoices` | POST |
| 7. Status faktury w sesji | `/sessions/{ref}/invoices/{invoiceRef}` | GET |
| 8. Pobranie UPO | `/sessions/{ref}/invoices/ksef/{ksefNumber}/upo` | GET |
| 9. Refresh access token | `/auth/token/refresh` | POST |
| 10. Zamknięcie sesji | `/auth/sessions/current` | DELETE |

---

## 5. Milestones

Każdy milestone = osobny mergeable krok z acceptance criteria. Developer
implementuje po każdym milestonie workflow `workflow_code_review`.

### Kolejność realizacji (zaktualizowana 2026-04-15)

Oryginalna: M0 → M1 → M2 → M3 → M4 → M5 → M6
**Zaktualizowana: M2 + M3 runtime (Block 1) → M1 → M0 → M4 → M3 enrollment → M5 → M6**

Powód: człowiek preferuje udowodnienie integracji z API zanim zainwestujemy
w refaktor XML (M0) i shadow DB (M1). Block 1 jest izolowany — nie dotyka
istniejących generatorów `tools/ksef_generate*.py`.

Szczegóły Block 1: `documents/human/plans/ksef_developer_block_1.md`.

### M0 — Konsolidacja (fundament)

**Cel:** Jeden spójny moduł `core/ksef/` zamiast duplikacji w 2 skryptach.
Zero zmian funkcjonalnych — tylko refaktor + testy regresyjne.

**Zakres:**
- `core/ksef/domain/` — dataclasses `Faktura`, `Korekta`, `Pozycja`, `Podmiot`, `Adnotacje`
- `core/ksef/adapters/erp_reader.py` — SQL → domain object
- `core/ksef/adapters/xml_builder.py` — domain → XML (wspólne buildery, rozgałęzienie per typ w dedykowanych metodach)
- `core/ksef/adapters/xsd_validator.py`
- `tools/ksef_generate.py` + `tools/ksef_generate_kor.py` → cienkie CLI nad nową warstwą
- Testy regresyjne: dla GID z produkcji XML identyczny byte-by-byte przed i po refaktorze (snapshot test)

**Acceptance:**
- [ ] Wszystkie istniejące `ksef_generuj_fs.bat` i `ksef_generuj_kor.bat` działają bez zmian CLI
- [ ] XML byte-identical z pre-refactor (snapshot test dla ≥3 GID FS + ≥2 GID FSK)
- [ ] Code review PASS na L3 Senior

**Estymacja:** 1 sesja Developera + 1 review.

---

### M1 — Shadow DB + Repository

**Cel:** Persystencja stanu wysyłek niezależna od ERP XL.

**Lokalizacja:** `data/ksef.db` (decyzja zatwierdzona 2026-04-15).

**Zakres:**
- Schema:
  ```sql
  CREATE TABLE ksef_wysylka (
    id INTEGER PRIMARY KEY,
    gid_erp INTEGER NOT NULL,
    rodzaj TEXT NOT NULL CHECK (rodzaj IN ('FS', 'FSK')),
    nr_faktury TEXT NOT NULL,
    data_wystawienia DATE NOT NULL,
    xml_path TEXT NOT NULL,
    xml_hash TEXT NOT NULL,       -- SHA-256 XML (idempotency)
    status TEXT NOT NULL,         -- DRAFT/QUEUED/AUTH_PENDING/SENT/ACCEPTED/REJECTED/ERROR
    ksef_session_ref TEXT,
    ksef_invoice_ref TEXT,
    ksef_number TEXT,             -- nr nadany przez KSeF
    upo_path TEXT,                -- ścieżka XML UPO
    error_code TEXT,
    error_msg TEXT,
    attempt INTEGER DEFAULT 1,
    created_at TIMESTAMP,
    sent_at TIMESTAMP,
    accepted_at TIMESTAMP,
    UNIQUE (gid_erp, rodzaj, attempt)
  );
  CREATE INDEX idx_status ON ksef_wysylka(status);
  CREATE INDEX idx_gid ON ksef_wysylka(gid_erp, rodzaj);
  ```
- `core/ksef/adapters/repo.py` — ShipmentRepository z interfejsem:
  - `has_pending_or_sent(gid, rodzaj) -> bool`
  - `create(...)`, `transition(id, new_status, **meta)`, `get(id)`
- Migration tool (`alembic` analogiczne do serce? Na razie raw SQL w `core/ksef/schema.sql`)

**Acceptance:**
- [ ] Schema tworzona przez `py tools/ksef_init_db.py`
- [ ] Repository pokryte testami (happy + edge: duplikat, transition z niedozwolonego stanu)
- [ ] Wykonanie M0 + zapis DRAFT w tabeli (bez wysyłki jeszcze)

---

### M2 — KSeF API Client (bez auth jeszcze)

**Cel:** Biblioteka klienta REST pokrywająca wszystkie endpointy z §4.4. Testowalna
w izolacji (mocki), ale weryfikowana przeciw Demo.

**Zakres:**
- `core/ksef/adapters/ksef_api.py`:
  - `KSeFApiClient(base_url, http_client)` — httpx/requests pod spodem
  - Metody: `get_challenge()`, `send_xades_auth(signed_xml)`, `redeem_token(auth_ref)`,
    `open_session(...)`, `send_invoice(session_ref, xml_b64)`,
    `get_invoice_status(session_ref, inv_ref)`, `get_upo(...)`, `close_session()`
  - Wszystkie odpowiedzi → typowane dataclasses (`AuthChallenge`, `Session`, `InvoiceStatus`, `Upo`)
  - Retry policy (tenacity): 3x z exp backoff dla 5xx i timeout; 0 retry dla 4xx (błędy biznesowe)
  - Rate limit respect: odczyt `Retry-After` z 429
- Env config: `KSEF_ENV=demo|prod` → base_url; zero hardcode
- Logi: structured (JSON) — endpoint, status, latency, ref_numbers

**Acceptance:**
- [ ] Testy jednostkowe na mockach (happy + 4xx + 5xx + timeout + 429)
- [ ] Smoke test przeciw Demo: pobranie `/auth/challenge` działa
- [ ] Zero logiki biznesowej w kliencie — czysty transport

---

### M3 — KSeF token enrollment + auth flow

**Cel:** Posiadanie długoterminowego tokena KSeF (credential CEiM w Demo) + działający
runtime auth flow daemona przez `/auth/ksef-token`.

**Prerequisite:** Konto CEiM w Demo KSeF (założone przez człowieka w MF).

**Zakres — enrollment (jednorazowo, przez operatora / dedykowany skrypt):**
- `tools/ksef_enroll_cert.py` — interaktywny skrypt prowadzący krok po kroku:
  - E1. `GET /certificates/enrollments/data` → pokaż dane do wniosku
  - E2. `POST /certificates/enrollments` → zapisz `referenceNumber`
  - E3. Polling `/certificates/enrollments/{ref}` aż status = ready
  - E4. `POST /certificates/retrieve` → zapis cert do pliku chronionego
  - E5. `POST /tokens` → wygeneruj KSeF token → zapis do bezpiecznego storage
- Storage sekretów: `.env` lokalny (poza repo), docelowo OS keyring lub vault
- Token ma długi TTL (wg spec — do weryfikacji), rotacja przez tenże skrypt

**Zakres — runtime auth flow:**
- `core/ksef/adapters/ksef_auth.py`:
  - `KSefAuth(token_provider)` — wstrzykiwany provider tokena (read from env/keyring)
  - `authenticate() -> AccessToken`:
    1. `POST /auth/challenge` → `{challenge, timestamp}`
    2. `POST /auth/ksef-token` (body: token + challenge response) → `authRef`
    3. Polling `GET /auth/{authRef}` aż status = finished
    4. `POST /auth/token/redeem` → `access_token` (krótki TTL, ~2h)
  - `ensure_valid() -> access_token` — zwraca aktywny token, refresh przez `/auth/token/refresh` gdy < 5 min do końca
  - Cache tokena w pamięci daemona + snapshot na dysk (restart recovery)

**Acceptance:**
- [ ] Enrollment kończy się otrzymaniem KSeF tokena na Demo
- [ ] Runtime auth: daemon uzyskuje access_token bez udziału operatora
- [ ] Token odświeżany automatycznie przed wygaśnięciem (test: mock clock)
- [ ] Sekrety (KSeF token, cert) nie trafiają do repo — pilnuje `.gitignore` + lint hook

---

### M4 — SendInvoice use case (end-to-end)

**Cel:** Jedno wywołanie `send_invoice(gid, rodzaj)` przechodzi pełny pipeline do UPO.

**Zakres:**
- `core/ksef/usecases/send_invoice.py`:
  ```
  1. repo.has_pending_or_sent(gid, rodzaj) → if yes: skip, log
  2. erp_reader.read(gid, rodzaj) → Faktura
  3. xml_builder.build(faktura) → xml_str
  4. xsd_validator.validate(xml_str) → raise if fail
  5. wysylka = repo.create(status=QUEUED, ...)
  6. auth.ensure_session() → access_token
  7. api.open_session() → session_ref
  8. repo.transition(wysylka, AUTH_PENDING, ksef_session_ref=...)
  9. api.send_invoice(session_ref, base64(xml)) → invoice_ref
  10. repo.transition(wysylka, SENT, ksef_invoice_ref=...)
  11. polling: api.get_invoice_status() aż ACCEPTED/REJECTED (backoff: 2s, 5s, 10s, 30s, 60s...)
  12. if ACCEPTED: api.get_upo() → zapis XML UPO na dysk + repo.transition(ACCEPTED)
  13. if REJECTED: repo.transition(REJECTED, error_...)
  14. api.close_session() (w finally)
  ```
- Obsługa błędów per krok — każdy wyjątek kończy stan `ERROR` z diagnostyką (nie crash)
- CLI: `py tools/ksef_send.py --gid N --rodzaj FS|FSK [--env demo|prod]`
- Smoke test: wysyłka 1 FS i 1 FSK na Demo, otrzymanie UPO

**Acceptance:**
- [ ] End-to-end test na Demo: 2 dokumenty (FS + FSK) przeszły do ACCEPTED z UPO
- [ ] Retry podwójnego uruchomienia = skip z logiem (idempotencja)
- [ ] Błąd w kroku 9 (np. REJECTED przez KSeF) poprawnie zapisany w DB

---

### M5 — Auto-scan daemon

**Cel:** Proces w tle skanuje ERP i wysyła nowe zatwierdzone dokumenty.

**Zakres:**
- `tools/ksef_daemon.py`:
  - Tick co N minut (konfig, default 60s)
  - Zapytanie do ERP: nowo zatwierdzone FS/FSK których GID nie ma w `ksef_wysylka`
  - **Wymóg zewnętrzny:** identyfikacja "co to znaczy zatwierdzona" w ERP XL —
    zadanie dla ERP Specialist (sygnalizuj przez handoff). Prawdopodobnie flaga
    `TrN_Stan`, `TrN_Bufor`, lub podobna. Potrzebny SQL-delta zwracający tylko
    nowe GID-y od ostatniego skanu.
  - Per GID: dispatch do `send_invoice()`; błąd jednego dokumentu nie zatrzymuje kolejnych
  - Graceful shutdown (SIGTERM) — dokończ bieżący dokument, zamknij sesję, zapisz stan
  - Heartbeat: zapis do `ksef_daemon_log` co tick (obserwowalność)
- Deployment: prosty systemd unit lub Windows service wrapper (w zależności od miejsca
  działania — do ustalenia)
- Monitoring: prosty `py tools/ksef_status.py` → podgląd ostatnich N wysyłek, błędów, stanu daemona

**Acceptance:**
- [ ] Daemon wykrywa nowo zatwierdzony dokument w ERP ≤ 60s od zmiany stanu
- [ ] 30 dokumentów w ciągu dnia obsłużone bez dropów (test: symulacja)
- [ ] Restart daemona nie traci stanu — dokumenty w `AUTH_PENDING` wznawiane

---

### M6 — Observability & safety

**Cel:** Operacyjnie bezpieczne, diagnostyczne działanie.

**Zakres:**
- Dashboard CLI: `py tools/ksef_status.py` — tabela: dziś, ostatnie 7 dni, per status
- Flag eskalacja: gdy `ERROR` lub `REJECTED` — `agent_bus flag` do człowieka (natychmiast, nie czekaj na dzienny raport)
- Dry-run mode: `--dry-run` wypisuje co by się wysłało, bez kontaktu z API
- Rate limit guard: nie więcej niż X dokumentów/minutę (ochrona przed bugiem daemona)
- Blokada trybu Prod: `KSEF_ENV=prod` wymaga dodatkowego `KSEF_PROD_CONFIRMED=yes` (zero-przypadkowa wysyłka na Prod)
- Alembic-style migracje DB (gdy schema będzie rosła)

**Acceptance:**
- [ ] Symulowany błąd 5xx KSeF → daemon kontynuuje, flag do człowieka po N porażkach
- [ ] Dry-run nie wykonuje żadnego żądania HTTP (weryfikowane w logach)
- [ ] Przełącznik Demo/Prod bezpieczny (test: próba Prod bez `KSEF_PROD_CONFIRMED` → refuse)

---

## 6. Ryzyka i mitygacje

| Ryzyko | Prawdopodobieństwo | Wpływ | Mitygacja |
|---|---|---|---|
| Brak konta CEiM w Demo KSeF w terminie | Średnie | Blokuje M3+ | Rejestracja w MF po stronie człowieka; równoległa praca M0-M2 niezależna od dostępu |
| Wyciek KSeF tokena (długoterminowy credential) | Niskie | Ktoś wysyła faktury w imieniu CEiM | Token wyłącznie w `.env` poza repo (docelowo keyring); `/tokens/{ref}/revoke` gdy wyciek |
| ERP Specialist nie zidentyfikuje flagi "zatwierdzona" | Średnie | Blokuje M5 | Zlecenie jako pierwszy handoff do ERP Specialist; fallback: poll po nowych GID niezależnie od stanu |
| KSeF Demo API niestabilne / zmiany schematu | Niskie | Opóźnienia | Feature flag per endpoint; kontrakt testy |
| Dual-state ERP ↔ shadow DB | Średnie | Desynchronizacja | Idempotencja po GID; shadow NIGDY nie modyfikuje ERP; manual reconcile tool (M6) |
| Wysłanie duplikatu do KSeF | Niskie (po M1) | Korekta u MF | Sprawdzenie `has_pending_or_sent` przed każdym send; unique constraint (gid, rodzaj) |
| Akcydentalne wysłanie na Prod z Demo danych | Niskie | Realna faktura błędna | Podwójny przełącznik (M6); dev env ma inny cert niż prod |
| Wygaśnięcie tokena w trakcie długiej sesji | Średnie | Faktura nie wysłana | `auth.ensure_session()` sprawdza TTL; auto-refresh |
| XSD zmienia się (nowa wersja KSeF) | Niskie | XML odrzucony | XSD w repo, update per release KSeF; CI test |

---

## 7. Zależności zewnętrzne

| Zależność | Kto dostarcza | Kiedy potrzebne |
|---|---|---|
| Konto CEiM w Demo KSeF (dostęp do enrollmentu cert) | Człowiek (rejestracja w MF) | przed M3 |
| KSeF token CEiM (Demo) | Enrollment przez `tools/ksef_enroll_cert.py` | M3 |
| Identyfikacja flagi "dokument zatwierdzony" w ERP XL | ERP Specialist | przed M5 |
| Schema XSD dla FA(3) | Człowiek (pobranie z gov.pl) | M0 (już mamy?) |
| Zgoda na deployment daemona (miejsce, systemd/usluga) | Człowiek | przed M5 |

---

## 8. ADR-y do wydzielenia

Po akceptacji planu, decyzje binarne wymagają osobnych ADR-ów (przez workflow_adr_design):

1. ~~**ADR-KSEF-001:** Lokalizacja DB~~ — **zdecydowane:** osobny `data/ksef.db` (2026-04-15)
2. ~~**ADR-KSEF-002:** Strategia auth~~ — **zdecydowane:** KSeF token (2026-04-15)
3. **ADR-KSEF-003:** State machine wysyłki — granularność, przejścia, retry policy
4. **ADR-KSEF-004:** Session lifecycle (per-invoice vs sticky warm session z 20-30 dok/dzień)
5. **ADR-KSEF-005:** Storage sekretów — **start:** `.env` + `.gitignore` (2026-04-15). **Docelowo:** ADR po Block 1 (keyring vs vault).

---

## 9. Następne kroki

**Uwaga:** handoffy do innych ról wstrzymane — człowiek chce dostarczyć dodatkowe
informacje przed startem. Plan pozostaje w statusie Draft do ich przekazania.

1. **Review planu** — człowiek akceptuje kierunek lub koryguje scope
2. **Uzupełnienie informacji** — człowiek dostarcza dodatkowe wymagania przed handoffami
3. Po akceptacji: sekwencja handoffów (ERP Specialist → flaga zatwierdzony, Developer → M0)
4. **Research PE (opcjonalnie):** szczegóły enrollmentu cert i generowania tokena KSeF dla Demo — jeśli dokumentacja w `openapiksef.json` okaże się niewystarczająca

---

## 10. Out of scope (świadomie)

- Wysyłanie faktur zakupu (FZ) i korekt zakupu — KSeF 2.0 fakultatywnie, nie priorytet
- Pobieranie faktur zakupowych z KSeF (tryb "odbiorca")
- Integracja z OCR / AI do rozpoznawania dokumentów
- Web UI do podglądu statusu — CLI wystarczy na starcie (M6 dashboard)
- Anulowanie faktury — w KSeF anulowanie = wystawienie korekty, standardowa ścieżka (istniejący `ksef_generate_kor.py` → pipeline)
- Multi-tenant (obsługa wielu firm z jednego daemona) — CEiM = jedna firma
