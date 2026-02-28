select TrP_FormaNazwa [Forma Płatności]
from cdn.TraPlat
JOIN cdn.TraNag ON TrN_GIDNumer = TrP_GIDNumer AND TrN_GIDTyp = TrP_GIDTyp
Where {filtrSQL}