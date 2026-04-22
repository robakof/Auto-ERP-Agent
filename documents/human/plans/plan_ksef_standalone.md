# KSeF — mapa plików i instalacja standalone

**Data:** 2026-04-22

---

## Mapa plików

```
ksef_standalone/
│
├── .env                          # Konfiguracja (hasla, tokeny, SMTP)
│
├── ksef_wyslij_demo.bat          # Launcher: daemon + watchdog
├── ksef_raport_dzienny.bat       # Launcher: raport email (Task Scheduler 13:30)
├── ksef_ustawienia.bat           # Launcher: GUI ustawien
│
├── tools/
│   ├── ksef_daemon.py            # Daemon — skanuje ERP, wysyla FV do KSeF
│   ├── ksef_watchdog.py          # Watchdog — pilnuje daemon, auto-restart
│   ├── ksef_report.py            # Raport — generuje + wysyla email
│   ├── ksef_config_gui.py        # GUI — okienko ustawien (tkinter)
│   ├── sql_query.py              # Adapter SQL → ERP (pyodbc)
│   └── lib/
│       ├── sql_client.py         # Polaczenie z SQL Server
│       └── excel_writer.py       # Export do xlsx (zaleznosc sql_query)
│
├── core/
│   └── ksef/
│       ├── __init__.py
│       ├── config.py             # Ladowanie .env (KSeF + SMTP config)
│       ├── guards.py             # Rate limiter + error escalator
│       ├── exceptions.py         # Wyjatki domenowe
│       ├── models.py             # Modele wspolne
│       ├── schema.sql            # Schemat SQLite (ksef.db)
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── shipment.py       # Wysylka — state machine
│       │   ├── invoice.py        # Model faktury
│       │   ├── correction.py     # Model korekty
│       │   └── events.py         # Eventy domenowe
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── repo.py           # ShipmentRepository (SQLite)
│       │   ├── http.py           # HTTP wrapper (httpx + retry)
│       │   ├── ksef_api.py       # KSeF API client
│       │   ├── ksef_auth.py      # Autentykacja KSeF
│       │   ├── encryption.py     # Szyfrowanie (RSA + AES)
│       │   ├── erp_reader.py     # Odczyt faktur z ERP (SQL)
│       │   ├── xml_builder.py    # Budowanie XML faktur (lxml)
│       │   ├── xsd_validator.py  # Walidacja XML vs XSD
│       │   ├── email_sender.py   # SMTP sender
│       │   └── report_renderer.py# HTML/text raportu
│       └── usecases/
│           ├── __init__.py
│           ├── scan_erp.py       # Skan ERP → pending docs
│           ├── send_invoice.py   # Wyslij fakture do KSeF
│           └── report.py         # Aggregacja danych raportu
│
├── data/                         # Dane runtime (tworzone automatycznie)
│   ├── ksef.db                   # Baza SQLite (historia wysylek)
│   ├── ksef_heartbeat.json       # Heartbeat daemon
│   └── ksef_watchdog.log         # Log watchdog
│
├── output/                       # XML wygenerowane (tworzone automatycznie)
│   └── ksef/
│       └── upo/                  # UPO z KSeF
│
├── tmp/                          # Pliki tymczasowe
│
└── output/schemat_FA3.xsd        # Schemat XSD faktur (walidacja)
```

## Zaleznosci pip (tylko potrzebne dla KSeF)

```
pyodbc>=5.0            # Polaczenie z SQL Server ERP
python-dotenv>=1.0     # Ladowanie .env
httpx>=0.27            # HTTP client do KSeF API
tenacity>=8.2          # Retry z exponential backoff
cryptography>=42.0     # Szyfrowanie RSA/AES (autentykacja KSeF)
lxml>=5.0              # Budowanie XML faktur
openpyxl>=3.1          # Export xlsx (zaleznosc sql_query)
```

Stdlib (nie trzeba instalowac): tkinter, smtplib, sqlite3, json, argparse

## Wymagania serwera

- Python 3.12+
- SQL Server ODBC Driver 17+ (do polaczenia z ERP Comarch XL)
- Dostep sieciowy do: SQL Server ERP, api-demo.ksef.mf.gov.pl, SMTP nazwa.pl
- Windows (tkinter GUI, Task Scheduler)
