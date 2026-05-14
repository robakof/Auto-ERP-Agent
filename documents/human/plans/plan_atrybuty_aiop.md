# Atrybuty → AIOP: analiza migracji zapytań ODBC

## Stan obecny

Narzędzia atrybutowe (`xl_attribute_set.py`, `xl_attribute_bulk.py`, `xl_attribute_template.py`)
używają 7 zapytań ODBC bezpośrednio na tabelach CDN.

## Zapytania vs AIOP.vKatalogProdukty

| # | Zapytanie | Tabele CDN | AIOP pokrywa? | Blokada |
|---|-----------|-----------|---------------|---------|
| 1 | Lista klas atrybutów (nazwa, typ, wielowartościowy, zamknięta) | AtrybutyKlasy + AtrybutyObiekty | NIE | AIOP ma 17 hardcoded atrybutów — nie zna listy klas ani ich metadanych (typ, wielowart, zamknięta) |
| 2 | GID towaru po kodzie (GIDNumer, GIDFirma, GIDTyp) | TwrKarty | CZESCIOWO | AIOP ma TwrGIDNumer, ale brakuje GIDFirma i GIDTyp (potrzebne do XL API) |
| 3 | Sprawdzenie czy atrybut istnieje | Atrybuty + AtrybutyKlasy | NIE | AIOP ma wartości konkretnych atrybutów, ale nie sprawdza istnienia dowolnej klasy |
| 4 | DELETE atrybutów | Atrybuty | NIE | AIOP to VIEW — readonly, nie da się przez niego usuwać |
| 5 | Lista produktów (all / grupa / po akronimach) | TwrKarty, TwrGrupy | CZESCIOWO | AIOP ma KodXL, ale brak Twr_Nazwa1, brak filtra po grupie towarowej |
| 6 | Istniejące wartości atrybutów (wszystkie / po akronimach) | Atrybuty + AtrybutyKlasy + TwrKarty | NIE | AIOP ma tylko 17 wybranych atrybutów jako kolumny — nie da się pobrać WSZYSTKICH dynamicznie |
| 7 | Walidacja nazwy klasy atrybutu | AtrybutyKlasy + AtrybutyObiekty | NIE | j.w. |

## Problem główny

**AIOP.vKatalogProdukty ma STAŁE 17 atrybutów jako kolumny** (CzasPalenia, Gramatura, Wysokosc...).
Narzędzia atrybutowe potrzebują **DYNAMICZNEJ listy WSZYSTKICH klas atrybutów** — łącznie z metadanymi
(typ, wielowartościowy, zamknięta). To fundamentalnie inny model danych.

## Rozwiązanie: nowy widok AIOP.vAtrybutyTowarow

Aby AIOP pokrył potrzeby narzędzi atrybutowych, potrzebny nowy widok:

```sql
CREATE OR ALTER VIEW AIOP.vAtrybutyTowarow AS
SELECT
    tk.Twr_Kod              AS KodXL,
    tk.Twr_Nazwa1           AS NazwaTowaru,
    tk.Twr_GIDNumer         AS TwrGIDNumer,
    tk.Twr_GIDFirma         AS TwrGIDFirma,
    tk.Twr_GIDTyp           AS TwrGIDTyp,
    ak.AtK_Nazwa            AS KlasaAtrybutu,
    ak.AtK_Typ              AS TypAtrybutu,        -- 1=TAK/NIE, 2=tekst, 3=liczba, 4=lista
    ak.AtK_Wielowart        AS Wielowartosciowy,
    ak.AtK_Zamknieta        AS ListaZamknieta,
    a.Atr_Wartosc           AS Wartosc
FROM CDN.TwrKarty tk
CROSS JOIN (
    SELECT DISTINCT ak.AtK_ID, ak.AtK_Nazwa, ak.AtK_Typ, ak.AtK_Wielowart, ak.AtK_Zamknieta
    FROM CDN.AtrybutyKlasy ak
    INNER JOIN CDN.AtrybutyObiekty ao ON ao.AtO_AtKId = ak.AtK_ID
    WHERE ao.AtO_GIDTyp = 16
) ak
LEFT JOIN CDN.Atrybuty a
    ON a.Atr_ObiNumer = tk.Twr_GIDNumer
    AND a.Atr_ObiTyp = 16
    AND a.Atr_AtkId = ak.AtK_ID
WHERE tk.Twr_Archiwalny = 0;
```

## Co ten widok zastąpi

| Zapytanie | Zastąpione przez |
|-----------|-----------------|
| #1 Lista klas | `SELECT DISTINCT KlasaAtrybutu, TypAtrybutu, Wielowartosciowy, ListaZamknieta FROM AIOP.vAtrybutyTowarow` |
| #2 GID towaru | `SELECT DISTINCT TwrGIDNumer, TwrGIDFirma, TwrGIDTyp FROM AIOP.vAtrybutyTowarow WHERE KodXL = ?` |
| #3 Czy istnieje | `SELECT COUNT(*) FROM AIOP.vAtrybutyTowarow WHERE TwrGIDNumer = ? AND KlasaAtrybutu = ? AND Wartosc IS NOT NULL` |
| #5 Lista produktów | `SELECT DISTINCT KodXL, NazwaTowaru FROM AIOP.vAtrybutyTowarow` |
| #6 Wartości | `SELECT KodXL, KlasaAtrybutu, Wartosc FROM AIOP.vAtrybutyTowarow WHERE Wartosc IS NOT NULL` |
| #7 Walidacja klasy | `SELECT DISTINCT KlasaAtrybutu FROM AIOP.vAtrybutyTowarow` |

## Co NIE da się zastąpić

- **#4 DELETE atrybutów** — wymaga bezpośredniego SQL na CDN.Atrybuty (widok jest readonly)
- **Zapis** — nadal przez XL API (XLDodajAtrybut)
- **Filtr po grupie towarowej** — wymaga osobnego widoku lub dodania kolumny grupy

## Podsumowanie

Jeden nowy widok `AIOP.vAtrybutyTowarow` zastąpi 6 z 7 zapytań ODBC.
Jedyny pozostający bezpośredni SQL to DELETE (tryb --update).
