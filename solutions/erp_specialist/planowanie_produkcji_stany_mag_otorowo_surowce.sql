-- Planowanie produkcji — stany magazynowe: Magazyn surowce Otorowo
-- Magazyn: OTOR_SUR (MAG_GIDNumer = 4)
-- Źródło: CDN.TwrZasobyMag + CDN.TwrPartie + CDN.TwrKarty
-- Data: 2026-03-30
-- Autor: ERP Specialist
--
-- Kontekst: surowce dostępne do planowania produkcji.
-- Developer używa tego jako drugiego wejścia (obok zamówień ZaN_Stan=2).
-- HAVING Stan > 0 — pomija towary z zerowym stanem.
--
-- Wynik: ~324 towary z niezerowym stanem (stan na 2026-03-30)

SELECT
    t.Twr_Kod                   AS Towar_Kod,
    t.Twr_Nazwa                 AS Towar_Nazwa,
    t.Twr_Jm                    AS Jednostka,
    SUM(zm.TZM_Ilosc)           AS Stan
FROM CDN.TwrZasobyMag zm
JOIN CDN.TwrPartie tp
    ON tp.TPa_Id = zm.TZM_TPaId
JOIN CDN.TwrKarty t
    ON t.Twr_GIDNumer = tp.TPa_TwrNumer
WHERE zm.TZM_MagNumer = 4          -- Magazyn surowce Otorowo (OTOR_SUR)
GROUP BY
    t.Twr_GIDNumer,
    t.Twr_Kod,
    t.Twr_Nazwa,
    t.Twr_Jm
HAVING SUM(zm.TZM_Ilosc) > 0
ORDER BY t.Twr_Kod;
