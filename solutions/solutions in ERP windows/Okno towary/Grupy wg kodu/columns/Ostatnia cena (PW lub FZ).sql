SELECT TOP 1
    CAST(CAST(TrE_CenaPoRabacie AS DECIMAL(15,2)) AS VARCHAR(20)) + ' ' + TrN_Waluta [Ostatnia cena]
FROM cdn.TwrKarty
JOIN cdn.TwrGrupy ON Twr_GIDNumer = TwG_GIDNumer AND Twr_GIDTyp = TwG_GIDTyp
JOIN cdn.TraElem ON TrE_TwrNumer = Twr_GIDNumer AND TrE_TwrTyp = Twr_GIDTyp
JOIN cdn.TraNag ON TrN_GIDNumer = TrE_GIDNumer AND TrN_GIDTyp = TrE_GIDTyp
WHERE TrN_GIDTyp IN (1617, 1521)
    AND {filtrSQL}
ORDER BY TrN_Data2 DESC, TrN_GIDNumer DESC
