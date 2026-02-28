select sum(ZaV_Netto) [Netto], sum(ZaV_Netto)  + sum(Zav_vat) [Brutto], ZaV_Waluta [Waluta]
from cdn.ZamNag
JOIN cdn.ZamVAT v ON Zan_gidtyp = ZaV_GIDTyp AND ZaN_GIDNumer = ZaV_GIDNumer
Where {filtrSQL}
GROUP BY ZaV_Waluta