select 
isnull(stuff((select ', ', [Rodzaj palety] as [text()], + ': ' + [Ilość]  as [text()]
from 
(select lt.Name as [Rodzaj palety],  convert(varchar(5),count (distinct lo.barcode)) as [Ilość] from  
		 CDN.MagNag
			join wms.documents d   with (nolock)on SourceDocumentId=MaN_GIDNumer
			join wms.items i  with (nolock) on d.id=i.DocumentId
			join wms.LogisticUnitObjects lo  with (nolock) on i.LogisticUnitId = lo.Id
			join wms.LogisticUnitTypes lt  with (nolock) on lo.LogisticsUnitTypeId=lt.Id
			where {filtrsql}
			group by lt.name
			having count (distinct lo.barcode) <>0) cte

for xml path ('')),1,2,''),'') as [Palety]
