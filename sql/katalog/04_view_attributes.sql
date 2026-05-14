-- ============================================================
-- WIDOK: Atrybuty towarow (dynamiczna lista wszystkich klas)
-- Jeden wiersz per produkt x klasa atrybutu
-- Produkt bez wartosci danego atrybutu = 1 wiersz z NULL w Wartosc
-- ============================================================

CREATE OR ALTER VIEW AIOP.vAtrybutyTowarow AS
SELECT
    -- Identyfikacja towaru
    tk.Twr_Kod              AS KodXL,
    tk.Twr_Nazwa1           AS NazwaTowaru,
    tk.Twr_GIDNumer         AS TwrGIDNumer,
    tk.Twr_GIDFirma         AS TwrGIDFirma,
    tk.Twr_GIDTyp           AS TwrGIDTyp,

    -- Klasa atrybutu
    ak.AtK_Nazwa            AS KlasaAtrybutu,
    ak.AtK_Typ              AS TypAtrybutu,        -- 1=TAK/NIE, 2=tekst, 3=liczba, 4=lista
    ak.AtK_Wielowart        AS Wielowartosciowy,
    ak.AtK_Zamknieta        AS ListaZamknieta,

    -- Wartosc (NULL = brak przypisanego atrybutu)
    a.Atr_Wartosc           AS Wartosc

FROM CDN.TwrKarty tk

CROSS JOIN (
    SELECT DISTINCT
        ak2.AtK_ID, ak2.AtK_Nazwa, ak2.AtK_Typ,
        ak2.AtK_Wielowart, ak2.AtK_Zamknieta
    FROM CDN.AtrybutyKlasy ak2
    INNER JOIN CDN.AtrybutyObiekty ao ON ao.AtO_AtKId = ak2.AtK_ID
    WHERE ao.AtO_GIDTyp = 16
) ak

LEFT JOIN CDN.Atrybuty a
    ON a.Atr_ObiNumer = tk.Twr_GIDNumer
    AND a.Atr_ObiTyp  = 16
    AND a.Atr_AtkId   = ak.AtK_ID

WHERE tk.Twr_Archiwalny = 0;
GO

-- ============================================================
-- Przyklady uzycia:
--
-- Lista klas atrybutow (z metadanymi):
--   SELECT DISTINCT KlasaAtrybutu, TypAtrybutu, Wielowartosciowy, ListaZamknieta
--   FROM AIOP.vAtrybutyTowarow
--
-- GID towaru po kodzie:
--   SELECT DISTINCT TwrGIDNumer, TwrGIDFirma, TwrGIDTyp
--   FROM AIOP.vAtrybutyTowarow WHERE KodXL = 'CZNI42027'
--
-- Wszystkie atrybuty jednego produktu:
--   SELECT KlasaAtrybutu, Wartosc
--   FROM AIOP.vAtrybutyTowarow
--   WHERE KodXL = 'CZNI42027' AND Wartosc IS NOT NULL
--
-- Produkty bez wypelnionego atrybutu CZAS PALENIA:
--   SELECT KodXL FROM AIOP.vAtrybutyTowarow
--   WHERE KlasaAtrybutu = 'CZAS PALENIA / DZIALANIA' AND Wartosc IS NULL
-- ============================================================
