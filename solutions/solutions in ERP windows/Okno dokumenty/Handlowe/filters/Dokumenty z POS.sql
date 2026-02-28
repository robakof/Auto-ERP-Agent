TrN_GIDNumer IN (
    SELECT n.TrN_GIDNumer
    FROM cdn.TraNag n
    JOIN cdn.OpeKarty o
      ON n.TrN_OpeTypW = o.Ope_GIDTyp
     AND n.TrN_OpeNumerW = o.Ope_GIDNumer
    WHERE UPPER(o.Ope_Ident) IN ('POSSYNC1','POSSYNC2')
)
