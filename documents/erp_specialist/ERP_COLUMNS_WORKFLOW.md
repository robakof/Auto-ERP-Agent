# ERP — Workflow dopisywania kolumn

Kolumna to pełne zapytanie SELECT zwracające dodatkowe dane dla każdego wiersza widoku ERP.

---

## Struktura obowiązkowa

```sql
SELECT
    kolumna [ALIAS WYSWIETLANY]
FROM cdn.TabelaGlowna
[LEFT JOIN ...]
WHERE {filtrsql}
```

### KRYTYCZNE: {filtrsql} jest obowiązkowe

Bez `{filtrsql}` system ERP dla każdego wiersza widoku uruchamia SELECT bez zawężenia —
ładuje wszystkie rekordy tabeli. Efekt: widok przestaje reagować lub ładuje się minutami.

- Alias kolumny w nawiasach kwadratowych: `kolumna [MOJA NAZWA]`
- `{filtrsql}` case-insensitive (`{filtrsql}` i `{filtrSQL}` są równoważne)
- Tabela główna musi być połączona z tabelą z `filtr.sql` (przez JOIN lub bezpośrednio)
- LEFT JOIN dla kolumn opcjonalnych

---

## Warianty WHERE

**Tylko filtrsql** (najczęstszy):
```sql
WHERE {filtrSQL}
```

**Stały warunek AND filtrsql:**
```sql
WHERE wfz_status = 'Wysyłka dokumentu' AND {filtrSQL}
```

**Z GROUP BY** (GROUP BY po filtrsql):
```sql
WHERE {filtrSQL}
GROUP BY ZaV_Waluta
```

Średnik na końcu (`WHERE {filtrSQL};`) jest dopuszczalny.

---

## TOP 1 — gdy JOIN może zwrócić wiele wierszy

Gdy JOIN dołącza tabelę z relacją 1:N, bez TOP 1 kolumna zwróci błąd. Użyj gdy powiązanie
może być wielokrotne:

```sql
SELECT TOP 1
    CASE
        WHEN WFP_DataZamkniecia = 0 THEN 'Błąd wysyłki'
        WHEN WFZ_Akcja = ''        THEN 'zamknięcie ręczne'
        ELSE 'Wysłano'
    END AS [Status wysyłki]
FROM cdn.TraNag
JOIN cdn.WF_Procesy ON TrN_GIDTyp = WFP_OBITyp AND TrN_GIDNumer = WFP_OBINumer
JOIN cdn.WF_Zadania ON WFZ_WFPID = WFP_ID
WHERE wfz_status = 'Wysyłka dokumentu' AND {filtrSQL}
```

---

## Wiele kolumn w jednym SELECT (agregaty)

```sql
SELECT
    SUM(ZaV_Netto)                 [Netto],
    SUM(ZaV_Netto) + SUM(ZaV_Vat) [Brutto],
    ZaV_Waluta                     [Waluta]
FROM cdn.ZamNag
JOIN cdn.ZamVAT v ON ZaN_GIDTyp = ZaV_GIDTyp AND ZaN_GIDNumer = ZaV_GIDNumer
WHERE {filtrSQL}
GROUP BY ZaV_Waluta
```

---

## Wielokrotny JOIN tej samej tabeli — różne aliasy

```sql
SELECT
    Ope_Ident       [Wystawiający],
    ak.Knt_Akronim  [Akwizytor],
    pl.Knt_Akronim  [Płatnik]
FROM cdn.TraNag
JOIN cdn.OpeKarty op ON TrN_OpeNumerW = Ope_GIDNumer AND TrN_OpeTypW = Ope_GIDTyp
JOIN cdn.KntKarty ak ON TrN_AkwNumer  = ak.Knt_GIDNumer AND TrN_AkwTyp = ak.Knt_GIDTyp
JOIN cdn.KntKarty pl ON TrN_KnpNumer  = pl.Knt_GIDNumer AND TrN_KnpTyp = pl.Knt_GIDTyp
WHERE {FiltrSQL}
```

---

## Widok elementów — FROM ≠ tabela widoku

Gdy `filtr.sql` odnosi się do tabeli nagłówka, a kolumna startuje od tabeli elementów:

```sql
SELECT odb.Knt_Akronim [Odbiorca]
FROM cdn.TraElem el
JOIN cdn.TraNag n
    ON n.TrN_GIDNumer = el.TrE_GIDNumer
LEFT JOIN cdn.KntKarty odb
    ON n.TrN_KnDTyp   = odb.Knt_GIDTyp
   AND n.TrN_KnDNumer = odb.Knt_GIDNumer
WHERE {FiltrSQL}
```

---

## Atrybuty — LEFT JOIN wielokrotny

```sql
SELECT
    k3.Atr_Wartosc [SEZON],
    k4.Atr_Wartosc [KOLOR]
FROM cdn.TwrKarty
LEFT JOIN cdn.Atrybuty k3 ON Twr_GIDNumer = k3.Atr_ObiNumer
    AND Twr_GIDTyp = k3.Atr_ObiTyp AND k3.Atr_AtKId = 3
LEFT JOIN cdn.Atrybuty k4 ON Twr_GIDNumer = k4.Atr_ObiNumer
    AND Twr_GIDTyp = k4.Atr_ObiTyp AND k4.Atr_AtKId = 4
WHERE {filtrsql}
```

Identyfikatory atrybutów dla Towary: `Atr_AtkId = 3` (Sezon), `59` (Status ofertowy).

---

## CDN.DefinicjeKolumn — numeracja zakładek

Numer zakładki (`DFK_IDListy`) dla kolumn jest **inny** niż dla filtrów (`FIL_ListaID`):

| Widok | FIL_ListaID | DFK_IDListy |
|---|---|---|
| Towary według EAN | 1 | 31 |
| Towary według grup | 2 | 30 |
| Handlowe (dokumenty) | 1 | 4 |
| Magazynowe (dokumenty) | 2 | 5 |
| Elementy (dokumenty) | 81 | 1008 |

---

## Checklist przed oddaniem

1. Przeczytaj `filtr.sql` widoku → tabela główna i typ obiektu
2. Sprawdź `solutions_search.py --type columns` dla widoku → naśladuj styl istniejących
3. `{filtrsql}` obecne w WHERE — **obowiązkowe**
4. Alias w `[NAWIASACH KWADRATOWYCH]`
5. LEFT JOIN dla kolumn opcjonalnych
6. TOP 1 gdy JOIN może zwrócić wiele wierszy
7. Przetestuj przez `sql_query.py` — sprawdź czy wynik sensowny
