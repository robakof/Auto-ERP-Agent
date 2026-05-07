-- ============================================================
-- WIDOK 2: Foldery produktowe
-- Mapowanie produkt -> folder (bezposrednie przypisanie)
-- Drzewo TwrGrupy ma cross-linki wiec zamiast rekurencji
-- uzywamy bezposredniego joina + jednego poziomu wyzej
-- Pelna sciezka klasyfikacyjna jest w atrybucie GRUPA
-- (dostepna w vKatalogProdukty.GrupaSciezka)
-- ============================================================

CREATE OR ALTER VIEW AIOP.vKatalogFoldery AS
SELECT
    tw.Twr_Kod              AS TowarKod,
    tw.Twr_GIDNumer         AS TwrGIDNumer,

    -- Folder lisc (bezposrednie przypisanie)
    g.TwG_GIDNumer          AS FolderID,
    g.TwG_Kod               AS FolderKod,
    g.TwG_Nazwa             AS FolderNazwa,

    -- Folder nadrzedny (1 poziom wyzej)
    gp.TwG_GIDNumer         AS ParentFolderID,
    gp.TwG_Kod              AS ParentFolderKod,
    gp.TwG_Nazwa            AS ParentFolderNazwa,

    -- Root (2 poziomy wyzej lub sam folder jesli root)
    COALESCE(gr.TwG_Kod, gp.TwG_Kod, g.TwG_Kod) AS RootKod,
    COALESCE(gr.TwG_Nazwa, gp.TwG_Nazwa, g.TwG_Nazwa) AS RootNazwa,

    -- Typ folderu
    CASE
        WHEN COALESCE(gr.TwG_Kod, gp.TwG_Kod, g.TwG_Kod) = '10_OFERTY'
            THEN 'OFERTA'
        WHEN COALESCE(gr.TwG_Kod, gp.TwG_Kod, g.TwG_Kod) = '06_POZOSTAŁA SPRZEDAŻ'
            THEN 'POZOSTALE'
        ELSE 'RODZINA'
    END AS TypFolderu

FROM CDN.TwrGrupyDom d
INNER JOIN CDN.TwrKarty tw ON d.TGD_GIDNumer = tw.Twr_GIDNumer
INNER JOIN CDN.TwrGrupy g  ON d.TGD_GrONumer = g.TwG_GIDNumer
LEFT  JOIN CDN.TwrGrupy gp ON g.TwG_GrONumer  = gp.TwG_GIDNumer
                           AND g.TwG_GrONumer <> 0
                           AND g.TwG_GrONumer <> g.TwG_GIDNumer
LEFT  JOIN CDN.TwrGrupy gr ON gp.TwG_GrONumer = gr.TwG_GIDNumer
                           AND gp.TwG_GrONumer <> 0
                           AND gp.TwG_GrONumer <> gp.TwG_GIDNumer;
GO

-- ============================================================
-- Przyklad uzycia:
--
-- Foldery CZNI42027:
--   SELECT * FROM AIOP.vKatalogFoldery WHERE TowarKod = 'CZNI42027'
--
-- Produkty w folderze OFERTA:
--   SELECT * FROM AIOP.vKatalogFoldery WHERE TypFolderu = 'OFERTA'
--
-- Pelna sciezka klasyfikacyjna: uzyj vKatalogProdukty.GrupaSciezka
-- ============================================================
