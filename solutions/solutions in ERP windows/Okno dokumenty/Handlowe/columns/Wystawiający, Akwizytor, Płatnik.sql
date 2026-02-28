select Ope_Ident [Wystawiający], ak.Knt_Akronim [Akwizytor], pl. Knt_Akronim [Płatnik]
from cdn.TraNag
JOIN cdn.OpeKarty op ON TrN_OpeNumerW = Ope_gidnumer AND TrN_OpeTypW = Ope_GIDTyp
JOIN cdn.KntKarty ak ON TrN_AkwNumer = ak.Knt_gidnumer AND TrN_AkwTyp = ak.Knt_GidTyp
JOIN cdn.KntKarty pl ON TrN_KnpNumer = pl.Knt_gidnumer AND TrN_KnpTyp = pl.Knt_GidTyp
Where {FiltrSQL}
