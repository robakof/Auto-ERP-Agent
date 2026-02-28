Zan_gidNumer IN (select ZaN_GIDNumer
from cdn.ZamNag
JOIN cdn.OpeKarty ON ZaN_OpeNumerW = Ope_gidNumer AND ZaN_OpeTypW = Ope_GIDTyp
Where Ope_Ident LIKE '%'+ + '%' OR Ope_Nazwisko LIKE '%'+ + '%')