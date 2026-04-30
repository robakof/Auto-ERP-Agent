# Architektura: KSeF daemon — raportowanie + interface

**Data:** 2026-04-22
**Autor:** Architect
**Status:** Approved

---

## Problem

User nie chce wchodzić w Comarch XL żeby sprawdzić stan faktur.
Potrzebuje automatycznych raportów mailowych: ile wysłano, ile błędów, co czeka.
Daemon działa w tle — user potrzebuje widoczności bez logowania do systemu.

**Reguła biznesowa: wszystkie FV muszą być wysłane tego samego dnia.**
End-of-day report to gate weryfikacyjny — nie tylko informacja.

---

## Istniejąca infrastruktura

| Zasób | Co daje |
|---|---|
| `ksef.db` → `ksef_wysylka` | Pełna historia: status, timestamps, GID, nr_faktury, ksef_number, error_msg |
| `ksef_transition` | Audit log zmian statusów (state machine) |
| `repo.count_by_status(since)` | Gotowe aggregation per status z filtrem czasowym |
| `repo.list_by_status(status)` | Lista wysyłek per status |
| `repo.list_recent(limit)` | Ostatnie N wysyłek |
| `data/ksef_heartbeat.json` | Zdrowie daemon: tick_count, last_tick, PID |
| Watchdog log: `data/ksef_watchdog.log` | Restarty, crashe |

**Wniosek:** Źródło danych jest kompletne. Wystarczy warstwa aggregacji + delivery.

---

## Architektura

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│ ksef_daemon  │────>│  ksef.db          │<────│ ksef_report  │
│ (wysyłki)    │     │  (shadow DB)      │     │ (aggregacja) │
└─────────────┘     └──────────────────┘     └──────┬───────┘
                                                     │
                                              ┌──────▼───────┐
                                              │ email_sender  │
                                              │ (SMTP)        │
                                              └──────┬───────┘
                                                     │
                                               biuro@ceim.pl
```

### 3 nowe moduły (separation of concerns)

**M1. Report Aggregator** — `core/ksef/usecases/report.py`
- Pure logic, zero I/O (poza DB read)
- Input: `ShipmentRepository` + zakres dat
- Output: `ReportData` (dataclass) — counts, lista błędów, lista niewysłanych, statystyki
- Pole `all_sent_today: bool` — gate weryfikacyjny (FV z dzisiaj: wszystkie ACCEPTED?)
- Reużywalny: email, CLI, przyszły dashboard — ten sam aggregator

**M2. Email Sender** — `core/ksef/adapters/email_sender.py`
- Adapter: SMTP via nazwa.pl (`smtplib` + `email.mime` — stdlib)
- Config z `.env`: `KSEF_SMTP_HOST`, `KSEF_SMTP_PORT`, itd.
- HTML body budowane funkcją Python (f-strings + loops) — zero deps templateowych
- Multipart: HTML + plain text fallback

**M3. Report CLI** — `tools/ksef_report.py`
- CLI entry point: `py tools/ksef_report.py --send-email`
- Tryby: `--send-email` (email), `--stdout` (terminal), `--file raport.md` (do pliku)
- Filtr: `--since today` (domyślne), `--since 24h`, `--since 7d`
- Schedulowany przez Windows Task Scheduler — **zero zależności od daemon**

---

## Decyzje architektoniczne

### D1. Report oddzielony od daemon (nie wbudowany w tick loop)

**Zyskujemy:**
- Daemon robi jedno: wysyła faktury. Single Responsibility.
- Raport może działać nawet gdy daemon jest wyłączony (czyta z DB).
- Różne schedule: daemon co 15 min, raport raz dziennie.
- Łatwiejszy test (raport testujemy osobno, bez mocków daemon).

**Tracimy:**
- Dodatkowy proces/schedule do skonfigurowania.

**Verdict:** Oddzielony. Koszt minimalny, korzyści duże.

### D2. SMTP stdlib via nazwa.pl

**Zyskujemy:**
- Zero nowych zależności (smtplib w stdlib).
- Pełna kontrola, zero vendor lock-in.

**Tracimy:**
- Brak delivery tracking.

**Verdict:** SMTP stdlib. Raport wewnętrzny, nie marketing.

### D3. HTML budowane Pythonem (nie template engine)

`string.Template` nie obsługuje pętli — raport ma zmienną listę błędów.
Jinja2 to overkill na jeden raport. Funkcja Python z f-strings + loop
jest prostsze, testowalne, zero deps.

### D4. Config w `.env` (rozszerzenie istniejącego wzorca)

Istniejące: `KSEF_ENV`, `KSEF_BASE_URL`, `KSEF_NIP`, `KSEF_TOKEN`.
Nowe:

```env
# --- SMTP (nazwa.pl) ---
KSEF_SMTP_HOST=smtp.nazwa.pl
KSEF_SMTP_PORT=465
KSEF_SMTP_USER=raporty@ceim.pl
KSEF_SMTP_PASS=...
KSEF_SMTP_SSL=true
KSEF_REPORT_TO=biuro@ceim.pl
KSEF_REPORT_FROM=raporty@ceim.pl
KSEF_REPORT_SUBJECT_PREFIX=[KSeF]
```

### D5. Dwa typy raportów

| Typ | Kiedy | Treść | Severity |
|---|---|---|---|
| **End-of-day** | Koniec dnia (np. 17:00) | Podsumowanie: ile wysłano, błędy, **czy wszystkie FV wysłane** | CRITICAL jeśli `all_sent_today=false` |
| **Error alert** | Po tick z błędami (opcjonalne, faza 2) | Lista błędów z ostatniego tick | WARNING |

**Faza 1:** End-of-day (wystarczy do pokrycia wymagania).
**Faza 2 (opcjonalna):** Instant error alert (hook w daemon on_tick callback).

---

## Zawartość raportu end-of-day (mockup)

```
Temat: [KSeF] Raport dzienny 2026-04-22 — ✓ wszystkie wysłane

════════════════════════════════════════
  KSeF — podsumowanie dnia 2026-04-22
════════════════════════════════════════

  Status dnia: ✓ WSZYSTKIE FAKTURY WYSŁANE
  (lub: ✗ UWAGA: 3 faktury niewysłane!)

  Stan daemon: aktywny (tick #142, PID 5834)
  Ostatni tick: 17:00:02

  ── Wysyłki dnia ─────────────────────
  Zaakceptowane (ACCEPTED):    12
  Wysłane (SENT):               0
  Oczekujące (QUEUED):          0
  Błędy (ERROR):                0
  Odrzucone (REJECTED):         0
  ─────────────────────────────────────
  Razem:                       12

  ── Watchdog ─────────────────────────
  Restarty dziś: 0

════════════════════════════════════════
  Wygenerowano: 2026-04-22 17:00:05
```

**Wariant z błędami:**

```
Temat: [KSeF] Raport dzienny 2026-04-22 — ✗ 3 błędy!

  Status dnia: ✗ UWAGA: 3 faktury z błędami

  ── Błędy (3) ────────────────────────
  #28  FS-201/04/26  GID=145  SchemaValidationError: P_9A
  #29  FS-202/04/26  GID=146  AuthTimeout after 120s
  #30  FSK-5/04/26   GID=89   ConnectionError: KSeF API

  ── Niewysłane faktury ───────────────
  (lista FV z data_wystawienia=dzisiaj które nie mają statusu ACCEPTED)
```

---

## Plan implementacji (Developer)

| # | Deliverable | Pliki | Effort |
|---|---|---|---|
| 1 | `ReportData` dataclass + `build_report()` usecase | `core/ksef/usecases/report.py` | S |
| 2 | Testy aggregatora (mock repo, edge cases) | `tests/ksef/test_report.py` | S |
| 3 | HTML builder (funkcja Python, zero deps) | `core/ksef/adapters/report_renderer.py` | S |
| 4 | Email sender adapter (SMTP multipart via nazwa.pl) | `core/ksef/adapters/email_sender.py` | M |
| 5 | Config rozszerzenie (SMTP vars) | `core/ksef/config.py` | S |
| 6 | CLI `ksef_report.py` (--send-email, --stdout, --file) | `tools/ksef_report.py` | M |
| 7 | Testy email sender (mock SMTP) + renderer | `tests/ksef/test_email_sender.py` | S |
| 8 | `.env.example` update | `.env.example` | XS |
| 9 | Windows Task Scheduler bat (13:30) | `ksef_raport_dzienny.bat` | XS |

**Kolejność:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

**Config SMTP:** Gotowe w `.env` — Developer nie musi konfigurować, tylko ładować przez `load_config()`.

---

## Parametry ustalone

- **Godzina raportu:** 13:30 (Task Scheduler)
- **SMTP:** server617240.nazwa.pl:465 SSL, raporty@ceim.pl
- **Odbiorca:** biuro@ceim.pl
- **Trigger:** Windows Task Scheduler — zero logiki scheduleowej w aplikacji
- **Template:** Python f-strings (zero deps)
- **Config:** `.env` (gotowe, sekcja KSEF_SMTP_*)
