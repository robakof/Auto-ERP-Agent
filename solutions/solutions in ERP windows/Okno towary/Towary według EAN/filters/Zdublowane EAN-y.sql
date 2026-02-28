Twr_Ean IN (select Twr_ean
from cdn.TwrKarty
Where Twr_ean <> '' 
GROUP BY Twr_Ean
HAVING count(twr_ean) > 1)