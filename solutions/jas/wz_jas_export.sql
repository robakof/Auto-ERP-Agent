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
-- ⚠ PRZED WDROŻENIEM — zweryfikuj format numeru WZ przez CDN.NazwaObiektu
--
-- Brakujące pola:
--   odbiorca_nr_domu — łącznie z ulicą w KnA_Ulica (np. "ul. Głuszyna 131")

SELECT
    -- -------------------------------------------------------------------------
    -- Identyfikacja WZ
    -- -------------------------------------------------------------------------
    'WZ-' + CAST(t.TrN_TrNNumer AS VARCHAR(10))
        + '/' + RIGHT('0' + CAST(t.TrN_TrNMiesiac AS VARCHAR(2)), 2)
        + '/' + RIGHT(CAST(t.TrN_TrNRok AS VARCHAR(4)), 2)
        + '/' + RTRIM(t.TrN_TrNSeria)
        AS numer_wz,

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
    -- Adres dostawy
    -- ⚠ KnA_Ulica zawiera ulicę i numer domu w jednym polu (np. "ul. Głuszyna 131")
    -- -------------------------------------------------------------------------
    adw.KnA_Nazwa1                          AS odbiorca_nazwa,
    adw.KnA_Ulica                           AS odbiorca_ulica_z_numerem,
    NULL                                    AS odbiorca_nr_domu,
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
-- Adres dostawy
LEFT JOIN CDN.KntAdresy adw
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
    t.TrN_GIDTyp    = 2001  -- WZ
    AND t.TrN_Stan      = 5     -- Zatwierdzone
    AND t.TrN_MagZNumer = 1     -- Buszewo

GROUP BY
    t.TrN_GIDNumer,
    t.TrN_TrNNumer, t.TrN_TrNMiesiac, t.TrN_TrNRok, t.TrN_TrNSeria,
    t.TrN_Data2, t.TrN_DataMag,
    t.TrN_ZaNNumer, t.TrN_ZaNTyp,
    t.TrN_AdWNumer, t.TrN_AdWTyp,
    t.TrN_LastMod,
    z.ZaN_DataRealizacji,
    o.TnO_Opis,
    adw.KnA_Nazwa1, adw.KnA_Ulica, adw.KnA_KodP, adw.KnA_Miasto, adw.KnA_Kraj,
    lt.Name

HAVING COUNT(DISTINCT lo.barcode) > 0

ORDER BY t.TrN_GIDNumer, lt.Name;
