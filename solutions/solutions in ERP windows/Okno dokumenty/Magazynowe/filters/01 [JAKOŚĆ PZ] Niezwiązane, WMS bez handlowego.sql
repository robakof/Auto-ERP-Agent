@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|Niezwiazany|&Brak powiązania z FZ:REG=all @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak','tak')|WmsOk|&Zrealizowane WMS bez handlowego:REG=all @? PAR@
(??_QNiezwiazany='all' OR MaN_ZrdNumer=0)
AND (??_QWmsOk='all' OR (ISNULL(MaN_ZrdTyp,0) IN (960,0) AND MaN_Stan=5))
