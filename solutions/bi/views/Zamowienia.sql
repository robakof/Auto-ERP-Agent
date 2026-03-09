CREATE OR ALTER VIEW BI.Zamowienia AS

-- BRUDNOPIS — BI.Zamowienia

SELECT
    -- === IDENTYFIKACJA ===
    n.ZaN_GIDNumer                                              AS ID_Zamowienia,
    'Zamówienie'                                                AS Typ_GID,
    CASE n.ZaN_ZamTyp
        WHEN 640  THEN 'Oferta zakupu'
        WHEN 768  THEN 'Oferta sprzedaży'
        WHEN 1152 THEN 'ZZ'
        WHEN 1280 THEN 'ZS'
        WHEN 2688 THEN 'Zapytanie ofertowe zakupu'
        WHEN 2816 THEN 'Zapytanie ofertowe sprzedaży'
        ELSE 'Nieznane (' + CAST(n.ZaN_ZamTyp AS VARCHAR) + ')'
    END                                                         AS Typ_Zamowienia,
    CASE n.ZaN_Stan
        WHEN 1  THEN 'Oferta'
        WHEN 2  THEN 'Zamówienie'
        WHEN 3  THEN 'Potwierdzone'
        WHEN 4  THEN 'Zaakceptowane'
        WHEN 5  THEN 'W realizacji'
        WHEN 19 THEN 'Odrzucone'
        WHEN 21 THEN 'Zrealizowane'
        WHEN 35 THEN 'Anulowane (potwierdzone)'
        WHEN 51 THEN 'Anulowane (arch.+potw.)'
        WHEN 53 THEN 'Zamknięte w realizacji'
        ELSE 'Nieznane (' + CAST(n.ZaN_Stan AS VARCHAR) + ')'
    END                                                         AS Stan,
    CASE n.ZaN_Rodzaj
        WHEN 4 THEN 'Zewnętrzne'
        WHEN 8 THEN 'Wewnętrzne'
        ELSE 'Nieznane (' + CAST(n.ZaN_Rodzaj AS VARCHAR) + ')'
    END                                                         AS Rodzaj,

    -- === NUMERY DOKUMENTÓW ===
    CASE n.ZaN_ZamTyp
        WHEN 640  THEN 'OFZ'
        WHEN 768  THEN 'OFS'
        WHEN 1152 THEN 'ZZ'
        WHEN 1280 THEN 'ZS'
        ELSE 'ZAM'
    END + '-' + CAST(n.ZaN_ZamNumer AS VARCHAR(10))
      + '/' + RIGHT('0' + CAST(n.ZaN_ZamMiesiac AS VARCHAR(2)), 2)
      + '/' + RIGHT(CAST(n.ZaN_ZamRok AS VARCHAR(4)), 2)
      + '/' + RTRIM(n.ZaN_ZamSeria)                            AS Numer_Dokumentu,

    CASE
        WHEN n.ZaN_PomNumer > 0
        THEN CASE n.ZaN_ZamTyp
                WHEN 640  THEN 'OFZ'
                WHEN 768  THEN 'OFS'
                WHEN 1152 THEN 'ZZ'
                WHEN 1280 THEN 'ZS'
                ELSE 'ZAM'
             END + '-' + CAST(n.ZaN_PomNumer AS VARCHAR(10))
               + '/' + RIGHT('0' + CAST(n.ZaN_PomMiesiac AS VARCHAR(2)), 2)
               + '/' + RIGHT(CAST(n.ZaN_PomRok AS VARCHAR(4)), 2)
               + '/' + RTRIM(n.ZaN_PomSeria)
    END                                                         AS Numer_Potwierdzenia,

    -- Źródłowy: self-join z warunkiem ZrdNumer != GIDNumer (aktualnie self-ref → NULL)
    CASE
        WHEN zrd.ZaN_GIDNumer IS NOT NULL
        THEN CASE zrd.ZaN_ZamTyp
                WHEN 640  THEN 'OFZ'
                WHEN 768  THEN 'OFS'
                WHEN 1152 THEN 'ZZ'
                WHEN 1280 THEN 'ZS'
                ELSE 'ZAM'
             END + '-' + CAST(zrd.ZaN_ZamNumer AS VARCHAR(10))
               + '/' + RIGHT('0' + CAST(zrd.ZaN_ZamMiesiac AS VARCHAR(2)), 2)
               + '/' + RIGHT(CAST(zrd.ZaN_ZamRok AS VARCHAR(4)), 2)
               + '/' + RTRIM(zrd.ZaN_ZamSeria)
    END                                                         AS Numer_Dokumentu_Zrodlowego,
    'Zamówienie'                                                AS Typ_Dokumentu_Zrodlowego,

    -- Korekta (2/12022 nonzero) — jako raw ID
    CASE WHEN n.ZaN_KorNumer > 0 THEN n.ZaN_KorNumer END       AS ID_Dokumentu_Korekty,
    CASE
        WHEN n.ZaN_KorTyp > 0
        THEN CASE n.ZaN_KorTyp
                WHEN 960 THEN 'Zamówienie'
                ELSE 'Nieznane (' + CAST(n.ZaN_KorTyp AS VARCHAR) + ')'
             END
    END                                                         AS Typ_Dokumentu_Korekty,

    -- === KONTRAHENT (CDN.KntKarty) ===
    n.ZaN_KntNumer                                              AS ID_Kontrahenta,
    k.Knt_Akronim                                               AS Akronim_Kontrahenta,
    k.Knt_Nazwa1                                                AS Nazwa_Kontrahenta,

    -- === ADRES KONTRAHENTA (CDN.KntAdresy) ===
    n.ZaN_KnANumer                                              AS ID_Adresu_Knt,
    kna.KnA_Akronim                                             AS Adres_Knt_Akronim,
    kna.KnA_Miasto                                              AS Adres_Knt_Miasto,
    kna.KnA_KodP                                                AS Adres_Knt_Kod_Pocztowy,
    kna.KnA_Ulica                                               AS Adres_Knt_Ulica,

    -- === ODBIORCA (CDN.KntKarty) ===
    CASE WHEN n.ZaN_KnDNumer > 0 THEN n.ZaN_KnDNumer END       AS ID_Odbiorcy,
    odb.Knt_Akronim                                             AS Akronim_Odbiorcy,
    odb.Knt_Nazwa1                                              AS Nazwa_Odbiorcy,

    -- === PŁATNIK (CDN.KntKarty) ===
    CASE WHEN n.ZaN_KnPNumer > 0 THEN n.ZaN_KnPNumer END       AS ID_Platnika,
    plat.Knt_Akronim                                            AS Akronim_Platnika,
    plat.Knt_Nazwa1                                             AS Nazwa_Platnika,

    -- === AKWIZYTOR (CDN.KntKarty) ===
    CASE WHEN n.ZaN_AkwNumer > 0 THEN n.ZaN_AkwNumer END       AS ID_Akwizytora,
    akw.Knt_Akronim                                             AS Akronim_Akwizytora,

    -- === ADRES WYSYŁKI (CDN.KntAdresy) ===
    n.ZaN_AdWNumer                                              AS ID_Adresu_Wysylki,
    adw.KnA_Akronim                                             AS Adres_Wysylki_Akronim,
    adw.KnA_Miasto                                              AS Adres_Wysylki_Miasto,
    adw.KnA_KodP                                                AS Adres_Wysylki_Kod_Pocztowy,
    adw.KnA_Ulica                                               AS Adres_Wysylki_Ulica,

    -- === MAGAZYN (CDN.Magazyny) ===
    n.ZaN_MagNumer                                              AS ID_Magazynu,
    m.MAG_Kod                                                   AS Kod_Magazynu,
    m.MAG_Nazwa                                                 AS Nazwa_Magazynu,

    -- === MAGAZYN DOCELOWY (CDN.Magazyny) ===
    CASE WHEN n.ZaN_MagDNumer > 0 THEN n.ZaN_MagDNumer END     AS ID_Magazynu_Docelowego,
    magd.MAG_Kod                                                AS Kod_Magazynu_Docelowego,
    magd.MAG_Nazwa                                              AS Nazwa_Magazynu_Docelowego,

    -- === FORMY I TERMINY PŁATNOŚCI ===
    n.ZaN_FormaNr                                               AS ID_Formy_Platnosci,
    CASE n.ZaN_FormaNr
        WHEN 0  THEN 'Brak'
        WHEN 10 THEN 'Gotówka'
        WHEN 20 THEN 'Przelew'
        WHEN 30 THEN 'Kredyt'
        WHEN 40 THEN 'Czek'
        WHEN 50 THEN 'Karta'
        WHEN 60 THEN 'Inne'
        ELSE 'Nieznane (' + CAST(n.ZaN_FormaNr AS VARCHAR) + ')'
    END                                                         AS Forma_Platnosci,
    RTRIM(n.ZaN_FormaNazwa)                                     AS Nazwa_Formy_Platnosci,
    n.ZaN_TerminPlatnosci                                       AS Termin_Platnosci,

    -- === WALUTA I KURS ===
    n.ZaN_Waluta                                                AS Waluta,
    n.ZaN_KursM                                                 AS Kurs_Mianownik,
    n.ZaN_KursL                                                 AS Kurs_Licznik,
    CASE n.ZaN_TypKursu
        WHEN 1 THEN 'Bieżący'
        WHEN 2 THEN 'Ustalony'
        WHEN 3 THEN 'Ustalony do daty'
        ELSE 'Nieznane (' + CAST(n.ZaN_TypKursu AS VARCHAR) + ')'
    END                                                         AS Typ_Kursu,
    CASE n.ZaN_WspolnaWaluta
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(n.ZaN_WspolnaWaluta AS VARCHAR) + ')'
    END                                                         AS Wspolna_Waluta,

    -- === RABATY ===
    CASE WHEN n.ZaN_Rabat = 0 THEN NULL ELSE n.ZaN_Rabat END   AS Rabat,
    CASE n.ZaN_TypRabatu
        WHEN 0 THEN NULL
        WHEN 1 THEN 'Procentowy'
        WHEN 2 THEN 'Kwotowy'
        ELSE 'Nieznane (' + CAST(n.ZaN_TypRabatu AS VARCHAR) + ')'
    END                                                         AS Typ_Rabatu,
    CASE WHEN n.ZaN_RabatW = 0 THEN NULL ELSE n.ZaN_RabatW END AS Rabat_Wartosciowy,
    n.ZaN_RabatPromocyjnyGlobalny                               AS Rabat_Promocyjny_Globalny,
    CASE n.ZaN_PromocjePar
        WHEN 0 THEN 'Z KGO'
        WHEN 1 THEN 'Bez KGO'
        WHEN 3 THEN 'Nieznane (3)'
        ELSE 'Nieznane (' + CAST(n.ZaN_PromocjePar AS VARCHAR) + ')'
    END                                                         AS Sposob_Naliczania_Rabatow,
    CASE WHEN n.ZaN_PcKID = 0 THEN NULL ELSE n.ZaN_PcKID END   AS ID_Cennika_Kontrahenta,

    -- === CENNIK (CDN.TwrCenyNag) ===
    n.ZaN_CenaSpr                                               AS ID_Cennika_Sprzedazy,
    RTRIM(tcn.Nazwa_Cennika)                                    AS Nazwa_Cennika_Sprzedazy,

    -- === REJESTR KASOWY (CDN.Rejestry) ===
    CASE WHEN n.ZaN_KarNumer > 0 THEN n.ZaN_KarNumer END       AS ID_Rejestru_Kasowego,
    rej.KAR_Seria                                               AS Seria_Rejestru_Kasowego,
    rej.KAR_Nazwa                                               AS Nazwa_Rejestru_Kasowego,

    -- === EKSPORT / INCOTERMS ===
    CASE n.ZaN_ExpoNorm
        WHEN 0  THEN 'Krajowa'
        WHEN 1  THEN 'Inna zagraniczna VAT 0%'
        WHEN 2  THEN 'Inna zagraniczna VAT dowolny'
        WHEN 6  THEN 'WW dostawa VAT 0%'
        WHEN 7  THEN 'WW dostawa VAT dowolny'
        WHEN 8  THEN 'WW dostawa trójstr. VAT 0%'
        WHEN 9  THEN 'WW dostawa trójstr. VAT dowolny'
        WHEN 10 THEN 'WW nabycie VAT 0%'
        WHEN 11 THEN 'WW nabycie VAT dowolny'
        WHEN 12 THEN 'WW nabycie trójstr. VAT 0%'
        WHEN 13 THEN 'WW nabycie trójstr. VAT dowolny'
        WHEN 26 THEN 'WSTO EE'
        ELSE 'Nieznane (' + CAST(n.ZaN_ExpoNorm AS VARCHAR) + ')'
    END                                                         AS Eksport_Norma,
    NULLIF(RTRIM(n.ZaN_IncotermsSymbol), '')                    AS Symbol_Incoterms,
    NULLIF(RTRIM(n.ZaN_KrajPrzezWys), '')                       AS Kraj_Przez_Wysylke,

    -- === DOSTAWA I CECHY ===
    NULLIF(RTRIM(n.ZaN_SpDostawy), '')                          AS Sposob_Dostawy,
    NULLIF(NULLIF(RTRIM(n.ZaN_CechaOpis), '<Nieokreślona>'), '') AS Cecha_Opis,

    -- === FLAGA NETTO/BRUTTO ===
    CASE n.ZaN_FlagaNB
        WHEN 'N' THEN 'Netto'
        WHEN 'B' THEN 'Brutto'
        ELSE 'Nieznane (' + n.ZaN_FlagaNB + ')'
    END                                                         AS Netto_Brutto,

    -- === DATY ===
    CASE WHEN n.ZaN_DataWystawienia > 0
        THEN CAST(DATEADD(d, n.ZaN_DataWystawienia, '18001228') AS DATE) END AS Data_Wystawienia,
    CASE WHEN n.ZaN_GodzinaWystawienia > 0
        THEN CAST(DATEADD(ss, n.ZaN_GodzinaWystawienia / 100, '19000101') AS TIME) END AS Godzina_Wystawienia,
    CASE WHEN n.ZaN_DataRealizacji > 0
        THEN CAST(DATEADD(d, n.ZaN_DataRealizacji, '18001228') AS DATE) END AS Data_Realizacji,
    CASE WHEN n.ZaN_DataWaznosci > 0
        THEN CAST(DATEADD(d, n.ZaN_DataWaznosci, '18001228') AS DATE) END AS Data_Waznosci,
    CASE WHEN n.ZaN_DataPotwierdz > 0
        THEN CAST(DATEADD(d, n.ZaN_DataPotwierdz, '18001228') AS DATE) END AS Data_Potwierdzenia,
    CASE WHEN n.ZaN_GodzinaPotwierdzenia > 0
        THEN CAST(DATEADD(ss, n.ZaN_GodzinaPotwierdzenia / 100, '19000101') AS TIME) END AS Godzina_Potwierdzenia,
    CASE WHEN n.ZaN_DataAktywacjiRez > 0
        THEN CAST(DATEADD(d, n.ZaN_DataAktywacjiRez, '18001228') AS DATE) END AS Data_Aktywacji_Rezerwacji,
    CASE WHEN n.ZaN_LimitKredytowyWaznyDo > 0
        THEN CAST(DATEADD(d, n.ZaN_LimitKredytowyWaznyDo, '18001228') AS DATE) END AS Limit_Kredytowy_Wazny_Do,
    CASE WHEN n.ZaN_LastMod > 0
        THEN CAST(DATEADD(ss, n.ZaN_LastMod, '1990-01-01') AS DATETIME) END AS Data_Ostatniej_Modyfikacji,
    CASE WHEN n.ZaN_OstatniaModyfikacjaPOS > 0
        THEN CAST(DATEADD(ss, n.ZaN_OstatniaModyfikacjaPOS, '1990-01-01') AS DATETIME) END AS Data_Ostatniej_Modyfikacji_POS,

    -- === REALIZACJA ===
    CASE n.ZaN_RealWCalosci
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(n.ZaN_RealWCalosci AS VARCHAR) + ')'
    END                                                         AS Realizacja_W_Calosci,
    CASE WHEN n.ZaN_StatusRealizacji = 0 THEN NULL
         ELSE slw_stat.SLW_WartoscS
    END                                                         AS Status_Realizacji,
    CASE n.ZaN_Wyslano
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(n.ZaN_Wyslano AS VARCHAR) + ')'
    END                                                         AS Wyslano,
    CASE n.ZaN_RezerwacjeNaNiepotwierdzonym
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(n.ZaN_RezerwacjeNaNiepotwierdzonym AS VARCHAR) + ')'
    END                                                         AS Rezerwacje_Na_Niepotwierdzonym,
    n.ZaN_PriorytetRez                                          AS Priorytet_Rezerwacji,

    -- === OPIEKUN (CDN.PrcKarty, GIDTyp=944) ===
    CASE WHEN n.ZaN_OpiNumer > 0 THEN n.ZaN_OpiNumer END       AS ID_Opiekuna,
    NULLIF(RTRIM(prc.Prc_Imie1 + ' ' + prc.Prc_Nazwisko), '') AS Imie_Nazwisko_Opiekuna,

    -- === OPERATORZY ===
    n.ZaN_OpeNumerW                                             AS ID_Operatora_Wystawiajacego,
    opew.Ope_Ident                                              AS Login_Operatora_Wystawiajacego,
    CASE WHEN n.ZaN_OpeNumerM > 0 THEN n.ZaN_OpeNumerM END     AS ID_Operatora_Modyfikujacego,
    opem.Ope_Ident                                              AS Login_Operatora_Modyfikujacego,
    CASE WHEN n.ZaN_OpeNumerZ > 0 THEN n.ZaN_OpeNumerZ END     AS ID_Operatora_Zatwierdzajacego,
    opez.Ope_Ident                                              AS Login_Operatora_Zatwierdzajacego,
    CASE WHEN n.ZaN_OpeNumerP > 0 THEN n.ZaN_OpeNumerP END     AS ID_Operatora_Potwierdzajacego,
    opep.Ope_Ident                                              AS Login_Operatora_Potwierdzajacego,
    CASE WHEN n.ZaN_OpeNumerMod > 0 THEN n.ZaN_OpeNumerMod END AS ID_Operatora_Mod,
    opemod.Ope_Ident                                            AS Login_Operatora_Mod,
    CASE WHEN n.ZaN_OperatorPOS > 0 THEN n.ZaN_OperatorPOS END AS ID_Operatora_POS,
    opepos.Ope_Ident                                            AS Login_Operatora_POS,

    -- === FIRMA HANDLOWA (CDN.FrmStruktura) ===
    n.ZaN_FrSID                                                 AS ID_Firmy_Handlowej,
    frs.FRS_Nazwa                                               AS Nazwa_Firmy_Handlowej,

    -- === FIASCO (CDN.Slowniki) ===
    CASE WHEN n.ZaN_FiaskoID > 0 THEN n.ZaN_FiaskoID END       AS ID_Przyczyny_Fiaska,
    slw_fiask.SLW_WartoscS                                      AS Przyczyna_Fiaska,
    slw_fiask.SLW_Kategoria                                     AS Kategoria_Fiaska,

    -- === POZOSTAŁE ===
    NULLIF(RTRIM(n.ZaN_DokumentObcy), '')                       AS Dokument_Obcy,
    NULLIF(RTRIM(n.ZaN_DokumentObcyP), '')                      AS Dokument_Obcy_P,
    n.ZaN_Url                                                   AS URL,
    n.ZaN_DokZwiazane                                           AS Dok_Zwiazane_Bitmask

FROM CDN.ZamNag n
LEFT JOIN CDN.ZamNag zrd
    ON zrd.ZaN_GIDNumer = n.ZaN_ZrdNumer
    AND n.ZaN_ZrdNumer > 0
    AND n.ZaN_ZrdNumer != n.ZaN_GIDNumer
LEFT JOIN CDN.KntKarty k
    ON k.Knt_GIDNumer = n.ZaN_KntNumer
    AND n.ZaN_KntNumer > 0
LEFT JOIN CDN.KntAdresy kna
    ON kna.KnA_GIDNumer = n.ZaN_KnANumer
    AND n.ZaN_KnANumer > 0
LEFT JOIN CDN.KntKarty odb
    ON odb.Knt_GIDNumer = n.ZaN_KnDNumer
    AND n.ZaN_KnDNumer > 0
LEFT JOIN CDN.KntKarty plat
    ON plat.Knt_GIDNumer = n.ZaN_KnPNumer
    AND n.ZaN_KnPNumer > 0
LEFT JOIN CDN.KntKarty akw
    ON akw.Knt_GIDNumer = n.ZaN_AkwNumer
    AND n.ZaN_AkwNumer > 0
LEFT JOIN CDN.KntAdresy adw
    ON adw.KnA_GIDNumer = n.ZaN_AdWNumer
    AND n.ZaN_AdWNumer > 0
LEFT JOIN CDN.Magazyny m
    ON m.MAG_GIDNumer = n.ZaN_MagNumer
    AND n.ZaN_MagNumer > 0
LEFT JOIN CDN.Magazyny magd
    ON magd.MAG_GIDNumer = n.ZaN_MagDNumer
    AND n.ZaN_MagDNumer > 0
LEFT JOIN CDN.OpeKarty opew
    ON opew.Ope_GIDNumer = n.ZaN_OpeNumerW
    AND n.ZaN_OpeNumerW > 0
LEFT JOIN CDN.OpeKarty opem
    ON opem.Ope_GIDNumer = n.ZaN_OpeNumerM
    AND n.ZaN_OpeNumerM > 0
LEFT JOIN CDN.OpeKarty opez
    ON opez.Ope_GIDNumer = n.ZaN_OpeNumerZ
    AND n.ZaN_OpeNumerZ > 0
LEFT JOIN CDN.OpeKarty opep
    ON opep.Ope_GIDNumer = n.ZaN_OpeNumerP
    AND n.ZaN_OpeNumerP > 0
LEFT JOIN CDN.OpeKarty opemod
    ON opemod.Ope_GIDNumer = n.ZaN_OpeNumerMod
    AND n.ZaN_OpeNumerMod > 0
LEFT JOIN CDN.OpeKarty opepos
    ON opepos.Ope_GIDNumer = n.ZaN_OperatorPOS
    AND n.ZaN_OperatorPOS > 0
LEFT JOIN CDN.FrmStruktura frs
    ON frs.FRS_ID = n.ZaN_FrSID
    AND n.ZaN_FrSID > 0
LEFT JOIN CDN.PrcKarty prc
    ON prc.Prc_GIDNumer = n.ZaN_OpiNumer
    AND prc.Prc_GIDTyp = 944
    AND n.ZaN_OpiNumer > 0
LEFT JOIN CDN.Rejestry rej
    ON rej.KAR_GIDNumer = n.ZaN_KarNumer
    AND n.ZaN_KarNumer > 0
LEFT JOIN (
    SELECT TCN_RodzajCeny, MIN(TCN_Nazwa) AS Nazwa_Cennika
    FROM CDN.TwrCenyNag
    GROUP BY TCN_RodzajCeny
) tcn ON tcn.TCN_RodzajCeny = n.ZaN_CenaSpr AND n.ZaN_CenaSpr > 0
LEFT JOIN CDN.Slowniki slw_fiask
    ON slw_fiask.SLW_ID = n.ZaN_FiaskoID
    AND n.ZaN_FiaskoID > 0
LEFT JOIN CDN.Slowniki slw_stat
    ON slw_stat.SLW_ID = n.ZaN_StatusRealizacji
    AND n.ZaN_StatusRealizacji > 0
