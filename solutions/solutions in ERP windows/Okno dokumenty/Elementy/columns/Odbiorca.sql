SELECT 
    odb.Knt_Akronim AS [Odbiorca]
FROM cdn.TraElem el
JOIN cdn.TraNag n
    ON n.TrN_GIDNumer = el.TrE_GIDNumer
LEFT JOIN cdn.KntKarty odb
    ON n.TrN_KnDTyp   = odb.Knt_GIDTyp
   AND n.TrN_KnDNumer = odb.Knt_GIDNumer
WHERE {FiltrSQL};
