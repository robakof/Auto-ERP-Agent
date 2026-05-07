-- ============================================================
-- WIDOK 3: Pakiety -- sklad (parent -> child)
-- Tabele: CDN.TwrPodm (zamienniki/komplety), CDN.TwrKarty
-- ============================================================

CREATE OR ALTER VIEW AIOP.vKatalogPakiety AS
SELECT
    -- Parent (pakiet)
    pak.Twr_Kod             AS PakietKod,
    pak.Twr_Nazwa           AS PakietNazwa,

    -- Child (produkt skladowy)
    child.Twr_Kod           AS ProduktKod,
    child.Twr_Nazwa         AS ProduktNazwa,

    -- Ilosc
    CAST(tp.TwP_PrzeliczL AS INT) AS IloscSzt,

    -- Klucze wewnetrzne
    pak.Twr_GIDNumer        AS PakietGIDNumer,
    child.Twr_GIDNumer      AS ProduktGIDNumer,
    tp.TwP_Id               AS PowiazanieId

FROM CDN.TwrPodm tp
INNER JOIN CDN.TwrKarty pak   ON tp.TwP_TwrNumer = pak.Twr_GIDNumer
INNER JOIN CDN.TwrKarty child ON tp.TwP_ZamNumer = child.Twr_GIDNumer
WHERE pak.Twr_Kod LIKE 'PAK%';
GO

-- ============================================================
-- Przyklad uzycia:
--
-- Sklad pakietu PAKZM012025:
--   SELECT * FROM AIOP.vKatalogPakiety WHERE PakietKod = 'PAKZM012025'
--
-- Wszystkie pakiety 2025:
--   SELECT * FROM AIOP.vKatalogPakiety WHERE PakietKod LIKE '%2025'
--
-- Suma wartosci pakietu (join z cenami):
--   SELECT p.PakietKod, p.ProduktKod, p.IloscSzt,
--          c.CenaNetto, p.IloscSzt * c.CenaNetto AS Wartosc
--   FROM AIOP.vKatalogPakiety p
--   LEFT JOIN AIOP.vKatalogProdukty c
--     ON c.KodXL = p.ProduktKod AND c.CennikRodzaj = 4
--   WHERE p.PakietKod = 'PAKZM012025'
-- ============================================================
