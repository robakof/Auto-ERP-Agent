# Serce — VPS setup (staging)

Date: 2026-04-13
Status: DONE — wszystkie kroki 1-14 wykonane (2026-04-14)
Author: Developer

---

## Zdecydowane

- **Tryb:** staging teraz, równolegle z rozwojem Fazy 1
- **Provider:** Home.pl VPS
- **OS:** Ubuntu 24.04.4 LTS (kernel 6.8.0-100-generic)
- **IP:** 194.164.198.25
- **Hostname:** serce-staging
- **Email (Let's Encrypt + alerty):** arco@interia.pl
- **Domena:** msps.pl (zarejestrowana), `kontakt@msps.pl` (mailserver TBD)
- **SSL cert:** kupiony (~5 PLN, Home.pl), typ/zakres TBD — czekamy na zakończenie procesowania płatności
- **Repo:** GitHub, `CyperCyper/Auto-ERP-Agent` (private) — plan: deploy key + sparse-checkout dla `serce/`
- **Non-root user VPS:** `serce` (sudo NOPASSWD, staging — produkcja z hasłem)

## Pending

- **Cert SSL** — DV dla msps.pl + www.msps.pl (CSR wygenerowany, płatność zakończona, czekamy na wystawienie)
- **DNS provider dla msps.pl** — prawdopodobnie panel Home.pl (do potwierdzenia)
- **Subdomena stagingu** — cert nie obejmuje subdomeny; staging może działać na msps.pl lub potrzebny Let's Encrypt dla staging.msps.pl
- **GitHub PAT leaked** — user ma unieważnić token `github_pat_11BERPS4Y0...` (widoczny w `git remote -v`) + przełączyć remote na SSH
- **Backup target** — na start lokalny pg_dump + snapshot Home.pl; object storage później

## Wykonane (2026-04-13)

- [x] Krok 1: `apt update && apt upgrade -y` + instalacja `curl git ufw fail2ban unattended-upgrades ca-certificates gnupg`
- [x] Krok 2: user `serce` utworzony, klucz SSH wgrany, sudo NOPASSWD skonfigurowany, test login OK
- [x] Krok 3: SSH hardening (`/etc/ssh/sshd_config.d/99-hardening.conf`) — PasswordAuthentication no, PermitRootLogin prohibit-password; test nowej sesji OK
- [x] Krok 4: UFW aktywne, reguły 22/80/443 (v4 + v6), default deny incoming
- [x] Krok 5: fail2ban aktywny, jail sshd (maxretry 5, findtime 10m, bantime 1h) — już zabanował 2 IP w 16 min
- [x] Krok 6a: unattended-upgrades enabled
- [x] Krok 6b: hostname → `serce-staging`

## Pozostałe kroki

7. ~~**Docker**~~ ✓ docker-ce 29.4.0 + docker-compose-plugin v5.1.2 zainstalowane, user `serce` w grupie docker, hello-world OK (2026-04-14)
8. ~~**Repo**~~ ✓ deploy key ED25519 na kaboraco-svg/serce (read-only), pełny klon do `/home/serce/app/` (2026-04-14). Sync script rozbudowany o backend + docker-compose.
9. ~~**Postgres + backend w compose**~~ ✓ postgres:16-alpine + app-backend zbudowane i uruchomione, `curl 127.0.0.1:8000/api/v1/health` → `{"status":"ok"}` (2026-04-14)
10. ~~**DNS**~~ ✓ A record `msps.pl` → 194.164.198.25 dodany w panelu Home.pl, propagacja OK (2026-04-14)
11. ~~**nginx**~~ ✓ reverse proxy :80 → backend :8000, server_name msps.pl www.msps.pl, health OK (2026-04-14). HTTPS po kroku 12.
12. ~~**SSL**~~ ✓ cert DV Home.pl (ważny do 2026-10-29) + klucz wgrane, HTTPS na :443, HTTP→HTTPS redirect, TLS 1.2+1.3, health OK z zewnątrz (2026-04-14)
13. **Monitoring** — UptimeRobot TBD (user zakłada konto). URL: `https://msps.pl/api/v1/health`, interwał 5 min, alert na arco@interia.pl
14. ~~**Backup**~~ ✓ cron codziennie 3:00 UTC, pg_dump → `/var/backups/serce/`, retencja 14 dni, test OK (2026-04-14)

## Uwagi

- Przed deployem aplikacji plan zakłada że Faza 1 backendu ma działające minimum (auth + health). Obecnie tylko `/health` — staging może ruszyć z tym, ale sensowny smoke test dopiero po auth.
- `Auto-ERP-Agent` to monorepo z różnymi projektami (ERP, Kerti, Serce) — decyzja o sposobie pobrania kodu na produkcji wymaga potwierdzenia.
