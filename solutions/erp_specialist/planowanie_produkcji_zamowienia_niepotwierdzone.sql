-- Planowanie produkcji — zamówienia o statusie NIEPOTWIERDZONE
-- ZaN_Stan = 2 (Stan_zamowienie) — zamówienie wystawione, nie potwierdzone
-- Źródło: CDN.ZamNag + CDN.ZamElem + CDN.KntKarty + CDN.ZaNOpisy
-- Data: 2026-03-30
-- Autor: ERP Specialist
--
-- Kontekst: podstawa do planowania produkcji przez Developera.
-- Developer filtruje dalej wg potrzebnych parametrów i eksportuje do Excel.
--
-- Wynik: 22 zamówienia, ~1022 pozycji (stan na 2026-03-30)
-- Sortowanie: data realizacji rosnąco, potem ID zamówienia i nr pozycji

SELECT
    zn.ZaN_GIDNumer                                             AS ID_Zamowienia,
    zn.ZaN_ZamNumer                                             AS Nr_Zamowienia,
    CAST(DATEADD(d, zn.ZaN_DataWystawienia, '18001228') AS DATE) AS Data_Wystawienia,
    CAST(DATEADD(d, zn.ZaN_DataRealizacji,  '18001228') AS DATE) AS Data_Realizacji,
    k.Knt_Akronim                                               AS Kontrahent_Kod,
    k.Knt_Nazwa1                                                AS Kontrahent_Nazwa,
    ze.ZaE_GIDLp                                                AS Nr_Pozycji,
    ze.ZaE_TwrKod                                               AS Towar_Kod,
    ze.ZaE_TwrNazwa                                             AS Towar_Nazwa,
    ze.ZaE_Ilosc                                                AS Ilosc,
    ze.ZaE_JmZ                                                  AS Jednostka,
    CAST(op.ZnO_Opis AS NVARCHAR(500))                          AS Opis
FROM CDN.ZamNag zn
JOIN CDN.ZamElem ze
    ON ze.ZaE_GIDNumer = zn.ZaN_GIDNumer
JOIN CDN.KntKarty k
    ON k.Knt_GIDNumer = zn.ZaN_KntNumer
LEFT JOIN CDN.ZaNOpisy op
    ON op.ZnO_ZamNumer = zn.ZaN_GIDNumer
WHERE zn.ZaN_Stan = 2
  -- AND YEAR(CAST(DATEADD(d, zn.ZaN_DataRealizacji, '18001228') AS DATE)) = --year   -- filtr roku: po stronie Developera
  AND ze.ZaE_TwrKod LIKE 'CZNI%'
  AND CAST(op.ZnO_Opis AS NVARCHAR(500)) LIKE 'Zamówienie%'
ORDER BY
    zn.ZaN_DataRealizacji,
    zn.ZaN_GIDNumer,
    ze.ZaE_GIDLp;
