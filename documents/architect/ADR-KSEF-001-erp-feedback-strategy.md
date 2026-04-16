# ADR-KSEF-001: Strategia feedbacku stanu KSeF do ERP Comarch XL

**Status:** Accepted
**Data:** 2026-04-16
**Decydent:** Architect (zatwierdzenie przez użytkownika)
**Kontekst:** Plan `documents/human/plans/ksef_api_automation.md` §2 (decyzja "Feedback do ERP: Shadow DB")

---

## Stan środowiska (krytyczne)

| Warstwa | Środowisko | Uwaga |
|---|---|---|
| **Baza ERP Comarch XL** | **Produkcyjna** (prawdziwe dane) | Czytamy realne FS/FSK z `CDN.TraNag` |
| **KSeF API** | **Demo v2** (`ksef-demo.mf.gov.pl`) | NIE produkcyjny KSeF |
| **Token KSeF** | Demo | Token od użytkownika, wyłącznie Demo |

Pipeline łączy się z prawdziwą bazą Comarch XL (realne dokumenty), ale faktury wysyła na KSeF Demo. Przejście na KSeF Prod = osobna decyzja człowieka (zabezpieczone przez Prod guard: `KSEF_PROD_CONFIRMED=yes`).

**Moduł potwierdzenia wysyłki w ERP (feedback do Comarch):** uruchamiamy dopiero po podniesieniu wersji Comarch XL, która wprowadzi natywne pole KSeF. Do tego czasu shadow DB = jedyne źródło prawdy.

---

## Kontekst

Pipeline KSeF (Block 1-7, M0-M6) wysyła faktury FS/FSK z ERP Comarch XL do KSeF API. Kluczowe pytanie architektoniczne z fazy planowania: **gdzie trzymać informację o wysłaniu dokumentu do KSeF?**

Rozważano trzy warianty:

| Wariant | Opis | Ocena |
|---|---|---|
| A. Własna kolumna w `CDN.TraNag` | Dodać `TrN_KsefStatus`, `TrN_KsefNumer`, `TrN_UpoData` do tabeli Comarch | Ingerencja w schemat ERP — dług techniczny, konflikt z przyszłym update'em Comarch |
| B. Osobna tabela w DB Comarch | `CDN.KSeFWysylki` jako extension tabela XL | Nadal ingerencja w DB Comarch, ryzyko po update |
| C. Shadow DB (nasza SQLite `data/ksef.db`) | Audit trail poza Comarch, jedyne źródło prawdy o stanie KSeF | Zero modyfikacji ERP, pełna kontrola schematu |

W planie startowym (2026-04-15) wybrano **Wariant C** z uzasadnieniem: "Zero modyfikacji ERP XL. Wszystko co wiemy o wysyłce — w naszej DB."

## Nowa informacja (2026-04-16)

**Comarch XL wyda update**, który wprowadzi **standardowe pole Comarch** do oznaczania statusu wysyłki KSeF. Dokładna lokalizacja (kolumna w `TraNag` vs osobna tabela KSeF Comarch) oraz schemat — do ustalenia po opublikowaniu wersji.

## Decyzja

**Nie tworzymy własnej kolumny ani tabeli w DB Comarch. Czekamy na update Comarch XL.**

Do czasu udostępnienia pola przez Comarch:
- **Shadow DB (`data/ksef.db`)** pełni rolę **jedynego źródła prawdy** o stanie wysyłek KSeF
- **Scan ERP** (`core/ksef/usecases/scan_erp.py`) filtruje dokumenty do wysłania przez `TrN_Bufor=0` (zatwierdzone) + Python-side check vs shadow DB (`get_latest() is not None`)
- **Feedback do operatora ERP** odbywa się wyłącznie przez dashboard `tools/ksef_status.py --summary` (nie przez widok/okno w Comarch)

Po udostępnieniu pola Comarch:
- Migracja scan SQL: dodać `AND <kolumna_comarch> IS NULL` (skan tylko niewysłanych) — oszczędza Python-side filter
- Shadow DB **pozostaje** jako trwały audit trail (próby, attempt count, error codes, UPO paths, timestamps) — redundancja na poziomie kontrolnym
- Zapis do pola Comarch: **świadomie NIE robimy** dopóki nie dostaniemy oficjalnego API/procedury zapisu od Comarch (ryzyko konfliktu z ich wewnętrzną logiką, lockami, trigerami)

## Uzasadnienie

### Dlaczego NIE własna kolumna

1. **Konflikt z update Comarch** — nasza `TrN_KsefStatus` zderzy się z oficjalną kolumną Comarch pod tą samą (lub podobną) nazwą. Migracja danych + konflikt schema = niepotrzebny ból.
2. **ALTER TABLE w produkcyjnym ERP** — wymaga współpracy administratora, testów regresji, backupów. Comarch może nie wspierać konfiguracji z naszymi modyfikacjami (support issue).
3. **Duplikacja funkcjonalności** — gdy Comarch udostępni pole, musielibyśmy je synchronizować z naszą kolumną. Dwa źródła prawdy = drift.

### Dlaczego Shadow DB wystarcza

1. **Audit trail lepszy niż pole w TraNag** — shadow DB trzyma pełną historię prób, stany pośrednie (`DRAFT → QUEUED → AUTH_PENDING → SENT → ACCEPTED`), UPO paths, error codes. Single column w `TraNag` może co najwyżej trzymać końcowy status.
2. **Niezależność od Comarch** — update/patch Comarch nie wpływa na nasz shadow DB. Pipeline działa dalej po każdym patchu ERP.
3. **Dashboard wystarcza operatorowi** — `ksef_status.py --summary` daje dzienny/tygodniowy obraz; nie trzeba klikać w kolumnę w oknie Comarch.

### Dlaczego NIE zapisujemy do pola Comarch (po update)

1. **Brak specyfikacji API** — dopóki Comarch nie opisze jak zapisać do pola (bezpośredni UPDATE vs stored proc vs API), improwizacja = ryzyko psucia logiki biznesowej ERP.
2. **Single writer** — pole Comarch jest "ich"; my je tylko **czytamy** do optymalizacji scan. Zapisuje Comarch (gdy ich UI/integracja wyśle dokument) albo my w przyszłości, jawnie zdecydowanym kanałem.

## Konsekwencje

### Gains
- Zero modyfikacji schematu Comarch XL (teraz i po update)
- Shadow DB jako pełny audit trail (bogatsze dane niż single column)
- Pipeline odporny na update Comarch
- Jasna granica: Comarch = ERP, nasz kod = integracja + audit

### Costs
- Operator musi nauczyć się dashboard CLI (`ksef_status.py --summary`) zamiast patrzeć w okno Comarch
- Python-side filter `_is_known` w `scan_erp.py` robi N+1 lookups (1 scan query + 1 lookup per doc w shadow DB) — OK dla 20-30 dok/dzień, nie dla 1000/dzień
- Przy imporcie historycznych wysyłek (backfill) musimy ręcznie zasilić shadow DB (wariant kolumny byłby tu prostszy)

### Risks
- **Comarch nie wyda update lub opóźni** — ryzyko akceptowalne; shadow DB i tak wystarcza
- **Comarch zmieni semantykę pola** — mitigation: scan SQL wydzielony do stałej, łatwy update
- **Operator chce feedback w oknie Comarch** — mitigation: można w przyszłości dodać SQL view join shadow DB z TraNag (tylko read, bez ingerencji)

## Migration Path — po update Comarch

Gdy Comarch udostępni pole:

1. **ERP Specialist** identyfikuje: nazwę kolumny/tabeli, typ pola, semantykę wartości (NULL vs "wysłane" vs "accepted"), dokumentację oficjalną
2. **Architect** weryfikuje: czy jest sens wpiąć (ew. zostawić status quo jeśli pole trywialne)
3. **Developer** aktualizuje:
   - `scan_erp.py`: dodaj `AND <kolumna> IS NULL` (lub odpowiedni warunek) do SQL
   - Zachowaj `_is_known()` via shadow DB jako redundancja (defense in depth)
   - Dodaj test regresji: scan pomija doc z wypełnionym polem Comarch
4. **Ten ADR** — aktualizacja sekcji "Status" na rozszerzoną, link do ADR następcy jeśli zakres się zmienia

Trigger migracji: **ERP Specialist zgłasza w `agent_bus` fakt dostępności pola po update Comarch** (handoff do Architect).

## Decyzje powiązane

- `documents/human/plans/ksef_api_automation.md` §2 — oryginalna decyzja "Feedback do ERP: Shadow DB"
- Block 2 (M1) — schemat `core/ksef/adapters/repo.py::ksef_wysylka` (shadow DB tabela)
- Block 6 (M5) — `core/ksef/usecases/scan_erp.py` (filter `TrN_Bufor=0` + `_is_known`)
- Block 7 (M6) — `tools/ksef_status.py --summary` (dashboard operatora)

## Status przyszłych rewizji

ADR jest **Accepted** w obecnej formie. Należy zrewidować (zmiana statusu na **Superseded** z linkiem do następcy lub rozszerzenie sekcji "Migration Path") gdy:
- Comarch ogłosi wersję z polem KSeF i ERP Specialist przekaże szczegóły
- Zmieni się skala ruchu (>200 dok/dzień) czyniąca Python-side filter problematycznym
- Operator zgłosi potrzebę feedbacku wewnątrz okna Comarch (wtedy: SQL view read-only, nie modyfikacja TraNag)
