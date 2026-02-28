@PAR ?@S100|Szukany_ciag|&Wpisz fragment opisu do wyszukania:REG=@? @U() PAR@

TrN_GIDNumer IN (
    SELECT o.TnO_TrnNumer
    FROM cdn.TrNOpisy o
    WHERE UPPER(o.Tno_Opis) LIKE '%' + ??Szukany_ciag + '%'
)
