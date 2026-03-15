USE [ERPXL_CEIM];
GO

CREATE OR ALTER VIEW AIBI.KntGrupy AS

-- AIBI.KntGrupy — brudnopis SELECT
-- Faza 2 — iteracja 2
-- Źródło: CDN.KntGrupy (GIDTyp=32 — przypisania kontrahent→grupa)
-- Baseline: 5 669 wierszy (bridge, wiele grup per kontrahent)

SELECT
    -- === Kontrahent ===
    br.KnG_GIDNumer                                 AS ID_Kontrahenta,
    k.Knt_Akronim                                   AS Akronim_Kontrahenta,
    k.Knt_Nazwa1                                    AS Nazwa_Kontrahenta,

    -- === Grupa ogólna ===
    br.KnG_GrONumer                                 AS ID_Grupy,
    ISNULL(RTRIM(grp.KnG_Akronim), 'Brak grupy')   AS Kod_Grupy,

    -- === Czas ===
    CASE WHEN br.KnG_CzasModyfikacji > 0
         THEN DATEADD(ss, br.KnG_CzasModyfikacji, '1990-01-01')
         ELSE NULL END                              AS Data_Modyfikacji,
    CASE WHEN br.KnG_CzasZalozenia > 0
         THEN DATEADD(ss, br.KnG_CzasZalozenia, '1990-01-01')
         ELSE NULL END                              AS Data_Zalozenia,

    -- === Operator ===
    br.KnG_OpeNumer                                 AS ID_Operatora,
    o.Ope_Ident                                     AS Login_Operatora,
    o.Ope_Nazwisko                                  AS Nazwisko_Operatora,

    -- === Techniczne ===
    br.KnG_SyncId                                   AS Sync_Id

FROM CDN.KntGrupy br

-- Akronim i nazwa kontrahenta
LEFT JOIN CDN.KntKarty k
    ON  k.Knt_GIDNumer = br.KnG_GIDNumer

-- Definicja grupy ogólnej
LEFT JOIN CDN.KntGrupy grp
    ON  grp.KnG_GIDTyp   = -32
    AND grp.KnG_GIDNumer = br.KnG_GrONumer

-- Operator zakładający przypisanie
LEFT JOIN CDN.OpeKarty o
    ON  o.Ope_GIDNumer = br.KnG_OpeNumer

WHERE br.KnG_GIDTyp = 32
