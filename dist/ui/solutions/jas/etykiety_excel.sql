-- =============================================================================
-- Etykiety wysyłkowe — dane dla listy kodów produktów (import z Excel)
-- Przeznaczenie: wypełnianie szablonu Word "Etykiety do wypełnienia.docx"
-- Jeden wiersz = jeden towar
-- =============================================================================
--
-- Parametr (podstawiany przez Python):
--   {kody_in}  — lista kodów Twr_Kod w formacie SQL: 'CZNI0001','CZNI0002',...
--
-- Źródła:
--   CDN.TwrKarty   — EAN, nazwa, kod
--   CDN.Atrybuty   — Wysokość (AtkId=12), Czas palenia (AtkId=9), Gramatura (AtkId=10)
--   CDN.TwrJm      — COLI (opak.), PALETA (paleta) — ilość szt. per jednostka
--

SELECT
    t.Twr_Ean                               AS ean,
    t.Twr_Nazwa                             AS nazwa,

    -- Atrybuty produktu
    MAX(CASE WHEN a.Atr_AtkId = 12 THEN a.Atr_Wartosc END)  AS wysokosc_cm,
    MAX(CASE WHEN a.Atr_AtkId = 9  THEN a.Atr_Wartosc END)  AS czas_palenia_h,
    MAX(CASE WHEN a.Atr_AtkId = 10 THEN a.Atr_Wartosc END)  AS gramatura_g,

    -- Jednostki pakowania
    MAX(CASE WHEN j.TwJ_JmZ = 'opak.'  THEN CAST(j.TwJ_PrzeliczL AS VARCHAR(10)) END)  AS coli_szt,
    MAX(CASE WHEN j.TwJ_JmZ = 'paleta' THEN CAST(j.TwJ_PrzeliczL AS VARCHAR(10)) END)  AS paleta_szt

FROM CDN.TwrKarty t
LEFT JOIN CDN.Atrybuty a
    ON  a.Atr_ObiNumer = t.Twr_GIDNumer
    AND a.Atr_ObiTyp   = 16
    AND a.Atr_AtkId    IN (9, 10, 12)
LEFT JOIN CDN.TwrJm j
    ON  j.TwJ_TwrNumer = t.Twr_GIDNumer
    AND j.TwJ_JmZ      IN ('opak.', 'paleta')

WHERE t.Twr_Kod IN ({kody_in})

GROUP BY
    t.Twr_GIDNumer,
    t.Twr_Ean,
    t.Twr_Nazwa

ORDER BY t.Twr_Nazwa;
