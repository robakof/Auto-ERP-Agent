# Widoki SQL katalogowe CEiM — schemat AIOP

## Kolejnosc uruchomienia w SSMS

1. `00_create_schema.sql` — tworzy schemat AIOP
2. `01_view_folders.sql` — AIOP.vKatalogFoldery
3. `02_view_products.sql` — AIOP.vKatalogProdukty
4. `03_view_packages.sql` — AIOP.vKatalogPakiety

Kazdy plik uruchamiasz osobno w SSMS (F5) na bazie Comarch XL.
Wymaga konta z uprawnieniem CREATE VIEW.

## Widoki

### AIOP.vKatalogProdukty
Jeden wiersz per produkt x cennik.
Zawiera: identyfikacje, atrybuty (czas palenia, wymiary, material...),
jednostki logistyczne (opak/warstwa/paleta), ceny, flage zdjecia.

Filtrowanie po cenniku:
```sql
SELECT * FROM AIOP.vKatalogProdukty WHERE CennikRodzaj = 4  -- BRICO
SELECT * FROM AIOP.vKatalogProdukty WHERE CennikId IS NULL   -- bez ceny
```

### AIOP.vKatalogFoldery
Mapowanie produkt -> folder (bezposrednie przypisanie z TwrGrupyDom).
Pelna sciezka klasyfikacyjna w atrybucie GRUPA (pole GrupaSciezka w vKatalogProdukty).

### AIOP.vKatalogPakiety
Sklad pakietow: parent (PAK*) -> child (produkt skladowy) + ilosc szt.
Tabela zrodlowa: CDN.TwrPodm (zamienniki/komplety).

```sql
SELECT * FROM AIOP.vKatalogPakiety WHERE PakietKod = 'PAKZM012025'
```

## Cenniki (RodzajCeny)
| RodzajCeny | Nazwa |
|-----------|-------|
| 1 | CENA 100 (bazowa) |
| 2 | CMENTARZ |
| 3 | FRANOWO |
| 4 | BRICO |
| 5 | INTER |
| 6 | MROWKA / PSB |
| 7 | CHATA POLSKA |
| 8 | AT |
| 9 | PRYZMAT |
