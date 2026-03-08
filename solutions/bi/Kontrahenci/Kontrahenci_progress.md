## Status: Faza 2 — Brudnopis SQL gotowy (151 kolumn), BLOKADA: Knt_EFaVatDataDo sentinel

**Tabela główna:** CDN.KntKarty
**Filtr techniczny:** brak (pełny zbiór)
**Baseline:** COUNT(*) = 4530, COUNT(DISTINCT Knt_GIDNumer) = 4530 ✓

---

## Enumeracje rozkodowane

| Pole | Wartości | Źródło |
|---|---|---|
| Knt_GIDTyp | 32=Kontrahent (stała — pominięte) | CDN.Obiekty |
| Knt_Typ | 8=Dostawca, 16=Odbiorca, 24=Dostawco-Odbiorca, 0=Nieokreślono | dokumentacja |
| Knt_Status | 0=Nieokreślono, 1=Podmiot gospodarczy, 2=Odbiorca finalny | dokumentacja |
| Knt_Archiwalny | 0=Nie (2064), 1=Tak (2466) | baza |
| Knt_Dewizowe | 0=Nie (4527), 1=Tak (3) | baza |
| Knt_PlatnikVat | 0=Nie (2512), 1=Tak (2018) | baza |
| Knt_Akwizytor | 0=Nie, 1=Tak | dokumentacja |
| Knt_ExpoKraj | 1=krajowy, 2=z UE, 3=spoza UE | dokumentacja |
| Knt_LimitTerminowy | 0=nieograniczony, 1=ograniczony | dokumentacja |
| Knt_StanPostep | 0=brak, 1=w trakcie postępowania | dokumentacja |
| Knt_EFaVatAktywne | 0=Nie, 1=Tak | dokumentacja |
| Knt_Nieaktywny | zawsze 0 → pominięte | baza |
| Knt_Zrodlo | zawsze 0 → pominięte | baza |
| Knt_LimitWart | "Nie wykorzystane" wg dok. → pominięte | dokumentacja |
| Knt_KrajSiedziby | "Pole nie jest obsługiwane" → pominięte | dokumentacja |

---

## Typy dat — CZĘŚCIOWO NIEZNANE

### Potwierdzone — Clarion DATE (DATEADD(d, col, '18001228'))

| Pole | Min–Max | Wynik konwersji |
|---|---|---|
| Knt_LastModL | 1047823554–1141724389 | Clarion TIMESTAMP (DATEADD(ss, col, '1990-01-01')) |
| Knt_VatDataRejestracji | 70316–82184 | Clarion DATE ✓ |
| Knt_DataOdLoj | 81239–81239 | Clarion DATE ✓ |
| Knt_DataWydania | 81112–82156 | Clarion DATE ✓ |

### Nieznane / do wyjaśnienia — BLOKUJE BUDOWĘ SQL

| Pole | Min–Max | Uwaga |
|---|---|---|
| Knt_EFaVatDataDo | 81169–**150483** | 150483 wykracza poza typowy Clarion DATE (~70k–100k) |
| Knt_DataKarty | brak danych (0 rek. > 0) | nie można określić |
| Knt_FAVATData | brak danych (0 rek. > 0) | nie można określić |
| Knt_DataDoLoj | nie sprawdzono | — |
| Knt_DataPromocji | nie sprawdzono | opis: "wg daty: 1=Wystawienia, 2=Realizacji" (może flaga, nie data) |
| Knt_VatDataPrzywrocenia | nie sprawdzono | — |
| Knt_VatDataOdmowy | nie sprawdzono | — |
| Knt_VatDataUsuniecia | nie sprawdzono | — |

**Kluczowe pytanie:** wartość 150483 w Knt_EFaVatDataDo — czy to:
- Clarion DATE dalekiej przyszłości (np. sentinel "bez daty wygaśnięcia")?
- Inny format daty używany przez Comarch XL?
- Błąd w danych?

Odpowiedź z web research oczekiwana — patrz plik `Kontrahenci_date_research_prompt.md`.

---

## JOINy ustalone (każdy 4530/4530 ✓)

| JOIN | Klucz | Dane |
|---|---|---|
| CDN.OpeKarty o | o.Ope_GIDNumer = k.Knt_OpeNumer AND k.Knt_OpeNumer > 0 | Ope_Ident, Ope_Nazwisko (LEFT) |
| CDN.FrmStruktura frs | frs.FRS_ID = k.Knt_FrsID AND k.Knt_FrsID > 0 | FRS_Nazwa (LEFT) |

**Ważne rozróżnienia:**
- Knt_OpeNumer = operator zakładający kartę (NIE opiekun — opiekun jest w CDN.KntOpiekun)
- Knt_KnGNumer = GIDNumer kontrahenta-rodzica (self-join CDN.KntKarty, NIE ID grupy z KntGrupy)
- CDN.KntGrupy = bridge table przynależności do grup (KnG_GIDTyp=32 → membership, KnG_GIDTyp=-32 → definicja grupy)

---

## Pola wykluczone (potwierdzone)

- Knt_GIDTyp, Knt_GIDFirma, Knt_GIDLp — stałe techniczne
- Knt_Nieaktywny, Knt_Zrodlo — zawsze 0
- Knt_LimitWart — nieużywane wg dokumentacji
- Knt_DataW, Knt_DataUtworzenia — wszystkie NULL/0 w bazie
- Knt_KrajSiedziby — nieobsługiwane wg dokumentacji
- Knt_PrcTyp/Firma/Numer/Lp — nieobsługiwane (opiekun w CDN.KntOpiekun)
- Knt_Aktywna — nieużywane wg dokumentacji
- Knt_HasloChk, Knt_HasloKontrahent, Knt_PIN — dane wrażliwe
- Knt_Soundex, Knt_AkronimFormat, Knt_Wsk, Knt_OutlookUrl — techniczne/przestarzałe
- Knt_GUIDdane — duplikat GUID

---

## Odkrycia infrastrukturalne (sesja 2026-03-08)

**Bug docs_search naprawiony:** `docs_search "" --table CDN.X` zwracał [] bo pusta fraza
powodowała early return przed wykonaniem zapytania do bazy.
Naprawiono w `tools/docs_search.py` — dodano `_execute_table_scan` dla trybu phrase="" + table_filter.
Commit: `04344ce`. Testy: 19/19 ✓.

`docs.db` w katalogu głównym = pusty plik (0 bajtów, artefakt).
Właściwa baza: `erp_docs/index/docs.db` (7 MB, 214 kolumn CDN.KntKarty z opisami i sample_values).

---

## Pliki

- Brudnopis: `solutions/bi/Kontrahenci/Kontrahenci_draft.sql`
- Plan: `solutions/bi/Kontrahenci/Kontrahenci_plan.xlsx` (211 wierszy, opisy + sample_values z docs.db, komentarze usera)
- Prompt do researchu: `solutions/bi/Kontrahenci/Kontrahenci_date_research_prompt.md`
- Progress: `solutions/bi/Kontrahenci/Kontrahenci_progress.md`

---

## Faza 2 — Brudnopis SQL (2026-03-08)

**Plik:** `solutions/bi/Kontrahenci/Kontrahenci_draft.sql`
**Eksport:** `solutions/bi/Kontrahenci/Kontrahenci_export.xlsx`
**Wynik:** 4530 wierszy ✓, 151 kolumn ✓

**JOINy w brudnopisie:**
- CDN.KntAdresy a — adres powiązany (KnA_GIDNumer = Knt_KnANumer)
- CDN.Banki bnk — bank (Bnk_GIDNumer = Knt_BnkNumer)
- CDN.OpeKarty o — operator zakładający (Ope_GIDNumer = Knt_OpeNumer)
- CDN.OpeKarty om — operator modyfikujący (Ope_GIDNumer = Knt_OpeNumerM)
- CDN.FrmStruktura frs — firma handlowa (FRS_ID = Knt_FrsID)
- CDN.KntKarty akw — akwizytor self-join (Knt_GIDNumer = Knt_AkwNumer)
- CDN.KntKarty plat — płatnik self-join (Knt_GIDNumer = Knt_KnPNumer)
- CDN.Rejestry rej — rejestr kasowy (KAR_GIDNumer = Knt_KarNumer)
- CDN.KntGrupy kg — grupa (KnG_GIDNumer = Knt_KnGNumer WHERE KnG_GIDTyp=-32)

**Formy płatności:** CASE z kodami 0/10/20/50/100 (brak tabeli słownikowej w DB)
**Daty potwierdzone Clarion DATE:** VatDataRejestracji/Przywrocenia/Usuniecia, DataOdLoj, DataDoLoj, DataWydania
**Daty potwierdzone Clarion TIMESTAMP:** LastModL/O/C
**TODO:** Knt_EFaVatDataDo — wartość 150483 → CASE WHEN > 100000 THEN NULL (sentinel do weryfikacji)

**Pola puste (0 rek.) → pominięte:** FaVATOsw, MSTwrGrupaNumer, PodzialPlat, VatWalSys, ZTrNumer, OpZNumer, LastTransLockDate, FAVATData, DataKarty
**Knt_DataPromocji:** to flaga (1=Wystawienia, 2=Realizacji), nie data

---

## Faza 2 — Rewizja draftu (2026-03-08, sesja 2)

**BLOKADA: sql_client.py odrzuca WITH CTE** — walidator sprawdza `startswith("SELECT")` (sql_client.py:81). Rozwiązanie: poprawić walidator aby akceptował `WITH ... SELECT` lub przepisać CTE jako podzapytanie.

**Zmiany w tej sesji:**
- Pełny rewrite draftu: czytelne nazwy kolumn (usunięto skróty _Loj, _Spr, _Zak, _Ka, _Mod, _Zal, EFaVat_, FK)
- Dodano WITH CTE `Sciezka_Grup` — rekurencja po CDN.KntGrupy (KnG_GIDTyp=-32), ścieżka bez korzenia "Grupa Główna"
- Nowy JOIN: CDN.TwrCenyNag (tcn) → Nazwa_Cennika_Sprzedazy (MIN(TCN_Nazwa) GROUP BY TCN_RodzajCeny)
- Nowy JOIN: CDN.Slowniki (slw) → Rodzaj_Kontrahenta (SLW_WartoscS gdzie SLW_ID=Knt_Rodzaj)
- Knt_TypDok: CASE 0=Brak, 2033=Faktura sprzedaży, 2034=Paragon
- Knt_Dzialalnosc: pełny CASE (0–9) z dokumentacji
- Knt_ExpoKraj: CASE 1=Krajowy, 2=Z UE, 3=Spoza UE
- Knt_LimitTerminowy: CASE 0=Nieograniczony, 1=Ograniczony
- Knt_Rodzaj 800=Kontrahent (z Slowniki), 0=NULL
- Usunięto duplikat Knt_Dewizowe (zostaje CASE)
- Błąd w drafcie: `k.Knt_KnGNumer AS ID_Rodzaju_Kontrahenta` — POWINNO BYĆ `k.Knt_Rodzaj AS ID_Rodzaju_Kontrahenta` — DO POPRAWY

**Odkrycia o cennikach (CDN.TwrCenyNag):**
- Knt_Cena = TCN_RodzajCeny (nie TCN_Id)
- Wartości: 1=CENA 100, 2=CMENTARZ, 3=FRANOWO, 4=BRICO, 5=INTER, 6=mrówka, 7=CHATA POLSKA, 8=AT, 9=PRYZMAT
- Wiele rekordów per TCN_RodzajCeny → używamy MIN(TCN_Nazwa) GROUP BY

**Struktura grup KntGrupy (KnG_GIDTyp=-32):**
- Korzeń: GIDNumer=0, GrONumer=-1, Akronim="Grupa Główna"
- Poziom 1 (GrONumer=0): 01.KLIENCI(5), 02.DOSTAWCY(11), 03.HANDLOWCY(2319), 04.AKWIZYTORZY(18)
- 01.KLIENCI ma dzieci: 01.DETAL(9), 02.DETAL+(2), 03.HURT(3), 04.CENTRALA(6), 05.BRICO(4), etc.
- CTE startuje od GrONumer=0 (pomija "Grupa Główna")
- 13 rekordów Knt_KnGNumer=0 → brak przypisania do grupy → NULL w Sciezka_Grupy

**Następny krok (priorytet):**
1. Poprawić sql_client.py: zmienić walidację aby akceptowała WITH...SELECT (lub zmienić CTE na podzapytanie inline)
2. Naprawić błąd: `k.Knt_KnGNumer` → `k.Knt_Rodzaj` w sekcji ATRYBUTY CRM
3. Przetestować pełny draft (4530 wierszy)
4. Eksport excel_export_bi.py + weryfikacja statystyk
5. CREATE OR ALTER VIEW BI.Kontrahenci
