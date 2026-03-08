-- BI.Rezerwacje — brudnopis SELECT
-- Tabela główna: CDN.Rezerwacje, filtr: Rez_TwrNumer > 0
-- Baseline: 1090 rekordów

SELECT
    -- === TYP REZERWACJI ===
    CASE r.Rez_GIDTyp
        WHEN 2592 THEN 'Rezerwacja u dostawcy'
        WHEN 2576 THEN 'Rezerwacja'
        ELSE 'Nieznany (' + CAST(r.Rez_GIDTyp AS VARCHAR) + ')'
    END                                                         AS Typ_Rezerwacji,

    -- === IDENTYFIKATOR ===
    r.Rez_GIDNumer                                             AS ID_Rezerwacji,

    -- === TOWAR ===
    r.Rez_TwrNumer                                             AS ID_Towaru,
    t.Twr_Kod                                                  AS Kod_Towaru,
    t.Twr_Nazwa                                                AS Nazwa_Towaru,

    -- === KONTRAHENT ===
    CASE WHEN r.Rez_KntNumer = 0 THEN NULL
         ELSE r.Rez_KntNumer END                               AS ID_Kontrahenta,
    k.Knt_Akronim                                              AS Kod_Kontrahenta,
    k.Knt_Nazwa1                                               AS Nazwa_Kontrahenta,

    -- === DOKUMENT ŹRÓDŁOWY ===
    CASE r.Rez_ZrdTyp
        WHEN 960   THEN 'Zamówienie'
        WHEN 14346 THEN 'Zasób procesu produkcyjnego (ZPZ)'
        WHEN 2592  THEN 'Rezerwacja u dostawcy'
        ELSE 'Nieznany (' + CAST(r.Rez_ZrdTyp AS VARCHAR) + ')'
    END                                                        AS Typ_Dok_Zrodlowego,
    r.Rez_ZrdNumer                                             AS ID_Dok_Zrodlowego,
    r.Rez_ZrdLp                                                AS Lp_Pozycji_Zrodlowej,
    -- Numery dokumentów źródłowych (inline, bez CDN.NazwaObiektu):
    -- ZrdTyp=960 (Zamówienie): prefix zależy od ZaN_ZamTyp: 1152→ZZ, 1280→ZW/ZS (ZS gdy seria PH_x/SPKR — aproksymacja)
    -- ZrdTyp=14346 (ZPZ): ZrdNumer=CDN.ProdZasoby.PZA_Id → PZA_PZLId → CDN.ProdZlecenia → format ZP-N/MM/RR/Seria
    -- ZrdTyp=2592 (Rez.u.dostawcy): brak numeru zewnętrznego (samoreferencja)
    CASE r.Rez_ZrdTyp
        WHEN 960 THEN
            CASE zam.ZaN_ZamTyp
                WHEN 1152 THEN 'ZZ'
                WHEN 1280 THEN
                    -- ZS: wszystkie serie PH_x (dowolna cyfra) + SPKR; ZW: OTO, BUS, FRA i inne znane
                    -- ELSE ujawnia nową serię zamiast ją cicho klasyfikować jako ZW
                    CASE WHEN zam.ZaN_ZamSeria LIKE 'PH[_]%' OR zam.ZaN_ZamSeria = 'SPKR'
                         THEN 'ZS'
                         WHEN zam.ZaN_ZamSeria IN ('OTO','BUS','FRA')
                         THEN 'ZW'
                         ELSE '??(' + zam.ZaN_ZamSeria + ')'
                    END
                ELSE '??Typ(' + CAST(zam.ZaN_ZamTyp AS VARCHAR) + ')'
            END
            + '-' + CAST(zam.ZaN_ZamNumer AS VARCHAR)
            + '/' + RIGHT('0' + CAST(zam.ZaN_ZamMiesiac AS VARCHAR), 2)
            + '/' + RIGHT(CAST(zam.ZaN_ZamRok AS VARCHAR), 2)
            + CASE WHEN zam.ZaN_ZamSeria <> '' THEN '/' + zam.ZaN_ZamSeria ELSE '' END
        WHEN 2592 THEN '<do uzupelnienia>'
        WHEN 14346 THEN
            'ZP-' + CAST(pzl.PZL_Numer AS VARCHAR)
            + '/' + RIGHT('0' + CAST(pzl.PZL_Miesiac AS VARCHAR), 2)
            + '/' + RIGHT(CAST(pzl.PZL_Rok AS VARCHAR), 2)
            + CASE WHEN pzl.PZL_Seria <> '' THEN '/' + pzl.PZL_Seria ELSE '' END
        ELSE NULL
    END                                                        AS Numer_Dok_Zrodlowego,

    -- === OPERATOR ===
    r.Rez_OpeNumer                                             AS ID_Operatora,
    o.Ope_Ident                                                AS Login_Operatora,
    o.Ope_Nazwisko                                             AS Imie_Nazwisko_Operatora,

    -- === MAGAZYN (0 = rezerwacja globalna, bez przypisanego magazynu) ===
    CASE WHEN r.Rez_MagNumer = 0 THEN NULL
         ELSE r.Rez_MagNumer END                               AS ID_Magazynu,
    m.Mag_Kod                                                  AS Kod_Magazynu,
    m.Mag_Nazwa                                                AS Nazwa_Magazynu,

    -- === DOSTAWA ===
    CASE WHEN r.Rez_DstNumer = 0 THEN NULL
         ELSE r.Rez_DstNumer END                               AS ID_Dostawy,
    CASE WHEN r.Rez_DstNumer = 0 THEN NULL
         ELSE
             CASE dst.Dst_TrnTyp
                 WHEN 1521 THEN 'FZ'
                 WHEN 1617 THEN 'PW'
                 WHEN 1489 THEN 'PZ'
                 ELSE 'Nieznany (' + CAST(dst.Dst_TrnTyp AS VARCHAR) + ')'
             END
             + '-' + CAST(trn.TrN_TrNNumer AS VARCHAR)
             + '/' + RIGHT('0' + CAST(trn.TrN_TrNMiesiac AS VARCHAR), 2)
             + '/' + RIGHT(CAST(trn.TrN_TrNRok AS VARCHAR), 2)
             + CASE WHEN trn.TrN_TrNSeria <> '' THEN '/' + trn.TrN_TrNSeria ELSE '' END
    END                                                        AS Numer_Dok_Dostawy,

    -- === ILOŚCI ===
    r.Rez_Ilosc                                                AS Ilosc_Zarezerwowana,
    r.Rez_Zrealizowano                                         AS Ilosc_Zrealizowana,
    r.Rez_IloscMag                                             AS Ilosc_Na_Dok_Mag,

    -- === DATY ===
    CASE WHEN r.Rez_TStamp        = 0 THEN NULL ELSE DATEADD(ss, r.Rez_TStamp,        '1990-01-01') END AS Data_Modyfikacji,
    CASE WHEN r.Rez_DataRealizacji = 0 THEN NULL ELSE DATEADD(d,  r.Rez_DataRealizacji,'18001228')   END AS Data_Realizacji,
    CASE WHEN r.Rez_DataWaznosci   = 0 THEN NULL ELSE DATEADD(d,  r.Rez_DataWaznosci,  '18001228')   END AS Data_Waznosci,
    CASE WHEN r.Rez_DataAktywacji  = 0 THEN NULL ELSE DATEADD(d,  r.Rez_DataAktywacji, '18001228')   END AS Data_Aktywacji,
    CASE WHEN r.Rez_DataPotwDst    = 0 THEN NULL ELSE DATEADD(d,  r.Rez_DataPotwDst,   '18001228')   END AS Data_Potwierdzenia_Dostawy,
    CASE WHEN r.Rez_DataRezerwacji = 0 THEN NULL ELSE DATEADD(ss, r.Rez_DataRezerwacji,'1990-01-01') END AS Data_Rezerwacji,

    -- === STATUSY ===
    CASE r.Rez_Aktywna
        WHEN 1 THEN 'Tak'
        WHEN 0 THEN 'Nie'
        ELSE 'Nieznana (' + CAST(r.Rez_Aktywna AS VARCHAR) + ')'
    END                                                        AS Aktywna,

    CASE r.Rez_Typ
        WHEN 1 THEN 'Rezerwacja'
        WHEN 0 THEN 'Nierezerwacja'
        ELSE 'Nieznany (' + CAST(r.Rez_Typ AS VARCHAR) + ')'
    END                                                        AS Typ,

    CASE r.Rez_Zrodlo
        WHEN 5  THEN 'Z zamówienia wewnętrznego'
        WHEN 6  THEN 'Ręczna wewnętrzna'
        WHEN 9  THEN 'Z zamówienia zewnętrznego'
        WHEN 10 THEN 'Ręczna zewnętrzna'
        WHEN 16 THEN 'Dok. magazynowy'
        ELSE 'Nieznane (' + CAST(r.Rez_Zrodlo AS VARCHAR) + ')'
    END                                                        AS Zrodlo,

    r.Rez_Priorytet                                            AS Priorytet,

    -- === CENTRUM STRUKTURY ===
    r.Rez_FrsID                                                AS ID_Centrum,
    frs.FRS_Nazwa                                              AS Nazwa_Centrum,

    -- === ZASÓB TECHNOLOGII (ZPZ) ===
    CASE WHEN r.Rez_PTZID = 0 THEN NULL
         ELSE r.Rez_PTZID END                                  AS ID_Zasobu_Technologii,
    ptz.PTZ_Nazwa                                              AS Nazwa_Zasobu_Technologii,

    -- === CECHY ===
    r.Rez_CCHNumer                                             AS ID_Cechy,
    r.Rez_Cecha                                                AS Cecha,

    -- === TECHNICZNE ===
    r.Rez_GUID                                                 AS GUID_Rezerwacji  -- zawsze pusty w bieżących danych

FROM CDN.Rezerwacje r
INNER JOIN CDN.TwrKarty      t   ON t.Twr_GIDNumer  = r.Rez_TwrNumer
LEFT  JOIN CDN.KntKarty      k   ON k.Knt_GIDNumer  = r.Rez_KntNumer   AND r.Rez_KntNumer > 0
INNER JOIN CDN.OpeKarty      o   ON o.Ope_GIDNumer  = r.Rez_OpeNumer
LEFT  JOIN CDN.Magazyny      m   ON m.Mag_GIDNumer  = r.Rez_MagNumer   AND r.Rez_MagNumer > 0
LEFT  JOIN CDN.FrmStruktura  frs ON frs.FRS_ID       = r.Rez_FrsID
LEFT  JOIN CDN.Dostawy       dst ON dst.Dst_GIDNumer = r.Rez_DstNumer   AND r.Rez_DstNumer > 0
LEFT  JOIN CDN.TraNag        trn ON trn.TrN_GIDNumer = dst.Dst_TrnNumer AND trn.TrN_GIDTyp = dst.Dst_TrnTyp
LEFT  JOIN CDN.ProdTechnologiaZasoby ptz ON ptz.PTZ_Id = r.Rez_PTZID   AND r.Rez_PTZID > 0
LEFT  JOIN CDN.ZamNag               zam ON zam.ZaN_GIDNumer = r.Rez_ZrdNumer AND r.Rez_ZrdTyp = 960
LEFT  JOIN CDN.ProdZasoby           pza ON pza.PZA_Id      = r.Rez_ZrdNumer AND r.Rez_ZrdTyp = 14346
LEFT  JOIN CDN.ProdZlecenia         pzl ON pzl.PZL_Id      = pza.PZA_PZLId

WHERE r.Rez_TwrNumer > 0
