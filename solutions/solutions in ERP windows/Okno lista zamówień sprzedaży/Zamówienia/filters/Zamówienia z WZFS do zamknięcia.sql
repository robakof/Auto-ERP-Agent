Zan_gidnumer IN (	SELECT DISTINCT 
		Zan_gidnumer
	FROM CDN.ZamNag
	JOIN CDN.ZamElem z ON ZaN_GIDNumer = ZaE_GIDNumer AND ZaN_GIDTyp = ZaE_GIDTyp AND ZaN_Rodzaj = 4 AND ZaN_ZamTyp = 1280 
	JOIN cdn.TraSElem ts ON ZaE_GIDTyp = TrS_ZlcTyp AND ZaE_GIDNumer = TrS_ZlcNumer AND ZaE_GIDLp = TrS_ZlcLp
	JOIN cdn.TraNag tsn  ON TrS_GIDTyp = tsn.TrN_gidtyp AND TrS_GIDNumer = tsn.TrN_GIDNumer
	LEFT JOIN cdn.Rezerwacje r ON ZaN_GIDNumer = Rez_ZrdNumer AND ZaN_GIDTyp = Rez_ZrdTyp
	LEFT JOIN cdn.RezMagazyny rm ON Rez_GIDTyp=ReM_RezTyp AND Rez_GIDNumer=ReM_RezNumer  
	Where TrN_Stan IN (3,4,5) AND ZaN_Stan = 5)