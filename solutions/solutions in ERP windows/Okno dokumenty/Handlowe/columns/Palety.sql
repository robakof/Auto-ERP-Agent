SELECT
    isnull(stuff((
        select ', ' + lt.Name + ': ' + convert(varchar(5), count(distinct lo.barcode))
        from CDN.MagNag m
        join wms.documents d with (nolock) on d.SourceDocumentId = m.MaN_GIDNumer
        join wms.items i with (nolock) on d.id=i.DocumentId
        join wms.LogisticUnitObjects lo with (nolock) on i.LogisticUnitId = lo.Id
        join wms.LogisticUnitTypes lt with (nolock) on lo.LogisticsUnitTypeId=lt.Id
        where m.MaN_ZrdNumer = TrN_GIDNumer and m.MaN_ZrdTyp = TrN_GIDTyp
        group by lt.Name
        having count(distinct lo.barcode) <> 0
        for xml path('')), 1, 2, ''), '') as [Palety]
FROM CDN.TraNag
WHERE {filtrsql}
