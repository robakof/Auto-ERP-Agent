SELECT ak.Knt_Akronim [AKWIZYTOR]
FROM cdn.TraPlat
JOIN cdn.TraNag ON TrN_GIDNumer = TrP_GIDNumer AND TrN_GIDTyp = TrP_GIDTyp
LEFT JOIN cdn.KntKarty ak ON TrN_AkwNumer = ak.Knt_GIDNumer AND TrN_AkwTyp = ak.Knt_GIDTyp
WHERE {filtrsql}