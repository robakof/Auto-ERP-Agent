NOT EXISTS (
    SELECT 1
    FROM CDN.TwrZasoby
    WHERE TwZ_TwrNumer = Twr_GIDNumer
      AND TwZ_Ilosc > 0
)
AND EXISTS (
    SELECT 1
    FROM CDN.Atrybuty
    WHERE Atr_ObiNumer = Twr_GIDNumer
      AND Atr_ObiTyp = Twr_GIDTyp
      AND Atr_AtkId = 59
      AND Atr_Wartosc IN ('Wyprzedaż', 'Wyprzedaż - deputat')
)