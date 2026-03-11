-- ============================================================
-- Wzorce numeracji dokumentów — zapytanie zbiorcze dla DBA
-- ============================================================
-- Cel: zebrać wzorce formatów numerów dokumentów ze wszystkich
--      głównych tabel transakcyjnych.
--
-- Wymagania: konto z EXECUTE na CDN.NazwaObiektu
-- Wynik:     zapisać jako solutions/reference/numeracja_wzorce.xlsx
--
-- Sygnatura: CDN.NazwaObiektu(@ObiTyp, @ObiNumer, @ObiLp, @Format)
--   @ObiLp   = 0  → nagłówek dokumentu (nie pozycja)
--   @Format  = 2  → zwraca tylko Akronim (numer dokumentu)
-- ============================================================


-- KROK 1: wszystkie typy obiektów w systemie
-- Pozwala zidentyfikować GIDTyp przed pisaniem wzorców.
-- Uruchom oddzielnie i przejrzyj wynik.
-- ============================================================

SELECT Ob_GIDTyp, Ob_Skrot, Ob_Nazwa
FROM CDN.Obiekty
ORDER BY Ob_GIDTyp


-- ============================================================
-- KROK 2: wzorce numerów dokumentów — jeden przykład na GIDTyp
-- Uruchom każdy blok osobno i zapisz wyniki do jednego arkusza.
-- ============================================================


-- CDN.TraNag — dokumenty handlowe (FS, FZ, PA, WZ, FSK, FZK, ...)
-- Pokrywa wszystkie typy dokumentów handlowych jednym zapytaniem.
; WITH min_numer AS (
    SELECT TrN_GIDTyp, MIN(TrN_GIDNumer) AS GIDNumer
    FROM CDN.TraNag
    GROUP BY TrN_GIDTyp
)
SELECT
    'CDN.TraNag'                                        AS Tabela,
    m.TrN_GIDTyp                                        AS GIDTyp,
    o.Ob_Nazwa                                          AS TypNazwa,
    CDN.NazwaObiektu(m.TrN_GIDTyp, m.GIDNumer, 0, 2)  AS PrzykladNumeru
FROM min_numer m
LEFT JOIN CDN.Obiekty o ON o.Ob_GIDTyp = m.TrN_GIDTyp
ORDER BY m.TrN_GIDTyp


-- CDN.ZamNag — zamówienia (ZS, ZZ)
; WITH min_numer AS (
    SELECT ZaN_GIDTyp, MIN(ZaN_GIDNumer) AS GIDNumer
    FROM CDN.ZamNag
    GROUP BY ZaN_GIDTyp
)
SELECT
    'CDN.ZamNag'                                        AS Tabela,
    m.ZaN_GIDTyp                                        AS GIDTyp,
    o.Ob_Nazwa                                          AS TypNazwa,
    CDN.NazwaObiektu(m.ZaN_GIDTyp, m.GIDNumer, 0, 2)  AS PrzykladNumeru
FROM min_numer m
LEFT JOIN CDN.Obiekty o ON o.Ob_GIDTyp = m.ZaN_GIDTyp
ORDER BY m.ZaN_GIDTyp


-- CDN.ProdZlecenia — zlecenia produkcyjne (ZP)
; WITH min_numer AS (
    SELECT MIN(PZL_Id) AS GIDNumer
    FROM CDN.ProdZlecenia
)
SELECT
    'CDN.ProdZlecenia'                                  AS Tabela,
    14343                                               AS GIDTyp,
    o.Ob_Nazwa                                          AS TypNazwa,
    CDN.NazwaObiektu(14343, m.GIDNumer, 0, 2)          AS PrzykladNumeru
FROM min_numer m
LEFT JOIN CDN.Obiekty o ON o.Ob_GIDTyp = 14343


-- CDN.MemNag — noty memoriałowe (NM i pochodne)
; WITH min_numer AS (
    SELECT MEN_GIDTyp, MIN(MEN_GIDNumer) AS GIDNumer
    FROM CDN.MemNag
    GROUP BY MEN_GIDTyp
)
SELECT
    'CDN.MemNag'                                        AS Tabela,
    m.MEN_GIDTyp                                        AS GIDTyp,
    o.Ob_Nazwa                                          AS TypNazwa,
    CDN.NazwaObiektu(m.MEN_GIDTyp, m.GIDNumer, 0, 2)  AS PrzykladNumeru
FROM min_numer m
LEFT JOIN CDN.Obiekty o ON o.Ob_GIDTyp = m.MEN_GIDTyp
ORDER BY m.MEN_GIDTyp


-- CDN.UpoNag — upomnienia / noty odsetkowe (NO)
; WITH min_numer AS (
    SELECT UPN_GIDTyp, MIN(UPN_GIDNumer) AS GIDNumer
    FROM CDN.UpoNag
    GROUP BY UPN_GIDTyp
)
SELECT
    'CDN.UpoNag'                                        AS Tabela,
    m.UPN_GIDTyp                                        AS GIDTyp,
    o.Ob_Nazwa                                          AS TypNazwa,
    CDN.NazwaObiektu(m.UPN_GIDTyp, m.GIDNumer, 0, 2)  AS PrzykladNumeru
FROM min_numer m
LEFT JOIN CDN.Obiekty o ON o.Ob_GIDTyp = m.UPN_GIDTyp
ORDER BY m.UPN_GIDTyp


-- CDN.Zapisy — zapisy kasowo-bankowe (KB)
; WITH min_numer AS (
    SELECT MIN(KAZ_GIDNumer) AS GIDNumer
    FROM CDN.Zapisy
)
SELECT
    'CDN.Zapisy'                                        AS Tabela,
    784                                                 AS GIDTyp,
    o.Ob_Nazwa                                          AS TypNazwa,
    CDN.NazwaObiektu(784, m.GIDNumer, 0, 2)            AS PrzykladNumeru
FROM min_numer m
LEFT JOIN CDN.Obiekty o ON o.Ob_GIDTyp = 784


-- CDN.RozniceKursowe — różnice kursowe (RK)
; WITH min_numer AS (
    SELECT MIN(RKN_Id) AS GIDNumer
    FROM CDN.RozniceKursowe
)
SELECT
    'CDN.RozniceKursowe'                                AS Tabela,
    435                                                 AS GIDTyp,
    o.Ob_Nazwa                                          AS TypNazwa,
    CDN.NazwaObiektu(435, m.GIDNumer, 0, 2)            AS PrzykladNumeru
FROM min_numer m
LEFT JOIN CDN.Obiekty o ON o.Ob_GIDTyp = 435
