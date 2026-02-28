Select Mag_Kod [Magazyn żródłowy]
from CDN.TraElem
JOIN CDN.TraNag ON TrN_GIDNumer = TrE_GIDNumer
LEFT JOIN CDN.Magazyny ON Mag_GIDNumer = TrN_MagZNumer
Where {filtrSQL}