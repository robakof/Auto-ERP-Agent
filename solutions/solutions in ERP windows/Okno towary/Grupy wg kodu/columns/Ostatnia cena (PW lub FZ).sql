SELECT TOP 1
    CAST(CAST(TrE_CenaPoRabacie AS DECIMAL(15,2)) AS VARCHAR(20)) + ' ' + TrE_Waluta [Ostatnia cena]
FROM cdn.TwrKarty
JOIN cdn.TwrGrupy ON Twr_GIDNumer = TwG_GIDNumer AND Twr_GIDTyp = TwG_GIDTyp
JOIN cdn.TraElem ON TrE_TwrNumer = Twr_GIDNumer
    AND TrE_TwrTyp = Twr_GIDTyp
    AND TrE_GIDTyp IN (1617, 1521)
WHERE {filtrSQL}
ORDER BY TrE_GIDNumer DESC
