-- AIBI.KntGrupy — brudnopis SELECT
-- Faza 2 — iteracja 1
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
         ELSE NULL END                              AS Data_Zalozenia

FROM CDN.KntGrupy br

-- Akronim i nazwa kontrahenta
LEFT JOIN CDN.KntKarty k
    ON  k.Knt_GIDNumer = br.KnG_GIDNumer

-- Definicja grupy ogólnej
LEFT JOIN CDN.KntGrupy grp
    ON  grp.KnG_GIDTyp   = -32
    AND grp.KnG_GIDNumer = br.KnG_GrONumer

WHERE br.KnG_GIDTyp = 32
