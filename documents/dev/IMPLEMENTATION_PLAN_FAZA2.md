# Plan implementacji — Faza 2: Warstwa BI + Bot Pytań

*Dokument przygotowany: 2026-03-10*

Szczegółowe wymagania: `PRD.md` | Architektura: `ARCHITECTURE.md` | Stack: `TECHSTACK.md`

---

## Stan obecny

Częściowo zrealizowana Faza 2a:

| Element | Stan |
|---------|------|
| `solutions/bi/views/` — Rezerwacje, KntKarty, ZamNag, Rozrachunki | ✓ |
| `solutions/bi/catalog.json` — Rezerwacje, KntKarty, Rozrachunki | ✓ (ZamNag brakuje) |
| `tools/bi_verify.py` | ✓ |
| `tools/search_bi.py` | ✗ |
| Bot (`bot/`) | ✗ |
| Konto `CEIM_AIBI` na SQL Server | ✗ (wymaga DBA) |

---

## Kamienie milowe

### KM1 — Fundament katalog BI

**Zakres:**
- Uzupełnić `catalog.json` o ZamNag i wszystkie kolejne widoki tworzone przez usera
- `tools/search_bi.py` — wyszukiwanie po nazwie/opisie/example_questions
- Reguła w `AGENT.md`: przed budowaniem JOINów z CDN.* sprawdź `search_bi.py`

**Warunek ukończenia:** agent ERP potrafi odnaleźć widok BI po pytaniu w języku naturalnym.

---

### KM2 — Bot core (bez kanałów)

**Zakres:**
- `bot/pipeline/nlp_pipeline.py` — match+generate (Claude API call 1): dopasowanie raportu LUB generowanie SQL ad-hoc
- `bot/pipeline/sql_validator.py` — guardrails: blokada DML/EXEC, wymuszenie TOP, tylko `AIBI.*`
- `bot/sql_executor.py` — pyodbc read-only na `AIBI.*` (konto CEIM_AIBI)
- `bot/pipeline/answer_formatter.py` — Claude API call 2: pytanie + dane → odpowiedź PL
- `bot/pipeline/conversation.py` — kontekst 3 tury per user, TTL 15 min

**Zależność:** konto `CEIM_AIBI` na SQL Server (DBA).

**Warunek ukończenia:** `python bot/pipeline/nlp_pipeline.py --question "jakie rezerwacje ma Bolsius"` zwraca poprawną odpowiedź.

---

### KM3 — Kanał Telegram

**Zakres:**
- `bot/channels/telegram_channel.py` — long polling, whitelist ID
- `bot/main.py` — entry point spinający pipeline z kanałem

**Warunek ukończenia:** pytanie przez Telegram → odpowiedź w PL w < 30s.

---

### KM4 — Biblioteka raportów

**Zakres:**
- Format plików: `solutions/bi/reports/[nazwa].sql` z nagłówkiem metadanych
- `tools/search_reports.py` — dopasowanie pytania do gotowego raportu
- Pierwsze 5–10 raportów na podstawie najczęstszych pytań

**Warunek ukończenia:** bot dla znanych pytań odpowiada z gotowego raportu (szybciej, pewniej).

---

### KM5 — Deployment

**Zakres:**
- `bot/health.py` — endpoint `/health` + watchdog ping co 5 min
- Rozszerzenie `requirements.txt` o zależności bota
- Konfiguracja NSSM (instrukcja w INSTALL.md)
- Rozszerzenie `verify.py` o weryfikację konta CEIM_AIBI i widoków BI

**Warunek ukończenia:** bot działa jako serwis Windows, restart automatyczny.

---

### KM6 — Kanał WhatsApp *(opcjonalny, zależny od Meta)*

**Zakres:**
- `bot/channels/whatsapp_channel.py` — webhook, FastAPI
- Cloudflare Tunnel setup

**Zależność:** zweryfikowane konto Meta Business Manager + dedykowany numer telefonu.
Realizacja po uruchomieniu Telegrama i potwierdzeniu działania pipeline.

---

## Kolejność prac

```
KM1 (search_bi) → KM2 (bot core) → KM3 (Telegram) → KM4 (raporty) → KM5 (deployment) → KM6 (WhatsApp)
```

KM2 jest zablokowane na konto CEIM_AIBI od DBA — można je realizować równolegle z KM1
używając CEiM_Reader jako tymczasowe konto testowe.
