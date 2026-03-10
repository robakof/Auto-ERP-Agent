@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|NieOpisane|&Nie opisane (FZ):REG=all @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|Zdublowane|&Zdublowany nr dostawcy:REG=all @? PAR@
(??_QNieOpisane='all' OR (TrN_GIDNumer NOT IN (SELECT OWE_GIDNumer FROM cdn.OpisWymElem) AND TrN_GIDTyp IN (1521,1529,1489,1497,1490,1498)))
AND (??_QZdublowane='all' OR (TrN_Stan<>6 AND TrN_DokumentObcy IN (SELECT TrN_DokumentObcy FROM cdn.TraNag WHERE TrN_DokumentObcy<>'' AND TrN_Stan<>6 GROUP BY TrN_DokumentObcy,TrN_GIDTyp,TrN_KntNumer HAVING COUNT(TrN_DokumentObcy)>1)))
