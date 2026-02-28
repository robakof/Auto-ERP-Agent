@PAR ?@S100|Szukaj|&Szukaj (kod / nazwa / EAN):REG= @? PAR@
@PAR ?@R(SELECT '0' AS ID,'(wsz.)' AS KOD UNION ALL SELECT Atr_Wartosc,Atr_Wartosc FROM CDN.Atrybuty WHERE Atr_AtkId=59 GROUP BY Atr_Wartosc ORDER BY 1)|Status|&Status ofertowy:REG=0 @? PAR@
@PAR ?@R(SELECT '0' AS ID,'(wsz.)' AS KOD UNION ALL SELECT Atr_Wartosc,Atr_Wartosc FROM CDN.Atrybuty WHERE Atr_AtkId=3 GROUP BY Atr_Wartosc ORDER BY 1)|Sezon|&Sezon:REG=0 @? PAR@
@PAR ?@R(SELECT '0' AS ID,'(wsz.)' AS KOD UNION ALL SELECT 'Tak','Archiwalny' UNION ALL SELECT 'Nie','Aktywny')|Archiwalny|&Archiwalny:REG=0 @? PAR@
@PAR ?@R(SELECT '0' AS ID,'(wsz.)' AS KOD UNION ALL SELECT 'brak','Brak stanu' UNION ALL SELECT 'ma','Z dowolnym stanem')|StanMag|&Stan magazynowy:REG=0 @? PAR@
@PAR ?@R(SELECT '0' AS ID,'(wsz.)' AS KOD UNION ALL SELECT 'Tak','Tak' UNION ALL SELECT 'Nie','Nie')|MobSpr|&Sprzedaz mobilna:REG=0 @? PAR@

(??Szukaj='' OR Twr_Kod LIKE '%'+??Szukaj+'%' OR Twr_Ean LIKE '%'+??Szukaj+'%' OR Twr_Nazwa LIKE '%'+??Szukaj+'%')
AND (??_QStatus='0' OR EXISTS(SELECT 1 FROM CDN.Atrybuty WHERE Atr_ObiNumer=Twr_GIDNumer AND Atr_ObiTyp=Twr_GIDTyp AND Atr_AtkId=59 AND Atr_Wartosc=??_QStatus))
AND (??_QSezon='0' OR EXISTS(SELECT 1 FROM CDN.Atrybuty WHERE Atr_ObiNumer=Twr_GIDNumer AND Atr_ObiTyp=Twr_GIDTyp AND Atr_AtkId=3 AND Atr_Wartosc=??_QSezon))
AND (??_QArchiwalny='0' OR Twr_Archiwalny=CASE WHEN ??_QArchiwalny='Tak' THEN 1 ELSE 0 END)
AND (??_QStanMag='0' OR (??_QStanMag='brak' AND NOT EXISTS(SELECT 1 FROM CDN.TwrZasoby WHERE TwZ_TwrNumer=Twr_GIDNumer AND TwZ_Ilosc>0)) OR (??_QStanMag='ma' AND EXISTS(SELECT 1 FROM CDN.TwrZasoby WHERE TwZ_TwrNumer=Twr_GIDNumer AND TwZ_Ilosc>0)))
AND (??_QMobSpr='0' OR Twr_MobSpr=CASE WHEN ??_QMobSpr='Tak' THEN '1' ELSE '0' END)