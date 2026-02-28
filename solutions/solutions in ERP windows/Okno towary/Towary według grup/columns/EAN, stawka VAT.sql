Select Twr_Ean [EAN], Twr_StawkaPodSpr [VAT Sprzedaż],  Twr_StawkaPodSpr [VAT Zakupy]
from cdn.TwrKarty
JOIN cdn.TwrGrupy ON Twr_GIDNumer = TwG_GIDNumer AND Twr_GIDTyp = TwG_GIDTyp
Where {filtrSQL}