# KSeF — Instrukcja operacyjna

Dokument opisuje architekture, codzienne uzytkowanie i wdrozenie produkcyjne
systemu integracji z Krajowym Systemem e-Faktur (KSeF).

---

## 1. Architektura

### 1.1 Struktura katalogow

```
Auto-ERP-Agent/
  core/ksef/                  # Biblioteka Python (logika biznesowa)
    adapters/                 #   erp_reader, xml_builder, ksef_api, repo, ...
    domain/                   #   shipment, invoice, correction, events
    usecases/                 #   scan_erp, send_invoice, report
    config.py                 #   Konfiguracja z .env (KSefConfig, SmtpConfig)
    paths.py                  #   Resolver sciezek per srodowisko (demo/prod)
    guards.py                 #   RateLimiter, ErrorEscalator
    models.py, exceptions.py

  tools/                      # Narzedzia CLI (cienkie wrappery nad core/)
    ksef_generate.py           #   Generowanie XML z faktur FS
    ksef_generate_kor.py       #   Generowanie XML z korekt FSK
    ksef_generate_skonto.py    #   Generowanie XML z korekt skontowych
    ksef_send.py               #   Reczna wysylka XML na KSeF
    ksef_daemon.py             #   Automat: scan ERP -> generate -> send (petla)
    ksef_watchdog.py           #   Monitor daemona (auto-restart, heartbeat)
    ksef_status.py             #   Podglad stanu wysylek (readonly)
    ksef_report.py             #   Raport dzienny + email SMTP
    ksef_init_db.py            #   Tworzenie/sprawdzanie shadow DB
    ksef_validate.py           #   Walidacja XML vs schemat XSD
    ksef_smoke.py              #   Smoke test lacznosci z API KSeF
    ksef_config_gui.py         #   GUI ustawien (.env) — tkinter
    ksef_install.py            #   Instalator standalone (kopiowanie + deps)

  ksef_api/                   # Dane runtime — oddzielone per srodowisko
    demo/
      data/                   #   ksef.db, ksef_daemon.log, ksef_watchdog.log,
                              #   ksef_heartbeat.json
      output/                 #   Wygenerowane XML faktur
        upo/                  #   Pobrane UPO (potwierdzenia z KSeF)
    prod/
      data/                   #   (puste do momentu wdrozenia)
      output/
        upo/

  tests/ksef/                 # Testy jednostkowe (241 testow)
  tests/integration/          # Test integracyjny (smoke na demo API)

  *.bat                       # Skroty Windows (dwuklik)
```

### 1.2 Przeplyw danych

```
ERP XL (SQL Server)
    |
    | SQL query (erp_reader.py)
    v
Faktura/Korekta (domain objects)
    |
    | xml_builder.py
    v
XML FA(3) plik
    |
    | ksef_send.py / daemon
    | (encrypt -> session -> send -> poll -> UPO)
    v
KSeF API (demo lub prod)
    |
    | status tracking
    v
Shadow DB (ksef.db) — lokalna kopia stanu wysylek
```

### 1.3 Srodowiska

Przelaczanie srodowiska odbywa sie przez zmienna `KSEF_ENV` w pliku `.env`.
Sciezki do danych (DB, output, logi) automatycznie wskazuja na `ksef_api/<env>/`.

| Srodowisko | KSEF_ENV | URL API | Opis |
|---|---|---|---|
| Demo | `demo` | `https://api-demo.ksef.mf.gov.pl/v2` | Testowe, brak konsekwencji |
| Produkcja | `prod` | `https://api.ksef.mf.gov.pl/v2` | Prawdziwe faktury (!) |
| Test | `test` | dowolne | Do testow jednostkowych |

**Bezpiecznik produkcyjny:** `KSEF_ENV=prod` wymaga dodatkowego `KSEF_PROD_CONFIRMED=yes`.
Bez tego daemon odmowi startu.

---

## 2. Konfiguracja

### 2.1 GUI ustawien

Najlatwiejszy sposob: dwuklik `ksef_ustawienia.bat` (lub `py tools/ksef_config_gui.py`).

Otwiera okno z zakladkami:
- **KSeF API** — srodowisko (demo/prod), URL, NIP, token
- **SMTP** — serwer, port, login, haslo, SSL
- **Raport** — nadawca, odbiorca, prefix tematu
- **Daemon** — interval ticka, timeout, rate limit, prog bledow
- **Watchdog** — max restartow/h, stale heartbeat

Pola z tokenem i haslem sa maskowane (gwiazdki).
Zapis nadpisuje `.env` zachowujac komentarze i kolejnosc.

### 2.2 Plik .env (reczna edycja)

Wszystkie ustawienia KSeF sa w `.env` w glownym katalogu projektu.
GUI edytuje ten sam plik — mozna tez edytowac reczne.

```ini
# Srodowisko
KSEF_ENV=demo
KSEF_BASE_URL=https://api-demo.ksef.mf.gov.pl/v2
KSEF_TOKEN=<token autoryzacyjny z portalu KSeF>
KSEF_NIP=7871003063

# Produkcja (odkomentuj po wdrozeniu)
# KSEF_PROD_CONFIRMED=yes

# SMTP — raporty dzienne
KSEF_SMTP_HOST=<host>
KSEF_SMTP_PORT=465
KSEF_SMTP_USER=<user>
KSEF_SMTP_PASS=<pass>
KSEF_SMTP_SSL=true
KSEF_REPORT_FROM=<nadawca>
KSEF_REPORT_TO=<odbiorca>
KSEF_REPORT_SUBJECT_PREFIX=[KSeF]

# Daemon
KSEF_DAEMON_INTERVAL=900
KSEF_DAEMON_TICK_TIMEOUT=300
```

### 2.3 Skad wziac token

1. Wejdz na portal KSeF: https://ksef.mf.gov.pl (prod) lub https://ksef-demo.mf.gov.pl (demo)
2. Zaloguj sie profilem zaufanym / certyfikatem
3. Wygeneruj token autoryzacyjny (typ: sesja batch)
4. Wklej do `.env` jako `KSEF_TOKEN=...`

---

## 3. Codzienne uzytkowanie

### 3.1 Skroty Windows (*.bat)

Dwuklik z Eksploratora:

| Plik | Co robi |
|---|---|
| `ksef_generuj_fs.bat` | Generuje XML z faktur (FS) za dzisiejszy dzien |
| `ksef_generuj_kor.bat` | Generuje XML z korekt (FSK) za dzisiejszy dzien |
| `ksef_generuj_skonto.bat` | Generuje XML z korekt skontowych za dzisiejszy dzien |
| `ksef_wyslij_demo.bat` | Uruchamia daemon+watchdog (demo) — auto wysylka |
| `ksef_raport_dzienny.bat` | Wysyla raport email lub wyswietla w terminalu |
| `ksef_ustawienia.bat` | Otwiera GUI ustawien (.env) |
| `test_ksef.bat` | Uruchamia testy automatyczne |

Wszystkie generatory otwieraja dialog wyboru folderu wyjsciowego.
Mozna tez podac date jako argument: `ksef_generuj_fs.bat 2026-04-01`

### 3.2 Flow reczny (produkcja)

```bash
# 1. Generuj XML z faktur za dzis
py tools/ksef_generate.py --date-from 2026-04-24

# 2. Generuj XML z korekt za dzis
py tools/ksef_generate_kor.py --date-from 2026-04-24

# 3. Generuj XML z korekt skontowych za dzis
py tools/ksef_generate_skonto.py --date-from 2026-04-24

# 4. Wyslij na KSeF
py tools/ksef_send.py ksef_api/demo/output/ksef_FS-*.xml

# 5. Sprawdz status
py tools/ksef_status.py --today
```

Opcje generatorow:
- `--gid 59 60` — konkretne GID faktury (zamiast daty)
- `--validate output/schemat_FA3.xsd` — walidacja XML vs XSD
- `--dry-run` — pokaz SQL bez generowania
- `--output-dir sciezka` — inny folder wyjsciowy

### 3.3 Flow automatyczny (daemon)

```bash
# Jednorazowy scan + wysylka
py tools/ksef_daemon.py --once

# Jednorazowy podglad (bez wysylki)
py tools/ksef_daemon.py --once --dry-run

# Ciagly daemon (tick co 15 min)
py tools/ksef_daemon.py

# Z watchdogiem (rekomendowane na produkcji)
py tools/ksef_watchdog.py --interval 300
```

Daemon automatycznie:
1. Skanuje ERP XL szukajac nowych faktur (TrN_Bufor=0, brak w shadow DB)
2. Generuje XML
3. Wysyla na KSeF (encrypt -> session -> send -> poll)
4. Zapisuje status + numer KSeF w shadow DB
5. Pobiera UPO (potwierdzenie)

### 3.4 Monitoring

```bash
# Podsumowanie (dzis, 7 dni, total)
py tools/ksef_status.py --summary

# Dzisiejsze wysylki
py tools/ksef_status.py --today

# Tylko bledy
py tools/ksef_status.py --status ERROR
py tools/ksef_status.py --status REJECTED

# Konkretna faktura
py tools/ksef_status.py --gid 123456

# Raport dzienny (terminal)
py tools/ksef_report.py --stdout

# Raport za 7 dni
py tools/ksef_report.py --since 7d --stdout
```

### 3.5 Diagnostyka

```bash
# Smoke test — czy API odpowiada
py tools/ksef_smoke.py

# Walidacja XML vs schemat XSD
py tools/ksef_validate.py output/schemat_FA3.xsd ksef_api/demo/output/*.xml

# Testy automatyczne
py -m pytest tests/ksef/ -v
```

---

## 4. Shadow DB (ksef.db)

Lokalna baza SQLite sledzaca stan kazdej wysylki. Lokalizacja: `ksef_api/<env>/data/ksef.db`.

### Tabela `ksef_wysylka`

| Kolumna | Opis |
|---|---|
| id | ID wysylki (auto) |
| gid_erp | GID faktury w ERP XL |
| rodzaj | FS / FSK / FSK_SKONTO |
| nr_faktury | Numer faktury (np. FS-59/04/26/SPKR) |
| data_wystawienia | Data wystawienia |
| xml_path | Sciezka do pliku XML |
| xml_hash | SHA-256 XML (deduplikacja) |
| status | DRAFT / QUEUED / SENT / ACCEPTED / REJECTED / ERROR |
| ksef_number | Numer KSeF (po akceptacji) |
| upo_path | Sciezka do UPO |
| error_msg | Komunikat bledu |
| attempt | Numer proby |

### Statusy

```
DRAFT -> QUEUED -> SENT -> ACCEPTED (sukces)
                       \-> REJECTED (KSeF odrzucil)
                       \-> ERROR (blad techniczny)
```

### Przegladanie DB

Najlatwiej: DB Browser for SQLite otwiera `ksef_api/demo/data/ksef.db`.

```sql
-- Ostatnie wysylki
SELECT id, nr_faktury, status, ksef_number, error_msg
FROM ksef_wysylka ORDER BY id DESC LIMIT 20;

-- Bledy i odrzucenia
SELECT * FROM ksef_wysylka WHERE status IN ('ERROR', 'REJECTED');
```

---

## 5. Wdrozenie produkcyjne

### 5.1 Checklist

Szczegolowy checklist: `documents/human/plans/ksef_deploy_prod_checklist.md`

Skrot:

1. **Token produkcyjny** — wygeneruj na https://ksef.mf.gov.pl
2. **Zmien .env:**
   ```ini
   KSEF_ENV=prod
   KSEF_BASE_URL=https://api.ksef.mf.gov.pl/v2
   KSEF_TOKEN=<token produkcyjny>
   KSEF_PROD_CONFIRMED=yes
   ```
3. **Inicjalizuj DB produkcyjna:**
   ```bash
   py tools/ksef_init_db.py
   ```
   (automatycznie utworzy `ksef_api/prod/data/ksef.db`)
4. **Test jednej faktury:**
   ```bash
   py tools/ksef_daemon.py --once --dry-run    # podglad
   py tools/ksef_daemon.py --once --rate-limit 1  # wysylka 1 faktury
   py tools/ksef_status.py --today             # weryfikacja
   ```
5. **Pelny start:** daemon z watchdogiem lub Task Scheduler

### 5.2 Rollback do demo

```ini
KSEF_ENV=demo
KSEF_BASE_URL=https://api-demo.ksef.mf.gov.pl/v2
KSEF_TOKEN=<token demo>
# Usun KSEF_PROD_CONFIRMED
```

---

## 6. Troubleshooting

| Problem | Przyczyna | Rozwiazanie |
|---|---|---|
| "KSEF_ENV must be one of..." | Brak lub zla wartosc KSEF_ENV w .env | Ustaw KSEF_ENV=demo lub prod |
| "KSEF_PROD_CONFIRMED=yes required" | Proba uruchomienia prod bez potwierdzenia | Dodaj KSEF_PROD_CONFIRMED=yes do .env |
| Daemon: 5 restartow/h, zatrzymany | Watchdog zablokowal (cos crashuje) | Sprawdz ksef_api/<env>/data/ksef_watchdog.log |
| REJECTED: "Duplikat faktury" | Faktura juz wyslana wczesniej | Sprawdz ksef_status --gid <GID> |
| ERROR przy wysylce | Blad API / siec / token wygasl | Sprawdz ksef_daemon.log, ksef_smoke.py |
| Brak faktur do wyslania | Faktury sa w buforze (TrN_Bufor!=0) | Zatwierdz faktury w ERP XL |

### Logi

| Plik | Lokalizacja | Co zawiera |
|---|---|---|
| Daemon log | `ksef_api/<env>/data/ksef_daemon.log` | Kazdy tick, wysylka, blad |
| Watchdog log | `ksef_api/<env>/data/ksef_watchdog.log` | Restarty, heartbeat |
| Heartbeat | `ksef_api/<env>/data/ksef_heartbeat.json` | Ostatni tick daemona (JSON) |

---

## 7. Testy

```bash
# Pelny suite (241 testow)
py -m pytest tests/ksef/ -v

# Szybki smoke
py -m pytest tests/ksef/ -x -q

# Integracyjny (wymaga polaczenia z demo API)
py -m pytest tests/integration/test_ksef_demo_smoke.py -v
```

Przed kazda zmiana w kodzie KSeF — uruchom testy. 100% PASS = jedyny akceptowalny stan.
