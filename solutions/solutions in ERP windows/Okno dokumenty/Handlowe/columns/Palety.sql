select
isnull(stuff((select ', ' + [Rodzaj palety] + ': ' + [Ilość]
from
(select lt.Name as [Rodzaj palety], convert(varchar(5),count(distinct lo.barcode)) as [Ilość]
from CDN.TraNag
join CDN.MagNag on MaN_ZrdTyp = TrN_GIDTyp and MaN_ZrdNumer = TrN_GIDNumer
join wms.documents d with (nolock) on d.SourceDocumentId = MaN_GIDNumer
join wms.items i with (nolock) on d.id=i.DocumentId
join wms.LogisticUnitObjects lo with (nolock) on i.LogisticUnitId = lo.Id
join wms.LogisticUnitTypes lt with (nolock) on lo.LogisticsUnitTypeId=lt.Id
where {filtrsql}
group by lt.name
having count(distinct lo.barcode) <> 0) cte
for xml path ('')),1,2,''),'') as [Palety]
