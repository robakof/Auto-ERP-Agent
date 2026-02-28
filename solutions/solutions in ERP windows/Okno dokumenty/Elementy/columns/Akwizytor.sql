select 
Knt_Akronim [Akwizytor]

from cdn.TraElem

JOIN cdn.KntKarty ak on TrE_AkwTyp = ak.Knt_GidTyp AND TrE_AkwNumer = ak.Knt_GidNumer

Where {FiltrSQL}