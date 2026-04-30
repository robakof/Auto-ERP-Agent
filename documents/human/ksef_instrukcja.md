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

### 3.0 Szybka kontrola — czy wszystko dziala?

**Nie musisz czytac logow.** Wystarczy jedno polecenie:

```
py tools/ksef_report.py --stdout --since 1d
```

Widzisz **"WSZYSTKIE FAKTURY WYSLANE"** → jest OK. Koniec.

**A jeszcze lepiej:** raport mailowy przychodzi codziennie o 13:30 na skonfigurowane
adresy email. Jak mail przyszedl i status jest OK — nie musisz robic nic.

**Kiedy reagowac:**

| Co widzisz | Co to znaczy | Co zrobic |
|---|---|---|
| "WSZYSTKIE FAKTURY WYSLANE" | Wszystko OK | Nic |
| "Oczekujace: N" | Faktury czekaja na wysylke | Poczekaj na nastepny tick (15 min) |
| "Bledy: N" | Blad techniczny (siec, API) | Daemon ponowi automatycznie |
| "Odrzucone: N" | KSeF odrzucil fakture | Sprawdz: `py tools/ksef_status.py --status REJECTED` |
| Brak maila o 13:30 | Daemon nie dziala | Sprawdz: `py tools/ksef_start.py` lub Task Scheduler |

**Sprawdzenie za konkretny dzien:**

```
py tools/ksef_report.py --stdout --since 3d    :: ostatnie 3 dni
py tools/ksef_report.py --stdout --since 7d    :: ostatni tydzien
```

### 3.1 Skroty Windows (*.bat)

Dwuklik z Eksploratora:

| Plik | Co robi |
|---|---|
| **`ksef_start.bat`** | **Glowny launcher: daemon + watchdog + raport o 13:30 (jedno okno)** |
| `ksef_generuj_fs.bat` | Generuje XML z faktur (FS) za dzisiejszy dzien |
| `ksef_generuj_kor.bat` | Generuje XML z korekt (FSK) za dzisiejszy dzien |
| `ksef_generuj_skonto.bat` | Generuje XML z korekt skontowych za dzisiejszy dzien |
| `ksef_wyslij_demo.bat` | Uruchamia daemon+watchdog (demo) — auto wysylka (bez raportu) |
| `ksef_raport_dzienny.bat` | Wysyla raport email lub wyswietla w terminalu |
| `ksef_ustawienia.bat` | Otwiera GUI ustawien (.env) |
| `test_ksef.bat` | Uruchamia testy automatyczne |

Wszystkie generatory otwieraja dialog wyboru folderu wyjsciowego.
Mozna tez podac date jako argument: `ksef_generuj_fs.bat 2026-04-01`

### 3.1a Glowny launcher — ksef_start.bat

**Rekomendowany sposob uruchomienia.** Jeden dwuklik startuje caly system:
- Watchdog monitoruje daemon (auto-restart przy crash/zawieszeniu)
- Daemon skanuje ERP co 15 min i wysyla faktury na KSeF
- O 13:30 automatycznie wysyla raport dzienny na email

```
ksef_start.bat                  -> pelny system (daemon + raport o 13:30)
ksef_start.bat --once           -> jeden scan + wysylka, potem zamyka
ksef_start.bat --dry-run        -> podglad (bez wysylki na KSeF)
ksef_start.bat --no-report      -> daemon bez raportu mailowego
ksef_start.bat --report-time 17:00  -> raport o innej godzinie
```

Zamkniecie: **Ctrl+C** w oknie terminala — zamyka daemon, watchdog i scheduler raportu.

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
| Start log | `data/ksef_start.log` | Log startu launchera (bledy uruchomienia) |
| Daemon log | `ksef_api/<env>/data/ksef_daemon.log` | Kazdy tick, wysylka, blad |
| Watchdog log | `ksef_api/<env>/data/ksef_watchdog.log` | Restarty, heartbeat |
| Heartbeat | `ksef_api/<env>/data/ksef_heartbeat.json` | Ostatni tick daemona (JSON) |

### Sprawdzanie czy daemon dziala

```bash
:: Czy procesy Python sa aktywne (3 procesy = start + watchdog + daemon)
tasklist /FI "IMAGENAME eq python.exe"

:: Ostatni heartbeat daemona
more ksef_api\demo\data\ksef_heartbeat.json

:: Log startu (czy launcher nie padl)
more data\ksef_start.log

:: Status wysylek z dzisiaj
py tools/ksef_status.py --today
```

### Autostart (Task Scheduler)

Daemon uruchamia sie automatycznie przy starcie serwera przez Windows Task Scheduler.
Zadanie: `KSEF DEAMON`, trigger: At system startup.

```bash
:: Sprawdz status zadania (z CMD admina)
schtasks /query /tn "KSEF DEAMON" /fo LIST /v

:: Reczne uruchomienie
schtasks /run /tn "KSEF DEAMON"

:: Zatrzymanie
schtasks /end /tn "KSEF DEAMON"

:: Restart (zatrzymaj + uruchom)
schtasks /end /tn "KSEF DEAMON" && schtasks /run /tn "KSEF DEAMON"
```

Komendy `schtasks` wymagaja terminala z prawami administratora
(Start → cmd → prawy klik → Uruchom jako administrator).

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

---

## 8. Spis wszystkich polecen terminalowych

Wszystkie komendy uruchamiasz z glownego katalogu projektu.

### 8.1 Glowny launcher (rekomendowany)

```bash
py tools/ksef_start.py                         # Pelny system: daemon + watchdog + raport o 13:30
py tools/ksef_start.py --once                  # Jednorazowy scan + wysylka, potem exit
py tools/ksef_start.py --once --dry-run        # Podglad co by wyslal (bez wysylki)
py tools/ksef_start.py --once --rate-limit 1   # Wysylka max 1 faktury (test produkcyjny)
py tools/ksef_start.py --no-report             # Daemon bez raportu mailowego
py tools/ksef_start.py --report-time 17:00     # Raport o innej godzinie niz 13:30
py tools/ksef_start.py --interval 300          # Daemon tick co 5 min (zamiast 15)
py tools/ksef_start.py --dry-run               # Caly system w trybie podgladu
```

### 8.2 Generowanie XML z faktur

```bash
py tools/ksef_generate.py --date-from 2026-04-24           # Faktury (FS) od daty
py tools/ksef_generate.py --gid 59 60                      # Konkretne GID
py tools/ksef_generate.py --date-from 2026-04-24 --dry-run # Pokaz SQL, nie generuj
py tools/ksef_generate.py --date-from 2026-04-24 --output-dir sciezka  # Inny folder

py tools/ksef_generate_kor.py --date-from 2026-04-24       # Korekty (FSK)
py tools/ksef_generate_kor.py --gid 100 101                # Konkretne GID korekt

py tools/ksef_generate_skonto.py --date-from 2026-04-24    # Korekty skontowe
```

### 8.3 Reczna wysylka na KSeF

```bash
py tools/ksef_send.py ksef_api/demo/output/ksef_FS-*.xml   # Wyslij pliki XML
py tools/ksef_send.py ksef_api/demo/output/*.xml            # Wyslij wszystkie XML
```

### 8.4 Daemon (samodzielnie, bez launchera)

```bash
py tools/ksef_daemon.py                        # Ciagly daemon (tick co 15 min)
py tools/ksef_daemon.py --once                 # Jednorazowy scan + wysylka
py tools/ksef_daemon.py --once --dry-run       # Podglad bez wysylki
py tools/ksef_daemon.py --once --rate-limit 1  # Wysylka max 1 faktury
py tools/ksef_daemon.py --interval 300         # Tick co 5 min
```

### 8.5 Watchdog (samodzielnie, bez launchera)

```bash
py tools/ksef_watchdog.py                      # Watchdog + daemon (domyslne ustawienia)
py tools/ksef_watchdog.py --interval 300       # Daemon tick co 5 min
py tools/ksef_watchdog.py --max-restarts 3     # Max 3 restarty na godzine
```

### 8.6 Status i monitoring

```bash
py tools/ksef_status.py --summary              # Podsumowanie: dzis, 7 dni, total
py tools/ksef_status.py --today                # Dzisiejsze wysylki
py tools/ksef_status.py --status ERROR         # Tylko bledy
py tools/ksef_status.py --status REJECTED      # Tylko odrzucone
py tools/ksef_status.py --status ACCEPTED      # Tylko zaakceptowane
py tools/ksef_status.py --gid 123456           # Konkretna faktura po GID
```

### 8.7 Raport dzienny

```bash
py tools/ksef_report.py --stdout               # Wyswietl raport w terminalu (dzis)
py tools/ksef_report.py --stdout --since 7d    # Raport za ostatnie 7 dni
py tools/ksef_report.py --stdout --since 3d    # Raport za ostatnie 3 dni
py tools/ksef_report.py --stdout --since 24h   # Raport za ostatnie 24 godziny
py tools/ksef_report.py --send-email           # Wyslij raport mailem
py tools/ksef_report.py --file raport.txt      # Zapisz raport do pliku
```

### 8.8 Konfiguracja

```bash
py tools/ksef_config_gui.py                    # GUI ustawien (.env) — okno z zakladkami
py tools/ksef_init_db.py                       # Utworz/sprawdz baze danych shadow DB
```

### 8.9 Diagnostyka i testy

```bash
py tools/ksef_smoke.py                         # Smoke test — czy API KSeF odpowiada
py tools/ksef_validate.py output/schemat_FA3.xsd ksef_api/demo/output/*.xml  # Walidacja XML vs XSD
py -m pytest tests/ksef/ -v                    # Pelny suite testow
py -m pytest tests/ksef/ -x -q                 # Szybki test (stop na 1. bledzie)
py -m pytest tests/integration/test_ksef_demo_smoke.py -v   # Test integracyjny z demo API
```

### 8.10 Instalacja standalone

```bash
py tools/ksef_install.py                       # Kopiuj do dist/ksef/
py tools/ksef_install.py --target D:\KSeF      # Kopiuj do wybranego katalogu
py tools/ksef_install.py --install-deps        # Kopiuj + zainstaluj pip dependencies
```
