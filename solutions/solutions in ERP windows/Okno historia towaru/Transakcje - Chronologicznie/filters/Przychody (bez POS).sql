(TrN_TrNTyp IN (1,2,6,12,19))
AND
TrN_GIDNumer NOT IN (
    SELECT n.TrN_GIDNumer
    FROM cdn.TraNag n
    JOIN cdn.OpeKarty o
      ON n.TrN_OpeTypW = o.Ope_GIDTyp
     AND n.TrN_OpeNumerW = o.Ope_GIDNumer
    WHERE UPPER(o.Ope_Ident) IN ('POSSYNC1','POSSYNC2')
)
