# Handoff: Analityk → ERP Specialist
Data: 2026-03-12
Dotyczy: audyt konwencji istniejących widoków BI

Źródło pełnego audytu: `solutions/analyst/konwencje/audyt_istniejacych.md`

---

## Do naprawy — potwierdzone naruszenia konwencji (3)

### FIX-1 | Rozrachunki.sql | Prefiks (Z): stara heurystyka

**Problem:** Prefiks dokumentu używa wyłącznie `TrN_Stan & 2 = 2` zamiast EXISTS (spinacz).
Brakuje warunku EXISTS jako pierwszego kroku w CASE.

**Gdzie:** linie 35–41 i 90–96 (identyczna logika dla trn1 i trn2)

**Obecny kod:**
```sql
WHEN trn1.TrN_Stan & 2 = 2
     AND trn1.TrN_GIDTyp IN (2041,1529,2042,2045) THEN '(Z)'
WHEN trn1.TrN_GenDokMag = -1
     AND trn1.TrN_GIDTyp IN (1521,1529,1489)      THEN '(A)'
WHEN trn1.TrN_GenDokMag = -1                       THEN '(s)'
ELSE ''
```

**Prawidłowy kod** (z developer_notes.md + ERP_SCHEMA_PATTERNS.md):
```sql
WHEN trn1.TrN_GIDTyp IN (2041, 2045, 1529)
     AND EXISTS (
         SELECT 1 FROM CDN.TraNag s
         WHERE s.TrN_SpiTyp   = trn1.TrN_GIDTyp
           AND s.TrN_SpiNumer = trn1.TrN_GIDNumer
           AND (
                (trn1.TrN_GIDTyp = 2041 AND s.TrN_GIDTyp = 2009) OR
                (trn1.TrN_GIDTyp = 2045 AND s.TrN_GIDTyp = 2013) OR
                (trn1.TrN_GIDTyp = 1529 AND s.TrN_GIDTyp = 1497)
           )
     )                                               THEN '(Z)'
WHEN trn1.TrN_Stan & 2 = 2
     AND trn1.TrN_GIDTyp IN (2041, 2045, 1529)      THEN '(Z)'
WHEN trn1.TrN_GenDokMag = -1
     AND trn1.TrN_GIDTyp IN (1521, 1529, 1489)      THEN '(A)'
WHEN trn1.TrN_GenDokMag = -1                        THEN '(s)'
ELSE ''
```

Zastosuj tę samą poprawkę dla trn2 (linie 90–96).

---

### FIX-2 | Rezerwacje.sql | JOIN KntKarty: brakuje drugiego klucza

**Problem:** JOIN na CDN.KntKarty bez warunku `Knt_GIDTyp = Rez_KntTyp`.
ERP_SCHEMA_PATTERNS.md wymaga dwuczęściowego klucza przy JOINie kontrahenta.

**Gdzie:** linia 144

**Obecny kod:**
```sql
LEFT JOIN CDN.KntKarty k ON k.Knt_GIDNumer = r.Rez_KntNumer AND r.Rez_KntNumer > 0
```

**Prawidłowy kod:**
```sql
LEFT JOIN CDN.KntKarty k ON k.Knt_GIDNumer = r.Rez_KntNumer
                         AND k.Knt_GIDTyp   = r.Rez_KntTyp
                         AND r.Rez_KntNumer > 0
```

Przed wdrożeniem: sprawdź `COUNT(*) vs COUNT(DISTINCT Rez_GIDNumer)` — zmiana nie powinna
zmienić liczby wierszy, ale zweryfikuj.

---

### FIX-3 | ZamNag.sql | Kolumna Typ_GID: stała wartość

**Problem:** Kolumna `'Zamówienie' AS Typ_GID` (linia 8) ma stałą wartość dla całej
tabeli CDN.ZamNag. Wg konwencji K24: kolumna ze stałą wartością (COUNT DISTINCT = 1)
powinna być pominięta — nie wnosi informacji, zaśmieca widok.

**Gdzie:** linia 8

**Obecny kod:**
```sql
'Zamówienie' AS Typ_GID,
```

**Poprawka:** usuń tę linię.

---

## Do wyjaśnienia przed decyzją (4)

Poniższe punkty wymagają odpowiedzi ERP Specialist lub decyzji Dawida.
Po wyjaśnieniu wróć z wynikiem do Analityka.

### Q-1 | KntKarty | Zakres sentinel dla dat VAT

Knt_EFaVatDataDo używa `BETWEEN 1 AND 109211` (zgodnie z dokumentacją).
Inne daty VAT (VatDataRejestracji, VatDataPrzywrocenia, VatDataOdmowy, VatDataUsuniecia)
używają `BETWEEN 1 AND 200000` — zakres szerszy bez komentarza.

Pytanie: czy 200000 był świadomy (inne sentinele w tych polach)?
Jeśli nie — ujednolicić do 109211.

### Q-2 | Rozrachunki | ROZ_GIDFirma w SELECT

Kolumna `ROZ_GIDFirma AS ID_Firma` jest w SELECT — jedyny widok gdzie GIDFirma
jest eksponowane. Konwencja mówi: pomijamy.

Pytanie: czy w CDN.Rozrachunki GIDFirma jest zawsze stała (jedna firma)?
Jeśli tak — usunąć. Jeśli baza jest wielofirmowa i to istotna informacja — zostawić
z adnotacją jako wyjątek od konwencji.

### Q-3 | ZamNag | Typ_Dokumentu_Zrodlowego: stała 'Zamówienie'

Kolumna `'Zamówienie' AS Typ_Dokumentu_Zrodlowego` (linia 77) — taka sama sytuacja jak
Typ_GID: stała wartość niezależnie od self-joinu.

Pytanie: czy self-join ZamNag → ZamNag zawsze wskazuje na zamówienie?
Jeśli tak — usunąć (jak FIX-3). Jeśli może wskazywać na inny typ — dodać CASE.

### Q-4 | Rozrachunki | Data_Podejrzana: granica 84000

Linia 147: `CASE WHEN ROZ_DataRozliczenia > 84000 THEN 'Tak' ELSE 'Nie' END`
Liczba 84000 bez komentarza. Brak dokumentacji tej granicy.

Pytanie: co oznacza 84000? Skąd ta wartość?
Dodaj komentarz inline wyjaśniający granicę.

---

## Priorytety

| # | Pilność | Co |
|---|---|---|
| FIX-1 | Wysoka | Rozrachunki: stara heurystyka (Z) — błąd logiczny w produkcji |
| FIX-2 | Średnia | Rezerwacje: brakujący klucz JOIN — potencjalny duplicate risk |
| FIX-3 | Niska | ZamNag: kolumna do usunięcia — estetyczna |
| Q-1–4 | — | Wyjaśnienia przed ewentualną poprawką |
