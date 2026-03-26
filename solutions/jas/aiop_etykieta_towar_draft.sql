-- =============================================================================
-- AIOP.EtykietaTowar — widok operacyjny dla etykiet wysyłkowych
-- Schema: AIOP (aplikacyjna warstwa dostępowa, read-only)
-- =============================================================================
--
-- Jeden wiersz = jeden towar (wszystkie aktywne kartoteki)
-- Filtrowanie odbywa się po stronie aplikacji:
--   Tryb ERP:   JOIN AIBI.TwrGrupy ON ID_Towaru = Twr_GIDNumer WHERE ID_Grupy = @klient_gid
--   Tryb Excel: WHERE Twr_Kod IN (...)
--
-- Kolumny:
--   Twr_GIDNumer  — klucz towaru (do JOINa z grupami)
--   Twr_Kod       — kod towaru (filtrowanie tryb Excel)
--   ean           — kod EAN-13
--   nazwa         — pełna nazwa towaru
--   wysokosc_cm   — atrybut AtkId=12
--   czas_palenia_h— atrybut AtkId=9
--   gramatura_g   — atrybut AtkId=10
--   coli_szt      — przelicznik JmZ='opak.'
--   paleta_szt    — przelicznik JmZ='paleta'
--
-- Rozszerzenie (np. kraj): ALTER VIEW AIOP.EtykietaTowar — dopisać kolumnę.
-- =============================================================================

CREATE VIEW AIOP.EtykietaTowar AS

SELECT
    t.Twr_GIDNumer,
    t.Twr_Kod,
    t.Twr_Ean                                                                           AS ean,
    t.Twr_Nazwa                                                                         AS nazwa,

    -- Atrybuty produktu
    MAX(CASE WHEN a.Atr_AtkId = 12 THEN a.Atr_Wartosc END)                             AS wysokosc_cm,
    MAX(CASE WHEN a.Atr_AtkId = 9  THEN a.Atr_Wartosc END)                             AS czas_palenia_h,
    MAX(CASE WHEN a.Atr_AtkId = 10 THEN a.Atr_Wartosc END)                             AS gramatura_g,

    -- Jednostki pakowania
    MAX(CASE WHEN j.TwJ_JmZ = 'opak.'  THEN CAST(j.TwJ_PrzeliczL AS VARCHAR(10)) END) AS coli_szt,
    MAX(CASE WHEN j.TwJ_JmZ = 'paleta' THEN CAST(j.TwJ_PrzeliczL AS VARCHAR(10)) END) AS paleta_szt

FROM CDN.TwrKarty t
LEFT JOIN CDN.Atrybuty a
    ON  a.Atr_ObiNumer = t.Twr_GIDNumer
    AND a.Atr_ObiTyp   = 16
    AND a.Atr_AtkId    IN (9, 10, 12)
LEFT JOIN CDN.TwrJm j
    ON  j.TwJ_TwrNumer = t.Twr_GIDNumer
    AND j.TwJ_JmZ      IN ('opak.', 'paleta')

GROUP BY
    t.Twr_GIDNumer,
    t.Twr_Kod,
    t.Twr_Ean,
    t.Twr_Nazwa;
