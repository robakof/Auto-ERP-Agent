select 
	Ope_Ident [Wystawiający],
	md.MAG_Kod [Magazyn]
from cdn.TraNag
JOIN cdn.OpeKarty ON TrN_OpeNumerW = Ope_gidnumer AND TrN_OpeTypW = Ope_GIDTyp
JOIN cdn.Magazyny md ON TrN_MagDNumer = md.MAG_GIDNumer AND TrN_MagDTyp = md.MAG_GIDTyp
Where {FiltrSQL}