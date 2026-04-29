-- KSeF coverage check — lista dokumentów kwalifikujących się do wysyłki
-- Używane przez raport do porównania: Comarch vs ksef_wysylka
-- Filtr daty: wstrzykiwany przez Python (WHERE_EXTRA)
-- Rodzaj klasyfikacji: FS / FSK / FSK_SKONTO (po stronie Python na podstawie typ + zwr_numer)

SELECT
    n.TrN_GIDNumer                                              AS gid,
    n.TrN_GIDTyp                                                AS typ,
    n.TrN_ZwrNumer                                              AS zwr_numer,
    CASE
        WHEN n.TrN_GIDTyp = 2033
        THEN 'FS-' + CAST(n.TrN_TrNNumer AS VARCHAR(20))
            + '/' + RIGHT('0' + CAST(MONTH(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(2)), 2)
            + '/' + RIGHT(CAST(YEAR(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(4)), 2)
            + '/' + RTRIM(n.TrN_TrNSeria)
        ELSE 'FSK-' + CAST(n.TrN_TrNNumer AS VARCHAR(20))
            + '/' + RIGHT('0' + CAST(MONTH(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(2)), 2)
            + '/' + RIGHT(CAST(YEAR(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(4)), 2)
            + '/' + RTRIM(n.TrN_TrNSeria)
    END                                                         AS nr_faktury,
    CONVERT(DATE, DATEADD(day, n.TrN_Data2, '1800-12-28'))      AS data_wystawienia
FROM CDN.TraNag n
WHERE n.TrN_GIDTyp IN (2033, 2041)
  AND n.TrN_Stan IN (3, 4, 5)
ORDER BY n.TrN_GIDTyp, n.TrN_GIDNumer
