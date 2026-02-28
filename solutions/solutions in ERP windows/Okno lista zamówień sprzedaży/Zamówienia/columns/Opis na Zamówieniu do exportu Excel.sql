SELECT cdn.ZaNOpisy.ZnO_Opis [Opis na Zamówieniu]
FROM cdn.ZaNOpisy


JOIN cdn.ZamNag AS ZamNag1 ON cdn.ZaNOpisy.ZnO_ZamNumer =  ZamNag1.ZaN_GIDNumer	

WHERE {filtrSQL}