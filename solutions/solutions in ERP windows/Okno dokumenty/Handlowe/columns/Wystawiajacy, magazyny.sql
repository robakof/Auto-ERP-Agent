select 
	Ope_Ident [Wystawiający],
	mz.MAG_Kod [Magazyn źródłowy],
	md.MAG_Kod [Magazyn docelowy]
from cdn.TraNag
JOIN cdn.OpeKarty ON TrN_OpeNumerW = Ope_gidnumer AND TrN_OpeTypW = Ope_GIDTyp
JOIN cdn.Magazyny mz ON TrN_MagZNumer = mz.MAG_GIDNumer AND TrN_MagZTyp = mz.MAG_GIDTyp
JOIN cdn.Magazyny md ON TrN_MagDNumer = md.MAG_GIDNumer AND TrN_MagDTyp = md.MAG_GIDTyp
Where {FiltrSQL}