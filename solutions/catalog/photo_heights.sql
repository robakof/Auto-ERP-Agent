-- =============================================================================
-- Wysokości produktów z atrybutów ERP (AtkId=12)
-- Przeznaczenie: photo_preprocess.py — skalowanie proporcjonalne zdjęć katalogowych
-- Parametr: lista kodów towarów jako IN (...)
-- =============================================================================
--
-- Wejście:  lista Twr_Kod (podstawiana przez skrypt)
-- Wyjście:  Twr_Kod, wysokosc_cm
--

SELECT
    t.Twr_Kod                           AS kod,
    CAST(a.Atr_Wartosc AS FLOAT)        AS wysokosc_cm

FROM CDN.TwrKarty t
JOIN CDN.Atrybuty a
    ON  a.Atr_ObiNumer = t.Twr_GIDNumer
    AND a.Atr_ObiTyp   = 16
    AND a.Atr_AtkId    = 12

WHERE t.Twr_Kod IN ({placeholders})
  AND a.Atr_Wartosc IS NOT NULL
  AND a.Atr_Wartosc <> ''

ORDER BY t.Twr_Kod;
