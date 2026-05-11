# KSeF — Handoff produkcyjny

**Data:** 2026-05-11
**Autor:** Developer (Mrowisko)
**Adresat:** osoba odpowiedzialna za wdrożenie KSeF na produkcji
**Status:** gotowe do go-live (wystawianie); faktury kosztowe poza scope

---

## 1. TL;DR

Otrzymujesz kompletny, samodzielny system integracji ERP XL ↔ KSeF, zainstalowany w katalogu `Auto-ERP-Agent`. Działa na środowisku demo MF (NIP 7871003063), w pełni przetestowany (241 testów jednostkowych + smoke integracyjny). Wystawianie faktur i korekt do KSeF jest gotowe do produkcji. Importowanie faktur kosztowych z KSeF do XL (drugi kierunek) jest w fazie stabilizacji — zostaje na demo do osobnej decyzji.

Aby przejść na prod musisz wykonać 5 czynności: token, .env, init DB, dry-run, jedna faktura. Szczegóły w sekcji 5.

---

## 2. Zakres handoffu

### W zakresie produkcji (wystawianie XL → KSeF)

| Funkcja | Status | Komentarz |
|---|---|---|
| Faktury sprzedaży FS | gotowe | Generator + wysyłka + UPO |
| Korekty FSK | gotowe | Z polem PrzyczynaKorekty |
| Korekty skontowe / rabat | gotowe | Zunifikowany generator rabat (zastąpił 3 odrębne) |
| Daemon + watchdog | gotowe | Auto-restart, heartbeat, max 5 restartów/h |
| Raport mailowy dzienny | gotowe | SMTP, godzina konfigurowalna, default 13:30 |
| Shadow DB SQLite | gotowe | Per środowisko (demo/prod) oddzielne |
| GUI ustawień | gotowe | tkinter — bez ręcznej edycji .env |
| Master launcher (`ksef_start.bat`) | gotowe | Jeden dwuklik = pełny system |

### Poza zakresem produkcji (na razie)

| Funkcja | Status | Decyzja |
|---|---|---|
| Import faktur kosztowych (KSeF FA(3) → XL FZ ZSKR) | w stabilizacji | Pozostaje na demo. Ostatnie 5 commitów to fixy parsera (KOR pomijane, ceny netto fallback, polski separator dla XL COM). Decyzja o wdrożeniu produkcyjnym po osobnej walidacji na ≥20 fakturach. |

---

## 3. Architektura — minimum do zrozumienia

### Stack

- Python 3.12+
- SQL Server ODBC Driver 17+ (ERP Comarch XL)
- Windows Server (tkinter GUI, Task Scheduler)
- Zewnętrzne API: `api.ksef.mf.gov.pl` (prod) / `api-demo.ksef.mf.gov.pl` (demo)
- SMTP (raporty) — obecnie nazwa.pl

### Przepływ

```
ERP XL (SQL Server)
   │  SQL query (erp_reader.py)
   ▼
Faktura/Korekta — model domenowy
   │  xml_builder.py (lxml)
   ▼
XML FA(3)
   │  ksef_send.py / daemon (encrypt → session → send → poll)
   ▼
KSeF API
   │  status + UPO
   ▼
Shadow DB SQLite (data/ksef.db)
```

### Środowiska — separacja danych

```
ksef_api/
  demo/data/   — DB i logi demo (NIE rusza prod)
  demo/output/ — XML demo
  prod/data/   — DB i logi prod (utworzy się przy init)
  prod/output/ — XML prod
```

`KSEF_ENV` w `.env` przełącza całość. Brak wycieku danych między środowiskami.

### Bezpiecznik produkcyjny

`KSEF_ENV=prod` wymaga dodatkowego `KSEF_PROD_CONFIRMED=yes`. Bez tego daemon odmawia startu. To zabezpieczenie przed przypadkowym wysłaniem na prod podczas testów.

---

## 4. Prerekvizity przed wdrożeniem

Sprawdź każdy punkt zanim cokolwiek zmienisz w konfiguracji:

- [ ] **Token produkcyjny KSeF** — wygenerowany na https://ksef.mf.gov.pl (nie demo!).
      Typ: token autoryzacyjny dla sesji batch. Format: `YYYYMMDD-...|nip-XXXXXXXXXX|hash`.
- [ ] **NIP firmy** — w kodzie zaszyte `7871003063`. Zweryfikuj że to właściwy NIP.
- [ ] **Konto SMTP** — login, hasło, host, port. Obecnie nazwa.pl, SSL 465.
- [ ] **Lista odbiorców raportu** — pojedynczy e-mail lub kilka (separator `;` lub `,`).
- [ ] **Backup demo DB** — `copy ksef_api\demo\data\ksef.db ksef_api\demo\data\ksef_backup_demo_2026-05-11.db`.
- [ ] **Potwierdzenie z księgowością** — faktury w ERP `TrN_Bufor=0` są zatwierdzone i gotowe do wysyłki.
- [ ] **Konto z prawami administratora** na serwerze (potrzebne dla Task Scheduler).
- [ ] **Dostęp sieciowy z serwera** do: SQL Server ERP, `api.ksef.mf.gov.pl:443`, `smtp.nazwa.pl:465`.

---

## 5. Go-live — krok po kroku

### Krok 1 — Edycja `.env`

Otwórz `ksef_ustawienia.bat` (GUI) lub edytuj bezpośrednio:

```ini
KSEF_ENV=prod
KSEF_BASE_URL=https://api.ksef.mf.gov.pl/v2
KSEF_TOKEN=<TOKEN PRODUKCYJNY>
KSEF_PROD_CONFIRMED=yes
KSEF_NIP=7871003063

KSEF_SMTP_HOST=<host>
KSEF_SMTP_PORT=465
KSEF_SMTP_USER=<user>
KSEF_SMTP_PASS=<pass>
KSEF_SMTP_SSL=true
KSEF_REPORT_FROM=<nadawca>
KSEF_REPORT_TO=<odbiorca1>;<odbiorca2>
KSEF_REPORT_SUBJECT_PREFIX=[KSeF]
```

### Krok 2 — Inicjalizacja DB produkcyjnej

```
py tools/ksef_init_db.py
```

Tworzy `ksef_api/prod/data/ksef.db` z aktualnym schematem v3.

### Krok 3 — Smoke test API

```
py tools/ksef_smoke.py
```

Sprawdza łączność z produkcyjnym API KSeF. Musi zwrócić OK.

### Krok 4 — Dry-run

```
py tools/ksef_daemon.py --once --dry-run
```

Pokazuje listę faktur które _by_ poleciały. Brak wysyłki. Zweryfikuj listę z księgowością.

### Krok 5 — Jedna faktura kontrolna

```
py tools/ksef_daemon.py --once --rate-limit 1
py tools/ksef_status.py --today
```

Oczekiwany wynik: 1× ACCEPTED z numerem KSeF. Jeśli ERROR/REJECTED — STOP, sprawdź `ksef_api/prod/data/ksef_daemon.log` i sekcję 8.

### Krok 6 — Autostart przez Task Scheduler

Po udanej fakturze kontrolnej utwórz zadanie systemowe:

- **Nazwa:** `KSEF DEAMON`
- **Program:** `C:\Users\ARobakowski\Desktop\Auto-ERP-Agent\ksef_start.bat`
- **Start in:** `C:\Users\ARobakowski\Desktop\Auto-ERP-Agent`
- **Trigger:** At system startup + co godzinę (zabezpieczenie)
- **Konto:** uruchomienie z prawami admina, niezależnie czy user jest zalogowany

Po starcie powinieneś widzieć w Task Scheduler stan _Running_, a w `ksef_api/prod/data/ksef_heartbeat.json` aktualny timestamp.

---

## 6. Codzienna obsługa

### Co dzień

Codziennie o 13:30 przychodzi mail z raportem. Jeśli widzisz **"WSZYSTKIE FAKTURY WYSŁANE"** — system działa. Koniec.

### Reagujesz tylko gdy

| Komunikat w raporcie | Co zrobić |
|---|---|
| "Oczekujące: N" | Poczekaj na następny tick (15 min). Daemon ponowi. |
| "Błędy: N" | Sprawdź `py tools/ksef_status.py --status ERROR`. Daemon ponawia automatycznie 3x. |
| "Odrzucone: N" | `py tools/ksef_status.py --status REJECTED`. To wymaga interwencji księgowej (duplikat, błędne dane). |
| Brak maila o 13:30 | Daemon nie działa. Sprawdź sekcję 7. |

### Co miesiąc

- Sprawdź czy token KSeF nie wygasa w najbliższym czasie (tokeny mają ograniczony czas życia).
- Backup `ksef_api/prod/data/ksef.db` (rotacja).

---

## 7. Monitoring i diagnostyka

### Sprawdzenie czy daemon żyje

```
py tools/ksef_status.py --summary
type ksef_api\prod\data\ksef_heartbeat.json
schtasks /query /tn "KSEF DEAMON" /fo LIST /v
```

### Logi

| Plik | Co zawiera |
|---|---|
| `ksef_api/prod/data/ksef_daemon.log` | Każdy tick, wysyłka, błąd |
| `ksef_api/prod/data/ksef_watchdog.log` | Restarty, heartbeat |
| `ksef_api/prod/data/ksef_heartbeat.json` | Ostatni tick (JSON) |
| `data/ksef_start.log` | Log startu launchera |

### Ręczne ponowienie wysyłki

```
py tools/ksef_send.py ksef_api/prod/output/ksef_FS-<numer>.xml
```

### Restart daemona

```
schtasks /end /tn "KSEF DEAMON"
schtasks /run /tn "KSEF DEAMON"
```

(wymaga terminala admin)

---

## 8. Rollback

W razie problemu wracasz na demo w 3 krokach:

1. Edycja `.env`:
   ```ini
   KSEF_ENV=demo
   KSEF_BASE_URL=https://api-demo.ksef.mf.gov.pl/v2
   KSEF_TOKEN=<TOKEN DEMO>
   # usuń linię KSEF_PROD_CONFIRMED
   ```
2. `schtasks /end /tn "KSEF DEAMON"`
3. `schtasks /run /tn "KSEF DEAMON"`

Dane demo i prod są w oddzielnych folderach — rollback nie nadpisze niczego.

---

## 9. Najczęstsze problemy

| Problem | Przyczyna | Rozwiązanie |
|---|---|---|
| Daemon nie startuje, "KSEF_PROD_CONFIRMED=yes required" | Brak potwierdzenia w .env | Dodaj `KSEF_PROD_CONFIRMED=yes` |
| Watchdog zatrzymany po 5 restartach/h | Coś crashuje cyklicznie | Sprawdź `ksef_watchdog.log` i `ksef_daemon.log` |
| REJECTED: "Duplikat faktury" | Faktura wysłana wcześniej (np. z demo) | Sprawdź `ksef_status --gid <GID>`. Decyzja księgowa. |
| Brak faktur do wysłania | Faktury w buforze ERP (`TrN_Bufor!=0`) | Zatwierdź faktury w ERP XL |
| ERROR przy wysyłce — token | Token wygasł | Wygeneruj nowy w portalu KSeF, podmień w `.env` |
| Brak maila o 13:30 | SMTP failure lub daemon padł | Sprawdź `ksef_daemon.log`, ręcznie: `py tools/ksef_report.py --send-email` |

---

## 10. Dokumenty referencyjne

Pełna dokumentacja w repozytorium:

| Plik | Co zawiera |
|---|---|
| `documents/human/ksef_instrukcja.md` | Pełna instrukcja operacyjna (architektura, codzienne użytkowanie, troubleshooting) — 565 lin |
| `documents/human/plans/ksef_deploy_prod_checklist.md` | Skrócony checklist deploy |
| `documents/human/plans/plan_ksef_standalone.md` | Mapa plików i zależności pip |
| `documents/human/plans/plan_ksef_daemon_resilience.md` | Mechanizm watchdog/heartbeat |
| `documents/human/plans/plan_ksef_reporting.md` | Raportowanie e-mailowe |
| `documents/human/plans/ksef_api_automation.md` | Specyfikacja automatyzacji KSeF API |
| `documents/human/reports/ksef_feasibility_field_mapping.md` | Mapowanie pól ERP → KSeF |
| `documents/human/reports/ksef_block_*_code_review.md` | Code review 7 bloków implementacyjnych |

---

## 11. Testy i jakość

- 241 testów jednostkowych: `py -m pytest tests/ksef/ -v`
- Test integracyjny smoke na demo API: `py -m pytest tests/integration/test_ksef_demo_smoke.py -v`
- Stan na 2026-05-11: 100% PASS
- Każda zmiana w kodzie KSeF wymaga zielonego suite testów przed mergem

---

## 12. Co dalej (po wdrożeniu)

Decyzje do podjęcia po stabilizacji prod (~30 dni):

1. **Faktury kosztowe (KSeF → XL FZ ZSKR)** — kierunek importowy.
   Branch zmergowany do main, ale w aktywnej iteracji.
   Walidacja na ≥20 fakturach na demo przed wdrożeniem.
2. **Retencja shadow DB** — po roku DB urośnie. Polityka archiwizacji do ustalenia.
3. **Monitoring długoterminowy** — czy potrzebny dashboard (Grafana) ponad mail dzienny.
4. **Eskalacja błędów** — czy ERROR threshold w daemon ma wysyłać natychmiastowe powiadomienie (SMS/Slack), czy wystarczy raport dzienny.

---

## 13. Kontakt techniczny

System został zbudowany przez agenta Developer w ramach projektu Mrowisko (`documents/methodology/SPIRIT.md`).

Sprawy techniczne, fixy, rozbudowy:
- Komunikacja przez `tools/agent_bus_cli.py` (rola: `developer` lub `erp_specialist`)
- Eskalacja do człowieka: `agent_bus_cli.py flag --from <rola> --reason-file ...`

Repo i historia commitów dostępne w git (`git log --grep=ksef`).
