select Ope_Ident [Wystawiający], Trn_VatRejestr [Rejestr VAT]
from cdn.TraNag
JOIN cdn.OpeKarty ON TrN_OpeNumerW = Ope_gidnumer AND TrN_OpeTypW = Ope_GIDTyp
Where {FiltrSQL}