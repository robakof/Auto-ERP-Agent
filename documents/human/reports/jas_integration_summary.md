# Podsumowanie projektu: Integracja JAS FBG

Data: 2026-03-24
Rola: Developer
Status: **Produkcja — działa**

---

## Co robi projekt

Automatycznie wysyła zlecenia spedycyjne do JAS FBG na podstawie wystawionych dokumentów WZ z systemu ERP Comarch XL.

**Flow:**
```
ERP (SQL Server) → AILO.wz_jas_export (widok SQL) → jas_export.py → JAS API (REST/OAuth2) → zlecenie spedycyjne
```

Użytkownik uruchamia:
```
python tools/jas_export.py --today
```

Narzędzie:
1. Pobiera wszystkie WZ z `data_realizacji_zs = dzisiaj` z widoku ERP
2. Pomija WZ już wcześniej wysłane (SQLite tracking)
3. Buduje payload JAS (grupuje palety per WZ)
4. Wysyła przez JAS Gateway API
5. Zapisuje wynik (jas_id, status) w lokalnej bazie jas.db

---

## Co zbudowaliśmy — szczegółowo

### Warstwa ERP (SQL)
**`solutions/jas/wz_jas_export.sql`** — widok `AILO.wz_jas_export`
- Autor: ERP Specialist (poprzednia sesja)
- Jeden wiersz = jeden typ palety na WZ
- Kolumny: numer_wz, daty, adres odbiorcy, typ_opakowania, wymiary, waga, wz_id
- Magazyny bez WMS (np. mag 5) → typ_opakowania = NULL, pomijane w cargo

**`solutions/jas/wz_jas_pending.sql`** — zapytanie SELECT z `{where_clause}`
- Parametryzowane przez Python (filtr po wz_id, numer lub data)

### Warstwa Python

**`tools/jas_client.py`** — klient HTTP JAS API
- OAuth2 Resource Owner Password (token cache'owany do wygaśnięcia)
- `create_shipment(payload)` → POST `/domestic-groupage-shipment/create`
- `get_shipment(id)` → GET `/domestic-groupage-shipment/{id}`

**`tools/jas_mapper.py`** — mapowanie ERP → JAS payload
- `rows_to_shipment(rows)` → `{"request": {"shipment": {...}, "cargo": [...]}}`
- Mapowanie typów opakowań:
  | ERP | JAS | Opis |
  |---|---|---|
  | `Paleta` | `EFN` | Paleta zwykła/jednorazowa (120×80, nie EPAL) |
  | `Paleta-EPAL` | `EPN` | Paleta EPAL (120×80) |
  | `Paleta-INNA` | `PPN` | Paleta inna (wymiary inne niż 120×80) |
- Pola wymagane przez JAS: `declaredValue=0`, `returnablePackaging=false`, `pickupDate=today`, `cod`, `notifications`, `payer`, `flatNo`, `contact`, `barcode="12"`, `sscc="12"`, `dangerousGoods=[]`

**`tools/lib/jas_db.py`** — tracking wysłanych WZ (SQLite)
- Baza: `jas.db` (lokalny plik, w .gitignore)
- Tabela: `jas_shipments(id, wz_id, numer_wz, jas_id, status, error_msg, sent_at)`
- `already_sent(wz_id)` → bool — blokuje duplikaty
- `record_result(wz_id, numer_wz, jas_id, error_msg)` → zapisuje wynik
- Decyzja architektoniczna: SQLite zamiast SQL Server — brak uprawnień CREATE TABLE w schemacie AILO (widoki) i CEiM_Reader (read-only)

**`tools/jas_export.py`** — główne CLI
- `--today` — WZ na dzisiaj (główny tryb produkcyjny)
- `--all` — wszystkie WZ z widoku
- `--all --date YYYY-MM-DD` — WZ na konkretny dzień
- `--wz-id ID` — jedna WZ po ID
- `--numer NR` — jedna WZ po numerze
- `--dry-run` — podgląd payload bez wysyłania
- Idempotentne: wielokrotne uruchomienie bezpieczne

### Dokumentacja referencyjna
- `documents/Wzory plików/Dokumentacja_ShipmentGatewayAPIv1.1.pdf` — pełna spec JAS Gateway API
- `documents/Wzory plików/sampleBodyGateway3.json` — przykładowy request JSON
- `documents/Wzory plików/sampleBodyGateway3.xml` — przykładowy request XML
- `solutions/jas/create_jas_shipments.sql` — DDL tracking (dokumentacja; nie wykonywany — zastąpiony przez SQLite)

---

## Problemy napotkane i rozwiązania

| Problem | Rozwiązanie |
|---|---|
| HTTP 500 od JAS | Brak wrappera `{"request": {...}}` — dodany |
| Błędy walidacji 400 | 15 brakujących wymaganych pól — uzupełnione |
| `PickupDate` z przeszłości | Dodano `pickupDate = today` w mapperze |
| `jas_id = None` | Response ma strukturę `shipment.id`, nie `id` — poprawione |
| Zniekształcone polskie znaki | `sys.stdout.reconfigure(encoding="utf-8")` na start `main()` |
| Brak filtra po dacie | Dodano `--date` i `--today` do CLI |
| Tracking w SQL Server niemożliwy | Brak uprawnień → SQLite (`jas.db`) |

---

## Jak uruchamiać

**Codziennie (przed cut-off JAS 12:00):**
```
python tools/jas_export.py --today
```

**Podgląd co zostanie wysłane:**
```
python tools/jas_export.py --today --dry-run
```

**Konkretny dzień:**
```
python tools/jas_export.py --all --date 2026-03-25
```

**Docelowa automatyzacja — decyzja otwarta (patrz niżej)**

---

## Stan jas.db po sesji

Wysłane zlecenia (status=sent):
- WZ-195/03/26/SPKR → jas_id=77309 (ROMEN Wolsztyn, 1x PPN)
- WZ-210/03/26/SPKR → jas_id=None (wysłana przed fixem response — ID niezapisane)

---

## Co pozostaje

- [ ] **DECYZJA: mechanizm automatyzacji** — patrz sekcja poniżej
- [ ] WZ-210: jas_id=None w DB — brak ID w tracking (wysłana przed fixem; nie blokuje działania)

---

## Decyzja: automatyzacja triggerowania

**Kontekst:** cut-off JAS 12:00. Na razie uruchamianie ręczne przez użytkownika.

### Opcja A — pętla polling (`--watch`)

`jas_export.py` działa jako długożyjący proces (np. uruchomiony raz rano).
Sprawdza nowe WZ co 30 minut w pętli `while True / sleep(1800)`.

```
python tools/jas_export.py --watch   # uruchom raz, działa do 12:00
```

**Zalety:** prosty, niezależny od ERP, gotowy do zbudowania od razu.
**Wady:** wymaga żeby proces był uruchomiony; max opóźnienie 30 min.

### Opcja B — trigger z Comarch XL

Nowe WZ w ERP wywołuje skrypt natychmiast (czas reakcji: sekundy).

Możliwe mechanizmy: SQL Server Agent job, makro XL, XL Runner, webhook.

**Zalety:** zdarzeniowy, brak opóźnienia, brak procesu-strażnika.
**Wady:** wymaga weryfikacji możliwości Comarch XL w bieżącej instalacji — zakres ERP Specialist.

### Do zrobienia przed decyzją

- [ ] Użytkownik weryfikuje czy Comarch XL obsługuje uruchamianie zewnętrznych skryptów przy tworzeniu dokumentów WZ (makra, XL Runner, inne mechanizmy automatyzacji)
- [ ] Po weryfikacji: wybrać opcję A lub B i zgłosić do Developera
