USE [ERPXL_CEIM];
GO

CREATE OR ALTER VIEW AIBI.KntGrupyDom AS

-- AIBI.KntGrupyDom — brudnopis SELECT
-- Faza 2 — iteracja 1
-- Źródło: CDN.KntGrupyDom (GIDTyp=32 — przypisania kontrahent→grupa)
-- Baseline: 4 544 wierszy (wykluczono KGD_GIDNumer=0)

WITH Sciezka_Grup AS (
    -- Anchor: korzenie (GrONumer=0)
    SELECT
        KGD_GIDNumer,
        CAST(RTRIM(KGD_Kod) AS NVARCHAR(2000)) AS Sciezka,
        0                                       AS Poziom
    FROM CDN.KntGrupyDom
    WHERE KGD_GIDTyp = -32
      AND KGD_GrONumer = 0

    UNION ALL

    -- Rekurencja: dzieci
    SELECT
        g.KGD_GIDNumer,
        CAST(p.Sciezka + '\' + RTRIM(g.KGD_Kod) AS NVARCHAR(2000)),
        p.Poziom + 1
    FROM CDN.KntGrupyDom g
    INNER JOIN Sciezka_Grup p ON p.KGD_GIDNumer = g.KGD_GrONumer
    WHERE g.KGD_GIDTyp = -32
      AND g.KGD_GrONumer > 0
      AND p.Poziom < 20
)

SELECT
    -- === Kontrahent ===
    kgd.KGD_GIDNumer                            AS ID_Kontrahenta,
    k.Knt_Akronim                               AS Akronim_Kontrahenta,
    k.Knt_Nazwa1                                AS Nazwa_Kontrahenta,

    -- === Grupa bezpośrednia ===
    kgd.KGD_GrONumer                            AS ID_Grupy,
    ISNULL(RTRIM(grp.KGD_Kod), 'Brak grupy')   AS Kod_Grupy,

    -- === Ścieżka w hierarchii ===
    ISNULL(sg.Sciezka, 'Brak grupy')            AS Sciezka_Grupy,
    ISNULL(sg.Poziom, -1)                       AS Poziom_Grupy

FROM CDN.KntGrupyDom kgd

-- Akronim i nazwa kontrahenta
LEFT JOIN CDN.KntKarty k
    ON  k.Knt_GIDNumer = kgd.KGD_GIDNumer

-- Kod grupy bezpośredniej (type=-32)
LEFT JOIN CDN.KntGrupyDom grp
    ON  grp.KGD_GIDTyp   = -32
    AND grp.KGD_GIDNumer = kgd.KGD_GrONumer

-- Ścieżka z CTE
LEFT JOIN Sciezka_Grup sg
    ON  sg.KGD_GIDNumer = kgd.KGD_GrONumer

WHERE kgd.KGD_GIDTyp   = 32
  AND kgd.KGD_GIDNumer > 0
