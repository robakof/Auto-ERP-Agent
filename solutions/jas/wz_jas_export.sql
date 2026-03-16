-- =============================================================================
-- WZ → JAS: eksport zatwierdzonych WZ z Buszewo
-- Przeznaczenie: system automatyzacji wysyłek spedytora JAS
-- Jeden wiersz = jeden typ palety na WZ (cargo z WMS)
-- =============================================================================
--
-- Tabele:
--   CDN.TraNag      — nagłówek WZ (filtr: GIDTyp=2001, Stan=5, MagZNumer=1)
--   CDN.KntAdresy   — adres dostawy (join przez TrN_AdWNumer/TrN_AdWTyp)
--   CDN.TrNOpisy    — opis/notatka handlowca
--   CDN.ZamNag      — data realizacji ZS (join przez TrN_ZaNNumer)
--   CDN.MagNag + wms.* — palety WMS (typ, ilość, wymiary ze stałego mapowania)
--
-- Mapowanie WMS → JAS (źródło: Mapowanie palet JAS.txt):
--   Europaleta             → Paleta-EPAL  120×80×200 cm  300 kg
--   Paleta jednorazowa     → Paleta       120×80×200 cm  300 kg
--   Pół paleta jednorazowa → Paleta-INNA   60×80×170 cm  150 kg
--

WITH addr AS (
    -- Parser ulicy: rozdziela KnA_Ulica na ulicę i numer domu
    -- Obsługiwane wzorce: "24", "121B", "36 A", "4/6", "36-38", NULL (brak numeru)
    SELECT
        a.KnA_GIDNumer,
        a.KnA_GIDTyp,
        a.KnA_Nazwa1,
        a.KnA_KodP,
        a.KnA_Miasto,
        a.KnA_Kraj,
        -- p1: pozycja ostatniej spacji od prawej
        CHARINDEX(' ', REVERSE(RTRIM(LTRIM(a.KnA_Ulica)))) AS p1,
        -- w1: ostatnie słowo
        CASE WHEN CHARINDEX(' ', REVERSE(RTRIM(LTRIM(a.KnA_Ulica)))) = 0
             THEN RTRIM(LTRIM(a.KnA_Ulica))
             ELSE RIGHT(RTRIM(LTRIM(a.KnA_Ulica)),
                        CHARINDEX(' ', REVERSE(RTRIM(LTRIM(a.KnA_Ulica)))) - 1)
        END AS w1,
        -- p2: pozycja przedostatniej spacji od prawej (dla wzorca "29 C")
        CASE WHEN CHARINDEX(' ', REVERSE(RTRIM(LTRIM(a.KnA_Ulica)))) = 0 THEN 0
             ELSE CHARINDEX(' ', REVERSE(LEFT(RTRIM(LTRIM(a.KnA_Ulica)),
                  LEN(RTRIM(LTRIM(a.KnA_Ulica)))
                  - CHARINDEX(' ', REVERSE(RTRIM(LTRIM(a.KnA_Ulica)))))))
        END AS p2,
        -- w2: przedostatnie słowo (dla wzorca "29 C")
        CASE WHEN CHARINDEX(' ', REVERSE(RTRIM(LTRIM(a.KnA_Ulica)))) = 0 THEN ''
             WHEN CHARINDEX(' ', REVERSE(LEFT(RTRIM(LTRIM(a.KnA_Ulica)),
                  LEN(RTRIM(LTRIM(a.KnA_Ulica)))
                  - CHARINDEX(' ', REVERSE(RTRIM(LTRIM(a.KnA_Ulica))))))) = 0
             THEN LEFT(RTRIM(LTRIM(a.KnA_Ulica)),
                  LEN(RTRIM(LTRIM(a.KnA_Ulica)))
                  - CHARINDEX(' ', REVERSE(RTRIM(LTRIM(a.KnA_Ulica)))))
             ELSE REVERSE(LEFT(
                    REVERSE(LEFT(RTRIM(LTRIM(a.KnA_Ulica)),
                            LEN(RTRIM(LTRIM(a.KnA_Ulica)))
                            - CHARINDEX(' ', REVERSE(RTRIM(LTRIM(a.KnA_Ulica)))))),
                    CHARINDEX(' ', REVERSE(LEFT(RTRIM(LTRIM(a.KnA_Ulica)),
                            LEN(RTRIM(LTRIM(a.KnA_Ulica)))
                            - CHARINDEX(' ', REVERSE(RTRIM(LTRIM(a.KnA_Ulica))))))) - 1
                  ))
        END AS w2,
        RTRIM(LTRIM(a.KnA_Ulica)) AS raw_ulica
    FROM CDN.KntAdresy a
)
SELECT
    -- -------------------------------------------------------------------------
    -- Identyfikacja WZ
    -- -------------------------------------------------------------------------
    t.TrN_DokumentObcy                      AS numer_wz,

    CASE WHEN t.TrN_Data2 = 0 THEN NULL
         ELSE CAST(DATEADD(d, t.TrN_Data2, '18001228') AS DATE)
    END AS data_wystawienia,

    CASE WHEN t.TrN_DataMag = 0 THEN NULL
         ELSE CAST(DATEADD(d, t.TrN_DataMag, '18001228') AS DATE)
    END AS data_sprzedazy,

    CASE WHEN z.ZaN_DataRealizacji = 0 THEN NULL
         ELSE CAST(DATEADD(d, z.ZaN_DataRealizacji, '18001228') AS DATE)
    END AS data_realizacji_zs,

    o.TnO_Opis                              AS opis,

    -- -------------------------------------------------------------------------
    -- Adres dostawy (ulica i numer domu rozdzielone parserem)
    -- NULL w nr_domu = adres bez numeru lub pole obcięte w ERP (42/616 adresów)
    -- -------------------------------------------------------------------------
    adw.KnA_Nazwa1                          AS odbiorca_nazwa,

    RTRIM(CASE
        -- wzorzec "29 C": ostatnie słowo to 1-2 litery, przedostatnie zaczyna cyfrą
        WHEN adw.w1 NOT LIKE '%[0-9]%' AND LEN(adw.w1) <= 2
         AND adw.p2 > 0 AND adw.w2 LIKE '[0-9]%'
            THEN LEFT(adw.raw_ulica, LEN(adw.raw_ulica) - adw.p1 - adw.p2)
        -- wzorzec prosty: ostatnie słowo zaczyna cyfrą
        WHEN adw.w1 LIKE '[0-9]%'
            THEN LEFT(adw.raw_ulica, LEN(adw.raw_ulica) - adw.p1)
        -- brak numeru
        ELSE adw.raw_ulica
    END)                                    AS odbiorca_ulica,

    CASE
        WHEN adw.w1 NOT LIKE '%[0-9]%' AND LEN(adw.w1) <= 2
         AND adw.p2 > 0 AND adw.w2 LIKE '[0-9]%'
            THEN adw.w2 + ' ' + adw.w1
        WHEN adw.w1 LIKE '[0-9]%'
            THEN adw.w1
        ELSE NULL
    END                                     AS odbiorca_nr_domu,

    adw.KnA_KodP                            AS odbiorca_kod_pocztowy,
    adw.KnA_Miasto                          AS odbiorca_miasto,
    ISNULL(NULLIF(adw.KnA_Kraj, ''), 'PL') AS odbiorca_kraj,

    -- -------------------------------------------------------------------------
    -- Cargo (palety z WMS — jeden wiersz = jeden typ palety)
    -- -------------------------------------------------------------------------
    CASE lt.Name
        WHEN 'Europaleta'             THEN 'Paleta-EPAL'
        WHEN 'Paleta jednorazowa'     THEN 'Paleta'
        WHEN 'Pół paleta jednorazowa' THEN 'Paleta-INNA'
        ELSE lt.Name
    END                                     AS typ_opakowania,

    COUNT(DISTINCT lo.barcode)              AS ilosc,

    CASE lt.Name
        WHEN 'Pół paleta jednorazowa' THEN 60
        ELSE 120
    END                                     AS dlugosc_cm,

    80                                      AS szerokosc_cm,

    CASE lt.Name
        WHEN 'Pół paleta jednorazowa' THEN 170
        ELSE 200
    END                                     AS wysokosc_cm,

    CASE lt.Name
        WHEN 'Pół paleta jednorazowa' THEN 150
        ELSE 300
    END                                     AS waga_kg_max,

    -- -------------------------------------------------------------------------
    -- Techniczne
    -- -------------------------------------------------------------------------
    t.TrN_GIDNumer                          AS wz_id,
    t.TrN_LastMod                           AS last_mod

FROM CDN.TraNag t
-- Adres dostawy (przez CTE z parserem)
LEFT JOIN addr adw
    ON  adw.KnA_GIDNumer = t.TrN_AdWNumer
    AND adw.KnA_GIDTyp   = t.TrN_AdWTyp
-- Opis/notatka
LEFT JOIN CDN.TrNOpisy o
    ON  o.TnO_TrnNumer = t.TrN_GIDNumer
    AND o.TnO_TrnTyp   = t.TrN_GIDTyp
    AND o.TnO_Typ      = 0
-- Data realizacji ZS
LEFT JOIN CDN.ZamNag z
    ON  z.ZaN_GIDNumer = t.TrN_ZaNNumer
    AND t.TrN_ZaNTyp   = 960
-- Palety z WMS
JOIN CDN.MagNag m
    ON  m.MaN_ZrdNumer = t.TrN_GIDNumer
    AND m.MaN_ZrdTyp   = t.TrN_GIDTyp
JOIN wms.documents d   WITH (NOLOCK) ON d.SourceDocumentId = m.MaN_GIDNumer
JOIN wms.items i       WITH (NOLOCK) ON d.Id = i.DocumentId
JOIN wms.LogisticUnitObjects lo WITH (NOLOCK) ON i.LogisticUnitId = lo.Id
JOIN wms.LogisticUnitTypes lt   WITH (NOLOCK) ON lo.LogisticsUnitTypeId = lt.Id

WHERE
    t.TrN_GIDTyp     = 2001  -- WZ
    AND t.TrN_Stan       = 5     -- Zatwierdzone
    AND t.TrN_MagZNumer  = 1     -- Buszewo
    AND t.TrN_TrNRok     = YEAR(GETDATE())  -- bieżący rok

GROUP BY
    t.TrN_GIDNumer,
    t.TrN_DokumentObcy,
    t.TrN_Data2, t.TrN_DataMag,
    t.TrN_ZaNNumer, t.TrN_ZaNTyp,
    t.TrN_AdWNumer, t.TrN_AdWTyp,
    t.TrN_LastMod,
    z.ZaN_DataRealizacji,
    o.TnO_Opis,
    adw.KnA_Nazwa1, adw.KnA_KodP, adw.KnA_Miasto, adw.KnA_Kraj,
    adw.raw_ulica, adw.w1, adw.w2, adw.p1, adw.p2,
    lt.Name

HAVING COUNT(DISTINCT lo.barcode) > 0

ORDER BY t.TrN_GIDNumer, lt.Name;
