-- BRUDNOPIS — BI.Kontrahenci
-- Etap 1: ID, typ, adres, dane identyfikacyjne (kolumny 1–20)

SELECT
    -- === IDENTYFIKACJA ===
    k.Knt_GIDNumer                                          AS ID_Kontrahenta,
    CASE k.Knt_Typ
        WHEN 8  THEN 'Dostawca'
        WHEN 16 THEN 'Odbiorca'
        WHEN 24 THEN 'Dostawca-Odbiorca'
        WHEN 0  THEN 'Nieokreślono'
        ELSE 'Nieznane (' + CAST(k.Knt_Typ AS VARCHAR) + ')'
    END                                                     AS Typ,
    CASE k.Knt_Status
        WHEN 0 THEN 'Nieokreślono'
        WHEN 1 THEN 'Podmiot gospodarczy'
        WHEN 2 THEN 'Odbiorca finalny'
        ELSE 'Nieznane (' + CAST(k.Knt_Status AS VARCHAR) + ')'
    END                                                     AS Status,
    k.Knt_Akronim                                           AS Akronim,
    k.Knt_Nazwa1                                            AS Nazwa1,
    k.Knt_Nazwa2                                            AS Nazwa2,
    k.Knt_Nazwa3                                            AS Nazwa3,

    -- === DANE IDENTYFIKACYJNE ===
    k.Knt_NipE                                              AS NIP,
    k.Knt_NipPrefiks                                        AS NIP_Prefiks,
    k.Knt_Regon                                             AS REGON,
    k.Knt_Pesel                                             AS PESEL,
    k.Knt_GLN                                               AS GLN,
    k.Knt_Ean                                               AS EAN,
    k.Knt_GUID                                              AS GUID,

    -- === ADRES GŁÓWNY (z KntKarty) ===
    k.Knt_KodP                                              AS Kod_Pocztowy,
    k.Knt_Miasto                                            AS Miasto,
    k.Knt_Ulica                                             AS Ulica,
    k.Knt_Adres                                             AS Adres,
    k.Knt_Kraj                                              AS Kraj,
    k.Knt_Wojewodztwo                                       AS Wojewodztwo,
    k.Knt_Powiat                                            AS Powiat,
    k.Knt_Gmina                                             AS Gmina,
    k.Knt_RegionCRM                                         AS Region_CRM,

    -- === ADRES POWIĄZANY (CDN.KntAdresy — adres główny kontrahenta) ===
    a.KnA_Akronim                                           AS Adres_Powiazany_Akronim,
    a.KnA_Nazwa1                                            AS Adres_Powiazany_Nazwa1,
    a.KnA_KodP                                              AS Adres_Powiazany_KodP,
    a.KnA_Miasto                                            AS Adres_Powiazany_Miasto,
    a.KnA_Ulica                                             AS Adres_Powiazany_Ulica,

    -- === KONTAKT ===
    k.Knt_Telefon1                                          AS Telefon1,
    k.Knt_Telefon2                                          AS Telefon2,
    k.Knt_Fax                                               AS Fax,
    k.Knt_EMail                                             AS Email,
    k.Knt_URL                                               AS URL,

    -- === BANK ===
    k.Knt_NrRachunku                                        AS Nr_Rachunku,
    k.Knt_NRB                                               AS NRB,
    bnk.Bnk_Kod                                             AS Kod_Banku,
    bnk.Bnk_Nazwa                                           AS Nazwa_Banku,

    -- === FORMY PŁATNOŚCI ===
    CASE k.Knt_FormaPl
        WHEN 0  THEN 'Nieokreślono'
        WHEN 10 THEN 'Przelew'
        WHEN 20 THEN 'Gotówka'
        WHEN 50 THEN 'Karta'
        WHEN 100 THEN 'Kompensata'
        ELSE 'Nieznane (' + CAST(k.Knt_FormaPl AS VARCHAR) + ')'
    END                                                     AS Forma_Platnosci_Sprzedaz,
    CASE k.Knt_FormaPlZak
        WHEN 0  THEN 'Nieokreślono'
        WHEN 10 THEN 'Przelew'
        WHEN 20 THEN 'Gotówka'
        WHEN 50 THEN 'Karta'
        WHEN 100 THEN 'Kompensata'
        ELSE 'Nieznane (' + CAST(k.Knt_FormaPlZak AS VARCHAR) + ')'
    END                                                     AS Forma_Platnosci_Zakup,

    -- === TERMINY PŁATNOŚCI ===
    k.Knt_TerminPlKa                                        AS Termin_Platnosci_Ka,
    k.Knt_TerminPlZak                                       AS Termin_Platnosci_Zak,
    k.Knt_SpTerminPlSpr                                      AS Termin_Spr_Specjalny,
    k.Knt_SpTerminPlZak                                      AS Termin_Zak_Specjalny,
    k.Knt_MaxTerminPlSpr                                    AS Max_Termin_Platnosci_Spr,
    k.Knt_MaxTerminPlZak                                    AS Max_Termin_Platnosci_Zak,
    k.Knt_MaxDniPoTerminie                                  AS Max_Dni_Po_Terminie,
    k.Knt_LimitTerminowy                                    AS Limit_Terminowy,

    -- === LIMITY KREDYTOWE ===
    k.Knt_LimitWart                                         AS Limit_Wartosciowy,
    k.Knt_MaxLimitWart                                      AS Max_Limit_Wartosciowy,
    k.Knt_LimitPoTerminie                                   AS Limit_Po_Terminie,
    k.Knt_LimitOkres                                        AS Limit_Okres,

    -- === RABATY I CENY ===
    k.Knt_Rabat                                             AS Rabat,
    k.Knt_Marza                                             AS Marza,
    k.Knt_Cena                                              AS Poziom_Ceny,
    k.Knt_Dewizowe                                          AS Czy_Dewizowe,
    k.Knt_Symbol                                            AS Waluta_Symbol,
    k.Knt_NrKursu                                           AS Nr_Kursu,

    -- === CECHY HANDLOWE ===
    k.Knt_ExpoKraj                                          AS Eksport_Kraj,
    k.Knt_SeriaFa                                           AS Seria_FA,
    k.Knt_TypDok                                            AS Typ_Dokumentu,
    k.Knt_TypDokZS                                          AS Typ_Dok_ZS,
    k.Knt_TypDokZZ                                          AS Typ_Dok_ZZ,
    k.Knt_SposobDostawy                                     AS Sposob_Dostawy,
    k.Knt_Kurier                                            AS Kurier,
    k.Knt_Odleglosc                                         AS Odleglosc,
    k.Knt_Priorytet                                         AS Priorytet,
    k.Knt_PriorytetRez                                      AS Priorytet_Rezerwacji,
    k.Knt_PojedynczeDokDoZam                                AS Pojedyncze_Dok_Do_Zam,

    -- === FLAGI HANDLOWE ===
    CASE k.Knt_PlatnikVat
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_PlatnikVat AS VARCHAR) + ')'
    END                                                     AS Platnik_VAT,
    CASE k.Knt_Archiwalny
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Archiwalny AS VARCHAR) + ')'
    END                                                     AS Archiwalny,
    CASE k.Knt_AdresNieAktualny
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_AdresNieAktualny AS VARCHAR) + ')'
    END                                                     AS Adres_Nieaktualny,
    CASE k.Knt_BlokadaTransakcji
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_BlokadaTransakcji AS VARCHAR) + ')'
    END                                                     AS Blokada_Transakcji,
    CASE k.Knt_BlokadaZam
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_BlokadaZam AS VARCHAR) + ')'
    END                                                     AS Blokada_Zamowien,
    CASE k.Knt_SplitPayment
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_SplitPayment AS VARCHAR) + ')'
    END                                                     AS Split_Payment,
    CASE k.Knt_MetodaKasowa
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_MetodaKasowa AS VARCHAR) + ')'
    END                                                     AS Metoda_Kasowa,
    CASE k.Knt_Controlling
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Controlling AS VARCHAR) + ')'
    END                                                     AS Controlling,
    CASE k.Knt_RolnikRyczaltowy
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_RolnikRyczaltowy AS VARCHAR) + ')'
    END                                                     AS Rolnik_Ryczaltowy,

    -- === OPERATOR ZAKŁADAJĄCY (CDN.OpeKarty) ===
    k.Knt_OpeNumer                                          AS ID_Operatora_Zal,
    o.Ope_Ident                                             AS Login_Operatora_Zal,
    o.Ope_Nazwisko                                          AS Nazwisko_Operatora_Zal,

    -- === OPERATOR MODYFIKUJĄCY (CDN.OpeKarty) ===
    k.Knt_OpeNumerM                                         AS ID_Operatora_Mod,
    om.Ope_Ident                                            AS Login_Operatora_Mod,
    om.Ope_Nazwisko                                         AS Nazwisko_Operatora_Mod,

    -- === FIRMA HANDLOWA (CDN.FrmStruktura) ===
    k.Knt_FrsID                                             AS ID_Firmy_Handlowej,
    frs.FRS_Nazwa                                           AS Nazwa_Firmy_Handlowej,

    -- === AKWIZYTOR (CDN.KntKarty self-join — akwizytor = kontrahent) ===
    k.Knt_AkwNumer                                          AS ID_Akwizytora,
    akw.Knt_Akronim                                         AS Akronim_Akwizytora,
    akw.Knt_Nazwa1                                          AS Nazwa_Akwizytora,
    k.Knt_AkwProwizja                                       AS Prowizja_Akwizytora,

    -- === PŁATNIK (CDN.KntKarty self-join) ===
    k.Knt_KnPNumer                                          AS ID_Platnika,
    plat.Knt_Akronim                                        AS Akronim_Platnika,
    plat.Knt_Nazwa1                                         AS Nazwa_Platnika,

    -- === REJESTR KASOWY (CDN.Rejestry) ===
    k.Knt_KarNumer                                          AS ID_Rejestru_Kasowego,
    rej.KAR_Seria                                           AS Seria_Rejestru_Kasowego,
    rej.KAR_Nazwa                                           AS Nazwa_Rejestru_Kasowego,

    -- === GRUPA KONTRAHENTA (CDN.KntGrupy) ===
    k.Knt_KnGNumer                                          AS ID_Grupy,
    kg.KnG_Akronim                                          AS Nazwa_Grupy,

    -- === DATY (Clarion DATE: DATEADD(d, col, '18001228')) ===
    CASE WHEN k.Knt_VatDataRejestracji > 0
        THEN DATEADD(d, k.Knt_VatDataRejestracji, '18001228') END AS Data_VAT_Rejestracji,
    CASE WHEN k.Knt_VatDataPrzywrocenia > 0
        THEN DATEADD(d, k.Knt_VatDataPrzywrocenia, '18001228') END AS Data_VAT_Przywrocenia,
    CASE WHEN k.Knt_VatDataOdmowy > 0
        THEN DATEADD(d, k.Knt_VatDataOdmowy, '18001228') END     AS Data_VAT_Odmowy,
    CASE WHEN k.Knt_VatDataUsuniecia > 0
        THEN DATEADD(d, k.Knt_VatDataUsuniecia, '18001228') END   AS Data_VAT_Usuniecia,
    CASE WHEN k.Knt_DataOdLoj > 0
        THEN DATEADD(d, k.Knt_DataOdLoj, '18001228') END         AS Data_Loj_Od,
    CASE WHEN k.Knt_DataDoLoj > 0
        THEN DATEADD(d, k.Knt_DataDoLoj, '18001228') END         AS Data_Loj_Do,
    -- LastMod — Clarion TIMESTAMP: DATEADD(ss, col, '1990-01-01')
    CASE WHEN k.Knt_LastModL > 0
        THEN DATEADD(ss, k.Knt_LastModL, '1990-01-01') END       AS Data_Ost_Modyfikacji,
    CASE WHEN k.Knt_LastModO > 0
        THEN DATEADD(ss, k.Knt_LastModO, '1990-01-01') END       AS Data_Ost_Mod_Ope,
    CASE WHEN k.Knt_LastModC > 0
        THEN DATEADD(ss, k.Knt_LastModC, '1990-01-01') END       AS Data_Ost_Mod_Cnf,
    -- TODO: Knt_EFaVatDataDo — wartość 150483 wymaga weryfikacji (sentinel?)
    CASE
        WHEN k.Knt_EFaVatDataDo = 0 THEN NULL
        WHEN k.Knt_EFaVatDataDo > 100000 THEN NULL  -- TODO: sentinel "bezterminowo"?
        ELSE DATEADD(d, k.Knt_EFaVatDataDo, '18001228')
    END                                                           AS Data_EFaVat_Do,
    k.Knt_DataUtworzenia                                         AS Data_Utworzenia,

    -- === E-FAKTURA VAT ===
    CASE k.Knt_EFaVatAktywne
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_EFaVatAktywne AS VARCHAR) + ')'
    END                                                           AS EFaVat_Aktywne,
    k.Knt_EFaVatEMail                                            AS EFaVat_Email,
    k.Knt_EFaVatOsw                                              AS EFaVat_Oswiadczenie,

    -- === VAT / PODATKI ===
    CASE k.Knt_PodatnikiemNabywca
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_PodatnikiemNabywca AS VARCHAR) + ')'
    END                                                           AS Podatnikiem_Nabywca,
    CASE k.Knt_WSTO
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_WSTO AS VARCHAR) + ')'
    END                                                           AS WSTO,
    CASE k.Knt_KSeFWyslij
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_KSeFWyslij AS VARCHAR) + ')'
    END                                                           AS KSeF_Wyslij,
    k.Knt_ProcTrnJpk                                             AS Proc_Trn_JPK,
    k.Knt_OplataSpozZakup                                        AS Oplata_Spoz_Zakup,
    k.Knt_OplataSpozSprzedaz                                     AS Oplata_Spoz_Sprzedaz,

    -- === LOYALNOŚĆ ===
    k.Knt_KartaLoj                                               AS Karta_Lojalnosciowa,
    k.Knt_Punkty                                                  AS Punkty,
    k.Knt_PunktyOdebr                                            AS Punkty_Odebrane,
    k.Knt_PunktyNalicz                                           AS Punkty_Naliczone,
    k.Knt_PunktyKorekta                                          AS Punkty_Korekta,

    -- === FLAGI DODATKOWE ===
    CASE k.Knt_Oddzialowy
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Oddzialowy AS VARCHAR) + ')'
    END                                                           AS Oddzialowy,
    CASE k.Knt_Spedytor
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Spedytor AS VARCHAR) + ')'
    END                                                           AS Spedytor,
    CASE k.Knt_Anonim
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Anonim AS VARCHAR) + ')'
    END                                                           AS Anonim,
    CASE k.Knt_ESklep
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_ESklep AS VARCHAR) + ')'
    END                                                           AS ESklep,
    CASE k.Knt_ObcaKarta
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_ObcaKarta AS VARCHAR) + ')'
    END                                                           AS Obca_Karta,
    CASE k.Knt_Osoba
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Osoba AS VARCHAR) + ')'
    END                                                           AS Osoba_Fizyczna,
    CASE k.Knt_StanPostep
        WHEN 0 THEN 'Brak'
        WHEN 1 THEN 'W trakcie postępowania'
        ELSE 'Nieznane (' + CAST(k.Knt_StanPostep AS VARCHAR) + ')'
    END                                                           AS Stan_Postepowania,
    CASE k.Knt_DataPromocji
        WHEN 0 THEN 'Brak'
        WHEN 1 THEN 'Wg daty wystawienia'
        WHEN 2 THEN 'Wg daty realizacji'
        ELSE 'Nieznane (' + CAST(k.Knt_DataPromocji AS VARCHAR) + ')'
    END                                                           AS Data_Promocji_Typ,

    -- === ATRYBUTY CRM ===
    k.Knt_Atrybut1                                               AS Atrybut1,
    k.Knt_Wartosc1                                               AS Wartosc1,
    k.Knt_Atrybut2                                               AS Atrybut2,
    k.Knt_Wartosc2                                               AS Wartosc2,
    k.Knt_Atrybut3                                               AS Atrybut3,
    k.Knt_Wartosc3                                               AS Wartosc3,
    k.Knt_Branza                                                  AS Branza,
    k.Knt_Rodzaj                                                  AS Rodzaj,
    k.Knt_RolaPartnera                                           AS Rola_Partnera,

    -- === DOKUMENT TOŻSAMOŚCI ===
    k.Knt_DokumentTozsamosci                                     AS Dokument_Tozsamosci,
    CASE WHEN k.Knt_DataWydania > 0
        THEN DATEADD(d, k.Knt_DataWydania, '18001228') END       AS Data_Wydania,
    k.Knt_OrganWydajacy                                          AS Organ_Wydajacy,

    -- === KONTRAHENT UMOWA / CRM ===
    k.Knt_Umowa                                                   AS Umowa,
    k.Knt_CechaOpis                                              AS Cecha_Opis,

    -- === KONTO HANDLOWE / RACHUNKI ===
    k.Knt_KontoDostawcy                                          AS Konto_FK_Dostawcy,
    k.Knt_KontoOdbiorcy                                          AS Konto_FK_Odbiorcy,

    -- === SPRZEDAŻ — POZOSTAŁE ===
    k.Knt_TypKarty                                               AS Typ_Karty,
    k.Knt_NumerKarty                                             AS Numer_Karty,
    k.Knt_Dzialalnosc                                            AS Dzialalnosc,

    -- === FLAGI POZOSTAŁE ===
    CASE k.Knt_Dewizowe
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Dewizowe AS VARCHAR) + ')'
    END                                                           AS Dewizowy,
    CASE k.Knt_Powiazany
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Powiazany AS VARCHAR) + ')'
    END                                                           AS Powiazany

FROM CDN.KntKarty k
LEFT JOIN CDN.KntAdresy a
    ON a.KnA_GIDNumer = k.Knt_KnANumer
    AND k.Knt_KnANumer > 0
LEFT JOIN CDN.Banki bnk
    ON bnk.Bnk_GIDNumer = k.Knt_BnkNumer
    AND k.Knt_BnkNumer > 0
LEFT JOIN CDN.OpeKarty o
    ON o.Ope_GIDNumer = k.Knt_OpeNumer
    AND k.Knt_OpeNumer > 0
LEFT JOIN CDN.OpeKarty om
    ON om.Ope_GIDNumer = k.Knt_OpeNumerM
    AND k.Knt_OpeNumerM > 0
LEFT JOIN CDN.FrmStruktura frs
    ON frs.FRS_ID = k.Knt_FrsID
    AND k.Knt_FrsID > 0
LEFT JOIN CDN.KntKarty akw
    ON akw.Knt_GIDNumer = k.Knt_AkwNumer
    AND k.Knt_AkwNumer > 0
LEFT JOIN CDN.KntKarty plat
    ON plat.Knt_GIDNumer = k.Knt_KnPNumer
    AND k.Knt_KnPNumer > 0
LEFT JOIN CDN.Rejestry rej
    ON rej.KAR_GIDNumer = k.Knt_KarNumer
    AND k.Knt_KarNumer > 0
LEFT JOIN CDN.KntGrupy kg
    ON kg.KnG_GIDNumer = k.Knt_KnGNumer
    AND kg.KnG_GIDTyp = -32
    AND k.Knt_KnGNumer > 0
