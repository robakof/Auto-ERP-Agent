# KSeF — Deploy na Produkcję — Checklist

Data: 2026-04-16
Status: Do realizacji przez człowieka

---

## Prerekvizity (zanim zmienisz .env)

- [ ] **Token produkcyjny KSeF** — wygeneruj na https://ksef.mf.gov.pl (nie demo!)
  - Typ: token autoryzacyjny (sesja interaktywna lub batch)
  - NIP: 7871003063 (ten sam co w demo)
  - Token ma format: `YYYYMMDD-...|nip-XXXXXXXXXX|hash`
- [ ] **Backup shadow DB** — `copy data\ksef.db data\ksef_backup_demo_2026-04-16.db`
  - DB demo zawiera test wysyłki FS-59 ACCEPTED na api-demo
  - Po przejściu na prod chcesz czyste DB — albo backup + reset, albo kontynuacja (oba OK)
- [ ] **Potwierdzenie z księgowością** — że faktury w ERP (TrN_Bufor=0) są gotowe do wysyłki

---

## Konfiguracja .env

Zmień poniższe wartości w `.env`:

```ini
# BYŁO (demo):
KSEF_ENV=demo
KSEF_BASE_URL=https://api-demo.ksef.mf.gov.pl/v2
KSEF_TOKEN=20260415-EC-1CFAC87000-...

# NOWE (prod):
KSEF_ENV=prod
KSEF_BASE_URL=https://api.ksef.mf.gov.pl/v2
KSEF_TOKEN=<TWÓJ TOKEN PRODUKCYJNY>
KSEF_PROD_CONFIRMED=yes
KSEF_NIP=7871003063
```

**Uwaga:** Bez `KSEF_PROD_CONFIRMED=yes` daemon odmówi startu (fail-fast safety guard).

---

## Pierwszy test na Prod (jedna faktura)

```bash
# 1. Dry-run — sprawdź co poleciałoby, BEZ wysyłki:
py tools/ksef_daemon.py --once --dry-run

# 2. Jeśli lista faktur wygląda OK — wyślij jedną (rate-limit 1):
py tools/ksef_daemon.py --once --rate-limit 1

# 3. Sprawdź status:
py tools/ksef_status.py --summary
py tools/ksef_status.py --today
```

Oczekiwany wynik: 1x ACCEPTED. Jeśli ERROR/REJECTED — sprawdź logi i ksef_status --status ERROR.

---

## Task Scheduler (produkcja ciągła)

Po udanym teście jednej faktury:

1. **Utwórz Task w Task Scheduler:**
   - Program: `py` (lub pełna ścieżka: `C:\Program Files\Python312\python.exe`)
   - Arguments: `tools/ksef_daemon.py --interval 300 --rate-limit 10 --error-threshold 3`
   - Start in: `C:\Users\arkadiusz\Desktop\Auto-ERP-Agent`
   - Trigger: przy starcie systemu / co godzinę (zabezpieczenie restart)
   - Run whether user is logged on or not

2. **Rekomendowane parametry:**
   - `--interval 300` — tick co 5 minut (wystarczające, ~20-30 dok/dzień)
   - `--rate-limit 10` — max 10 dok/min (ochrona przed runaway)
   - `--error-threshold 3` — eskalacja do człowieka przy >=3 błędach/tick

3. **Logi:** stdout → plik (Task Scheduler output redirect) lub Windows Event Log

---

## Monitoring codzienny

```bash
# Poranny przegląd:
py tools/ksef_status.py --summary

# Jeśli UWAGA przy ERROR/REJECTED:
py tools/ksef_status.py --status ERROR
py tools/ksef_status.py --status REJECTED
```

---

## Rollback do demo

Jeśli coś pójdzie nie tak:

```ini
KSEF_ENV=demo
KSEF_BASE_URL=https://api-demo.ksef.mf.gov.pl/v2
KSEF_TOKEN=<TOKEN DEMO>
# Usuń KSEF_PROD_CONFIRMED
```

Restart daemon (kill Task Scheduler task + uruchom ponownie).

---

## Gotowe komendy

| Akcja | Komenda |
|---|---|
| Dry-run (podgląd) | `py tools/ksef_daemon.py --once --dry-run` |
| Jedna faktura | `py tools/ksef_daemon.py --once --rate-limit 1` |
| Pełny batch | `py tools/ksef_daemon.py --once` |
| Daemon ciągły | `py tools/ksef_daemon.py --interval 300` |
| Status summary | `py tools/ksef_status.py --summary` |
| Dzisiejsze | `py tools/ksef_status.py --today` |
| Errory | `py tools/ksef_status.py --status ERROR` |
| Konkretny GID | `py tools/ksef_status.py --gid 123` |
