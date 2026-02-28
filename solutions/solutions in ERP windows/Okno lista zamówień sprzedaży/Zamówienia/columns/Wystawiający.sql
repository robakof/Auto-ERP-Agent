select Ope_Ident [Wystawiający] 
from cdn.ZamNag
JOIN cdn.OpeKarty ON ZaN_OpeNumerW = Ope_gidnumer AND ZaN_OpeTypW = Ope_GIDTyp
Where {FiltrSQL}