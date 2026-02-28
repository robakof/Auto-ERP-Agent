@PAR ?@S25|NumerDokumentu|&Numer Dokumentu:REG= @? PAR@

TrN_gidnumer IN (select Trn_gidnumer from cdn.TraNag where cdn.NazwaObiektu(trn_gidtyp, Trn_gidnumer,0,2) LIKE '%' + ??NumerDokumentu + '%')