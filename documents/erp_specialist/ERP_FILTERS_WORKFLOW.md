# ERP — Workflow tworzenia filtrów

Filtr to wyłącznie warunek WHERE — bez SELECT, bez FROM.
System ERP wstrzykuje go w odpowiednie miejsce zapytania widoku.

---

## Filtr prosty (bez parametrów)

```sql
Twr_Archiwalny = 1
```

```sql
Twr_Ean IN (
    SELECT Twr_Ean FROM cdn.TwrKarty
    WHERE Twr_Ean <> ''
    GROUP BY Twr_Ean
    HAVING COUNT(Twr_Ean) > 1
)
```

---

## Limit znaków

- **≤ 2000 znaków** — bezpieczny cel
- 2043 znaków działa; 2090 nie zapisuje się
- `CDN.Filtry.FIL_FiltrSQL` to varchar(4096) — NIE jest granicą (limit narzuca aplikacja kliencka)

---

## Parametry @PAR — składnia

```
@PAR ?@TYP|NAZWA_ZMIENNEJ|&Etykieta:REG=wartość_domyślna @? PAR@
```

Parametry deklarowane przed warunkiem, każdy w osobnej linii.

---

## Modyfikatory (między `@?` a `PAR@`)

| Modyfikator | Znaczenie |
|---|---|
| `@U()` | Wymusza wielkie litery przy wpisywaniu |
| `@RL(n)` | Minimalna wartość numeryczna |
| `@RH(n)` | Maksymalna wartość numeryczna |

```sql
@PAR ?@S20|Kod|&Kod towaru:REG= @? @U() PAR@
@PAR ?@n-16_.2|Kwota|&Kwota:REG=0 @? @RL(-99999999) @RH(99999999) PAR@
```

---

## Typ S — String

```sql
@PAR ?@S100|Szukaj|&Szukaj:REG= @? PAR@

Twr_Kod LIKE '%' + ??Szukaj + '%'
OR Twr_Nazwa LIKE '%' + ??Szukaj + '%'
```

Format: `S[max_długość]`. Referencja w WHERE: `??NazwaParam`.

---

## Typ D — Data

```sql
@PAR ?@D17|DataOd|&DataOd:REG=0 @? PAR@
@PAR ?@D17|DataDo|&DataDo:REG=0 @? PAR@

(??DataOd=0 OR Twr_DataUtworzenia/86400+69035 >= ??DataOd)
AND (??DataDo=0 OR Twr_DataUtworzenia/86400+69035 <= ??DataDo)
```

ERP podstawia wartość numeryczną (Clarion date). `REG=0` = "pomiń filtr" przy `??=0`.
Alternatywne wartości domyślne: `{DateClwFirstDay('m')}`, `{DateClwLastDay('m')}`.

---

## Typ O — Opcje (radio)

```sql
@PAR ?@O(Tak:1|Nie:0)|Zgoda|&Zgoda:REG=1 @? PAR@
Knt_EFaVatAktywne = ??Zgoda
```

Format opcji: `Etykieta:Wartość|Etykieta2:Wartość2`.

---

## Typ n — Numeryczny

```sql
@PAR ?@n-16_.2|Kwota|&Kwota:REG=0 @? @RL(-99999999) @RH(99999999) PAR@

TrP_Kwota = CASE WHEN ??Kwota = 0 THEN TrP_Kwota ELSE ??Kwota END
```

Format: `@n-[szerokość]_.[miejsca_dziesiętne]`. Wartość → `??Param`.

---

## Typ R — Lista rozwijana (dropdown)

### Reguła `??_Q` — krytyczna

| Typ ID | Referencja w WHERE |
|---|---|
| varchar | `??_QNazwaParam` (ERP otacza cudzysłowami) |
| numeric | `??NazwaParam` (bez `_Q`) |

### Stałe opcje (UNION)

```sql
@PAR ?@R(
    SELECT 'Tak' AS ID, 'Tak' AS Kod
    UNION ALL
    SELECT 'Nie' AS ID, 'Nie' AS Kod
)|UdostepnienieMS|&Udostępnione w mobilnej sprzedaży:REG=Tak @? PAR@

Twr_MobSpr = CASE WHEN ??_QUdostepnienieMS = 'Tak' THEN '1' ELSE '0' END
```

### Dynamiczna lista z bazy

```sql
@PAR ?@R(
    SELECT DISTINCT
        CAST(CAST(Twr_StawkaPodSpr AS INT) AS VARCHAR(2)) + ' (' + Twr_GrupaPodSpr + ')' AS "KOD",
        Twr_StawkaPodSpr AS "ID"
    FROM cdn.TwrKarty ORDER BY 1
)|StawkaVat|&Stawka Vat:REG= @? PAR@

Twr_StawkaPodSpr = ??StawkaVat
```

### Parametr opcjonalny — sentinel `'all'`

**UWAGA:** sentinel `''` nie działa dla `@R` (ERP podstawia NULL, nie pusty string).
Działający wzorzec: `'all'` jako sentinel, `REG=all`.

```sql
@PAR ?@R(
    SELECT '(wszystkie)' AS KOD, 'all' AS ID
    UNION ALL
    SELECT 'brak', 'Brak stanu'
    UNION ALL
    SELECT 'ma', 'Z dowolnym stanem'
)|StanMag|&Stan magazynowy:REG=all @? PAR@

(??_QStanMag='all' OR (??_QStanMag='brak' AND NOT EXISTS(...)) OR (??_QStanMag='ma' AND EXISTS(...)))
```

Ograniczenie: `REG=all` działa tylko przy statycznej liście (UNION bez zapytania do tabeli).

### Opcjonalny z dynamicznym dropdownem — sentinel numeryczny `0`

```sql
@PAR ?@R(SELECT '(wszystkie)' AS KOD, 0 AS ID
UNION ALL
SELECT Mag_Kod AS KOD, Mag_GIDNumer AS ID FROM cdn.Magazyny ORDER BY 1
)|Magazyn|&Magazyn:REG=0 @? PAR@

(??Magazyn=0 OR Twr_GIDNumer IN (
    SELECT TwZ_TwrNumer FROM cdn.TwrZasoby
    WHERE TwZ_MagNumer = ??Magazyn
    GROUP BY TwZ_TwrNumer
    HAVING SUM(TwZ_IlMag) <> SUM(TwZ_IlSpr)
))
```

### Bezpieczeństwo typów w UNION

Gdy UNION miesza typy ID — rzutuj na VARCHAR:

```sql
CAST(CAST(Twr_StawkaPodSpr AS INT) AS VARCHAR(2)) AS ID
-- Warunek WHERE:
CAST(CAST(Twr_StawkaPodSpr AS INT) AS VARCHAR(2)) = ??_QStawkaVat
```

---

## Filtry globalne — metodologia testowania

Gdy nowy filtr ma być częścią istniejącego filtru zbiorczego:

1. **Nie twórz osobnego pliku** dla nowej funkcjonalności
2. **Najpierw podaj samą logikę warunku** (bez @PAR, bez struktury zbiorczej) — user
   przekopiuje do ERP i przetestuje ręcznie
3. **Po potwierdzeniu że działa** — wygeneruj pełną zaktualizowaną wersję zbiorczą i zapisz z `--force`

---

## Checklist przed oddaniem

1. Tylko warunek WHERE — bez SELECT, bez FROM
2. `@R` varchar ID → `??_QNazwa` / numeric ID → `??Nazwa`
3. `@S` → `??Nazwa`, `@D` → `??Nazwa` z przelicznikiem `/86400+69035`
4. Parametry opcjonalne: `@D` i `@n` — `REG=0` + warunek `??=0`; `@R` — `REG=all` + sentinel
5. Całość ≤ 2000 znaków
6. Przetestuj logikę z podstawionymi wartościami przez `sql_query.py`
