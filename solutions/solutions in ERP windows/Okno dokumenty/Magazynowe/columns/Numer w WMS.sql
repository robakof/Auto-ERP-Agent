select top 1 numberstring as [Numer WMS] 

from cdn.magnag 

join wms.documents d on man_gidnumer=d.sourcedocumentid

where d.DocumentCancellationDate IS NULL AND {filtrSQL}