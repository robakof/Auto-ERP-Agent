TrN_DokumentObcy IN(
select TrN_DokumentObcy
from cdn.TraNag 
where TrN_DokumentObcy <> '' AND TrN_Stan <> 6
GROUP BY TrN_DokumentObcy, TrN_GIDTyp, Trn_kntNumer
HAVING count(TrN_DokumentObcy) > 1) AND Trn_stan <> 6