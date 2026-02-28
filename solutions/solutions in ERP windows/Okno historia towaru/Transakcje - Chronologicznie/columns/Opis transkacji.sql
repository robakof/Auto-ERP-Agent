Select TnO_Opis [Opis transakcji]
from CDN.TraElem
JOIN CDN.TraNag ON TrN_GIDNumer = TrE_GIDNumer
LEFT JOIN CDN.TrNOpisy ON TrN_GIDNumer = TnO_TrnNumer
Where {filtrSQL}