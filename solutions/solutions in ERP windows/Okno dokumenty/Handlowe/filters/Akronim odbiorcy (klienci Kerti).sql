@PAR ?@S50|Kod_odbiorcy|&Wpisz kod/akronim odbiorcy:REG=@? @U() PAR@

TrN_GIDNumer IN (
    SELECT n.TrN_GIDNumer
    FROM cdn.TraNag n
    JOIN cdn.KntKarty k
      ON n.TrN_KnDTyp   = k.Knt_GIDTyp
     AND n.TrN_KnDNumer = k.Knt_GIDNumer
    WHERE UPPER(k.Knt_Akronim) LIKE '%' + ??Kod_odbiorcy + '%'
)
