# Plan: KSeF — kompletna instalacja standalone

**Data:** 2026-05-12
**Status:** DO AKCEPTACJI
**Cel:** `py tools/ksef_install.py --target D:\KSeF` tworzy samodzielny katalog.
Usunięcie plików KSeF z Auto-ERP-Agent nie psuje działania standalone.

---

## Stan obecny

`tools/ksef_install.py` istnieje i kopiuje pliki do docelowego katalogu.
Kod używa `Path(__file__).resolve().parents[N]` — ścieżki rozwiązują się
relatywnie do nowej lokalizacji, więc **mechanizm działa**.

Problem: lista plików jest niekompletna + brak guard na `agent_bus_cli.py`.

---

## Zmiany do wykonania

### 1. Aktualizacja listy plików w `ksef_install.py`

**Dodać:**

| Plik | Rola |
|---|---|
| `solutions/ksef/ksef_fsk_rabat_draft.sql` | SQL korekty rabatowej |
| `core/ksef/adapters/erp_counter.py` | Zliczanie eligible docs (raport) |
| `tools/ksef_generate_rabat.py` | Generowanie XML rabatów |
| `tools/ksef_status.py` | Sprawdzanie statusu wysyłek |
| `tools/ksef_send.py` | Wysyłka pojedyncza/batch |
| `tools/ksef_smoke.py` | Health check (konfiguracja + DB + API) |
| `tools/ksef_init_db.py` | Inicjalizacja/migracja DB |
| `tools/ksef_validate.py` | Walidacja XML vs XSD |
| `tools/ksef_install.py` | Installer (do re-instalacji/update) |
| `ksef_generuj_rabat.bat` | Launcher bat |
| `ksef_generuj_skonto.bat` | Launcher bat (już w liście) |
| `tools/lib/output.py` | Dependency sql_query (już w liście — weryfikacja) |

**Usunąć (pliki nie istnieją):**

| Plik | Powód |
|---|---|
| `tools/ksef_generate_skonto.py` | Plik nie istnieje w repo |
| `solutions/ksef/ksef_fsk_skonto_draft.sql` | Plik nie istnieje w repo |

**Effort:** ~15 min, zmiana w jednym pliku.

### 2. Guard na `agent_bus_cli.py` w daemon i watchdog

Daemon i watchdog wywołują `agent_bus_cli.py flag` do eskalacji.
W standalone `agent_bus_cli.py` nie istnieje.

Istniejący kod jest already best-effort (`try/except`), więc daemon nie crash-uje.
Ale subprocess rzuca `FileNotFoundError` → warning w logu.

**Fix:** Dodać explicit guard na początku `_flag_to_human()`:

```python
# tools/ksef_daemon.py i tools/ksef_watchdog.py
def _flag_to_human(reason: str) -> None:
    if not _AGENT_BUS_CLI.exists():
        _LOG.warning('{"event": "flag_skip", "reason": "agent_bus not available"}')
        return
    # ... reszta bez zmian
```

**Effort:** ~3 linie x 2 pliki.

### 3. Minimalny `.env.example` dla standalone

Obecny `.env` zawiera zmienne dla całego projektu (30+ kluczy).
Standalone potrzebuje ~15 kluczy.

**Akcja:** Stworzyć `ksef.env.example` — kopiowany jako `.env` przy instalacji.
Sekcje:
- `[SQL Server]` — connection string do ERP
- `[KSeF API]` — env, URL, NIP, token, prod confirmed
- `[Daemon]` — interwał, limity, thresholdy
- `[SMTP]` — opcjonalne, do raportów email
- `[Watchdog]` — max restartów, heartbeat timeout

**Effort:** ~20 min.

### 4. Walidacja po instalacji

Dodać do `ksef_install.py` krok weryfikacyjny po kopiowaniu:
- Scan importów w skopiowanych `.py` → sprawdź czy plik docelowy istnieje
- Raport: `OK: 45/45 plików, 0 brakujących importów`

**Effort:** ~30 min.

### 5. Test instalacji

```bash
py tools/ksef_install.py --target tmp/ksef_test
cd tmp/ksef_test
py tools/ksef_smoke.py        # health check
py tools/ksef_status.py       # sprawdzenie DB
```

**Effort:** ~15 min.

---

## Docelowa struktura standalone

```
D:\KSeF\
├── .env                              # Konfiguracja (z ksef.env.example)
├── requirements.txt                  # Zależności pip (generowany)
│
├── ksef_start.bat                    # Master launcher (daemon + watchdog + raport)
├── ksef_service.bat                  # Alias
├── ksef_wyslij_demo.bat              # Demo mode
├── ksef_raport_dzienny.bat           # Raport (Task Scheduler)
├── ksef_ustawienia.bat               # GUI konfiguracji
├── ksef_generuj_fs.bat               # Generuj XML faktury
├── ksef_generuj_kor.bat              # Generuj XML korekty
├── ksef_generuj_rabat.bat            # Generuj XML rabatu
│
├── tools/
│   ├── ksef_start.py                 # Master launcher
│   ├── ksef_daemon.py                # Daemon (scan ERP → send KSeF)
│   ├── ksef_watchdog.py              # Watchdog (auto-restart)
│   ├── ksef_report.py                # Raport email
│   ├── ksef_config_gui.py            # GUI ustawień (tkinter)
│   ├── ksef_generate.py              # Generuj XML FS
│   ├── ksef_generate_kor.py          # Generuj XML FSK
│   ├── ksef_generate_rabat.py        # Generuj XML FSK rabat
│   ├── ksef_send.py                  # Wyślij do KSeF
│   ├── ksef_status.py                # Status wysyłek
│   ├── ksef_smoke.py                 # Health check
│   ├── ksef_validate.py              # Walidacja XML vs XSD
│   ├── ksef_init_db.py               # Init/migracja DB
│   ├── ksef_install.py               # Re-instalacja/update
│   ├── sql_query.py                  # Adapter SQL → ERP
│   └── lib/
│       ├── __init__.py
│       ├── sql_client.py             # Połączenie SQL Server
│       ├── excel_writer.py           # Export xlsx
│       └── output.py                 # JSON output helper
│
├── core/
│   ├── __init__.py
│   └── ksef/
│       ├── __init__.py
│       ├── config.py                 # Ładowanie .env
│       ├── paths.py                  # Ścieżki runtime (ksef_api/<env>/)
│       ├── guards.py                 # Rate limiter + error escalator
│       ├── exceptions.py             # Wyjątki domenowe
│       ├── models.py                 # Modele API
│       ├── schema.sql                # Schemat SQLite
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── shipment.py           # Wysyłka — state machine
│       │   ├── invoice.py            # Model faktury
│       │   ├── correction.py         # Model korekty
│       │   └── events.py             # Eventy
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── repo.py               # ShipmentRepository (SQLite WAL)
│       │   ├── http.py               # HTTP wrapper (httpx + retry)
│       │   ├── ksef_api.py           # KSeF API client
│       │   ├── ksef_auth.py          # Autentykacja
│       │   ├── encryption.py         # RSA + AES
│       │   ├── erp_reader.py         # Odczyt faktur z ERP
│       │   ├── erp_counter.py        # Zliczanie eligible docs
│       │   ├── xml_builder.py        # XML faktur (lxml)
│       │   ├── xsd_validator.py      # Walidacja XML
│       │   ├── email_sender.py       # SMTP
│       │   └── report_renderer.py    # HTML/text raportu
│       └── usecases/
│           ├── __init__.py
│           ├── scan_erp.py           # Skan ERP → pending docs
│           ├── send_invoice.py       # Wyślij fakturę
│           └── report.py             # Dane raportu
│
├── solutions/
│   └── ksef/
│       ├── ksef_fs_draft.sql         # SQL faktura sprzedaży
│       ├── ksef_fsk_draft.sql        # SQL korekta
│       ├── ksef_fsk_rabat_draft.sql  # SQL korekta rabatowa
│       └── ksef_count_eligible.sql   # SQL zliczanie eligible
│
├── output/
│   └── schemat_FA3.xsd               # Schemat XSD faktur
│
├── ksef_api/                          # Runtime (tworzone automatycznie)
│   ├── demo/
│   │   ├── data/ksef.db              # SQLite shadow DB
│   │   └── output/upo/              # UPO z KSeF
│   └── prod/
│       ├── data/ksef.db
│       └── output/upo/
│
└── tmp/                               # Pliki tymczasowe
```

---

## Zależności pip (standalone)

```
pyodbc>=5.0            # SQL Server ERP
python-dotenv>=1.0     # .env
httpx>=0.27            # HTTP client KSeF API
tenacity>=8.2          # Retry backoff
cryptography>=42.0     # RSA/AES (auth KSeF)
lxml>=5.0              # XML
openpyxl>=3.1          # Excel export
```

Stdlib (wbudowane): tkinter, smtplib, sqlite3, json, argparse, logging

---

## Wymagania docelowej maszyny

- Python 3.12+
- SQL Server ODBC Driver 17+
- Sieć: SQL Server ERP, ksef.mf.gov.pl, SMTP (opcjonalnie)
- Windows (Task Scheduler, tkinter)

---

## Effort łączny

| Krok | Czas |
|---|---|
| 1. Aktualizacja listy plików | ~15 min |
| 2. Guard agent_bus | ~5 min |
| 3. ksef.env.example | ~20 min |
| 4. Walidacja po instalacji | ~30 min |
| 5. Test | ~15 min |
| **Razem** | **~1.5h** |

---

## Ryzyka

| Ryzyko | Mitygacja |
|---|---|
| Nowy plik w core/ksef a nie dodany do instalatora | Krok 4: auto-scan importów |
| SQL connection string niekompletny | ksef.env.example z komentarzami |
| Przyszłe zmiany wymagają ręcznej aktualizacji listy | Backlog: test CI kompletności |
