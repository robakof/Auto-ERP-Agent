-- ============================================================
-- Wykrywanie nieznanych prefiksów dokumentów TraNag
-- ============================================================
-- Cel: znaleźć prefiksy w numerach dokumentów których NIE MA
--      w zestawie znanych: (s), (A), (Z), brak.
--      Jeśli wynik pusty — baza wiedzy jest kompletna.
--
-- Wymagania: konto z EXECUTE na CDN.NazwaObiektu (uruchomić przez DBA w SSMS)
--
-- Jak działa:
--   1. Grupuje po (GIDTyp, GenDokMag, Stan & 2) — minimalna liczba wywołań funkcji
--   2. Wywołuje CDN.NazwaObiektu na każdym kandydacie
--   3. Wyciąga prefiks: wszystko przed pierwszą wielką literą w członie przed '-'
--      np. '(s)FS-1/06/23' → '(s)' | 'FS-1/06/23' → '' | '(k)FS-1/06/23' → '(k)'
--   4. Filtruje do nieznanych prefiksów
--   5. Zwraca pola diagnostyczne — od razu widać co różni te dokumenty
--
-- Znane prefiksy (wykluczone z wyniku):
--   ''    — brak prefiksu (dokument standardowy)
--   (s)   — TrN_GenDokMag = -1, typ sprzedażowy
--   (A)   — TrN_GenDokMag = -1, typ zakupowy (FZ/FZK/PZ)
--   (Z)   — TrN_Stan & 2 = 2, korekta anulowana (FSK/FZK/PAK/FKE)
-- ============================================================

; WITH kandydaci AS (
    SELECT
        TrN_GIDTyp,
        TrN_GenDokMag,
        TrN_Stan & 2        AS StanBit2,
        MIN(TrN_GIDNumer)   AS GIDNumer
    FROM CDN.TraNag
    GROUP BY TrN_GIDTyp, TrN_GenDokMag, TrN_Stan & 2
),
z_numerem AS (
    SELECT
        k.TrN_GIDTyp,
        k.GIDNumer,
        k.TrN_GenDokMag,
        k.StanBit2,
        t.TrN_Stan,
        CDN.NazwaObiektu(k.TrN_GIDTyp, k.GIDNumer, 0, 2) AS Numer
    FROM kandydaci k
    JOIN CDN.TraNag t
        ON  t.TrN_GIDNumer = k.GIDNumer
        AND t.TrN_GIDTyp   = k.TrN_GIDTyp
),
z_prefiksem AS (
    SELECT
        *,
        CASE
            WHEN Numer IS NOT NULL
                 AND CHARINDEX('-', Numer) > 1
                 AND PATINDEX('%[A-Z]%', LEFT(Numer, CHARINDEX('-', Numer) - 1)) > 1
            THEN LEFT(
                    LEFT(Numer, CHARINDEX('-', Numer) - 1),
                    PATINDEX('%[A-Z]%', LEFT(Numer, CHARINDEX('-', Numer) - 1)) - 1
                 )
            ELSE ''
        END AS Prefiks
    FROM z_numerem
)
SELECT
    'CDN.TraNag'        AS Tabela,
    p.TrN_GIDTyp        AS GIDTyp,
    o.Ob_Nazwa          AS TypNazwa,
    p.Prefiks           AS NieznanyPrefiks,
    p.Numer             AS PrzykladNumeru,
    p.TrN_GenDokMag     AS GenDokMag,
    p.TrN_Stan          AS Stan,
    p.StanBit2
FROM z_prefiksem p
LEFT JOIN CDN.Obiekty o ON o.Ob_GIDTyp = p.TrN_GIDTyp
WHERE p.Prefiks NOT IN ('', '(s)', '(A)', '(Z)')
ORDER BY p.TrN_GIDTyp, p.Prefiks
