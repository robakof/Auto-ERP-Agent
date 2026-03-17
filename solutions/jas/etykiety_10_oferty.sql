-- =============================================================================
-- Etykiety wysyłkowe — dane dla grupy 10_OFERTY (pełna hierarchia)
-- Przeznaczenie: wypełnianie szablonu Word "Etykiety do wypełnienia.docx"
-- Jeden wiersz = jeden towar
-- =============================================================================
--
-- Źródła:
--   CDN.TwrGrupy      — rekurencja po drzewie grup (GIDTyp=-16) od 10_OFERTY (GID=9139)
--   AIBI.TwrGrupy     — widok: bezpośrednia grupa towaru (Kod_Grupy = podgrupa etykiety)
--   CDN.TwrKarty      — EAN, nazwa, kod
--   CDN.Atrybuty      — Wysokość (AtkId=12), Czas palenia (AtkId=9), Gramatura (AtkId=10)
--   CDN.TwrJm         — COLI (opak.), PALETA (paleta) — ilość szt. per jednostka
--
-- Uwaga: AIBI.TwrGrupy pokazuje tylko bezpośredniego rodzica towaru.
-- Filtr przez rekurencyjny CTE zapewnia objęcie całej hierarchii
-- (np. AUCHAN → 2025 → 10_OFERTY).
--

WITH grupy_10_oferty AS (
    -- Korzeń: sam 10_OFERTY
    SELECT TwG_GIDNumer, TwG_Kod
    FROM   CDN.TwrGrupy
    WHERE  TwG_GIDNumer = 9139
      AND  TwG_GIDTyp   = -16

    UNION ALL

    -- Rekurencja: wszystkie podgrupy na dowolnej głębokości
    SELECT g.TwG_GIDNumer, g.TwG_Kod
    FROM   CDN.TwrGrupy g
    JOIN   grupy_10_oferty p
        ON  g.TwG_GrONumer = p.TwG_GIDNumer
        AND g.TwG_GIDTyp   = -16
)

SELECT
    t.Twr_Ean                               AS ean,
    t.Twr_Nazwa                             AS nazwa,
    ag.Kod_Grupy                            AS podgrupa,

    -- Atrybuty produktu
    MAX(CASE WHEN a.Atr_AtkId = 12 THEN a.Atr_Wartosc END)  AS wysokosc_cm,
    MAX(CASE WHEN a.Atr_AtkId = 9  THEN a.Atr_Wartosc END)  AS czas_palenia_h,
    MAX(CASE WHEN a.Atr_AtkId = 10 THEN a.Atr_Wartosc END)  AS gramatura_g,

    -- Jednostki pakowania
    MAX(CASE WHEN j.TwJ_JmZ = 'opak.'  THEN CAST(j.TwJ_PrzeliczL AS VARCHAR(10)) END)  AS coli_szt,
    MAX(CASE WHEN j.TwJ_JmZ = 'paleta' THEN CAST(j.TwJ_PrzeliczL AS VARCHAR(10)) END)  AS paleta_szt

FROM CDN.TwrKarty t
JOIN AIBI.TwrGrupy ag
    ON  ag.ID_Towaru = t.Twr_GIDNumer
    AND ag.ID_Grupy  IN (SELECT TwG_GIDNumer FROM grupy_10_oferty)
LEFT JOIN CDN.Atrybuty a
    ON  a.Atr_ObiNumer = t.Twr_GIDNumer
    AND a.Atr_ObiTyp   = 16
    AND a.Atr_AtkId    IN (9, 10, 12)
LEFT JOIN CDN.TwrJm j
    ON  j.TwJ_TwrNumer = t.Twr_GIDNumer
    AND j.TwJ_JmZ      IN ('opak.', 'paleta')

GROUP BY
    t.Twr_GIDNumer,
    t.Twr_Ean,
    t.Twr_Nazwa,
    ag.Kod_Grupy

ORDER BY ag.Kod_Grupy, t.Twr_Nazwa;
