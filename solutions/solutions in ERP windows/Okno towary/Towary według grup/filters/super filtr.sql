@PAR ?@S100|Szukaj|&Szukaj (kod / nazwa / EAN):REG= @? PAR@
@PAR ?@R(SELECT '' AS ID,'(wsz.)' AS KOD UNION ALL SELECT Atr_Wartosc,Atr_Wartosc FROM CDN.Atrybuty WHERE Atr_AtkId=59 GROUP BY Atr_Wartosc ORDER BY 1)|StatusOfertowy|&Status ofertowy:REG= @? PAR@
@PAR ?@R(SELECT '' AS ID,'(wsz.)' AS KOD UNION ALL SELECT 'Tak','Archiwalny' UNION ALL SELECT 'Nie','Aktywny')|Archiwalny|&Archiwalny:REG= @? PAR@
@PAR ?@R(SELECT '' AS ID,'(wsz.)' AS KOD UNION ALL SELECT 'brak','Brak stanu' UNION ALL SELECT 'ma','Z dowolnym stanem')|StanMag|&Stan magazynowy:REG= @? PAR@
@PAR ?@R(SELECT '' AS ID,'(wsz.)' AS KOD UNION ALL SELECT 'Tak','Tak' UNION ALL SELECT 'Nie','Nie')|MobSpr|&Sprzedaz mobilna:REG= @? PAR@
@PAR ?@R(SELECT '' AS ID,'(wsz.)' AS KOD UNION ALL SELECT CAST(CAST(Twr_StawkaPodSpr AS INT) AS VARCHAR(2)),CAST(CAST(Twr_StawkaPodSpr AS INT) AS VARCHAR(2))+' ('+Twr_GrupaPodSpr+')' FROM CDN.TwrKarty GROUP BY Twr_StawkaPodSpr,Twr_GrupaPodSpr)|StawkaVatSpr|&Stawka VAT sprzedaz:REG= @? PAR@
@PAR ?@D17|DataOd|&Utworzono od:REG=0 @? PAR@
@PAR ?@D17|DataDo|&Utworzono do:REG=0 @? PAR@

(??Szukaj='' OR Twr_Kod LIKE '%'+??Szukaj+'%' OR Twr_Ean LIKE '%'+??Szukaj+'%' OR Twr_Nazwa LIKE '%'+??Szukaj+'%')
AND (??StatusOfertowy='' OR EXISTS(SELECT 1 FROM CDN.Atrybuty WHERE Atr_ObiNumer=Twr_GIDNumer AND Atr_ObiTyp=Twr_GIDTyp AND Atr_AtkId=59 AND Atr_Wartosc=??StatusOfertowy))
AND (??Archiwalny='' OR Twr_Archiwalny=CASE WHEN ??Archiwalny='Tak' THEN 1 ELSE 0 END)
AND (??StanMag='' OR (??StanMag='brak' AND NOT EXISTS(SELECT 1 FROM CDN.TwrZasoby WHERE TwZ_TwrNumer=Twr_GIDNumer AND TwZ_Ilosc>0)) OR (??StanMag='ma' AND EXISTS(SELECT 1 FROM CDN.TwrZasoby WHERE TwZ_TwrNumer=Twr_GIDNumer AND TwZ_Ilosc>0)))
AND (??MobSpr='' OR Twr_MobSpr=CASE WHEN ??MobSpr='Tak' THEN '1' ELSE '0' END)
AND (??StawkaVatSpr='' OR CAST(CAST(Twr_StawkaPodSpr AS INT) AS VARCHAR(2))=??StawkaVatSpr)
AND (??DataOd=0 OR Twr_DataUtworzenia/86400+69035>=??DataOd)
AND (??DataDo=0 OR Twr_DataUtworzenia/86400+69035<=??DataDo)