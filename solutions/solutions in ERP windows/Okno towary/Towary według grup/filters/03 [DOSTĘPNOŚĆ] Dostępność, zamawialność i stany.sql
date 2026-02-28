@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|Wyprzedane|&Wyprzedane:REG=all @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|Buszewo|&Brak na Buszewie:REG=all @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak' UNION ALL SELECT 'Nie','nie')|Mobilna|&Mobilna sprzedaż:REG=all @? PAR@
(??_QWyprzedane='all' OR (
    NOT EXISTS(SELECT 1 FROM CDN.TwrZasoby WHERE TwZ_TwrNumer=Twr_GIDNumer AND TwZ_Ilosc>0)
    AND EXISTS(SELECT 1 FROM CDN.Atrybuty WHERE Atr_ObiNumer=Twr_GIDNumer AND Atr_ObiTyp=Twr_GIDTyp AND Atr_AtkId=59 AND Atr_Wartosc IN ('Wyprzedaż','Wyprzedaż - deputat'))
))
AND (??_QBuszewo='all' OR (
    ISNULL((SELECT SUM(z.TwZ_IlSpr) FROM CDN.TwrZasoby z WHERE z.TwZ_TwrNumer=Twr_GIDNumer AND z.TwZ_MagNumer IN (SELECT Mag_GIDNumer FROM CDN.Magazyny WHERE MAG_Kod IN ('OTOR_GŁ','PIASK_WG'))),0)>0
    AND ISNULL((SELECT SUM(z.TwZ_IlSpr) FROM CDN.TwrZasoby z WHERE z.TwZ_TwrNumer=Twr_GIDNumer AND z.TwZ_MagNumer IN (SELECT Mag_GIDNumer FROM CDN.Magazyny WHERE MAG_Kod='BUSZ_GŁ')),0)=0
))
AND (??_QMobilna='all' OR Twr_MobSpr=CASE WHEN ??_QMobilna='tak' THEN '1' ELSE '0' END)