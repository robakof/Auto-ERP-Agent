-- =============================================================================
-- Etykiety wysyłkowe — dane dla wybranego klienta w grupie 10_OFERTY
-- Przeznaczenie: wypełnianie szablonu Word "Etykiety do wypełnienia.docx"
-- Jeden wiersz = jeden towar
-- =============================================================================
--
-- Parametr:
--   @klient_gid  INT  — GIDNumer grupy klienta (np. 9402 = AUCHAN)
--
-- Hierarchia grup (zawsze 3 poziomy):
--   10_OFERTY (9139)
--     └── rok:    ROM-POL (9140) | 2025 (9235) | WYPRZEDAŻ (9557) | 2026 (10719)
--                └── klient: AUCHAN (9402) | ...
--
-- Źródła:
--   AIBI.TwrGrupy  — bezpośrednia grupa towaru; filtr: ID_Grupy = @klient_gid
--   CDN.TwrKarty   — EAN, nazwa, kod
--   CDN.Atrybuty   — Wysokość (AtkId=12), Czas palenia (AtkId=9), Gramatura (AtkId=10)
--   CDN.TwrJm      — COLI (opak.), PALETA (paleta) — ilość szt. per jednostka
--

DECLARE @klient_gid INT = 9402;   -- << podstaw GIDNumer grupy klienta

SELECT
    t.Twr_Ean                               AS ean,
    t.Twr_Nazwa                             AS nazwa,
    ag.Kod_Grupy                            AS klient,

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
    AND ag.ID_Grupy  = @klient_gid
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

ORDER BY t.Twr_Nazwa;
