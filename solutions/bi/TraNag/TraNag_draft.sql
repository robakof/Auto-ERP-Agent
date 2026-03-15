-- BRUDNOPIS -- wylacznie SELECT, bez CREATE VIEW
-- AIBI.TraNag -- naglowki dokumentow handlowych
-- Status: Faza 2 -- uzupelnienia po zatwierdzeniu v1 (user 2026-03-15)
-- Odchylenie od planu: Akwizytor_Login -> Akwizytor_Akronim
--   TrN_AkwTyp w danych: 32=48461 (KntKarty), 944=2 (PrcKarty), 128=0
-- Uzupelnienia (user): Numer_Dok_Korygowanego, Adres_Kontrahenta,
--   Adres_Wysylki, Numer_Zamowienia, Nazwa_Cennika

WITH CenBase AS (
    SELECT t.TCN_RodzajCeny, t.TCN_Nazwa
    FROM CDN.TwrCenyNag t
    WHERE t.TCN_Id = (
        SELECT MIN(t2.TCN_Id) FROM CDN.TwrCenyNag t2
        WHERE t2.TCN_RodzajCeny = t.TCN_RodzajCeny
    )
)
SELECT
    -- === TYP I IDENTYFIKACJA ===
    CASE n.TrN_GIDTyp
        WHEN 2034 THEN 'Paragon'
        WHEN 2033 THEN 'Faktura sprzedazy'
        WHEN 1617 THEN 'Przychod wewnetrzny'
        WHEN 2001 THEN 'Wydanie zewnetrzne'
        WHEN 1521 THEN 'Faktura zakupu'
        WHEN 2009 THEN 'Korekta wydania zewnetrznego'
        WHEN 1603 THEN 'Przesuniecie MM wydanie'
        WHEN 1604 THEN 'Przesuniecie MM przyjecie'
        WHEN 1616 THEN 'Rozchod wewnetrzny'
        WHEN 2041 THEN 'Korekta faktury sprzedazy'
        WHEN 2003 THEN 'Korekta kosztu'
        WHEN 1489 THEN 'Przyjecie zewnetrzne'
        WHEN 1497 THEN 'Korekta przyjecia zewnetrznego'
        WHEN 1625 THEN 'Korekta przychodu wewnetrznego'
        WHEN 1529 THEN 'Korekta faktury zakupu'
        WHEN 2042 THEN 'Korekta paragonu'
        WHEN 2037 THEN 'Faktura eksportowa'
        WHEN 2013 THEN 'Korekta wydania eksportowego'
        WHEN 2005 THEN 'Wydanie zewnetrzne eksportowe'
        WHEN 1624 THEN 'Korekta rozchodu wewnetrznego'
        WHEN 2039 THEN 'Raport sprzedazy'
        WHEN 2045 THEN 'Korekta faktury eksportowej'
        WHEN 2035 THEN 'Faktura do paragonu'
        WHEN 2004 THEN 'Deprecjacja'
        WHEN 1232 THEN 'Koszt dodatkowy zakupu'
        ELSE 'Nieznane (' + CAST(n.TrN_GIDTyp AS VARCHAR(10)) + ')'
    END                                                             AS Typ_Dok,
    n.TrN_GIDNumer                                                  AS ID_Dokumentu,

    -- === DOKUMENT KORYGOWANY ===
    CASE
        WHEN n.TrN_ZwrTyp = 0    THEN NULL
        WHEN n.TrN_ZwrTyp = 2034 THEN 'Paragon'
        WHEN n.TrN_ZwrTyp = 2033 THEN 'Faktura sprzedazy'
        WHEN n.TrN_ZwrTyp = 2001 THEN 'Wydanie zewnetrzne'
        WHEN n.TrN_ZwrTyp = 1489 THEN 'Przyjecie zewnetrzne'
        WHEN n.TrN_ZwrTyp = 2009 THEN 'Korekta wydania zewnetrznego'
        WHEN n.TrN_ZwrTyp = 2041 THEN 'Korekta faktury sprzedazy'
        WHEN n.TrN_ZwrTyp = 1497 THEN 'Korekta przyjecia zewnetrznego'
        WHEN n.TrN_ZwrTyp = 1617 THEN 'Przychod wewnetrzny'
        WHEN n.TrN_ZwrTyp = 1625 THEN 'Korekta przychodu wewnetrznego'
        ELSE 'Nieznane (' + CAST(n.TrN_ZwrTyp AS VARCHAR(10)) + ')'
    END                                                             AS Typ_Dok_Korygowanego,
    CASE WHEN n.TrN_ZwrNumer = 0 THEN NULL ELSE n.TrN_ZwrNumer END AS ID_Dok_Korygowanego,
    -- Numer korygowanego: bez prefiksu (Z) -- wymagalby kolejnego self-JOIN
    CASE WHEN zwrot.TrN_GIDNumer IS NULL THEN NULL ELSE
        CASE
            WHEN zwrot.TrN_GenDokMag = -1
                 AND zwrot.TrN_GIDTyp IN (1521, 1529, 1489) THEN '(A)'
            WHEN zwrot.TrN_GenDokMag = -1                   THEN '(s)'
            ELSE ''
        END
        + CASE zwrot.TrN_GIDTyp
            WHEN 2034 THEN 'PA'   WHEN 2033 THEN 'FS'   WHEN 1617 THEN 'PW'
            WHEN 2001 THEN 'WZ'   WHEN 1521 THEN 'FZ'   WHEN 2009 THEN 'WZK'
            WHEN 1603 THEN 'MMW'  WHEN 1604 THEN 'MMP'  WHEN 1616 THEN 'RW'
            WHEN 2041 THEN 'FSK'  WHEN 2003 THEN 'KK'   WHEN 1489 THEN 'PZ'
            WHEN 1497 THEN 'PZK'  WHEN 1625 THEN 'PWK'  WHEN 1529 THEN 'FZK'
            WHEN 2042 THEN 'PAK'  WHEN 2037 THEN 'FSE'  WHEN 2013 THEN 'WKE'
            WHEN 2005 THEN 'WZE'  WHEN 1624 THEN 'RWK'  WHEN 2039 THEN 'RS'
            WHEN 2045 THEN 'FKE'  WHEN 2035 THEN 'RA'   WHEN 2004 THEN 'DP'
            WHEN 1232 THEN 'KDZ'
            ELSE CAST(zwrot.TrN_GIDTyp AS VARCHAR(10))
          END
        + '-' + CAST(zwrot.TrN_TrNNumer AS VARCHAR(10))
        + '/' + RIGHT('0' + CAST(zwrot.TrN_TrNMiesiac AS VARCHAR(2)), 2)
        + '/' + RIGHT(CAST(zwrot.TrN_TrNRok AS VARCHAR(4)), 2)
        + CASE WHEN RTRIM(zwrot.TrN_TrNSeria) = '' THEN ''
               ELSE '/' + RTRIM(zwrot.TrN_TrNSeria) END
    END                                                             AS Numer_Dok_Korygowanego,

    -- === KONTRAHENT ===
    CASE WHEN n.TrN_KntNumer = 0 THEN NULL ELSE n.TrN_KntNumer END AS ID_Kontrahenta,
    knt.Knt_Akronim                                                 AS Kontrahent_Akronim,
    knt.Knt_Nazwa1                                                  AS Kontrahent_Nazwa,
    CASE WHEN n.TrN_KnANumer = 0 THEN NULL ELSE n.TrN_KnANumer END AS ID_Adresu_Kontrahenta,
    CASE WHEN kna_k.KnA_GIDNumer IS NULL THEN NULL ELSE
        NULLIF(
            RTRIM(COALESCE(kna_k.KnA_Ulica, ''))
            + CASE WHEN RTRIM(COALESCE(kna_k.KnA_Adres, '')) <> ''
                   THEN ' ' + RTRIM(kna_k.KnA_Adres) ELSE '' END
            + CASE WHEN RTRIM(COALESCE(kna_k.KnA_KodP, '')) <> ''
                   THEN ', ' + RTRIM(kna_k.KnA_KodP) ELSE '' END
            + CASE WHEN RTRIM(COALESCE(kna_k.KnA_Miasto, '')) <> ''
                   THEN ' ' + RTRIM(kna_k.KnA_Miasto) ELSE '' END,
        '')
    END                                                             AS Adres_Kontrahenta,

    -- === AKWIZYTOR ===
    CASE WHEN n.TrN_AkwNumer = 0 THEN NULL ELSE n.TrN_AkwNumer END AS ID_Akwizytora,
    COALESCE(akw_knt.Knt_Akronim, akw_prc.Prc_Akronim)             AS Akwizytor_Akronim,

    -- === ADRES WYSYLKI ===
    CASE WHEN n.TrN_AdWNumer = 0 THEN NULL ELSE n.TrN_AdWNumer END AS ID_Adresu_Wysylki,
    CASE WHEN kna_w.KnA_GIDNumer IS NULL THEN NULL ELSE
        NULLIF(
            RTRIM(COALESCE(kna_w.KnA_Ulica, ''))
            + CASE WHEN RTRIM(COALESCE(kna_w.KnA_Adres, '')) <> ''
                   THEN ' ' + RTRIM(kna_w.KnA_Adres) ELSE '' END
            + CASE WHEN RTRIM(COALESCE(kna_w.KnA_KodP, '')) <> ''
                   THEN ', ' + RTRIM(kna_w.KnA_KodP) ELSE '' END
            + CASE WHEN RTRIM(COALESCE(kna_w.KnA_Miasto, '')) <> ''
                   THEN ' ' + RTRIM(kna_w.KnA_Miasto) ELSE '' END,
        '')
    END                                                             AS Adres_Wysylki,

    -- === ZAMOWIENIE ===
    CASE WHEN n.TrN_ZaNNumer = 0 THEN NULL ELSE n.TrN_ZaNNumer END AS ID_Zamowienia,
    CASE WHEN zam.ZaN_GIDNumer IS NULL THEN NULL ELSE
        'ZS-' + CAST(zam.ZaN_ZamNumer AS VARCHAR(10))
        + '/' + RIGHT('0' + CAST(zam.ZaN_ZamMiesiac AS VARCHAR(2)), 2)
        + '/' + RIGHT(CAST(zam.ZaN_ZamRok AS VARCHAR(4)), 2)
        + CASE WHEN RTRIM(zam.ZaN_ZamSeria) = '' THEN ''
               ELSE '/' + RTRIM(zam.ZaN_ZamSeria) END
    END                                                             AS Numer_Zamowienia,

    -- === STAN I NUMERACJA ===
    CASE n.TrN_Stan
        WHEN 0 THEN 'Edycja po dodaniu'
        WHEN 1 THEN 'Bufor'
        WHEN 2 THEN 'Po edycji w buforze'
        WHEN 3 THEN 'Zatwierdzona / nierozliczona'
        WHEN 4 THEN 'Po edycji platnosci'
        WHEN 5 THEN 'Rozliczona'
        WHEN 6 THEN 'Anulowana'
        ELSE 'Nieznane (' + CAST(n.TrN_Stan AS VARCHAR(5)) + ')'
    END                                                             AS Stan_Dok,
    n.TrN_TrNNumer                                                  AS Nr_Kolejny,
    n.TrN_TrNMiesiac                                                AS Miesiac_Dok,
    n.TrN_TrNRok                                                    AS Rok_Dok,
    RTRIM(n.TrN_TrNSeria)                                           AS Seria_Dok,
    CASE WHEN n.TrN_TrNLp = 127 THEN 'Tak' ELSE 'Nie' END          AS Aktywny_Dok,

    -- === NUMER DOKUMENTU ===
    CASE
        WHEN n.TrN_GIDTyp IN (2041, 2045, 1529)
             AND EXISTS (
                 SELECT 1 FROM CDN.TraNag s
                 WHERE s.TrN_SpiTyp   = n.TrN_GIDTyp
                   AND s.TrN_SpiNumer = n.TrN_GIDNumer
                   AND (   (n.TrN_GIDTyp = 2041 AND s.TrN_GIDTyp = 2009)
                        OR (n.TrN_GIDTyp = 2045 AND s.TrN_GIDTyp = 2013)
                        OR (n.TrN_GIDTyp = 1529 AND s.TrN_GIDTyp = 1497))
             )                                              THEN '(Z)'
        WHEN n.TrN_Stan & 2 = 2
             AND n.TrN_GIDTyp IN (2041, 2045, 1529)         THEN '(Z)'
        WHEN n.TrN_GenDokMag = -1
             AND n.TrN_GIDTyp IN (1521, 1529, 1489)         THEN '(A)'
        WHEN n.TrN_GenDokMag = -1                           THEN '(s)'
        ELSE ''
    END
    + CASE n.TrN_GIDTyp
        WHEN 2034 THEN 'PA'   WHEN 2033 THEN 'FS'   WHEN 1617 THEN 'PW'
        WHEN 2001 THEN 'WZ'   WHEN 1521 THEN 'FZ'   WHEN 2009 THEN 'WZK'
        WHEN 1603 THEN 'MMW'  WHEN 1604 THEN 'MMP'  WHEN 1616 THEN 'RW'
        WHEN 2041 THEN 'FSK'  WHEN 2003 THEN 'KK'   WHEN 1489 THEN 'PZ'
        WHEN 1497 THEN 'PZK'  WHEN 1625 THEN 'PWK'  WHEN 1529 THEN 'FZK'
        WHEN 2042 THEN 'PAK'  WHEN 2037 THEN 'FSE'  WHEN 2013 THEN 'WKE'
        WHEN 2005 THEN 'WZE'  WHEN 1624 THEN 'RWK'  WHEN 2039 THEN 'RS'
        WHEN 2045 THEN 'FKE'  WHEN 2035 THEN 'RA'   WHEN 2004 THEN 'DP'
        WHEN 1232 THEN 'KDZ'
        ELSE CAST(n.TrN_GIDTyp AS VARCHAR(10))
      END
    + '-' + CAST(n.TrN_TrNNumer AS VARCHAR(10))
    + '/' + RIGHT('0' + CAST(n.TrN_TrNMiesiac AS VARCHAR(2)), 2)
    + '/' + RIGHT(CAST(n.TrN_TrNRok AS VARCHAR(4)), 2)
    + CASE WHEN RTRIM(n.TrN_TrNSeria) = '' THEN '' ELSE '/' + RTRIM(n.TrN_TrNSeria) END
                                                                    AS Numer_Dokumentu,

    -- === DATY (Clarion DATE, sentinel BETWEEN 1 AND 109211) ===
    CASE WHEN n.TrN_Data2 BETWEEN 1 AND 109211
         THEN CAST(DATEADD(d, n.TrN_Data2 - 36163, '1899-12-28') AS DATE)
         ELSE NULL END                                              AS Data_Wystawienia,
    CASE WHEN n.TrN_Data3 BETWEEN 1 AND 109211
         THEN CAST(DATEADD(d, n.TrN_Data3 - 36163, '1899-12-28') AS DATE)
         ELSE NULL END                                              AS Data_Sprzedazy,
    CASE WHEN n.TrN_Termin BETWEEN 1 AND 109211
         THEN CAST(DATEADD(d, n.TrN_Termin - 36163, '1899-12-28') AS DATE)
         ELSE NULL END                                              AS Termin_Platnosci,
    CASE WHEN n.TrN_DataMag BETWEEN 1 AND 109211
         THEN CAST(DATEADD(d, n.TrN_DataMag - 36163, '1899-12-28') AS DATE)
         ELSE NULL END                                              AS Data_Magazynowa,
    CASE WHEN n.TrN_DataRoz BETWEEN 1 AND 109211
         THEN CAST(DATEADD(d, n.TrN_DataRoz - 36163, '1899-12-28') AS DATE)
         ELSE NULL END                                              AS Data_Rozliczenia,
    CASE WHEN n.TrN_DataPO BETWEEN 1 AND 109211
         THEN CAST(DATEADD(d, n.TrN_DataPO - 36163, '1899-12-28') AS DATE)
         ELSE NULL END                                              AS Data_Obowiazku_Pod,
    CASE WHEN n.TrN_DataWplywu BETWEEN 1 AND 109211
         THEN CAST(DATEADD(d, n.TrN_DataWplywu - 36163, '1899-12-28') AS DATE)
         ELSE NULL END                                              AS Data_Wplywu,
    CASE WHEN n.TrN_DataWysylki BETWEEN 1 AND 109211
         THEN CAST(DATEADD(d, n.TrN_DataWysylki - 36163, '1899-12-28') AS DATE)
         ELSE NULL END                                              AS Data_Wysylki,

    -- === DATY KOREKT (brak sentinela, 0 = NULL) ===
    CASE WHEN n.TrN_DataWystOrg = 0 THEN NULL
         ELSE CAST(DATEADD(d, n.TrN_DataWystOrg - 36163, '1899-12-28') AS DATE)
    END                                                             AS Data_Wyst_Oryginalu,
    CASE WHEN n.TrN_DataSprOrg = 0 THEN NULL
         ELSE CAST(DATEADD(d, n.TrN_DataSprOrg - 36163, '1899-12-28') AS DATE)
    END                                                             AS Data_Spr_Oryginalu,
    CASE WHEN n.TrN_DataOdKor = 0 THEN NULL
         ELSE CAST(DATEADD(d, n.TrN_DataOdKor - 36163, '1899-12-28') AS DATE)
    END                                                             AS Data_Zakresu_Kor_Od,
    CASE WHEN n.TrN_DataDoKor = 0 THEN NULL
         ELSE CAST(DATEADD(d, n.TrN_DataDoKor - 36163, '1899-12-28') AS DATE)
    END                                                             AS Data_Zakresu_Kor_Do,
    CASE WHEN n.TrN_DataOdprawyPotwierdzenia = 0 THEN NULL
         ELSE CAST(DATEADD(d, n.TrN_DataOdprawyPotwierdzenia - 36163, '1899-12-28') AS DATE)
    END                                                             AS Data_Odprawy,

    -- === TIMESTAMP ===
    CASE WHEN n.TrN_LastMod = 0 THEN NULL
         ELSE CAST(DATEADD(ss, n.TrN_LastMod, '1990-01-01') AS DATETIME)
    END                                                             AS DataCzas_Modyfikacji,

    -- === MAGAZYNY ===
    CASE WHEN n.TrN_MagZNumer = 0 THEN NULL ELSE n.TrN_MagZNumer END AS ID_Mag_Zrodlowego,
    mag_z.MAG_Kod                                                   AS Mag_Zrodlowy_Symbol,
    mag_z.MAG_Nazwa                                                 AS Mag_Zrodlowy_Nazwa,
    CASE WHEN n.TrN_MagDNumer = 0 THEN NULL ELSE n.TrN_MagDNumer END AS ID_Mag_Docelowego,
    mag_d.MAG_Kod                                                   AS Mag_Docelowy_Symbol,
    mag_d.MAG_Nazwa                                                 AS Mag_Docelowy_Nazwa,

    -- === OPERATORZY ===
    CASE WHEN n.TrN_OpeNumerW = 0 THEN NULL ELSE n.TrN_OpeNumerW END AS ID_Operatora_Wystawil,
    ope_w.Ope_Ident                                                 AS Login_Operatora_Wyst,
    CASE WHEN n.TrN_OpeNumerZ = 0 THEN NULL ELSE n.TrN_OpeNumerZ END AS ID_Operatora_Zatwierdzil,
    ope_z.Ope_Ident                                                 AS Login_Operatora_Zatw,
    CASE WHEN n.TrN_OpeNumerR = 0 THEN NULL ELSE n.TrN_OpeNumerR END AS ID_Operatora_Rozliczyl,
    ope_r.Ope_Ident                                                 AS Login_Operatora_Roz,
    CASE WHEN n.TrN_OpeNumerM = 0 THEN NULL ELSE n.TrN_OpeNumerM END AS ID_Operatora_Mod,
    ope_m.Ope_Ident                                                 AS Login_Operatora_Mod,

    -- === OPIEKUN ===
    CASE WHEN n.TrN_OpiNumer = 0 THEN NULL ELSE n.TrN_OpiNumer END AS ID_Opiekuna,
    prc_opi.Prc_Akronim                                             AS Opiekun_Akronim,

    -- === ODBIORCA ===
    CASE WHEN n.TrN_KnDNumer = 0 THEN NULL ELSE n.TrN_KnDNumer END AS ID_Odbiorcy,
    knd.Knt_Akronim                                                 AS Odbiorca_Akronim,
    knd.Knt_Nazwa1                                                  AS Odbiorca_Nazwa,

    -- === PLATNOSC ===
    CASE
        WHEN n.TrN_FormaNr = 10 THEN 'Gotowka'
        WHEN n.TrN_FormaNr = 20 THEN 'Przelew'
        WHEN n.TrN_FormaNr = 30 THEN 'Kredyt'
        WHEN n.TrN_FormaNr = 40 THEN 'Czek'
        WHEN n.TrN_FormaNr = 50 THEN 'Karta'
        WHEN n.TrN_FormaNr = 60 THEN 'Inne'
        WHEN n.TrN_FormaNr = 0  THEN NULL
        ELSE 'Uzytkownika (' + CAST(n.TrN_FormaNr AS VARCHAR(5)) + ')'
    END                                                             AS Forma_Platnosci,
    n.TrN_Rabat                                                     AS Rabat_Proc,
    n.TrN_CenaSpr                                                   AS Nr_Cennika,
    cen.TCN_Nazwa                                                   AS Nazwa_Cennika,

    -- === WARTOSCI ===
    n.TrN_NettoP                                                    AS Wartosc_Netto_Przychod,
    n.TrN_NettoR                                                    AS Wartosc_Netto_Rozchod,
    n.TrN_WartoscWal                                                AS Wartosc_Walutowa,
    n.TrN_WartoscDPPrzed                                            AS Wartosc_Przed_Deprecjacja,
    n.TrN_WartoscDPPo                                               AS Wartosc_Po_Deprecjacji,
    n.TrN_Waluta                                                    AS Waluta,
    CASE WHEN n.TrN_Waluta = 'PLN' THEN NULL
         ELSE CAST(n.TrN_KursL AS DECIMAL(10,4))
              / CAST(NULLIF(n.TrN_KursM, 0) AS DECIMAL(10,4))
    END                                                             AS Kurs_Walutowy,

    -- === VAT ===
    CASE n.TrN_VatTyp
        WHEN 1 THEN 'Zakup'
        WHEN 2 THEN 'Sprzedaz'
        WHEN 0 THEN NULL
        ELSE 'Nieznane (' + CAST(n.TrN_VatTyp AS VARCHAR(5)) + ')'
    END                                                             AS Rejestr_VAT,
    CASE n.TrN_FlagaNB
        WHEN 'N' THEN 'Od netto'
        WHEN 'B' THEN 'Od brutto'
        ELSE n.TrN_FlagaNB
    END                                                             AS VAT_Od,
    CASE n.TrN_Platnosci
        WHEN 1 THEN 'Tak'
        WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(n.TrN_Platnosci AS VARCHAR(3)) + ')'
    END                                                             AS Jest_Platnosc,

    -- === DODATKOWE ===
    n.TrN_DokumentObcy                                              AS Nr_Dokumentu_Obcego,
    NULLIF(RTRIM(n.TrN_IncotermsSymbol), '')                        AS Incoterms,
    NULLIF(RTRIM(n.TrN_DokTypJPK), '')                              AS Kod_JPK

FROM CDN.TraNag n
LEFT JOIN CDN.TraNag zwrot
       ON zwrot.TrN_GIDNumer = n.TrN_ZwrNumer
      AND n.TrN_ZwrNumer     > 0
LEFT JOIN CDN.KntKarty knt
       ON knt.Knt_GIDNumer = n.TrN_KntNumer
      AND knt.Knt_GIDTyp   = n.TrN_KntTyp
      AND n.TrN_KntNumer   > 0
LEFT JOIN CDN.KntKarty knd
       ON knd.Knt_GIDNumer = n.TrN_KnDNumer
      AND knd.Knt_GIDTyp   = n.TrN_KnDTyp
      AND n.TrN_KnDNumer   > 0
LEFT JOIN CDN.KntAdresy kna_k
       ON kna_k.KnA_GIDNumer = n.TrN_KnANumer
      AND n.TrN_KnANumer     > 0
LEFT JOIN CDN.KntAdresy kna_w
       ON kna_w.KnA_GIDNumer = n.TrN_AdWNumer
      AND n.TrN_AdWNumer     > 0
LEFT JOIN CDN.KntKarty akw_knt
       ON akw_knt.Knt_GIDNumer = n.TrN_AkwNumer
      AND n.TrN_AkwTyp         = 32
      AND n.TrN_AkwNumer       > 0
LEFT JOIN CDN.PrcKarty akw_prc
       ON akw_prc.Prc_GIDNumer = n.TrN_AkwNumer
      AND n.TrN_AkwTyp         = 944
      AND n.TrN_AkwNumer       > 0
LEFT JOIN CDN.ZamNag zam
       ON zam.ZaN_GIDNumer = n.TrN_ZaNNumer
      AND n.TrN_ZaNNumer   > 0
LEFT JOIN CDN.Magazyny mag_z
       ON mag_z.MAG_GIDNumer = n.TrN_MagZNumer
      AND n.TrN_MagZNumer    > 0
LEFT JOIN CDN.Magazyny mag_d
       ON mag_d.MAG_GIDNumer = n.TrN_MagDNumer
      AND n.TrN_MagDNumer    > 0
LEFT JOIN CDN.OpeKarty ope_w
       ON ope_w.Ope_GIDNumer = n.TrN_OpeNumerW
      AND n.TrN_OpeNumerW    > 0
LEFT JOIN CDN.OpeKarty ope_z
       ON ope_z.Ope_GIDNumer = n.TrN_OpeNumerZ
      AND n.TrN_OpeNumerZ    > 0
LEFT JOIN CDN.OpeKarty ope_r
       ON ope_r.Ope_GIDNumer = n.TrN_OpeNumerR
      AND n.TrN_OpeNumerR    > 0
LEFT JOIN CDN.OpeKarty ope_m
       ON ope_m.Ope_GIDNumer = n.TrN_OpeNumerM
      AND n.TrN_OpeNumerM    > 0
LEFT JOIN CDN.PrcKarty prc_opi
       ON prc_opi.Prc_GIDNumer = n.TrN_OpiNumer
      AND n.TrN_OpiTyp         = 944
      AND n.TrN_OpiNumer       > 0
LEFT JOIN CenBase cen
       ON cen.TCN_RodzajCeny = n.TrN_CenaSpr
      AND n.TrN_CenaSpr      > 0
