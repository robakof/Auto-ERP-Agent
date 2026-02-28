@PAR ?@R(
    SELECT DISTINCT Ope_GIDNumer AS ID, Ope_Nazwisko AS Kod
    FROM cdn.OpeKarty
)|Wystawiający|&Wystawiający:REG= @? PAR@

Trn_gidNumer IN (
    SELECT TrN_GIDNumer
    FROM cdn.TraNag
    JOIN cdn.OpeKarty ON TrN_OpeNumerW = Ope_GIDNumer AND TrN_OpeTypW = Ope_GIDTyp
    WHERE Ope_GIDNumer = ??Wystawiający
)

