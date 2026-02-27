NOT EXISTS (
    SELECT 1
    FROM CDN.DaneObiekty dao
    JOIN CDN.DaneBinarne dab ON dao.DAO_DABId = dab.DAB_ID
    WHERE dao.DAO_ObiNumer = TwG_GIDNumer
      AND dao.DAO_ObiTyp = TwG_GIDTyp
      AND LOWER(dab.DAB_Rozszerzenie) = 'jpg'
)