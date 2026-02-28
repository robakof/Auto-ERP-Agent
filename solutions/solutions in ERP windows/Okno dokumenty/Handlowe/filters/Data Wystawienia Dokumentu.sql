@PAR ?@D17|DataWystawieniaOd|&Data Wystawienia Od:REG={Today()} @? PAR@
@PAR ?@D17|DataWystawieniaDo|&Data Wystawienia Do:REG={Today()} @? PAR@

Trn_gidnumer IN (select Trn_gidnumer
from cdn.TraNag Where TrN_Data2 between ??DataWystawieniaOd AND ??DataWystawieniaDo)