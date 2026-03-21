-- MagNag draft SELECT
-- Brudnopis widoku BI dla CDN.MagNag (nagłówki dokumentów magazynowych)
-- Nie używać CREATE VIEW — wyłącznie SELECT
-- Tabela główna: CDN.MagNag | Baseline: 199 862 wierszy

SELECT TOP 100000

    -- === IDENTYFIKATOR DOKUMENTU ===
    CASE n.MaN_GIDTyp
        WHEN 1089 THEN 'Przyjęcie magazynowe'
        WHEN 1093 THEN 'Awizo dostawy'
        WHEN 1601 THEN 'Wydanie magazynowe'
        WHEN 1605 THEN 'Zlecenie wydania z magazynu'
        ELSE 'Nieznane (' + CAST(n.MaN_GIDTyp AS VARCHAR) + ')'
    END                                                                 AS Typ_Dokumentu,

    n.MaN_GIDNumer                                                      AS ID_Dokumentu,

    -- === NUMER DOKUMENTU ===
    CASE n.MaN_GIDTyp
        WHEN 1089 THEN 'PM'
        WHEN 1093 THEN 'AWD'
        WHEN 1601 THEN 'WM'
        WHEN 1605 THEN 'ZWM'
        ELSE '??'
    END
    + '-' + CAST(n.MaN_TrNNumer AS VARCHAR(10))
    + '/' + RIGHT('0' + CAST(n.MaN_TrNMiesiac AS VARCHAR(2)), 2)
    + '/' + RIGHT(CAST(n.MaN_TrNRok AS VARCHAR(4)), 2)
    + CASE WHEN RTRIM(n.MaN_TrNSeria) = '' THEN '' ELSE '/' + RTRIM(n.MaN_TrNSeria) END
                                                                        AS Nr_Dokumentu,

    n.MaN_TrNRok                                                        AS Rok_Transakcji,
    n.MaN_TrNMiesiac                                                    AS Miesiac_Transakcji,
    NULLIF(RTRIM(n.MaN_TrNSeria), '')                                   AS Seria,

    -- === DOKUMENT ŹRÓDŁOWY ===
    CASE
        WHEN n.MaN_ZrdTyp = 0     THEN NULL
        WHEN n.MaN_ZrdTyp = 960   THEN 'Zamówienie'
        WHEN n.MaN_ZrdTyp = 1489  THEN 'Przyjęcie zewnętrzne'
        WHEN n.MaN_ZrdTyp = 1497  THEN 'Korekta PZ'
        WHEN n.MaN_ZrdTyp = 1521  THEN 'Faktura zakupu'
        WHEN n.MaN_ZrdTyp = 1529  THEN 'Korekta FZ'
        WHEN n.MaN_ZrdTyp = 1603  THEN 'Przesunięcie MMW'
        WHEN n.MaN_ZrdTyp = 1604  THEN 'Przesunięcie MMP'
        WHEN n.MaN_ZrdTyp = 1616  THEN 'Rozchód wewnętrzny'
        WHEN n.MaN_ZrdTyp = 1617  THEN 'Przychód wewnętrzny'
        WHEN n.MaN_ZrdTyp = 1624  THEN 'Korekta RW'
        WHEN n.MaN_ZrdTyp = 1625  THEN 'Korekta PW'
        WHEN n.MaN_ZrdTyp = 2001  THEN 'Wydanie zewnętrzne'
        WHEN n.MaN_ZrdTyp = 2005  THEN 'WZ eksportowe'
        WHEN n.MaN_ZrdTyp = 2009  THEN 'Korekta WZ'
        WHEN n.MaN_ZrdTyp = 2013  THEN 'Korekta WZE'
        WHEN n.MaN_ZrdTyp = 2033  THEN 'Faktura sprzedaży'
        WHEN n.MaN_ZrdTyp = 2034  THEN 'Paragon'
        WHEN n.MaN_ZrdTyp = 2037  THEN 'Faktura eksportowa'
        WHEN n.MaN_ZrdTyp = 2041  THEN 'Korekta FS'
        WHEN n.MaN_ZrdTyp = 2042  THEN 'Korekta paragonu'
        ELSE 'Nieznane (' + CAST(n.MaN_ZrdTyp AS VARCHAR) + ')'
    END                                                                 AS Typ_Dokumentu_Zrodlowego,

    CASE WHEN n.MaN_ZrdNumer = 0 THEN NULL ELSE n.MaN_ZrdNumer END      AS ID_Dokumentu_Zrodlowego,

    -- Nr_Dokumentu_Zrodlowego: ZamNag (typ 960) lub TraNag (pozostałe)
    CASE
        WHEN n.MaN_ZrdNumer = 0 THEN NULL
        WHEN n.MaN_ZrdTyp = 960 THEN
            CASE WHEN zrd_zan.ZaN_GIDNumer IS NULL THEN NULL
            ELSE
                CASE zrd_zan.ZaN_ZamTyp
                    WHEN 640  THEN 'OFZ'
                    WHEN 768  THEN 'OFS'
                    WHEN 1152 THEN 'ZZ'
                    WHEN 1280 THEN 'ZS'
                    WHEN 2688 THEN 'ZZ'
                    WHEN 2816 THEN 'ZS'
                    ELSE '??'
                END
                + '-' + CAST(zrd_zan.ZaN_ZamNumer AS VARCHAR(10))
                + '/' + RIGHT('0' + CAST(zrd_zan.ZaN_ZamMiesiac AS VARCHAR(2)), 2)
                + '/' + RIGHT(CAST(zrd_zan.ZaN_ZamRok AS VARCHAR(4)), 2)
                + CASE WHEN RTRIM(zrd_zan.ZaN_ZamSeria) = '' THEN '' ELSE '/' + RTRIM(zrd_zan.ZaN_ZamSeria) END
            END
        ELSE
            CASE WHEN zrd_trn.TrN_GIDNumer IS NULL THEN NULL
            ELSE
                CASE
                    WHEN zrd_trn.TrN_GenDokMag = -1 AND zrd_trn.TrN_GIDTyp IN (1521, 1529, 1489) THEN '(A)'
                    WHEN zrd_trn.TrN_GenDokMag = -1 THEN '(s)'
                    ELSE ''
                END
                + CASE zrd_trn.TrN_GIDTyp
                    WHEN 2034 THEN 'PA'   WHEN 2033 THEN 'FS'   WHEN 1617 THEN 'PW'
                    WHEN 2001 THEN 'WZ'   WHEN 1521 THEN 'FZ'   WHEN 2009 THEN 'WZK'
                    WHEN 1603 THEN 'MMW'  WHEN 1604 THEN 'MMP'  WHEN 1616 THEN 'RW'
                    WHEN 2041 THEN 'FSK'  WHEN 1489 THEN 'PZ'   WHEN 1497 THEN 'PZK'
                    WHEN 1625 THEN 'PWK'  WHEN 1529 THEN 'FZK'  WHEN 2042 THEN 'PAK'
                    WHEN 2037 THEN 'FSE'  WHEN 2013 THEN 'WKE'  WHEN 2005 THEN 'WZE'
                    WHEN 1624 THEN 'RWK'
                    ELSE CAST(zrd_trn.TrN_GIDTyp AS VARCHAR(10))
                  END
                + '-' + CAST(zrd_trn.TrN_TrNNumer AS VARCHAR(10))
                + '/' + RIGHT('0' + CAST(zrd_trn.TrN_TrNMiesiac AS VARCHAR(2)), 2)
                + '/' + RIGHT(CAST(zrd_trn.TrN_TrNRok AS VARCHAR(4)), 2)
                + CASE WHEN RTRIM(zrd_trn.TrN_TrNSeria) = '' THEN '' ELSE '/' + RTRIM(zrd_trn.TrN_TrNSeria) END
            END
    END                                                                 AS Nr_Dokumentu_Zrodlowego,

    -- === MAGAZYNY ===
    n.MaN_TrMNumer                                                      AS ID_Magazynu_Transakcji,
    mag_trm.MAG_Kod                                                     AS Kod_Magazynu_Transakcji,
    mag_trm.MAG_Nazwa                                                   AS Nazwa_Magazynu_Transakcji,

    CASE n.MaN_TrNTyp
        WHEN 8 THEN 'Wydanie'
        WHEN 9 THEN 'Przyjęcie'
        ELSE 'Nieznane (' + CAST(n.MaN_TrNTyp AS VARCHAR) + ')'
    END                                                                 AS Typ_Transakcji,

    -- === KONTRAHENT ===
    CASE WHEN n.MaN_KntNumer = 0 THEN NULL ELSE n.MaN_KntNumer END      AS ID_Kontrahenta,
    knt.Knt_Akronim                                                     AS Akronim_Kontrahenta,
    knt.Knt_Nazwa1                                                      AS Nazwa_Kontrahenta,

    -- === ADRES KONTRAHENTA ===
    CASE WHEN n.MaN_KnANumer = 0 THEN NULL ELSE n.MaN_KnANumer END      AS ID_Adresu_Kontrahenta,
    kna.KnA_Akronim                                                     AS Akronim_Adresu_Kontrahenta,

    -- === OPERATOR ===
    n.MaN_OpeNumer                                                      AS ID_Operatora,
    ope.Ope_Ident                                                       AS Akronim_Operatora,

    -- === DATA WYSTAWIENIA ===
    CASE WHEN n.MaN_Data3 = 0 THEN NULL
         ELSE CAST(DATEADD(d, n.MaN_Data3, '18001228') AS DATE)
    END                                                                 AS Data_Wystawienia,

    -- === STAN I STATUS ===
    CASE n.MaN_Stan
        WHEN 0 THEN 'W edycji'
        WHEN 1 THEN 'W buforze'
        WHEN 2 THEN 'Po edycji w buforze'
        WHEN 5 THEN 'Zatwierdzona'
        WHEN 6 THEN 'Anulowana'
        ELSE 'Nieznane (' + CAST(n.MaN_Stan AS VARCHAR) + ')'
    END                                                                 AS Stan_Dokumentu,

    CASE n.MaN_Status
        WHEN 0 THEN 'Niezatwierdzony'
        WHEN 1 THEN 'Zatwierdzony'
        WHEN 2 THEN 'W realizacji'
        WHEN 3 THEN 'Zrealizowany'
        WHEN 4 THEN 'Zamknięty'
        WHEN 5 THEN 'Zamknięty bez realizacji'
        WHEN 6 THEN 'Zamknięty do edycji'
        ELSE 'Nieznane (' + CAST(n.MaN_Status AS VARCHAR) + ')'
    END                                                                 AS Status_Zlecenia,

    -- === MAGAZYN DOCELOWY ===
    n.MaN_MagDNumer                                                     AS ID_Magazynu_Docelowego,
    mag_d.MAG_Kod                                                       AS Kod_Magazynu_Docelowego,
    mag_d.MAG_Nazwa                                                     AS Nazwa_Magazynu_Docelowego,

    -- === CENTRUM ===
    n.MaN_FrsID                                                         AS ID_Centrum,
    frs.FRS_Nazwa                                                       AS Nazwa_Centrum,

    -- === CECHA ===
    NULLIF(n.MaN_CechaOpis, '')                                         AS Cecha,

    -- === OPERATOR MODYFIKUJĄCY ===
    CASE WHEN n.MaN_OpeNumerM = 0 THEN NULL ELSE n.MaN_OpeNumerM END    AS ID_Operatora_Modyfikujacego,
    ope_m.Ope_Ident                                                     AS Akronim_Operatora_Modyfikujacego,

    -- === OPERATOR REALIZUJĄCY ===
    CASE WHEN n.MaN_OpeNumerR = 0 THEN NULL ELSE n.MaN_OpeNumerR END    AS ID_Operatora_Realizujacego,
    ope_r.Ope_Ident                                                     AS Akronim_Operatora_Realizujacego,

    -- === ZAMÓWIENIE ===
    CASE WHEN n.MaN_ZaNNumer = 0 THEN NULL ELSE n.MaN_ZaNNumer END      AS ID_Zamowienia,
    CASE WHEN n.MaN_ZaNNumer = 0 THEN NULL
    ELSE
        CASE zan.ZaN_ZamTyp
            WHEN 640  THEN 'OFZ'
            WHEN 768  THEN 'OFS'
            WHEN 1152 THEN 'ZZ'
            WHEN 1280 THEN 'ZS'
            WHEN 2688 THEN 'ZZ'
            WHEN 2816 THEN 'ZS'
            ELSE '??'
        END
        + '-' + CAST(zan.ZaN_ZamNumer AS VARCHAR(10))
        + '/' + RIGHT('0' + CAST(zan.ZaN_ZamMiesiac AS VARCHAR(2)), 2)
        + '/' + RIGHT(CAST(zan.ZaN_ZamRok AS VARCHAR(4)), 2)
        + CASE WHEN RTRIM(zan.ZaN_ZamSeria) = '' THEN '' ELSE '/' + RTRIM(zan.ZaN_ZamSeria) END
    END                                                                 AS Nr_Zamowienia,

    -- === DATY TIMESTAMPS ===
    CASE WHEN n.MaN_LastMod = 0 THEN NULL
         ELSE CAST(DATEADD(ss, n.MaN_LastMod, '1990-01-01') AS DATETIME)
    END                                                                 AS DataCzas_Modyfikacji,

    CASE WHEN n.MaN_DataOd = 0 THEN NULL
         ELSE CAST(DATEADD(ss, n.MaN_DataOd, '1990-01-01') AS DATETIME)
    END                                                                 AS DataCzas_Od,

    CASE WHEN n.MaN_DataDo = 0 THEN NULL
         ELSE CAST(DATEADD(ss, n.MaN_DataDo, '1990-01-01') AS DATETIME)
    END                                                                 AS DataCzas_Do,

    -- === DATA ZATWIERDZENIA ===
    CASE WHEN n.MaN_DataZatwierdzenia = 0 THEN NULL
         ELSE CAST(DATEADD(d, n.MaN_DataZatwierdzenia, '18001228') AS DATE)
    END                                                                 AS Data_Zatwierdzenia,

    -- === REALIZACJA I DOSTAWY ===
    n.MaN_Realizacja                                                    AS Realizacja_Procent,
    NULLIF(n.MaN_SposobDostawy, '')                                     AS Sposob_Dostawy,
    n.MaN_Priorytet                                                     AS Priorytet_Zlecenia,

    -- === POWIĄZANIE ŹRÓDŁOWE ===
    CASE n.MaN_Zrodlo
        WHEN 0 THEN 'Niepowiązany'
        WHEN 1 THEN 'Powiązany'
        WHEN 2 THEN 'Powiązany wielokrotnie'
        ELSE 'Nieznane (' + CAST(n.MaN_Zrodlo AS VARCHAR) + ')'
    END                                                                 AS Powiazanie_Zrodlowe,

    -- === WMS ===
    CASE n.MaN_WMS
        WHEN 0   THEN 'Nie'
        WHEN 177 THEN 'Tak'
        ELSE 'Nieznane (' + CAST(n.MaN_WMS AS VARCHAR) + ')'
    END                                                                 AS Dokument_WMS

FROM CDN.MagNag n

-- Magazyn transakcji (zawsze obecny)
LEFT JOIN CDN.Magazyny mag_trm ON mag_trm.MAG_GIDNumer = n.MaN_TrMNumer

-- Magazyn docelowy (zawsze obecny)
LEFT JOIN CDN.Magazyny mag_d   ON mag_d.MAG_GIDNumer = n.MaN_MagDNumer

-- Kontrahent (tylko gdy KntNumer > 0)
LEFT JOIN CDN.KntKarty knt     ON knt.Knt_GIDNumer = n.MaN_KntNumer
                               AND knt.Knt_GIDTyp   = n.MaN_KntTyp
                               AND n.MaN_KntNumer > 0

-- Adres kontrahenta (tylko gdy KnANumer > 0)
LEFT JOIN CDN.KntAdresy kna    ON kna.KnA_GIDNumer = n.MaN_KnANumer
                               AND kna.KnA_GIDTyp   = n.MaN_KnATyp
                               AND n.MaN_KnANumer > 0

-- Operator wystawiający (zawsze obecny)
LEFT JOIN CDN.OpeKarty ope     ON ope.Ope_GIDNumer = n.MaN_OpeNumer

-- Operator realizujący (tylko gdy OpeNumerR > 0)
LEFT JOIN CDN.OpeKarty ope_r   ON ope_r.Ope_GIDNumer = n.MaN_OpeNumerR
                               AND n.MaN_OpeNumerR > 0

-- Operator modyfikujący (tylko gdy OpeNumerM > 0)
LEFT JOIN CDN.OpeKarty ope_m   ON ope_m.Ope_GIDNumer = n.MaN_OpeNumerM
                               AND n.MaN_OpeNumerM > 0

-- Centrum struktury praw (zawsze obecne)
LEFT JOIN CDN.FrmStruktura frs ON frs.FRS_ID = n.MaN_FrsID

-- Zamówienie powiązane (tylko gdy ZaNNumer > 0)
LEFT JOIN CDN.ZamNag zan       ON zan.ZaN_GIDNumer = n.MaN_ZaNNumer
                               AND n.MaN_ZaNNumer > 0

-- Dokument źródłowy: ZamNag (ZrdTyp=960)
LEFT JOIN CDN.ZamNag zrd_zan   ON zrd_zan.ZaN_GIDNumer = n.MaN_ZrdNumer
                               AND n.MaN_ZrdTyp = 960
                               AND n.MaN_ZrdNumer > 0

-- Dokument źródłowy: TraNag (wszystkie inne typy)
LEFT JOIN CDN.TraNag zrd_trn   ON zrd_trn.TrN_GIDNumer = n.MaN_ZrdNumer
                               AND zrd_trn.TrN_GIDTyp   = n.MaN_ZrdTyp
                               AND n.MaN_ZrdTyp <> 960
                               AND n.MaN_ZrdNumer > 0
;
