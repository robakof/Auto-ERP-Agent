# Audyt istniejących widoków BI pod kątem konwencji

Data: 2026-03-12
Analityk: pierwsza sesja (audyt rozruchowy)
Źródła: solutions/bi/views/{KntKarty,Rezerwacje,ZamNag,Rozrachunki}.sql

Legenda:
  [KONWENCJA] — naruszenie reguły, wymaga rozstrzygnięcia
  [INFO]      — zgodne z konwencją lub neutralne, dla potwierdzenia
  [PYTANIE]   — nie wiem jak ocenić, wymaga odpowiedzi ERP Specialist lub Developera

---

## AIBI.KntKarty

[INFO] K01 — GIDFirma nieobecna w SELECT. Poprawnie.
[INFO] K03 — ID_Kontrahenta = Knt_GIDNumer. Poprawnie.
[INFO] K04 — GIDLp nieobecny. Poprawnie.
[INFO] K05 — Wszystkie flagi 0/1 przetłumaczone przez CASE z 'Tak'/'Nie'. Poprawnie.
[INFO] K06 — Wszystkie CASE mają ELSE z surową wartością. Poprawnie.
[INFO] K07 — Knt_TypDok: 'Faktura sprzedaży', 'Paragon' — pełne nazwy. Poprawnie.
[INFO] K09 — Clarion DATE: VatData*, DataOdLoj, DataDoLoj — DATEADD(d, col, '18001228'). Poprawnie.
[INFO] K10 — Clarion TIMESTAMP: LastModL/O/C — DATEADD(ss, col, '1990-01-01'). Poprawnie.
[INFO] K11 — EFaVatDataDo: BETWEEN 1 AND 109211 → NULL dla sentineli. Poprawnie (zgodne z ERP_SCHEMA_PATTERNS.md).
[INFO] K16 — Schemat AIBI. Poprawnie.
[INFO] K21 — Nie dotyczy (brak CDN.Rozrachunki). N/A.
[INFO] K22 — Nie dotyczy (brak CDN.TraNag). N/A.
[INFO] K23 — Nie dotyczy (brak CDN.TraNag). N/A.

[PYTANIE] K09-sentinel — VatDataRejestracji, VatDataPrzywrocenia, VatDataOdmowy, VatDataUsuniecia:
  wzorzec BETWEEN 1 AND 200000 (nie 109211 jak w ERP_SCHEMA_PATTERNS.md).
  Czy zakres 200000 był świadomy? EFaVatDataDo używa 109211 w tym samym widoku — niespójność.

[PYTANIE] K08 — Knt_TypDokZZ (ID_Typu_Dokumentu_Z_Zamowienia_Zakupu): raw ID bez JOIN i bez CASE.
  Czy ta enumeracja jest niezdefiniowana i dlatego zostawiona jako ID? Potwierdzenie z ERP Specialist.

[PYTANIE] K19 — JOINy na CDN.KntKarty (self-join dla akwizytora, płatnika):
  używają tylko jednego klucza (Knt_GIDNumer). Brak drugiego klucza GIDTyp.
  W KntKarty self-join GIDTyp jest stały — czy to wystarczające uzasadnienie pominięcia?

[PYTANIE] K08 — Knt_DataUtworzenia (linia 256): przekazana bez konwersji (AS Data_Utworzenia).
  Czy to SQL DATE (nie Clarion integer)? Jeśli tak — poprawnie. Wymaga potwierdzenia.

---

## AIBI.Rezerwacje

[INFO] K01 — GIDFirma nieobecna. Poprawnie.
[INFO] K02 — Rez_GIDTyp przetłumaczony przez CASE. Poprawnie.
[INFO] K03 — ID_Rezerwacji = Rez_GIDNumer. Poprawnie.
[INFO] K04 — GIDLp nieobecny. Poprawnie.
[INFO] K05 — Rez_Aktywna, Rez_Typ, Rez_Zrodlo — CASE z etykietami i ELSE. Poprawnie.
[INFO] K06 — Wszystkie CASE mają ELSE z surową wartością. Poprawnie.
[INFO] K07 — Typ_Dok_Zrodlowego: pełne nazwy PL. Numery dokumentów używają skrótów jako składnik numeru — poprawne. Poprawnie.
[INFO] K08 — Klucze obce: TwrKarty, KntKarty, OpeKarty, Magazyny, FrmStruktura, Dostawy, ZamNag, ProdZasoby/Zlecenia — wszystkie mają JOIN + kod/nazwa + ID. Poprawnie.
[INFO] K09/K10 — Konwersje dat poprawne: DATE (DataRealizacji, Waznosci, Aktywacji, PotwDst) i TIMESTAMP (TStamp, DataRezerwacji). Poprawnie.
[INFO] K14 — WHERE Rez_TwrNumer > 0 — filtr techniczny. Poprawnie.
[INFO] K16 — Schemat AIBI. Poprawnie.
[INFO] K22 — Brak bezpośredniego prefiksu TraNag (Dostawy to PZ/FZ/PW — nie korekty). N/A.
[INFO] K23 — TrN_TypNumeracji nie używane. Poprawnie.

[KONWENCJA] K19 — JOIN CDN.KntKarty (linia 144):
  ON k.Knt_GIDNumer = r.Rez_KntNumer AND r.Rez_KntNumer > 0
  Brak drugiego klucza: AND k.Knt_GIDTyp = r.Rez_KntTyp
  ERP_SCHEMA_PATTERNS.md wprost: JOIN kontrahenta wymaga dwuczęściowego klucza.
  Rez_KntTyp istnieje w CDN.Rezerwacje. Poprawka: dodać AND k.Knt_GIDTyp = r.Rez_KntTyp.

[PYTANIE] Numer_Dok_Zrodlowego dla Rez_ZrdTyp = 2592:
  zwraca placeholder '<do uzupelnienia>'. Czy to świadomy dług techniczny czy przeoczone?
  Wymaga decyzji ERP Specialist — czy numeracja dla Rezerwacji u dostawcy jest znana.

---

## AIBI.ZamNag

[INFO] K01 — GIDFirma nieobecna. Poprawnie.
[INFO] K02 — ZaN_GIDTyp = 960 zawsze → pomięty. ZaN_ZamTyp używany do rozróżnienia. Poprawnie.
[INFO] K03 — ID_Zamowienia = ZaN_GIDNumer. Poprawnie.
[INFO] K04 — GIDLp nieobecny. Poprawnie.
[INFO] K05 — ZaN_RealWCalosci, ZaN_RezerwacjeNaNiepotwierdzonym, ZaN_WspolnaWaluta — CASE Tak/Nie/Nieznane. Poprawnie.
[INFO] K06 — Wszystkie CASE mają ELSE z surową wartością. Poprawnie.
[INFO] K07 — Typ_Zamowienia: 'Oferta zakupu', 'Zamówienie zakupu' itd. — pełne nazwy PL. Poprawnie.
[INFO] K08 — Klucze obce: KntKarty, KntAdresy, Magazyny, OpeKarty, FrmStruktura, PrcKarty, Rejestry, TwrCenyNag, Slowniki — wszystkie z JOIN + opis + ID. Poprawnie.
[INFO] K09/K10 — Konwersje dat poprawne (DATE + TIMESTAMP). Poprawnie.
[INFO] K14 — Brak WHERE (zwraca pełny zbiór CDN.ZamNag). Poprawnie.
[INFO] K16 — Schemat AIBI. Poprawnie.
[INFO] K22 — Nie dotyczy (brak CDN.TraNag). N/A.
[INFO] K23 — TrN_TypNumeracji nie używane. N/A.

[KONWENCJA] K24 — Kolumna Typ_GID (linia 8):
  'Zamówienie' — stała wartość dla całej tabeli CDN.ZamNag.
  Wg K24: pominąć gdy COUNT DISTINCT = 1. Kolumna nie wnosi informacji, powinna być usunięta.

[PYTANIE] K19 — JOINy na CDN.KntKarty (kontrahent, odbiorca, płatnik, akwizytor):
  używają tylko Knt_GIDNumer bez GIDTyp. Analogicznie jak KntKarty self-join.
  Czy uzasadnione (GIDTyp stały dla KntKarty)?

[PYTANIE] Typ_Dokumentu_Zrodlowego (linia 77):
  stała wartość 'Zamówienie' niezależnie od faktycznego ZaN_ZrdNumer.
  Czy self-join ZamNag → ZamNag zawsze wychodzi na zamówienie? Jeśli tak — informacja
  redundantna (jak Typ_GID). Jeśli nie — wymaga CASE. Potwierdzenie z ERP Specialist.

[PYTANIE] ZaN_DokZwiazane (Dok_Zwiazane_Bitmask):
  przekazana jako surowa bitmaska bez tłumaczenia.
  Czy definicja bitów jest dostępna? Jeśli tak — powinien być CASE lub osobne kolumny bool.
  Jeśli brak dokumentacji — akceptowalne zostawienie jako ID.

---

## AIBI.Rozrachunki

[INFO] K03 — ID_Rozliczenia = ROZ_GIDNumer. Poprawnie.
[INFO] K04 — ROZ_GIDLp w WHERE (= 1), nie w SELECT. Poprawnie.
[INFO] K05 — ROZ_RKStrona: CASE 'Brak'/'Winien'/'Ma'. Poprawnie.
[INFO] K06 — Wszystkie CASE mają ELSE z surową wartością. Poprawnie.
[INFO] K07 — Typ_Dok1, Typ_Dok2: pełne nazwy PL. Poprawnie.
[INFO] K08 — ROZ_OpeNumerRL → JOIN CDN.OpeKarty → Ident, Nazwisko. Poprawnie.
[INFO] K14 — WHERE ROZ_GIDLp = 1 — filtr techniczny. Poprawnie.
[INFO] K16 — Schemat AIBI. Poprawnie.
[INFO] K21 — WHERE ROZ_GIDLp = 1. Poprawnie.
[INFO] K23 — TrN_TypNumeracji nie używane. Poprawnie.

[KONWENCJA] K01 — ROZ_GIDFirma obecna w SELECT jako ID_Firma.
  Wg K01: GIDFirma pomijamy. Jest to jedyny widok gdzie GIDFirma jest w kolumnach.
  Możliwe uzasadnienie: rozrachunki mogą być wielofirmowe i GIDFirma niesie sens biznesowy.
  Do rozstrzygnięcia z ERP Specialist: czy GIDFirma w Rozrachunkach jest stała czy zmienna?

[KONWENCJA] K22 — Prefiks TraNag używa starej heurystyki (linie 35-41, 90-96):
  WHEN TrN_Stan & 2 = 2 AND TrN_GIDTyp IN (2041,1529,2042,2045) THEN '(Z)'
  Brak warunku EXISTS (spinacz) jako pierwszego kroku.
  Prawidłowa kolejność: EXISTS spinacz → Stan&2 fallback → GenDokMag.
  ZNANY DŁUG TECHNICZNY — wymieniony w developer_notes.md i ERP_SCHEMA_PATTERNS.md.
  Wymaga aktualizacji przez ERP Specialist.

[PYTANIE] K09 — ROZ_DataRozliczenia:
  DATEADD(d, col, '18001228') bez CAST AS DATE — zwraca DATETIME.
  Inne widoki castują do DATE. Czy dla Rozrachunki DATETIME jest zamierzony?

[PYTANIE] Data_Podejrzana (linie 147-148):
  CASE WHEN ROZ_DataRozliczenia > 84000 THEN 'Tak' ELSE 'Nie' END
  Liczba 84000 bez komentarza. Co oznacza ta granica?
  84000 dni od 1800-12-28 = ok. 2031-01-01. Czy to sentinel dla dat przyszłych?
  Wymaga wyjaśnienia od ERP Specialist lub Developera.

[PYTANIE] K15 — ID_Operator (linia 129):
  Inne widoki używają ID_Operatora_X (z przyrostkiem). Tu brak przyrostka.
  Drobna niespójność stylistyczna — czy świadoma (jeden operator, brak rozróżnienia)?

---

## Podsumowanie odchyleń

### [KONWENCJA] — wymagają rozstrzygnięcia (4)

| # | Widok | Reguła | Opis |
|---|---|---|---|
| 1 | Rezerwacje | K19 | JOIN KntKarty bez drugiego klucza (GIDTyp) |
| 2 | ZamNag | K24 | Kolumna Typ_GID = stała 'Zamówienie' — powinna być pominięta |
| 3 | Rozrachunki | K01 | ROZ_GIDFirma w SELECT (jedyny widok łamiący tę regułę) |
| 4 | Rozrachunki | K22 | Stara heurystyka prefiksu (Z) — znany dług techniczny |

### [PYTANIE] — wymagają odpowiedzi (9)

| # | Widok | Opis |
|---|---|---|
| 1 | KntKarty | VatData*: BETWEEN 1 AND 200000 zamiast 109211 (niespójność z EFaVatDataDo) |
| 2 | KntKarty | Knt_TypDokZZ: raw ID bez JOIN/CASE — czy enumeracja niezdefiniowana? |
| 3 | KntKarty | JOINy self-join: brak GIDTyp — uzasadnione przez stałość GIDTyp? |
| 4 | KntKarty | Knt_DataUtworzenia bez konwersji — czy SQL DATE? |
| 5 | Rezerwacje | Numer_Dok_Zrodlowego dla Rez_ZrdTyp=2592: placeholder |
| 6 | ZamNag | JOINy KntKarty: brak GIDTyp — uzasadnione? |
| 7 | ZamNag | Typ_Dokumentu_Zrodlowego: stała 'Zamówienie' — redundantne? |
| 8 | ZamNag | Dok_Zwiazane_Bitmask: czy definicja bitów dostępna? |
| 9 | Rozrachunki | Data_Podejrzana: granica 84000 bez wyjaśnienia |
| 10 | Rozrachunki | ROZ_DataRozliczenia: DATETIME zamiast DATE — zamierzone? |
| 11 | Rozrachunki | ID_Operator bez przyrostka — świadoma niespójność? |
