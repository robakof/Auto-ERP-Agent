SELECT
    SUM(TrP_PozostajeSys) [Przeterminowane należności (PLN)]
FROM cdn.ZamNag
JOIN cdn.TraPlat
    ON TrP_KntNumer = ISNULL(NULLIF(ZaN_KnPNumer, 0), ZaN_KntNumer)
    AND TrP_KntTyp  = ISNULL(NULLIF(ZaN_KnPTyp,  0), ZaN_KntTyp)
WHERE TrP_Typ = 2
    AND TrP_Rozliczona = 0
    AND TrP_Pozostaje > 0
    AND TrP_Termin < DATEDIFF(day, '18001228', GETDATE())
    AND {filtrSQL}
