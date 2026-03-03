# TECHSTACK: Faza 2 — Warstwa BI + Bot Pytań

*Dokument przygotowany: 2026-03-03*

---

## 1. Przegląd decyzji technicznych

| Komponent | Wybrana technologia | Alternatywa odrzucona | Powód wyboru |
|-----------|--------------------|-----------------------|--------------|
| Bot backend | Python 3.12 | Node.js, Go | Spójność z Fazą 1 |
| Windows service | NSSM | pywin32, Task Scheduler | Zero kodu serwisowego, niezawodne |
| Kanał testowy | python-telegram-bot | Discord, Slack | Brak weryfikacji biznesowej, prosty API |
| Kanał docelowy | Meta WhatsApp Cloud API | Twilio, MessageBird | Brak kosztów pośrednika |
| Webhook tunnel | Cloudflare Tunnel | ngrok, własny SSL | Darmowy, trwały URL, brak otwierania portów |
| NLP engine | Claude API (claude-sonnet-4-6) | GPT-4, lokalny LLM | Już używany w projekcie |
| SQL execution | pyodbc | sqlalchemy | Spójność z Fazą 1, zero ORM |
| Katalog BI views | JSON + FTS5 (sqlite3) | Tylko JSON | Spójność z docs.db; FTS gdy katalog urośnie |
| Biblioteka raportów | pliki .sql + JSON metadata | SQLite | Spójność z solutions/ |
| Power BI | DirectQuery → SQL Server BI.* | Import mode | Dane zawsze aktualne |
| Excel | Power Query / ODBC → SQL Server BI.* | Eksport CSV | Dane zawsze aktualne |

---

## 2. Bot backend — Python + NSSM

**Decyzja:** Python 3.12, uruchomiony jako serwis Windows przez NSSM
(Non-Sucking Service Manager).

**Uzasadnienie:**
- Ten sam ekosystem co Faza 1 — wspólne zależności (`pyodbc`, `python-dotenv`)
- NSSM zarządza restartem procesu bez pisania kodu serwisowego
- Alternatywa `pywin32` wymaga znacznie więcej kodu boilerplate

**Konfiguracja serwisu:**
```
nssm install ERP-Bot python bot\main.py
nssm set ERP-Bot AppDirectory C:\erp-agent
nssm set ERP-Bot AppRestartDelay 5000
```

**Zależności:**
| Pakiet | Zastosowanie |
|--------|-------------|
| `anthropic` | Claude API (NLP pipeline) |
| `python-telegram-bot` | Telegram Bot API |
| `requests` | WhatsApp Cloud API (REST) |
| `pyodbc` | Wykonywanie SQL na SQL Server |
| `python-dotenv` | Zmienne środowiskowe |

---

## 3. Kanały komunikacji

### Telegram (kanał testowy)

**Biblioteka:** `python-telegram-bot` (async, oficjalna, dobrze utrzymana)

**Model połączenia:** long polling — bot odpytuje serwer Telegram co N sekund.
Nie wymaga publicznego endpointu HTTP, działa za NAT/firewall.

```python
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.run_polling()
```

**Autoryzacja:** whitelist `TELEGRAM_ALLOWED_IDS` w `.env` — lista ID użytkowników.

---

### WhatsApp Business (kanał docelowy)

**API:** Meta WhatsApp Cloud API (bezpłatny tier: 1000 rozmów/miesiąc).

**Model połączenia:** webhook — Meta wysyła POST na nasz endpoint przy każdej wiadomości.
Bot musi mieć publicznie dostępny URL HTTPS.

**Wymagania:**
- Zweryfikowane konto Meta Business Manager
- Numer telefonu dedykowany dla bota (nie może być używany w WhatsApp normalnie)
- URL webhooka zarejestrowany w Meta Developer Console

**Implementacja webhooka:** FastAPI (lekki, async, dobry dla jednego endpointu).

```python
@app.post("/webhook")
async def webhook(request: Request):
    ...
```

---

### Cloudflare Tunnel (rozwiązanie problemu webhooka WhatsApp)

**Problem:** Meta wymaga publicznego URL HTTPS dla webhooka. Serwer firmowy
nie ma publicznego IP — i nie powinien go mieć (bezpieczeństwo).

**Rozwiązanie:** Cloudflare Tunnel — tworzy zaszyfrowany tunel między serwerem
a siecią Cloudflare. Serwer sam inicjuje połączenie wychodzące (brak otwierania portów).

```
Internet → cloudflare.com → tunel → serwer firmowy:8000
```

**Konfiguracja:**
```
# Instalacja (jednorazowo)
cloudflared tunnel create erp-bot
cloudflared tunnel route dns erp-bot bot.firma.com

# Uruchomienie (serwis Windows)
cloudflared tunnel run erp-bot
```

**Bezpieczeństwo:** tylko ruch do `/webhook` przechodzi przez tunel;
SQL Server pozostaje całkowicie niedostępny z zewnątrz.

---

## 4. NLP Pipeline — Claude API

**Model:** `claude-sonnet-4-6` (balans koszt/jakość dla polskiego języka naturalnego)

**Przepływ:**

```
1. Pytanie użytkownika (PL)
        ↓
2. Report Matcher
   - Porównanie pytania z metadanymi biblioteki raportów
   - Jeśli score > próg → wykonaj gotowy raport z parametrami
        ↓ (brak dopasowania)
3. SQL Generator (Claude API)
   - Prompt zawiera: pytanie + katalog BI views (nazwy, kolumny, opisy)
   - Claude zwraca SELECT na BI.*
        ↓
4. SQL Executor (pyodbc, read-only, BI schema)
        ↓
5. Answer Formatter (Claude API)
   - Dane SQL + pytanie → odpowiedź w języku naturalnym (PL)
```

**Co trafia do Claude API:** pytanie użytkownika + schemat BI views (nazwy kolumn,
opisy). Żadne dane z bazy nie opuszczają sieci firmowej przed uformowaniem odpowiedzi —
tylko metadane schematu i pytanie.

---

## 5. Schema BI — SQL Server

**Decyzja:** Dedykowany schema `BI` na istniejącym SQL Serverze SQLSERVER\SQLEXPRESS.

**Konta SQL:**
| Konto | Uprawnienia | Zastosowanie |
|-------|-------------|-------------|
| `CEiM_Reader` | SELECT na CDN.* | Agent ERP Faza 1 (bez zmian) |
| `CEiM_BI` | SELECT na BI.* (brak CDN.*) | Bot + Power BI + Excel |

**Zasady projektowania widoków:**
- Nazwy widoków: rzeczowniki w liczbie mnogiej (`Towary`, `Zamowienia`)
- Nazwy kolumn: opisowe, PascalCase (`NazwaKontrahenta`, `DataZamowienia`)
- Każdy widok ma kolumnę `ID` jako klucz (umożliwia relacje w Power BI)
- Widoki nie zawierają logiki filtrowania — zwracają pełne zbiory danych
- Definicje w `solutions/bi/views/*.sql`, wersjonowane w Git

---

## 6. Katalog BI views

**Format:** `solutions/bi/catalog.json` — jeden wpis per widok.

```json
{
  "views": [
    {
      "name": "BI.Zamowienia",
      "description": "Zamówienia sprzedaży z danymi kontrahenta i pozycjami",
      "columns": ["ID", "NumerZamowienia", "DataZamowienia", "NazwaKontrahenta", ...],
      "example_questions": ["kto zamawiał X", "zamówienia z tego miesiąca", ...]
    }
  ]
}
```

**Wyszukiwanie:** `tools/search_bi.py` — FTS5 (sqlite3) gdy katalog > 20 widoków,
prosta iteracja JSON dla mniejszych katalogów.

---

## 7. Biblioteka raportów

**Format:** pliki `.sql` w `solutions/bi/reports/` — jeden plik per raport.

Nagłówek pliku (komentarz SQL):
```sql
-- name: ostatnie_zamowienia_kontrahenta
-- description: Ostatnie N zamówień wskazanego kontrahenta
-- example_questions: kto zamawiał X, ostatnie zamówienia od X
-- params: kontrahent:string, limit:int=10
SELECT TOP ??limit ...
FROM BI.Zamowienia
WHERE NazwaKontrahenta LIKE '%' + ??kontrahent + '%'
ORDER BY DataZamowienia DESC
```

**Dopasowanie pytania do raportu:** Claude API — prompt z pytaniem i listą
`name + example_questions` wszystkich raportów. Tani call (mało tokenów).

---

## 8. Power BI i Excel

**Brak dodatkowych komponentów** — Power BI i Excel łączą się bezpośrednio
z SQL Serverem przez istniejącą infrastrukturę.

**Power BI:**
- Połączenie: `Get Data → SQL Server → serwer\instancja → schema BI`
- Tryb: DirectQuery (dane zawsze aktualne, bez schedulowania odświeżania)
- Konto: `CEiM_BI` (read-only na BI.*)

**Excel:**
- Połączenie: `Data → Get Data → From Database → SQL Server`
- Lub przez ODBC Data Source (dla użytkowników bez Power Query)
- Konto: `CEiM_BI`

**Dla użytkowników Power BI:** semantyczne nazwy kolumn eliminują potrzebę
transformacji w Power Query — tabele są gotowe do użycia od razu.

---

*Dokument przygotowany: 2026-03-03*
