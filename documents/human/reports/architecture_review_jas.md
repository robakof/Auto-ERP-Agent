# Architectural Review: JAS — integracja WZ → spedytor

Date: 2026-03-23
Scope: pełna ocena architektoniczna projektu JAS (nie code review — to osobny dokument)
Ref: `documents/human/reports/code_review_jas_api.md`

---

## Obecna architektura (as-is)

```
[człowiek]
    │ ręcznie
    ▼
jas_export.py (CLI)
    │
    ├─── SqlClient → AILO.wz_jas_export (SQL View w ERP)
    │                      │
    │               ERP tabele: TraNag, KntAdresy, ZamNag, TrNOpisy
    │               WMS tabele: documents, items, LogisticUnitObjects, LogisticUnitTypes
    │
    ├─── jas_mapper.py → rows_to_shipment()
    │
    └─── jas_client.py → JAS REST API (OAuth2)
                              │
                              └─ odpowiedź (JAS shipment ID) → stdout → UTRACONA
```

Wzorzec: **Fire & Forget CLI**. Jeden kierunek, brak stanu, brak pętli zwrotnej.

---

## Ocena architektoniczna

### Co działa dobrze

1. **Separacja warstw** — SQL view / mapper / klient / CLI. Każda warstwa robi jedną rzecz.
2. **SQL view jako kontrakt** — `wz_jas_export` izoluje ERP od Pythona. Zmiana schematu ERP = zmiana widoku, nie kodu Python.
3. **Thin mapper** — `jas_mapper.py` to czysty mapping bez side effects. Testowalny.
4. **Dry-run** — `--dry-run` pozwala walidować payloady bez wysyłania.

---

### Problemy architektoniczne

#### [P1 — CRITICAL] Brak warstwy stanu: system nie wie co wysłał

To nie jest bug w kodzie — to fundamentalny brak w architekturze.

Obecny przepływ:
```
--all → pobierz wszystkie WZ bez FV → wyślij → zapomnij
```

Problem: WZ znika z widoku dopiero gdy dostanie FV. Między wysłaniem do JAS
a wystawieniem FV może minąć kilka dni. W tym czasie każde `--all` wyśle duplikat.

Brakująca warstwa:
```
przed wysłaniem → sprawdź czy wz_id był już wysłany
po wysłaniu    → zapisz: wz_id, jas_id, sent_at, status
```

Bez tej warstwy system nie jest bezpieczny w produkcji.

---

#### [P2 — HIGH] Brak pętli zwrotnej: ERP nie wie że WZ zostało wysłane do JAS

Po wysłaniu JAS zwraca `shipment_id`. Ten ID jest wypisywany na stdout i znika.

Skutki:
- W ERP nie ma informacji "ta WZ trafiła do spedytora pod ID X"
- Handlowiec nie wie czy WZ zostało wysłane
- W razie reklamacji JAS — brak możliwości sprawdzenia ID bez logów konsoli
- Brak możliwości śledzenia statusu przesyłki w przyszłości

---

#### [P3 — HIGH] Ręczny trigger: człowiek musi pamiętać o wysłaniu

System wymaga `python tools/jas_export.py --all` uruchomionego przez człowieka.
Nie ma automatyzacji. Jeśli ktoś zapomni — WZ nie trafi do JAS.

W kontekście projektu (autonomiczna firma) to jest szczególnie nieakceptowalne.
Człowiek nie powinien być wymagany w pętli dla powtarzalnego, deterministycznego procesu.

---

#### [P4 — MEDIUM] SQL view robi za dużo — God View

`wz_jas_export` łączy w jednym obiekcie:
1. Logikę biznesową (filtr WZ bez FV)
2. Parser adresu (CHARINDEX/REVERSE — 35 linii)
3. Mapowanie WMS → typy JAS (CASE)
4. Hardcoded wymiary palet

Skutki:
- Parser adresu jest nietesowalny (nie ma unit testów dla SQL)
- Zmiana mapowania palet = ALTER VIEW = ryzyko regresjii
- Widok jest trudny do utrzymania i debugowania

Parser adresu powinien być w Pythonie (jas_mapper.py) — tam jest jednostkowo testowalny.
Wymiary palet powinny być w tabeli konfiguracyjnej lub Python dict — nie w SQL CASE.

---

#### [P5 — MEDIUM] Brak obsługi błędów API po stronie biznesowej

Gdy JAS odrzuca zlecenie (HTTP 4xx) — błąd jest logowany w `errors[]` i wypisywany.
Nie ma mechanizmu:
- Retry dla błędów przejściowych (5xx, timeout)
- Alertu gdy WZ nie została wysłana
- Przechowywania błędów między sesjami

WZ która nie trafiła do JAS znika z radaru — do następnego `--all` gdzie znów spróbuje
(co jest przypadkowe — tylko dopóki nie ma FV).

---

#### [P6 — LOW] Brak observability

Nie ma centralnego logu operacji JAS. Co zostało wysłane, kiedy, z jakim wynikiem —
dostępne tylko w stdout sesji CLI. Brak możliwości audytu po fakcie.

---

## Docelowa architektura (to-be)

```
[trigger: cron / zdarzenie ERP / CLI]
    │
    ▼
jas_export.py
    │
    ├─── SqlClient → AILO.wz_jas_export
    │
    ├─── AILO.jas_shipments            ← NOWE: check idempotentności
    │         (wz_id, jas_id, sent_at, status, error)
    │
    ├─── jas_mapper.py
    │         └─ adres parser w Python  ← PRZENIESIONE z SQL
    │         └─ pallet dimensions dict ← PRZENIESIONE z SQL
    │
    ├─── jas_client.py → JAS REST API
    │
    └─── po wysłaniu:
              ├─ INSERT AILO.jas_shipments  ← NOWE: zapis stanu
              └─ opcjonalnie: UPDATE ERP (pole/atrybut na WZ)
```

---

## Priorytety zmian

| # | Zmiana | Priorytet | Effort |
|---|--------|-----------|--------|
| 1 | Tabela `AILO.jas_shipments` + idempotentność w `jas_export.py` | CRITICAL | mały |
| 2 | Automatyczny trigger (cron co N minut lub hook na zdarzenie ERP) | HIGH | średni |
| 3 | Parser adresu → Python (`jas_mapper.py`) | MEDIUM | średni |
| 4 | Wymiary palet → Python dict lub tabela konfiguracyjna | MEDIUM | mały |
| 5 | Retry dla błędów 5xx (max 3 próby, backoff) | MEDIUM | mały |
| 6 | Alert / log do agent_bus gdy WZ nie wysłana | LOW | mały |

---

## ADR-0001: Tabela jas_shipments jako warstwa stanu

```
Context:
  System wysyła WZ do JAS bez śledzenia co zostało wysłane.
  Brak idempotentności powoduje ryzyko duplikatów w produkcji.

Decision:
  Tworzymy tabelę AILO.jas_shipments(wz_id, jas_id, sent_at, status, error_msg).
  Przed wysłaniem: SELECT WHERE wz_id AND status='sent' → skip jeśli istnieje.
  Po wysłaniu: INSERT z jas_id i sent_at.

Consequences:
  + System jest idempotentny — --all można uruchamiać wielokrotnie bezpiecznie.
  + Pełny audit trail (kiedy wysłano, jaki JAS ID).
  + Podstawa pod przyszłe śledzenie statusu przesyłki.
  - Wymaga DDL (CREATE TABLE) w schemacie AILO — decyzja do zatwierdzenia przez użytkownika.
  - Tabela może się rozrosnąć — potrzebny cleanup starych rekordów (np. >1 rok).
```

---

## Podsumowanie

Projekt JAS ma solidne fundamenty (separacja warstw, testowalny mapper, dry-run).
Jest funkcjonalny jako MVP na jednorazowe użycie.

**Nie jest bezpieczny jako produkcyjny, autonomiczny system** — brakuje:
1. Stanu (co wysłano)
2. Automacji (człowiek musi pamiętać)
3. Pętli zwrotnej (ERP nie wie co się stało)

Najważniejsza zmiana to P1 (tabela `jas_shipments`) — mały effort, eliminuje największe ryzyko.
P2 (automatyczny trigger) to krok w kierunku autonomii systemu zgodnie z SPIRIT.md.
