SELECT
    CASE WHEN MAX(TrP_Termin) = 0 THEN NULL
         ELSE CAST(DATEADD(d, MAX(TrP_Termin), '18001228') AS DATE)
    END [Termin płatności]
FROM CDN.TraPlat
JOIN CDN.TraNag ON TrN_GIDNumer = TrP_GIDNumer AND TrN_GIDTyp = TrP_GIDTyp
WHERE {filtrsql}