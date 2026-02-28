@PAR ?@S20|Towar|Kod towaru:REG= @? PAR@

exists (
 select null from cdn.magelem me
where me.MaE_GIDNumer = MaN_GIDNumer and me.MaE_twrkod like '%' + ??Towar + '%'
)