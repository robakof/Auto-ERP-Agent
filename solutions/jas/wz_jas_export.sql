-- =============================================================================
-- WZ → JAS: eksport zatwierdzonych WZ z Buszewo
-- Przeznaczenie: system automatyzacji wysyłek spedytora JAS
-- Jedno WZ = wiele wierszy (jeden wiersz = jedna pozycja cargo)
-- =============================================================================
--
-- Tabele:
--   CDN.TraNag      — nagłówek WZ (filtr: GIDTyp=2001, Stan=5, MagZNumer=1)
--   CDN.TraElem     — pozycje WZ (join przez TrE_GIDNumer = TrN_GIDNumer)
--   CDN.KntAdresy   — adres dostawy (join przez TrN_AdWNumer/TrN_AdWTyp)
--   CDN.TrNOpisy    — opis/notatka handlowca (join przez TnO_TrnNumer)
--   CDN.ZamNag      — data realizacji ZS (join przez TrN_ZaNNumer, ZaNTyp=960)
--   CDN.MagNag + wms.* — palety WMS (subquery per WZ)
--
-- ⚠ PRZED WDROŻENIEM — zweryfikuj format numeru WZ przez CDN.NazwaObiektu
--   i porównaj z ręczną konstrukcją na kilku realnych dokumentach.
--
-- Brakujące pola (nie ma w ERP):
--   dlugosc_cm, szerokosc_cm, wysokosc_cm  — brak w TwrKarty (brak kolumn wymiarów)
--   waga_kg                                 — TwJ_Waga/Twr_Waga = 0 (niepopulowane)
--   odbiorca_nr_domu                        — łącznie z ulicą w KnA_Ulica
--   typ_opakowania (JAS)                    — ERP przechowuje TrE_JmZ ("opak.","szt.",
--                                             "karton","warstwa","paleta"); mapowanie poniżej

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

    -- data_sprzedazy = data magazynowa (data realnego wydania towaru z magazynu)
    CASE WHEN t.TrN_DataMag = 0 THEN NULL
         ELSE CAST(DATEADD(d, t.TrN_DataMag, '18001228') AS DATE)
    END AS data_sprzedazy,

    o.TnO_Opis                              AS opis,

    -- Data realizacji z powiązanego ZS (może być NULL gdy brak ZS lub brak daty)
    CASE WHEN z.ZaN_DataRealizacji = 0 THEN NULL
         ELSE CAST(DATEADD(d, z.ZaN_DataRealizacji, '18001228') AS DATE)
    END                                     AS data_realizacji_zs,

    -- Palety z WMS (format: "EPN: 2, KRT: 5") — NULL gdy brak dokumentu WMS
    ISNULL(STUFF((
        SELECT ', ' + lt.Name + ': ' + CONVERT(VARCHAR(5), COUNT(DISTINCT lo.barcode))
        FROM CDN.MagNag m
        JOIN wms.documents d   WITH (NOLOCK) ON d.SourceDocumentId = m.MaN_GIDNumer
        JOIN wms.items i       WITH (NOLOCK) ON d.Id = i.DocumentId
        JOIN wms.LogisticUnitObjects lo WITH (NOLOCK) ON i.LogisticUnitId = lo.Id
        JOIN wms.LogisticUnitTypes lt   WITH (NOLOCK) ON lo.LogisticsUnitTypeId = lt.Id
        WHERE m.MaN_ZrdNumer = t.TrN_GIDNumer
          AND m.MaN_ZrdTyp   = t.TrN_GIDTyp
        GROUP BY lt.Name
        HAVING COUNT(DISTINCT lo.barcode) <> 0
        FOR XML PATH('')
    ), 1, 2, ''), '')                       AS palety,

    -- -------------------------------------------------------------------------
    -- Adres dostawy (z nagłówka WZ → CDN.KntAdresy)
    -- ⚠ KnA_Ulica zawiera ulicę i numer domu w jednym polu (np. "Rynek 5")
    -- -------------------------------------------------------------------------
    adw.KnA_Nazwa1                          AS odbiorca_nazwa,
    adw.KnA_Ulica                           AS odbiorca_ulica_z_numerem,
    NULL                                    AS odbiorca_nr_domu,    -- brak w ERP
    adw.KnA_KodP                            AS odbiorca_kod_pocztowy,
    adw.KnA_Miasto                          AS odbiorca_miasto,
    ISNULL(NULLIF(adw.KnA_Kraj, ''), 'PL') AS odbiorca_kraj,

    -- -------------------------------------------------------------------------
    -- Pozycja cargo (jedna pozycja = jeden wiersz)
    -- -------------------------------------------------------------------------

    -- Mapowanie JmZ → kody JAS
    -- ⚠ Mapping do potwierdzenia z użytkownikiem — wartości JmZ z ERP:
    --   "opak."   → EPN (opakowanie paletowe netto)?
    --   "szt."    → EPN?
    --   "karton"  → KRT
    --   "paleta"  → EPN (lub EFN dla pełnej palety)?
    --   "warstwa" → ?
    CASE e.TrE_JmZ
        WHEN 'karton'  THEN 'KRT'
        WHEN 'paleta'  THEN 'EPN'
        -- pozostałe wartości wymagają potwierdzenia
        ELSE e.TrE_JmZ   -- zwróć surową wartość ERP do czasu ustalenia mapowania
    END                                     AS typ_opakowania_jas,

    e.TrE_JmZ                               AS typ_opakowania_erp,   -- surowa wartość

    CAST(e.TrE_Ilosc AS DECIMAL(10,4))     AS ilosc,
    e.TrE_TwrKod                            AS kod_towaru,
    e.TrE_TwrNazwa                          AS nazwa_towaru,

    NULL                                    AS dlugosc_cm,           -- brak w ERP
    NULL                                    AS szerokosc_cm,         -- brak w ERP
    NULL                                    AS wysokosc_cm,          -- brak w ERP
    NULL                                    AS waga_kg,              -- brak w ERP (Twr_Waga=0)

    -- -------------------------------------------------------------------------
    -- Techniczne — dla debugowania / pętli 30s
    -- -------------------------------------------------------------------------
    t.TrN_GIDNumer                          AS wz_id,
    t.TrN_LastMod                           AS last_mod              -- do delta polling

FROM CDN.TraNag t
-- Pozycje
JOIN CDN.TraElem e
    ON  e.TrE_GIDNumer = t.TrN_GIDNumer
    AND e.TrE_GIDTyp   = t.TrN_GIDTyp
-- Adres dostawy
LEFT JOIN CDN.KntAdresy adw
    ON  adw.KnA_GIDNumer = t.TrN_AdWNumer
    AND adw.KnA_GIDTyp   = t.TrN_AdWTyp
-- Opis/notatka (TnO_Typ=0 = opis główny; LEFT JOIN — większość WZ bez opisu)
LEFT JOIN CDN.TrNOpisy o
    ON  o.TnO_TrnNumer = t.TrN_GIDNumer
    AND o.TnO_TrnTyp   = t.TrN_GIDTyp
    AND o.TnO_Typ      = 0
-- Data realizacji z powiązanego ZS
LEFT JOIN CDN.ZamNag z
    ON  z.ZaN_GIDNumer = t.TrN_ZaNNumer
    AND t.TrN_ZaNTyp   = 960

WHERE
    t.TrN_GIDTyp   = 2001  -- WZ (Wydanie zewnętrzne)
    AND t.TrN_Stan     = 5     -- Zatwierdzone
    AND t.TrN_MagZNumer = 1    -- Magazyn główny Buszewo (WMS)

ORDER BY t.TrN_GIDNumer, e.TrE_GIDLp;
