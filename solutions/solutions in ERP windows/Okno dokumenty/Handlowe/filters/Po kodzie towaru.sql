@PAR ?@S20|Towar|Kod towaru:REG= @? PAR@

exists (
 select null from cdn.traelem te
where te.TrE_GIDNumer = TrN_GIDNumer and te.tre_twrkod like '%' + ??Towar + '%'
)