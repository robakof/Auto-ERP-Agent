SELECT
    CASE WHEN z.ZaN_DataRealizacji = 0 THEN NULL
         ELSE CAST(DATEADD(d, z.ZaN_DataRealizacji, '18001228') AS DATE)
    END [Data realizacji ZS]
FROM CDN.TraNag
LEFT JOIN CDN.ZamNag z ON z.ZaN_GIDNumer = TrN_ZaNNumer AND TrN_ZaNTyp = 960
WHERE {filtrsql}
