SELECT cdn.TrNOpisy.Tno_Opis [Opis na dokumencie]
FROM cdn.TrNOpisy

JOIN cdn.TraNag AS TraNag1 ON cdn.TrNOpisy.TnO_TrnNumer = TraNag1.TrN_GIDNumer
JOIN cdn.TraElem ON TraElem.TrE_GIDNumer = TraNag1.TrN_GIDNumer
JOIN cdn.TraNag AS TraNag2 ON TraElem.TrE_GIDNumer = TraNag2.TrN_GIDNumer

Where {FiltrSQL}