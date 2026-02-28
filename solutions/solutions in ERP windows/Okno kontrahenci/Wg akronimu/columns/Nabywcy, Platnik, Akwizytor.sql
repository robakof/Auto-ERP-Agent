select NabAkronim [Nabywca], PlaAkronim [Płatnik], CASE WHEN AkwKntnumer = 0 THEN '' ELSE AkwAkronim END [Akwizytor]
from cdn.KntKarty odb 
join (select Knt_GIDNumer as NabKntnumer, knt_akronim as NabAkronim from cdn.KntKarty ) as nab ON odb.Knt_KnGNumer = NabKntnumer
JOIN (select Knt_GIDNumer as PlaKntnumer, knt_akronim as PlaAkronim from cdn.KntKarty ) as pla ON odb.Knt_KnPNumer = PlaKntnumer
JOIN (select Knt_GIDNumer as AkwKntnumer, knt_akronim as AkwAkronim from cdn.KntKarty ) as akw ON odb.Knt_AkwNumer = AkwKntnumer
Where {filtrSQL}