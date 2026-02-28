Zan_gidNumer IN (Select CDN.ZamNag.ZaN_GIDNumer

FROM CDN.ZamNag

JOIN 
CDN.ZaNOpisy ON CDN.ZaNOpisy.ZnO_ZamNumer = CDN.ZamNag.ZaN_GIDNumer

WHERE 
CDN.ZaNOpisy.ZnO_Opis COLLATE Latin1_General_CI_AS LIKE '%SEZON%')