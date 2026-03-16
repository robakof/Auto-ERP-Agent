@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|Archiwalne|&Archiwalne:REG=all @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|BrakJpg|&Brak zdjęcia jpg:REG=all @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|DuplEAN|&Zdublowane EAN:REG=all @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|EanJm|&Niespójne EAN/JM:REG=all @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|JmMobile|&JM opak./karton bez flagi mobile:REG=all @? PAR@
@PAR ?@D17|DataOd|&Kartoteki od:REG=0 @? PAR@
@PAR ?@D17|DataDo|&do:REG=0 @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|ZlaGrupa|&Nieprawidłowa grupa:REG=all @? PAR@
(??_QArchiwalne='all' OR twr_archiwalny=1)
AND (??_QBrakJpg='all' OR NOT EXISTS(
    SELECT 1 FROM CDN.DaneObiekty dao
    JOIN CDN.DaneBinarne dab ON dao.DAO_DABId=dab.DAB_ID
    WHERE dao.DAO_ObiNumer=Twr_GIDNumer AND dao.DAO_ObiTyp=Twr_GIDTyp
    AND LOWER(dab.DAB_Rozszerzenie)='jpg'
))
AND (??_QDuplEAN='all' OR Twr_Ean IN (
    SELECT Twr_Ean FROM cdn.TwrKarty WHERE Twr_Ean<>''
    GROUP BY Twr_Ean HAVING COUNT(Twr_Ean)>1
))
AND (??_QEanJm='all' OR Twr_GIDNumer IN (
    SELECT t.Twr_GIDNumer FROM cdn.TwrKarty t
    JOIN cdn.TwrKody tk ON Twr_GIDNumer=TwK_TwrNumer AND TwK_Jm<>t.Twr_Jm
    LEFT JOIN cdn.TwrJM jm ON TwK_TwrNumer=TwJ_TwrNumer AND Twk_jm=TwJ_JmZ
    WHERE TwK_Kod IS NOT NULL AND TwJ_TwrTyp IS NULL
))
AND (??_QJmMobile='all' OR (Twr_MobSpr=1
    AND EXISTS(SELECT 1 FROM cdn.TwrJM WHERE TwJ_TwrNumer=Twr_GIDNumer AND TwJ_JmZ IN ('opak.','karton'))
    AND NOT EXISTS(SELECT 1 FROM cdn.TwrJM WHERE TwJ_TwrNumer=Twr_GIDNumer AND TwJ_JmZ IN ('opak.','karton') AND TwJ_MobSpr=1)
))
AND (??DataOd=0 OR Twr_DataUtworzenia/86400+69035>=??DataOd)
AND (??DataDo=0 OR Twr_DataUtworzenia/86400+69035<=??DataDo)
AND (??_QZlaGrupa='all' OR NOT EXISTS (
    SELECT 1 FROM CDN.TwrGrupy a
    JOIN CDN.TwrGrupy b ON b.TwG_GIDNumer=a.TwG_GrONumer AND b.TwG_GIDTyp=-16
    LEFT JOIN CDN.TwrGrupy c ON c.TwG_GIDNumer=b.TwG_GrONumer AND c.TwG_GIDTyp=-16
    LEFT JOIN CDN.TwrGrupy d ON d.TwG_GIDNumer=c.TwG_GrONumer AND d.TwG_GIDTyp=-16
    LEFT JOIN CDN.TwrGrupy e ON e.TwG_GIDNumer=d.TwG_GrONumer AND e.TwG_GIDTyp=-16
    LEFT JOIN CDN.TwrGrupy f ON f.TwG_GIDNumer=e.TwG_GrONumer AND f.TwG_GIDTyp=-16
    WHERE a.TwG_GIDNumer=Twr_GIDNumer AND a.TwG_GIDTyp=16
    AND (
        (b.TwG_GrONumer=0 AND b.TwG_GIDNumer IN (1,2,4,9,6))
        OR (c.TwG_GrONumer=0 AND c.TwG_GIDNumer IN (1,2,4,9,6))
        OR (d.TwG_GrONumer=0 AND d.TwG_GIDNumer IN (1,2,4,9,6))
        OR (e.TwG_GrONumer=0 AND e.TwG_GIDNumer IN (1,2,4,9,6))
        OR (f.TwG_GrONumer=0 AND f.TwG_GIDNumer IN (1,2,4,9,6))
    )
))