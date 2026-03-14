## Status: Faza 1 — Plan zatwierdzony, gotowy do SQL

**Tabela główna:** CDN.Rozrachunki, 340 960 rekordów
**Filtr techniczny:** ROZ_GIDLp = 1 → 170 480 wierszy roboczych

**Baseline:** COUNT(*) z GIDLp=1 = 170 480 ✓

---

## Struktura tabeli

Każde rozliczenie = 2 wiersze (GIDLp=1 i GIDLp=2) — lustro z zamienionymi TRP/KAZ i różną walutą.
Widok bierze tylko GIDLp=1.

---

## Typy dokumentów (ROZ_TrpTyp / ROZ_KAZTyp)

```
435  = Różnica kursowa (RK)
784  = Zapis kasowy/bankowy (KB)
1489 = Przyjęcie zewnętrzne (PZ)
1521 = Faktura zakupu (FZ)
1529 = Korekta faktury zakupu (FZK)
2033 = Faktura sprzedaży (FS)
2034 = Paragon (PA)
2037 = Faktura eksportowa (FSE)
2041 = Korekta faktury sprzedaży (FSK)
2042 = Korekta paragonu (PAK)
2045 = Korekta faktury eksportowej (FKE)
2832 = Nota odsetkowa (NO)
4144 = Nota memoriałowa (NM)
```

Rozkład TRP: PA=135027, KB=23695, FS=9963, FSK=852, FZ=461, PAK=201, NM=180, FZK=86, FSE=11, NO=3, FKE=1

---

## JOINy — potwierdzone

| Typ (TrpTyp/KAZTyp) | Tabela | Klucz JOIN | Kolumna numeru |
|---|---|---|---|
| FS/PA/FSE/FSK/PAK/FKE/FZ/FZK/PZ/NO (TraNag typy) | CDN.TraNag | TrN_GIDTyp + TrN_GIDNumer | inline — patrz niżej |
| 784 (KB) | CDN.Zapisy | KAZ_GIDTyp + KAZ_GIDNumer | KAZ_NumerDokumentu (gotowy string) |
| 4144 (NM) | CDN.MemNag | MEN_GIDNumer (180/180 matched) | inline: MEN_Seria/YYYY/MM/MEN_Numer |
| 435 (RK) | CDN.RozniceKursowe | RKN_ID = ROZ_KAZNumer | inline: RK-RKN_Numer/YY |
| Operator | CDN.OpeKarty | Ope_GIDNumer = ROZ_OpeNumerRL | Ope_Ident, Ope_Nazwisko |

---

## Formaty numerów dokumentów — ZWERYFIKOWANE

### TraNag (FS, PA, FSE, FSK, PAK, FKE, FZ, FZK, PZ, NO)

```sql
CASE
    WHEN TrN_Stan & 2 = 2 AND TrN_GIDTyp IN (2041,1529,2042,2045) THEN '(Z)'
    WHEN TrN_GenDokMag = -1 AND TrN_GIDTyp IN (1521,1529,1489)    THEN '(A)'
    WHEN TrN_GenDokMag = -1                                        THEN '(s)'
    ELSE ''
END
+ OB_Skrot + '-'
+ CAST(TrN_TrNNumer AS VARCHAR(20))
+ '/' + RIGHT('0' + CAST(TrN_TrNMiesiac AS VARCHAR(2)), 2)
+ '/' + RIGHT(CAST(TrN_TrNRok AS VARCHAR(4)), 2)
+ CASE WHEN TrN_TrNSeria <> '' THEN '/' + TrN_TrNSeria ELSE '' END
```

Pokrycie: 99.999% (170 478 / 170 480). Znany wyjątek: 1 rekord FSK (GIDNumer=6394119,
FSK-8/01/26/SPKRK) dostaje (Z) z CDN.NazwaObiektu mimo Stan=5 (bit1=0). Nie udało się
ustalić przyczyny — wszystkie pola TraNag identyczne jak sąsiednie (s)FSK.
Prompt dla agenta researchującego: Rozrachunki_researcher_prompt.md

**Prefiksy — znaczenie:**
- (s) = serwisowy / bez dokumentu magazynowego (GenDokMag=-1 dla typów sprzedażowych)
- (A) = anulowany (GenDokMag=-1 dla FZ/FZK/PZ — typy zakupowe)
- (Z) = zwrot (korekty z TrN_Stan & 2 = 2)
- brak = standard (GenDokMag=2)

**PA specyfika:** GenDokMag przyjmuje wartości 0, 1, 2 (nie tylko -1/2) — brak prefiksu dla PA.

### Zapisy (KB, typ 784)

```sql
KAZ_NumerDokumentu  -- gotowy string, np. "PA-1/06/23/FRA"
```

### MemNag (NM, typ 4144)

Format z systemu: `NM-INN/2026/02/2` → schemat: Skrot-Seria/YYYY/MM/Numer

```sql
'NM-' + MEN_Seria
+ '/' + LEFT(CAST(MEN_RokMiesiac AS VARCHAR(6)), 4)
+ '/' + RIGHT('0' + CAST(MEN_RokMiesiac % 100 AS VARCHAR(2)), 2)
+ '/' + CAST(MEN_Numer AS VARCHAR(10))
```
UWAGA: format NM nie był weryfikowany przez CDN.NazwaObiektu — do potwierdzenia.

### RozniceKursowe (RK, typ 435)

Format z systemu: `RK-10/25` → schemat: RK-Numer/YY

```sql
'RK-' + CAST(RKN_Numer AS VARCHAR(10))
+ '/' + RIGHT(CAST(RKN_Rok AS VARCHAR(4)), 2)
```

---

## Stałe (pominięte w widoku)

ROZ_GIDTyp=433, ROZ_GIDLp (filtr=1), ROZ_DtTyp/Firma/Numer/Lp=0,
ROZ_CtTyp/Firma/Numer/Lp=0, ROZ_DataOddzialu=0, ROZ_DataCentrali=0,
ROZ_DTDC=0, ROZ_CTDC=0, ROZ_OpeTypRL=128, ROZ_OpeLpRL=0,
ROZ_OpeTypRZ/FirmaRZ/NumerRZ/LpRZ=0, ROZ_DataRozrachunku=0, ROZ_Wycena=0

---

## ROZ_DataRozliczenia

Typ: Clarion DATE → `DATEADD(d, ROZ_DataRozliczenia, '18001228')`
Min: 81238 = 2023-05-31, Max: 1908212 = 7025 (błąd w danych ERP)
Liczba rekordów z datą > ok. 2030: 4 rekordy
User chce: zachować datę + flaga `Data_Podejrzana = CASE WHEN > 84000 THEN 'Tak' ELSE 'Nie' END`
Próg 84000 ≈ rok 2030 (bezpieczny margines).

---

## Enumeracje

ROZ_RKStrona: 0=Brak RK (170439 rek.), 1=Winien (30 rek.), 2=Ma (11 rek.)
ROZ_GIDFirma / ROZ_TrpFirma / ROZ_KAZFirma: distinct=2 → {1464833, 11528}

---

## Pliki

- Brudnopis:    solutions/bi/Rozrachunki/Rozrachunki_draft.sql
- Plan Excel:   solutions/bi/Rozrachunki/Rozrachunki_plan.xlsx  ← ZATWIERDZONE przez usera
- Plan src:     solutions/bi/Rozrachunki/Rozrachunki_plan_src.sql
- Obiekty:      solutions/bi/Rozrachunki/Rozrachunki_objects.sql
- Verify:       solutions/bi/Rozrachunki/Rozrachunki_objects_verify.sql
- Researcher:   solutions/bi/Rozrachunki/Rozrachunki_researcher_prompt.md

---

## Status: Faza 4 — ZAKOŃCZONE ✓

**Baseline aktualny:** 170 484–170 487 (baza produkcyjna rośnie między zapytaniami)
**Brak mnożenia wierszy:** COUNT(*) = COUNT(DISTINCT ROZ_GIDNumer) ✓
**Nr_Dok1 NULL:** 0 strukturalnych (artefakty wyścigu czasowego w eksporcie) ✓
**Nr_Dok2 NULL:** 0 strukturalnych ✓

### Odkrycie: Nota odsetkowa w CDN.UpoNag

Typ 2832 (NO) NIE jest w CDN.TraNag — rekordy są w CDN.UpoNag.
JOIN: `upo.UPN_GIDNumer = r.ROZ_TrpNumer/KAZNumer` przy danym typie.
Kolumny numeru: UPN_Numer, UPN_Rok, UPN_Seria.
3 rekordów TRP=NO, 7 rekordów KAZ=NO — wszystkie matchują.

Format numeru NO (ZWERYFIKOWANY przez CDN.NazwaObiektu):
`NO-{RIGHT(Rok,2)}/{Numer}` np. NO-25/3

```sql
'NO-' + RIGHT(CAST(UPN_Rok AS VARCHAR(4)), 2)
+ '/' + CAST(UPN_Numer AS VARCHAR(10))
+ CASE WHEN UPN_Seria <> '' THEN '/' + UPN_Seria ELSE '' END
```

### Pliki

- Brudnopis: solutions/bi/Rozrachunki/Rozrachunki_draft.sql (iteracja 3)
- Eksport:   solutions/bi/Rozrachunki/Rozrachunki_export.xlsx

### bi_verify (Faza 3) — wyniki

- 170 490 wierszy, 26 kolumn ✓
- ID_Rozliczenia distinct = row_count — klucz unikalny ✓
- Brak "Nieznane" w Typ_Dok1 / Typ_Dok2 ✓
- Nr_Dok1 null=2, Nr_Dok2 null=4 — artefakty wyścigu czasowego, 0 strukturalnych ✓
- Operator 18 distinct, 0 null ✓
- Waluta PLN/EUR, Strona_RK Brak/Winien/Ma ✓

### Faza 4 — ZAKOŃCZONA

- `solutions/bi/views/Rozrachunki.sql` — CREATE OR ALTER VIEW AIBI.Rozrachunki
- `solutions/bi/catalog.json` — wpis dodany (nazwa AIBI.Rozrachunki)
- Schema zmieniona z BI → AIBI (user zmienił catalog.json ręcznie)
- Widok NIE jest jeszcze wdrożony na bazie — plik SQL gotowy, wymaga uruchomienia w SSMS
- AIBI.KntKarty działa na bazie ✓, AIBI.Rozrachunki i AIBI.Rezerwacje jeszcze nie

### Reguła GID (potwierdzona przez usera, zapisana w ERP_VIEW_WORKFLOW.md)

- GIDFirma → pomijamy
- GIDTyp → tłumaczymy przez CASE
- GIDNumer → zostawiamy
- GIDLp → pomijamy
