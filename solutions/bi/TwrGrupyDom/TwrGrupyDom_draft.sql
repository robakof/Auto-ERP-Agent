-- AIBI.TwrGrupyDom — brudnopis SELECT
-- Faza 2 — iteracja 2 (dodano Kod_Towaru, Nazwa_Towaru via JOIN CDN.TwrKarty)
-- Źródło: CDN.TwrGrupyDom (GIDTyp=16 — przypisania towar→grupa)
-- Baseline: 10 122 wierszy (wykluczono TGD_GIDNumer=0)

WITH Sciezka_Grup AS (
    -- Anchor: korzenie (GrONumer=0)
    SELECT
        TGD_GIDNumer,
        CAST(RTRIM(TGD_Kod) AS NVARCHAR(2000)) AS Sciezka,
        0                                       AS Poziom
    FROM CDN.TwrGrupyDom
    WHERE TGD_GIDTyp = -16
      AND TGD_GrONumer = 0

    UNION ALL

    -- Rekurencja: dzieci
    SELECT
        g.TGD_GIDNumer,
        CAST(p.Sciezka + '\' + RTRIM(g.TGD_Kod) AS NVARCHAR(2000)),
        p.Poziom + 1
    FROM CDN.TwrGrupyDom g
    INNER JOIN Sciezka_Grup p ON p.TGD_GIDNumer = g.TGD_GrONumer
    WHERE g.TGD_GIDTyp = -16
      AND g.TGD_GrONumer > 0
      AND p.Poziom < 20
)

SELECT
    -- === Towar ===
    tgd.TGD_GIDNumer                            AS ID_Towaru,
    t.Twr_Kod                                   AS Kod_Towaru,
    t.Twr_Nazwa                                 AS Nazwa_Towaru,

    -- === Grupa bezpośrednia ===
    tgd.TGD_GrONumer                            AS ID_Grupy,
    ISNULL(RTRIM(grp.TGD_Kod), 'Brak grupy')   AS Kod_Grupy,

    -- === Ścieżka w hierarchii ===
    ISNULL(sg.Sciezka, 'Brak grupy')            AS Sciezka_Grupy,
    ISNULL(sg.Poziom, -1)                       AS Poziom_Grupy

FROM CDN.TwrGrupyDom tgd

-- Kod i nazwa towaru
LEFT JOIN CDN.TwrKarty t
    ON  t.Twr_GIDNumer = tgd.TGD_GIDNumer

-- Kod grupy bezpośredniej (type=-16)
LEFT JOIN CDN.TwrGrupyDom grp
    ON  grp.TGD_GIDTyp   = -16
    AND grp.TGD_GIDNumer = tgd.TGD_GrONumer

-- Ścieżka z CTE
LEFT JOIN Sciezka_Grup sg
    ON  sg.TGD_GIDNumer = tgd.TGD_GrONumer

WHERE tgd.TGD_GIDTyp   = 16
  AND tgd.TGD_GIDNumer > 0
