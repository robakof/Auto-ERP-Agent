select top(1) isnull(mag.MAG_KOD, '<Oryginalny>') AS [Magazyn]from cdn.TraNag tn
left join cdn.magazyny mag on mag.MAG_GIDNumer = tn.TrN_MAGDNumer
where {filtrSQL}