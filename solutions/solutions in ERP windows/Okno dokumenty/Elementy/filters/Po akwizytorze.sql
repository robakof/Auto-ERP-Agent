@PAR ?@R(
    select distinct Knt_Akronim as ID, Knt_Akronim as Kod
    from cdn.KntKarty
    where 
        Knt_Akronim LIKE 'PH\_%' ESCAPE '\'
        OR Knt_Akronim LIKE 'KS\_%' ESCAPE '\'
        OR Knt_Akronim = 'JEDNORAZOWY'
)|Akwizytor|&Akronim:REG=Karta @? PAR@

TrE_AkwNumer IN (select TrE_AkwNumer

from cdn.KntKarty

JOIN cdn.TraElem te on te.TrE_AkwTyp = Knt_GidTyp AND te.TrE_AkwNumer = Knt_GidNumer

Where Knt_Akronim = ??_QAkwizytor)
