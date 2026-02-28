TrN_GIDNumer IN (
    SELECT o.TnO_TrnNumer
    FROM cdn.TrNOpisy o
    WHERE UPPER(o.Tno_Opis) LIKE '%SEZON%'
)
