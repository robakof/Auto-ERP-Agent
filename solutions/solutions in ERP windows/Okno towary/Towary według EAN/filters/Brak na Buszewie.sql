(
    ISNULL((
        SELECT SUM(z.TwZ_IlSpr)
        FROM CDN.TwrZasoby z
        WHERE z.TwZ_TwrNumer = Twr_GIDNumer
          AND z.TwZ_MagNumer IN (
              SELECT m.Mag_GIDNumer
              FROM CDN.Magazyny m
              WHERE m.MAG_Kod IN ('OTOR_GŁ','PIASK_WG')
          )
    ), 0) > 0
)
AND
(
    ISNULL((
        SELECT SUM(z.TwZ_IlSpr)
        FROM CDN.TwrZasoby z
        WHERE z.TwZ_TwrNumer = Twr_GIDNumer
          AND z.TwZ_MagNumer IN (
              SELECT m.Mag_GIDNumer
              FROM CDN.Magazyny m
              WHERE m.MAG_Kod = 'BUSZ_GŁ'
          )
    ), 0) = 0
)
