exists (
    select 1
    from cdn.Atrybuty a
    where a.Atr_ObiNumer = Twr_GIDNumer
      and a.Atr_ObiTyp   = Twr_GIDTyp
      and a.Atr_AtKId    = 59
      and a.Atr_Wartosc <> 'Dostępny w ofercie'
)
