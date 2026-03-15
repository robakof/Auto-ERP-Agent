-- Weryfikacja formatu numerów dokumentów TraNag przez CDN.NazwaObiektu
-- Uruchom DBA (CEiM_Reader nie ma EXECUTE)
-- Cel: potwierdzić czy rok jest YY czy YYYY, i czy format zgadza się z ręczną konstrukcją

SELECT
    sub.TrN_GIDTyp,
    sub.TrN_GIDNumer,
    sub.TrN_TrNSeria,
    sub.TrN_TrNNumer,
    sub.TrN_TrNRok,
    CDN.NazwaObiektu(sub.TrN_GIDTyp, sub.TrN_GIDNumer, 0, 2) AS Nr_Oficjalny,
    -- Porównaj z ręczną konstrukcją (prefiks + seria/numer/rok)
    CASE
        WHEN sub.TrN_GIDTyp IN (2041, 2045, 1529)
             AND EXISTS (
                 SELECT 1 FROM CDN.TraNag s
                 WHERE s.TrN_SpiTyp   = sub.TrN_GIDTyp
                   AND s.TrN_SpiNumer = sub.TrN_GIDNumer
                   AND (
                        (sub.TrN_GIDTyp = 2041 AND s.TrN_GIDTyp = 2009) OR
                        (sub.TrN_GIDTyp = 2045 AND s.TrN_GIDTyp = 2013) OR
                        (sub.TrN_GIDTyp = 1529 AND s.TrN_GIDTyp = 1497)
                   )
             )                                                          THEN '(Z)'
        WHEN sub.TrN_Stan & 2 = 2
             AND sub.TrN_GIDTyp IN (2041, 2045, 1529)                  THEN '(Z)'
        WHEN sub.TrN_GenDokMag = -1
             AND sub.TrN_GIDTyp IN (1521, 1529, 1489)                  THEN '(A)'
        WHEN sub.TrN_GenDokMag = -1                                    THEN '(s)'
        ELSE ''
    END
    + RTRIM(sub.TrN_TrNSeria) + '/' + CAST(sub.TrN_TrNNumer AS VARCHAR(10))
    + '/' + RIGHT(CAST(sub.TrN_TrNRok AS VARCHAR(4)), 2) AS Nr_Reczny_YY,
    RTRIM(sub.TrN_TrNSeria) + '/' + CAST(sub.TrN_TrNNumer AS VARCHAR(10))
    + '/' + CAST(sub.TrN_TrNRok AS VARCHAR(4))             AS Nr_Reczny_YYYY
FROM (
    SELECT TOP 1 WITH TIES
        TrN_GIDTyp, TrN_GIDNumer, TrN_TrNSeria, TrN_TrNNumer, TrN_TrNRok,
        TrN_Stan, TrN_GenDokMag
    FROM CDN.TraNag
    WHERE TrN_TrNLp = 127
    ORDER BY ROW_NUMBER() OVER (PARTITION BY TrN_GIDTyp ORDER BY TrN_GIDNumer DESC)
) sub
ORDER BY sub.TrN_GIDTyp;
