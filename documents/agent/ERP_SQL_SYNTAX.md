# ERP SQL Syntax — Rdzeń

Podstawowe zasady SQL w systemie ERP Comarch XL.
Przed generowaniem kodu dla konkretnego zadania załaduj odpowiedni plik:

- Kolumny ERP → `ERP_COLUMNS_WORKFLOW.md`
- Filtry ERP → `ERP_FILTERS_WORKFLOW.md`
- Widoki BI → `ERP_VIEW_WORKFLOW.md`
- Wzorce schematu (daty, tabele pomocnicze) → `ERP_SCHEMA_PATTERNS.md`

---

## 1. Struktura widoku — punkt wejścia

Każdy widok w ERP posiada plik `filtr.sql` — określa tabelę źródłową i kotwicę widoku.
Przeczytaj go przed generowaniem kodu — wyznacza tabelę startową i dostępne kolumny.

```sql
-- Przykład: Towary według EAN
(Twr_GIDNumer=3282)

-- Przykład: Towary według grup
(TwG_GIDTyp=16 AND TwG_GIDNumer=3282 AND TwG_GrOTyp=-16 AND TwG_GrONumer=48)
```

Prefiks kolumn w `filtr.sql` wyznacza tabelę główną (np. `Twr_` → CDN.TwrKarty).

---

## 2. Wbudowane funkcje ERP

### cdn.NazwaObiektu — nazwa dokumentu

```sql
cdn.NazwaObiektu(trn_gidtyp, Trn_gidnumer, 0, 2)
```

Zwraca wyświetlaną nazwę dokumentu (np. "FS 1/2024").

**UWAGA:** Konto `CEiM_Reader`/`CEiM_BI` **nie ma** EXECUTE na funkcje CDN (error 229).
Dostępne wyłącznie w filtrach ERP lub widokach tworzonych przez DBA.

### Gotowe procedury AI_ChatERP

| Procedura | Parametry | Opis |
|---|---|---|
| `CDN.AI_ChatERP_PodajSprzedaz` | @KntNipNazwaAkronim VARCHAR(255), @ZakresDaty TINYINT | Sprzedaż dla kontrahenta |
| `CDN.AI_ChatERP_PodajNajwiecejKupowane` | @IloscRekordow INT, @ZakresDaty TINYINT | Top N kupowanych towarów |
| `CDN.AI_ChatERP_PodajNajwiecejSprzedawane` | @IloscRekordow INT, @ZakresDaty TINYINT | Top N sprzedawanych towarów |
| `CDN.AI_ChatERP_PodajNajwiekszychOdbiorcow` | @IloscRekordow INT, @ZakresDaty TINYINT | Top N odbiorców (FS) |
| `CDN.AI_ChatERP_PodajNajwiekszychDostawcow` | @IloscRekordow INT, @ZakresDaty TINYINT | Top N dostawców (FZ) |
| `CDN.AI_ChatERP_PodajNajwiekszychDluznikow` | @IloscRekordow INT | Top N dłużników |
| `CDN.AI_ChatERP_PodajNajwiekszychWierzycieli` | @IloscRekordow INT | Top N wierzycieli |
| `CDN.AI_ChatERP_PodajNiezrealizowaneZamowieniaPrzeterminowane` | @IloscRekordow INT | Przeterminowane ZS/ZZ |
| `CDN.AI_ChatERP_PodajPrzeterminowaneFaktury` | @IloscRekordow INT | Przeterminowane faktury |
| `CDN.AI_ChatERP_PodajKupcow` | @IloscRekordow INT, @TwrKod VARCHAR(255), @ZakresDaty TINYINT | Kupcy towaru |
| `CDN.AI_ChatERP_PodajZalegajaceTowary` | @IloscRekordow INT | Towary zalegające |
| `CDN.AI_ChatERP_PodajWzrostSprzedazyNarastajaco` | — | Wzrost sprzedaży YTD |

**@ZakresDaty:** `0` = ostatni tydzień, `1` = ostatni miesiąc, `2` = ostatni rok

### Funkcje konwersji dat CDN (referencja — CEiM_Reader może nie mieć EXECUTE)

| Funkcja | Sygnatura | Działanie |
|---|---|---|
| `CDN.DateToClarion` | `(@dt DATETIME) → INT` | DATETIME → Clarion int (`DATEDIFF(dd,'1800-12-28',@dt)`) |
| `CDN.DateToTS` | `(@dt DATETIME) → INT` | DATETIME → sekundy od 1990-01-01 |
| `CDN.DateDiffClarion` | `(@typ SMALLINT, @D1 INT, @D2 INT) → INT` | Różnica Clarion: 1=dni, 2=mies, 3=lata |
| `CDN.DataClarionPrzesun` | `(@DataPrzed INT, @Ile INT, @Jed INT) → INT` | Przesuń datę Clarion: 0=dni, 1=tyg, 2=mies, 3=lata |
| `CDN.Data` | `(@Rok INT, @Miesiac INT, @Dzien INT) → INT` | Rok/Miesiąc/Dzień → Clarion int |
| `CDN.YMD` | `(@Year INT, @Month INT, @Day INT) → DATETIME` | Rok/Miesiąc/Dzień → DATETIME |
| `CDN.DniZwloki` | `(@DataRoz INT, @Termin INT, @Today INT, @Rozliczony INT) → INT` | Dni zwłoki |

W widokach BI używaj wzorców inline — patrz `ERP_SCHEMA_PATTERNS.md`.

---

## 3. GIDTyp — kody typów dokumentów

| GIDTyp | Symbol | Opis |
|---|---|---|
| 16 | TWR | Karta towaru (CDN.TwrKarty) |
| 32 | KNT | Karta kontrahenta (CDN.KntKarty) |
| 960 | ZS | Zamówienie sprzedaży (CDN.ZamNag, ZaN_ZamTyp=960) |
| 1152 | ZZ | Zamówienie zakupu (CDN.ZamNag, ZaN_ZamTyp=1152) |
| 1489 | PZ | Przyjęcie zewnętrzne |
| 1521 | FZ | Faktura zakupu |
| 2001 | WZ | Wydanie zewnętrzne |
| 2033 | FS | Faktura sprzedaży |
| 2041 | FSK | Korekta faktury sprzedaży |
| 2592 | BkRez | Rezerwacja u dostawcy (CDN.Rezerwacje) |

**WAŻNE:** `ZaN_GIDTyp` w CDN.ZamNag zawsze = 960 (typ obiektu/tabeli).
Kierunek dokumentu (ZS/ZZ) wyznacza `ZaN_ZamTyp`: 960 = ZS, 1152 = ZZ.

Pełna lista: `erp_docs/raw/Dokumnetacja bazy/e_typy.html`
Mapowanie GIDTyp → tabela: `CDN.GIDTyp2Tabela(GIDTyp)`

---

*Szczegóły implementacji w plikach workflow i schema patterns.*
