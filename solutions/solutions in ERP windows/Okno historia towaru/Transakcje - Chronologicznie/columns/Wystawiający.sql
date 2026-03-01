SELECT Ope_Ident [Wystawiający]
FROM CDN.TraElem
JOIN CDN.TraNag ON TrN_GIDNumer = TrE_GIDNumer
LEFT JOIN CDN.OpeKarty ON TrN_OpeNumerW = Ope_GIDNumer AND TrN_OpeTypW = Ope_GIDTyp
WHERE {filtrSQL}