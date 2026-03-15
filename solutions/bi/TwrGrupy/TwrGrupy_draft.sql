-- AIBI.TwrGrupy — brudnopis SELECT
-- Faza 2 — iteracja 2
-- Źródło: CDN.TwrGrupy (GIDTyp=16 — przypisania towar→grupa)
-- Baseline: 13 817 wierszy (bridge, wiele grup per towar)

SELECT
    -- === Towar ===
    br.TwG_GIDNumer                                 AS ID_Towaru,
    t.Twr_Kod                                       AS Kod_Towaru,
    t.Twr_Nazwa                                     AS Nazwa_Towaru,

    -- === Grupa ogólna ===
    br.TwG_GrONumer                                 AS ID_Grupy,
    ISNULL(RTRIM(grp.TwG_Kod),   'Brak grupy')     AS Kod_Grupy,
    ISNULL(RTRIM(grp.TwG_Nazwa), 'Brak grupy')     AS Nazwa_Grupy,

    -- === Czas ===
    DATEADD(ss, br.TwG_CzasModyfikacji, '1990-01-01') AS Data_Modyfikacji,

    -- === Techniczne ===
    br.TwG_SyncId                                   AS Sync_Id

FROM CDN.TwrGrupy br

-- Kod i nazwa towaru
LEFT JOIN CDN.TwrKarty t
    ON  t.Twr_GIDNumer = br.TwG_GIDNumer

-- Definicja grupy ogólnej
LEFT JOIN CDN.TwrGrupy grp
    ON  grp.TwG_GIDTyp   = -16
    AND grp.TwG_GIDNumer = br.TwG_GrONumer

WHERE br.TwG_GIDTyp = 16
