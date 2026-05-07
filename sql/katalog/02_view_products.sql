-- ============================================================
-- WIDOK 1: Produkty katalogowe
-- Jeden wiersz per produkt x cennik (filtruj po CennikId/CennikRodzaj)
-- Produkt bez cennika = 1 wiersz z NULL w polach cenowych
-- ============================================================

CREATE OR ALTER VIEW AIOP.vKatalogProdukty AS
SELECT
    -- A. Identyfikacja
    tw.Twr_Kod              AS KodXL,
    tw.Twr_Ean              AS KodEAN,
    tw.Twr_Nazwa            AS NazwaHandlowa,

    -- B. Klasyfikacja (atrybut GRUPA = sciezka folderowa)
    atr_grupa.Wartosc       AS GrupaSciezka,
    atr_sezon.Wartosc       AS Sezon,
    atr_kolor.Wartosc       AS Kolor,
    atr_status.Wartosc      AS StatusOfertowy,

    -- C. Parametry produktu
    TRY_CAST(atr_czas.Wartosc AS DECIMAL(7,2))       AS CzasPalenia_h,
    TRY_CAST(atr_gram.Wartosc AS DECIMAL(7,2))        AS GramaturaWkladu_g,
    TRY_CAST(atr_wys_n.Wartosc AS DECIMAL(7,2))       AS WysokoscNetto_cm,
    TRY_CAST(atr_szer_n.Wartosc AS DECIMAL(7,2))      AS SzerokoscNetto_cm,
    TRY_CAST(atr_sred.Wartosc AS DECIMAL(7,2))        AS SrednicaProduktu_cm,
    atr_mat.Wartosc                                    AS Material,
    atr_zapach.Wartosc                                 AS Zapach,
    TRY_CAST(atr_waga.Wartosc AS DECIMAL(7,2))        AS WagaProduktu_g,
    TRY_CAST(atr_sred_otw.Wartosc AS DECIMAL(7,2))    AS SrednicaOtworu_cm,

    -- D. Wymiary opakowania
    TRY_CAST(atr_szer_b.Wartosc AS DECIMAL(7,2))      AS SzerokoscBrutto_cm,
    TRY_CAST(atr_wys_b.Wartosc AS DECIMAL(7,2))       AS WysokoscBrutto_cm,
    TRY_CAST(atr_gleb_b.Wartosc AS DECIMAL(7,2))      AS GlebokoscBrutto_cm,

    -- E. Jednostki logistyczne
    jm_opak.Ilosc           AS SztWOpakowaniu,
    jm_warstwa.Ilosc        AS SztNaWarstwie,
    jm_paleta.Ilosc         AS SztNaPalecie,

    -- F. Ceny (wiele wierszy per produkt -- filtruj po CennikRodzaj)
    cn.TCN_Id               AS CennikId,
    RTRIM(cn.TCN_Nazwa)     AS CennikNazwa,
    cn.TCN_RodzajCeny       AS CennikRodzaj,
    tc.TwC_Wartosc          AS CenaNetto,
    tc.TwC_Waluta           AS CenaWaluta,

    -- G. Zdjecia
    CASE WHEN foto.LiczbaZdjec > 0 THEN 1 ELSE 0 END AS MaZdjecie,
    foto.LiczbaZdjec        AS LiczbaZdjec,

    -- Dodatkowe atrybuty
    atr_zasilanie.Wartosc   AS Zasilanie,
    atr_bateria.Wartosc     AS CzyBateriaWZestawie,
    atr_trend.Wartosc       AS TrendNowosc,

    -- Klucz wewnetrzny
    tw.Twr_GIDNumer         AS TwrGIDNumer

FROM CDN.TwrKarty tw

-- --- Ceny: LEFT JOIN = produkt x cennik ---
LEFT JOIN CDN.TwrCeny tc ON tc.TwC_TwrNumer = tw.Twr_GIDNumer
    AND tc.TwC_KntNumer = 0
LEFT JOIN CDN.TwrCenyNag cn ON tc.TwC_TcnId = cn.TCN_Id

-- --- Atrybuty (OUTER APPLY per klasa atrybutu) ---
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 44
) atr_grupa       -- GRUPA (sciezka folderowa)
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 3
) atr_sezon       -- SEZON
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 5
) atr_kolor       -- KOLOR
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 59
) atr_status      -- STATUS OFERTOWY PRODUKTU
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 9
) atr_czas        -- CZAS PALENIA / DZIALANIA
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 10
) atr_gram        -- GRAMATURA WKLADU
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 12
) atr_wys_n       -- WYSOKOSC NETTO PRODUKTU
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 11
) atr_szer_n      -- SZEROKOSC NETTO PRODUKTU
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 16
) atr_sred        -- SREDNICA PRODUKTU
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 6
) atr_mat         -- MATERIAL
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 4
) atr_zapach      -- ZAPACH
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 55
) atr_waga        -- WAGA PRODUKTU
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 56
) atr_sred_otw    -- SREDNICA OTWORU
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 13
) atr_szer_b      -- SZEROKOSC BRUTTO OPAKOWANIA
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 14
) atr_wys_b       -- WYSOKOSC BRUTTO OPAKOWANIA
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 15
) atr_gleb_b      -- GLEBOKOSC BRUTTO OPAKOWANIA
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 7
) atr_zasilanie   -- ZASILANIE
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 8
) atr_bateria     -- CZY BATERIA W ZESTAWIE
OUTER APPLY (
    SELECT TOP 1 a.Atr_Wartosc AS Wartosc
    FROM CDN.Atrybuty a WHERE a.Atr_ObiTyp = 16
        AND a.Atr_ObiNumer = tw.Twr_GIDNumer AND a.Atr_AtkId = 18
) atr_trend       -- TREND NOWOSCI

-- --- Jednostki logistyczne ---
OUTER APPLY (
    SELECT TOP 1 CAST(j.TwJ_PrzeliczL AS INT) AS Ilosc
    FROM CDN.TwrJm j
    WHERE j.TwJ_TwrNumer = tw.Twr_GIDNumer AND j.TwJ_JmZ LIKE 'opak%'
) jm_opak
OUTER APPLY (
    SELECT TOP 1 CAST(j.TwJ_PrzeliczL AS INT) AS Ilosc
    FROM CDN.TwrJm j
    WHERE j.TwJ_TwrNumer = tw.Twr_GIDNumer AND j.TwJ_JmZ LIKE 'warst%'
) jm_warstwa
OUTER APPLY (
    SELECT TOP 1 CAST(j.TwJ_PrzeliczL AS INT) AS Ilosc
    FROM CDN.TwrJm j
    WHERE j.TwJ_TwrNumer = tw.Twr_GIDNumer AND j.TwJ_JmZ LIKE 'palet%'
) jm_paleta

-- --- Zdjecia ---
OUTER APPLY (
    SELECT COUNT(*) AS LiczbaZdjec
    FROM CDN.DaneObiekty dao
    INNER JOIN CDN.DaneBinarne dab ON dao.DAO_DABId = dab.DAB_ID
    WHERE dao.DAO_ObiTyp = 16
      AND dao.DAO_ObiNumer = tw.Twr_GIDNumer
      AND dab.DAB_Rozszerzenie IN ('jpg','png','jpeg','JPG','PNG','JPEG')
) foto;
GO

-- ============================================================
-- Przyklad uzycia:
--
-- Wszystkie produkty z cennika BRICO (RodzajCeny=4):
--   SELECT * FROM AIOP.vKatalogProdukty WHERE CennikRodzaj = 4
--
-- Jeden produkt, wszystkie cenniki:
--   SELECT * FROM AIOP.vKatalogProdukty WHERE KodXL = 'CZNI42027'
--
-- Produkty bez ceny (jeszcze nie wycenione):
--   SELECT * FROM AIOP.vKatalogProdukty WHERE CennikId IS NULL
-- ============================================================
