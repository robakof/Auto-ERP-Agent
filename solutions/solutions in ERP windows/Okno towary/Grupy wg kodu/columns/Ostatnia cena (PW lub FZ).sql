SELECT TOP 1
    CAST(sub.TrE_CenaPoRabacie AS DECIMAL(15,2)) [Ostatnia cena]
FROM (
    -- Ostatnia FZ (dowolna)
    SELECT TOP 1
        e.TrE_CenaPoRabacie, e.TrE_GIDNumer, e.TrE_Waluta
    FROM cdn.TwrKarty tw
    JOIN cdn.TwrGrupy ON tw.Twr_GIDNumer = TwG_GIDNumer AND tw.Twr_GIDTyp = TwG_GIDTyp
    JOIN cdn.TraElem e ON e.TrE_TwrNumer = tw.Twr_GIDNumer
        AND e.TrE_TwrTyp = tw.Twr_GIDTyp
        AND e.TrE_GIDTyp = 1521
    WHERE {filtrSQL}
    ORDER BY e.TrE_GIDNumer DESC

    UNION ALL

    -- Ostatnie PW z opisem zaczynającym się od "P_P Otorowo"
    SELECT TOP 1
        e.TrE_CenaPoRabacie, e.TrE_GIDNumer, e.TrE_Waluta
    FROM cdn.TwrKarty tw
    JOIN cdn.TwrGrupy ON tw.Twr_GIDNumer = TwG_GIDNumer AND tw.Twr_GIDTyp = TwG_GIDTyp
    JOIN cdn.TraElem e ON e.TrE_TwrNumer = tw.Twr_GIDNumer
        AND e.TrE_TwrTyp = tw.Twr_GIDTyp
        AND e.TrE_GIDTyp = 1617
    WHERE {filtrSQL}
        AND EXISTS (
            SELECT 1 FROM cdn.TrNOpisy o
            WHERE o.TnO_TrnNumer = e.TrE_GIDNumer
                AND o.TnO_TrnTyp = e.TrE_GIDTyp
                AND o.TnO_Opis LIKE 'P_P Otorowo%'
        )
    ORDER BY e.TrE_GIDNumer DESC
) AS sub
ORDER BY sub.TrE_GIDNumer DESC
