Select Twr_Ean [EAN]
from cdn.TwrKarty
JOIN cdn.TwrGrupy ON Twr_GIDNumer = TwG_GIDNumer AND Twr_GIDTyp = TwG_GIDTyp
Where {filtrSQL}