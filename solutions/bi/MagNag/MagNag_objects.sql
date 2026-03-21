-- Zapytanie do weryfikacji formatów numerów dokumentów CDN.MagNag
-- Uruchom na koncie z EXECUTE na CDN.NazwaObiektu (np. CEiM_Reader pełny lub DBA)
-- Per jeden przykład na każdy GIDTyp

SELECT
    MaN_GIDTyp,
    ob.OB_Nazwa AS Typ_Dokumentu,
    MaN_TrNNumer,
    MaN_TrNMiesiac,
    MaN_TrNRok,
    MaN_TrNSeria,
    CDN.NazwaObiektu(MaN_GIDTyp, MaN_GIDNumer, 0, 2) AS Nr_Dokumentu
FROM CDN.MagNag
INNER JOIN CDN.Obiekty ob ON ob.OB_GIDTyp = MaN_GIDTyp
WHERE MaN_GIDNumer IN (
    SELECT MIN(MaN_GIDNumer) FROM CDN.MagNag GROUP BY MaN_GIDTyp
)
ORDER BY MaN_GIDTyp;
