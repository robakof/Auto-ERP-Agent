@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|FiskalneRS|&Fiskalne bez RS:REG=all @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|Niezafiskal|&Niezafiskalizowane:REG=all @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|WydPrzyj|&Wydania/przyjęcia do weryfikacji:REG=all @? PAR@
(??_QFiskalneRS='all' OR (trn_fiskalny<>0 AND trn_konnumer=0))
AND (??_QNiezafiskal='all' OR (trn_fiskalny IN (0,2) AND TrN_GIDTyp!=2042 AND trn_stan!=6))
AND (??_QWydPrzyj='all' OR (trn_stan<>6 AND trn_spinumer=0
    AND NOT EXISTS(SELECT 1 FROM cdn.TraSElem WHERE TrS_SpiNumer=TrN_GIDNumer)
    AND EXISTS(SELECT 1 FROM cdn.TraSElem WHERE TrS_ZwrNumer=TrN_GIDNumer)
    AND NOT EXISTS(SELECT 1 FROM cdn.trnopisy WHERE tno_trnnumer=trn_gidnumer AND tno_trntyp=trn_gidtyp AND tno_opis='Dokument wygenerowany automatycznie w wyniku zatwierdzenia faktury-spinacza z ceną różną od ceny na elemencie źródłowym')))
