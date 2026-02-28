select Ope_Ident [Wystawiający], Knt_Akronim [Akwizytor]
from cdn.TraNag
JOIN cdn.OpeKarty ON TrN_OpeNumerW = Ope_gidnumer AND TrN_OpeTypW = Ope_GIDTyp
JOIN cdn.KntKarty ON TrN_AkwNumer = Knt_gidnumer AND TrN_AkwTyp = Knt_GidTyp
Where {filtrSQL}