# Serce — VPS setup (staging)

Date: 2026-04-13
Status: IN PROGRESS — bootstrap done, next: Docker (Krok 7)
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

- **Typ certa SSL** — wildcard vs DV zwykły; decyzja po zakończeniu płatności
- **DNS provider dla msps.pl** — prawdopodobnie panel Home.pl (do potwierdzenia)
- **Subdomena stagingu** — rekomendacja: `staging.msps.pl`
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

7. **Docker** — docker-ce + docker-compose-plugin (`curl -fsSL https://get.docker.com | sh`, add `serce` to docker group, test `docker run hello-world`)
8. **Repo** — deploy key GitHub, sparse-checkout tylko `serce/` do `/home/serce/app/`
9. **Postgres + backend w compose** — uruchomienie lokalnie na VPS (`curl 127.0.0.1:8000/api/v1/health`)
10. **DNS** — A record `staging.msps.pl` → 194.164.198.25 (panel DNS msps.pl)
11. **nginx** — reverse proxy :443 → backend :8000, HTTP→HTTPS redirect
12. **SSL** — kupiony cert (jeśli wildcard/staging) albo Let's Encrypt (certbot + auto-renewal)
13. **Monitoring** — UptimeRobot na `/api/v1/health`
14. **Backup** — cron: codzienny pg_dump → `/var/backups/serce/`, retencja 14 dni

## Uwagi

- Przed deployem aplikacji plan zakłada że Faza 1 backendu ma działające minimum (auth + health). Obecnie tylko `/health` — staging może ruszyć z tym, ale sensowny smoke test dopiero po auth.
- `Auto-ERP-Agent` to monorepo z różnymi projektami (ERP, Kerti, Serce) — decyzja o sposobie pobrania kodu na produkcji wymaga potwierdzenia.
