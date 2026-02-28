@PAR ?@R(select distinct TrP_FormaNazwa as ID, Trp_FormaNazwa AS Kod
from cdn.TraPlat
UNION
Select '%' as ID, '%' AS Kod)|FormaPlatnosci|&Forma Płatności:REG=Karta @? PAR@

@PAR ?@D17|DataWystawienia|&Data Wystawienia:REG={Today()} @? PAR@

@PAR ?@n-16_.2|Kwota|&Kwota:REG=0 @? @RL(-99999999) @RH(99999999) PAR@

Trn_gidnumer IN (select Trn_gidnumer
from cdn.TraPlat
JOIN cdn.TraNag ON TrN_GIDNumer = TrP_GIDNumer AND TrN_GIDTyp = TrP_GIDTyp
Where TrP_FormaNazwa LIKE '%' + ??_QFormaPlatnosci  + '%' AND TrN_Data2 = ??DataWystawienia AND TrP_Kwota = CASE WHEN ??Kwota = 0 THEN TrP_Kwota ELSE ??Kwota  END)