-- ============================================================
-- Wykrywanie nieznanych prefiksów dokumentów — wszystkie tabele
-- ============================================================
-- Cel: znaleźć prefiksy w numerach dokumentów których NIE MA
--      w zestawie znanych: (s), (A), (Z), brak.
--      Jeśli wynik pusty — baza wiedzy jest kompletna.
--
-- Wymagania: konto z EXECUTE na CDN.NazwaObiektu (uruchomić przez DBA w SSMS)
--
-- Logika ekstrakcji prefiksu:
--   Jeśli numer zaczyna się od '(' → prefiks = wszystko do pierwszego ')'
--   Np. '(s)FS-1/06/23' → '(s)' | 'FS-1/06/23' → '' | '(k)FS-1/06/23' → '(k)'
--   Uwaga: PATINDEX('%[A-Z]%') jest niebezpieczny na collacji CI — łapie małe litery.
--
-- CDN.TraNag — grupowanie po polach różnicujących (GenDokMag, Stan & 2)
--   Znane prefiksy wykluczone: '' | (s) | (A) | (Z)
--
-- Pozostałe tabele — próbka MIN + MAX per GIDTyp
--   Filtr: każdy prefiks jest nieznany (Prefiks <> '')
-- ============================================================


-- ============================================================
-- CZĘŚĆ 1: CDN.TraNag — smart grouping po polach różnicujących
-- ============================================================
; WITH tra_kandydaci AS (
    SELECT
        TrN_GIDTyp,
        TrN_GenDokMag,
        TrN_Stan & 2        AS StanBit2,
        MIN(TrN_GIDNumer)   AS GIDNumer
    FROM CDN.TraNag
    GROUP BY TrN_GIDTyp, TrN_GenDokMag, TrN_Stan & 2
),
tra_z_numerem AS (
    SELECT
        k.TrN_GIDTyp        AS GIDTyp,
        k.GIDNumer,
        k.TrN_GenDokMag     AS GenDokMag,
        k.StanBit2,
        t.TrN_Stan          AS Stan,
        CDN.NazwaObiektu(k.TrN_GIDTyp, k.GIDNumer, 0, 2) AS Numer
    FROM tra_kandydaci k
    JOIN CDN.TraNag t
        ON  t.TrN_GIDNumer = k.GIDNumer
        AND t.TrN_GIDTyp   = k.TrN_GIDTyp
),
tra_wynik AS (
    SELECT
        'CDN.TraNag'    AS Tabela,
        GIDTyp,
        Numer,
        GenDokMag,
        Stan,
        StanBit2,
        CASE
            WHEN Numer IS NOT NULL AND LEFT(Numer, 1) = '(' AND CHARINDEX(')', Numer) > 0
            THEN LEFT(Numer, CHARINDEX(')', Numer))
            ELSE ''
        END AS Prefiks
    FROM tra_z_numerem
),

-- ============================================================
-- CZĘŚĆ 2: pozostałe tabele — próbka MIN + MAX per GIDTyp
-- ============================================================

-- CDN.ZamNag
zan_kandydaci AS (
    SELECT ZaN_GIDTyp AS GIDTyp, MIN(ZaN_GIDNumer) AS GIDNumer FROM CDN.ZamNag GROUP BY ZaN_GIDTyp
    UNION ALL
    SELECT ZaN_GIDTyp,           MAX(ZaN_GIDNumer)             FROM CDN.ZamNag GROUP BY ZaN_GIDTyp
),
zan_wynik AS (
    SELECT DISTINCT
        'CDN.ZamNag'    AS Tabela,
        GIDTyp,
        CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2) AS Numer,
        NULL AS GenDokMag, NULL AS Stan, NULL AS StanBit2,
        CASE
            WHEN CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2) IS NOT NULL
                 AND LEFT(CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2), 1) = '('
                 AND CHARINDEX(')', CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2)) > 0
            THEN LEFT(CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2),
                      CHARINDEX(')', CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2)))
            ELSE ''
        END AS Prefiks
    FROM zan_kandydaci
),

-- CDN.MemNag
mem_kandydaci AS (
    SELECT MEN_GIDTyp AS GIDTyp, MIN(MEN_GIDNumer) AS GIDNumer FROM CDN.MemNag GROUP BY MEN_GIDTyp
    UNION ALL
    SELECT MEN_GIDTyp,           MAX(MEN_GIDNumer)             FROM CDN.MemNag GROUP BY MEN_GIDTyp
),
mem_wynik AS (
    SELECT DISTINCT
        'CDN.MemNag'    AS Tabela,
        GIDTyp,
        CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2) AS Numer,
        NULL AS GenDokMag, NULL AS Stan, NULL AS StanBit2,
        CASE
            WHEN CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2) IS NOT NULL
                 AND LEFT(CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2), 1) = '('
                 AND CHARINDEX(')', CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2)) > 0
            THEN LEFT(CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2),
                      CHARINDEX(')', CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2)))
            ELSE ''
        END AS Prefiks
    FROM mem_kandydaci
),

-- CDN.UpoNag
upo_kandydaci AS (
    SELECT UPN_GIDTyp AS GIDTyp, MIN(UPN_GIDNumer) AS GIDNumer FROM CDN.UpoNag GROUP BY UPN_GIDTyp
    UNION ALL
    SELECT UPN_GIDTyp,           MAX(UPN_GIDNumer)             FROM CDN.UpoNag GROUP BY UPN_GIDTyp
),
upo_wynik AS (
    SELECT DISTINCT
        'CDN.UpoNag'    AS Tabela,
        GIDTyp,
        CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2) AS Numer,
        NULL AS GenDokMag, NULL AS Stan, NULL AS StanBit2,
        CASE
            WHEN CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2) IS NOT NULL
                 AND LEFT(CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2), 1) = '('
                 AND CHARINDEX(')', CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2)) > 0
            THEN LEFT(CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2),
                      CHARINDEX(')', CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2)))
            ELSE ''
        END AS Prefiks
    FROM upo_kandydaci
),

-- CDN.ProdZlecenia (GIDTyp = 14343, klucz = PZL_Id)
prod_kandydaci AS (
    SELECT 14343 AS GIDTyp, MIN(PZL_Id) AS GIDNumer FROM CDN.ProdZlecenia
    UNION ALL
    SELECT 14343,            MAX(PZL_Id)             FROM CDN.ProdZlecenia
),
prod_wynik AS (
    SELECT DISTINCT
        'CDN.ProdZlecenia' AS Tabela,
        GIDTyp,
        CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2) AS Numer,
        NULL AS GenDokMag, NULL AS Stan, NULL AS StanBit2,
        CASE
            WHEN CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2) IS NOT NULL
                 AND LEFT(CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2), 1) = '('
                 AND CHARINDEX(')', CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2)) > 0
            THEN LEFT(CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2),
                      CHARINDEX(')', CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2)))
            ELSE ''
        END AS Prefiks
    FROM prod_kandydaci
),

-- CDN.Zapisy (GIDTyp = 784, klucz = KAZ_GIDNumer)
zap_kandydaci AS (
    SELECT 784 AS GIDTyp, MIN(KAZ_GIDNumer) AS GIDNumer FROM CDN.Zapisy
    UNION ALL
    SELECT 784,            MAX(KAZ_GIDNumer)             FROM CDN.Zapisy
),
zap_wynik AS (
    SELECT DISTINCT
        'CDN.Zapisy'    AS Tabela,
        GIDTyp,
        CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2) AS Numer,
        NULL AS GenDokMag, NULL AS Stan, NULL AS StanBit2,
        CASE
            WHEN CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2) IS NOT NULL
                 AND LEFT(CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2), 1) = '('
                 AND CHARINDEX(')', CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2)) > 0
            THEN LEFT(CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2),
                      CHARINDEX(')', CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2)))
            ELSE ''
        END AS Prefiks
    FROM zap_kandydaci
),

-- CDN.RozniceKursowe (GIDTyp = 435, klucz = RKN_Id)
rk_kandydaci AS (
    SELECT 435 AS GIDTyp, MIN(RKN_Id) AS GIDNumer FROM CDN.RozniceKursowe
    UNION ALL
    SELECT 435,            MAX(RKN_Id)             FROM CDN.RozniceKursowe
),
rk_wynik AS (
    SELECT DISTINCT
        'CDN.RozniceKursowe' AS Tabela,
        GIDTyp,
        CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2) AS Numer,
        NULL AS GenDokMag, NULL AS Stan, NULL AS StanBit2,
        CASE
            WHEN CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2) IS NOT NULL
                 AND LEFT(CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2), 1) = '('
                 AND CHARINDEX(')', CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2)) > 0
            THEN LEFT(CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2),
                      CHARINDEX(')', CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2)))
            ELSE ''
        END AS Prefiks
    FROM rk_kandydaci
)

-- ============================================================
-- WYNIK KOŃCOWY
-- ============================================================
SELECT
    w.Tabela,
    w.GIDTyp,
    o.Ob_Nazwa          AS TypNazwa,
    w.Prefiks           AS NieznanyPrefiks,
    w.Numer             AS PrzykladNumeru,
    w.GenDokMag,
    w.Stan,
    w.StanBit2
FROM (
    SELECT * FROM tra_wynik  WHERE Prefiks NOT IN ('', '(s)', '(A)', '(Z)')
    UNION ALL
    SELECT * FROM zan_wynik  WHERE Prefiks <> ''
    UNION ALL
    SELECT * FROM mem_wynik  WHERE Prefiks <> ''
    UNION ALL
    SELECT * FROM upo_wynik  WHERE Prefiks <> ''
    UNION ALL
    SELECT * FROM prod_wynik WHERE Prefiks <> ''
    UNION ALL
    SELECT * FROM zap_wynik  WHERE Prefiks <> ''
    UNION ALL
    SELECT * FROM rk_wynik   WHERE Prefiks <> ''
) w
LEFT JOIN CDN.Obiekty o ON o.Ob_GIDTyp = w.GIDTyp
ORDER BY w.Tabela, w.GIDTyp, w.Prefiks
