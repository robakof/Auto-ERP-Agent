CREATE OR ALTER VIEW BI.Kontrahenci AS

WITH Sciezka_Grup AS (
    -- Anchor: grupy poziomu 1 (bezpośrednie dzieci korzenia GIDNumer=0)
    SELECT
        KGD_GIDNumer,
        CAST(KGD_Kod AS NVARCHAR(2000)) AS Sciezka
    FROM CDN.KntGrupyDom
    WHERE KGD_GIDTyp = -32 AND KGD_GrONumer = 0
    UNION ALL
    SELECT
        g.KGD_GIDNumer,
        CAST(p.Sciezka + '\' + RTRIM(g.KGD_Kod) AS NVARCHAR(2000))
    FROM CDN.KntGrupyDom g
    INNER JOIN Sciezka_Grup p ON p.KGD_GIDNumer = g.KGD_GrONumer
    WHERE g.KGD_GIDTyp = -32 AND g.KGD_GrONumer > 0
)

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

    -- === ADRES DODATKOWY (CDN.KntAdresy — wskazany adres powiązany) ===
    a.KnA_Akronim                                           AS Adres_Dodatkowy_Akronim,
    a.KnA_Nazwa1                                            AS Adres_Dodatkowy_Nazwa,
    a.KnA_KodP                                              AS Adres_Dodatkowy_Kod_Pocztowy,
    a.KnA_Miasto                                            AS Adres_Dodatkowy_Miasto,
    a.KnA_Ulica                                             AS Adres_Dodatkowy_Ulica,

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
    k.Knt_TerminPlKa                                        AS Termin_Platnosci_Kaucji,
    k.Knt_TerminPlZak                                       AS Termin_Platnosci_Zakup,
    k.Knt_SpTerminPlSpr                                     AS Termin_Platnosci_Sprzedaz_Specjalny,
    k.Knt_SpTerminPlZak                                     AS Termin_Platnosci_Zakup_Specjalny,
    k.Knt_MaxTerminPlSpr                                    AS Max_Termin_Platnosci_Sprzedaz,
    k.Knt_MaxTerminPlZak                                    AS Max_Termin_Platnosci_Zakup,
    k.Knt_MaxDniPoTerminie                                  AS Max_Dni_Po_Terminie,
    CASE k.Knt_LimitTerminowy
        WHEN 0 THEN 'Nieograniczony'
        WHEN 1 THEN 'Ograniczony'
        ELSE 'Nieznane (' + CAST(k.Knt_LimitTerminowy AS VARCHAR) + ')'
    END                                                     AS Limit_Terminowy,

    -- === LIMITY KREDYTOWE ===
    k.Knt_LimitWart                                         AS Limit_Wartosciowy,
    k.Knt_MaxLimitWart                                      AS Max_Limit_Wartosciowy,
    k.Knt_LimitPoTerminie                                   AS Limit_Po_Terminie,
    k.Knt_LimitOkres                                        AS Limit_Okres,

    -- === RABATY I CENY ===
    k.Knt_Rabat                                             AS Rabat,
    k.Knt_Marza                                             AS Marza,
    k.Knt_Cena                                              AS ID_Cennika_Sprzedazy,
    RTRIM(tcn.Nazwa_Cennika)                                AS Nazwa_Cennika_Sprzedazy,
    k.Knt_Symbol                                            AS Waluta,
    k.Knt_NrKursu                                           AS Nr_Kursu,

    -- === CECHY HANDLOWE ===
    CASE k.Knt_ExpoKraj
        WHEN 1 THEN 'Krajowy'
        WHEN 2 THEN 'Z Unii Europejskiej'
        WHEN 3 THEN 'Spoza Unii Europejskiej'
        WHEN 0 THEN 'Nieokreślono'
        ELSE 'Nieznane (' + CAST(k.Knt_ExpoKraj AS VARCHAR) + ')'
    END                                                     AS Eksport_Rodzaj,
    k.Knt_SeriaFa                                           AS Seria_Faktury,
    CASE k.Knt_TypDok
        WHEN 0    THEN 'Brak'
        WHEN 2033 THEN 'Faktura sprzedaży'
        WHEN 2034 THEN 'Paragon'
        ELSE 'Nieznane (' + CAST(k.Knt_TypDok AS VARCHAR) + ')'
    END                                                     AS Typ_Rachunku,
    CASE k.Knt_TypDokZS
        WHEN 0    THEN 'Brak'
        WHEN 2001 THEN 'Wydanie zewnętrzne'
        ELSE 'Nieznane (' + CAST(k.Knt_TypDokZS AS VARCHAR) + ')'
    END                                                     AS Typ_Dokumentu_Z_Zamowienia_Sprzedazy,
    k.Knt_TypDokZZ                                          AS ID_Typu_Dokumentu_Z_Zamowienia_Zakupu,
    k.Knt_SposobDostawy                                     AS Sposob_Dostawy,
    k.Knt_Kurier                                            AS Kurier,
    k.Knt_Odleglosc                                         AS Odleglosc,
    k.Knt_Priorytet                                         AS Priorytet,
    k.Knt_PriorytetRez                                      AS Priorytet_Rezerwacji,
    k.Knt_PojedynczeDokDoZam                                AS Pojedynczy_Dokument_Do_Zamowienia,

    -- === FLAGI HANDLOWE ===
    CASE k.Knt_PlatnikVat
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_PlatnikVat AS VARCHAR) + ')'
    END                                                     AS Platnik_VAT,
    CASE k.Knt_Dewizowe
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Dewizowe AS VARCHAR) + ')'
    END                                                     AS Dewizowy,
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
    k.Knt_OpeNumer                                          AS ID_Operatora_Zalozenia,
    o.Ope_Ident                                             AS Login_Operatora_Zalozenia,
    o.Ope_Nazwisko                                          AS Nazwisko_Operatora_Zalozenia,

    -- === OPERATOR MODYFIKUJĄCY (CDN.OpeKarty) ===
    k.Knt_OpeNumerM                                         AS ID_Operatora_Modyfikacji,
    om.Ope_Ident                                            AS Login_Operatora_Modyfikacji,
    om.Ope_Nazwisko                                         AS Nazwisko_Operatora_Modyfikacji,

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

    -- === GRUPA KONTRAHENTA — pełna ścieżka (CDN.KntGrupyDom, rekurencyjnie) ===
    kgd.KGD_GrONumer                                        AS ID_Grupy,
    ISNULL(sg.Sciezka, 'Grupa główna')                      AS Sciezka_Grupy,

    -- === DATY (Clarion DATE: DATEADD(d, col, '18001228')) ===
    CASE WHEN k.Knt_VatDataRejestracji > 0
        THEN DATEADD(d, k.Knt_VatDataRejestracji, '18001228') END   AS Data_Rejestracji_VAT,
    CASE WHEN k.Knt_VatDataPrzywrocenia > 0
        THEN DATEADD(d, k.Knt_VatDataPrzywrocenia, '18001228') END  AS Data_Przywrocenia_VAT,
    CASE WHEN k.Knt_VatDataOdmowy > 0
        THEN DATEADD(d, k.Knt_VatDataOdmowy, '18001228') END       AS Data_Odmowy_VAT,
    CASE WHEN k.Knt_VatDataUsuniecia > 0
        THEN DATEADD(d, k.Knt_VatDataUsuniecia, '18001228') END     AS Data_Usuniecia_VAT,
    CASE WHEN k.Knt_DataOdLoj > 0
        THEN DATEADD(d, k.Knt_DataOdLoj, '18001228') END           AS Data_Lojalnosci_Od,
    CASE WHEN k.Knt_DataDoLoj > 0
        THEN DATEADD(d, k.Knt_DataDoLoj, '18001228') END           AS Data_Lojalnosci_Do,
    -- LastMod — Clarion TIMESTAMP: DATEADD(ss, col, '1990-01-01')
    CASE WHEN k.Knt_LastModL > 0
        THEN DATEADD(ss, k.Knt_LastModL, '1990-01-01') END         AS Data_Ostatniej_Modyfikacji,
    CASE WHEN k.Knt_LastModO > 0
        THEN DATEADD(ss, k.Knt_LastModO, '1990-01-01') END         AS Data_Modyfikacji_Operator,
    CASE WHEN k.Knt_LastModC > 0
        THEN DATEADD(ss, k.Knt_LastModC, '1990-01-01') END         AS Data_Modyfikacji_Kontrahent,
    -- Knt_EFaVatDataDo: wartości >109211 (np. 117976, 150483) = sentinel "bezterminowo"
    CASE
        WHEN k.Knt_EFaVatDataDo BETWEEN 1 AND 109211
        THEN DATEADD(d, k.Knt_EFaVatDataDo, '18001228')
        ELSE NULL
    END                                                             AS EFaktura_VAT_Data_Waznosci,
    k.Knt_DataUtworzenia                                           AS Data_Utworzenia,

    -- === E-FAKTURA VAT ===
    CASE k.Knt_EFaVatAktywne
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_EFaVatAktywne AS VARCHAR) + ')'
    END                                                             AS EFaktura_VAT_Aktywna,
    k.Knt_EFaVatEMail                                              AS EFaktura_VAT_Email,
    k.Knt_EFaVatOsw                                                AS EFaktura_VAT_Oswiadczenie,

    -- === VAT / PODATKI ===
    CASE k.Knt_PodatnikiemNabywca
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_PodatnikiemNabywca AS VARCHAR) + ')'
    END                                                             AS Podatnikiem_Nabywca,
    CASE k.Knt_WSTO
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_WSTO AS VARCHAR) + ')'
    END                                                             AS WSTO,
    CASE k.Knt_KSeFWyslij
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_KSeFWyslij AS VARCHAR) + ')'
    END                                                             AS KSeF_Wyslij,
    k.Knt_ProcTrnJpk                                               AS Procedura_JPK,
    k.Knt_OplataSpozZakup                                          AS Oplata_Spozywcza_Zakup,
    k.Knt_OplataSpozSprzedaz                                       AS Oplata_Spozywcza_Sprzedaz,

    -- === PROGRAM LOJALNOŚCIOWY ===
    k.Knt_KartaLoj                                                  AS Karta_Lojalnosciowa,
    k.Knt_Punkty                                                    AS Punkty,
    k.Knt_PunktyOdebr                                              AS Punkty_Odebrane,
    k.Knt_PunktyNalicz                                             AS Punkty_Naliczone,
    k.Knt_PunktyKorekta                                            AS Punkty_Korekta,

    -- === FLAGI DODATKOWE ===
    CASE k.Knt_Oddzialowy
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Oddzialowy AS VARCHAR) + ')'
    END                                                             AS Oddzialowy,
    CASE k.Knt_Spedytor
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Spedytor AS VARCHAR) + ')'
    END                                                             AS Spedytor,
    CASE k.Knt_Anonim
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Anonim AS VARCHAR) + ')'
    END                                                             AS Anonim,
    CASE k.Knt_ESklep
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_ESklep AS VARCHAR) + ')'
    END                                                             AS ESklep,
    CASE k.Knt_ObcaKarta
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_ObcaKarta AS VARCHAR) + ')'
    END                                                             AS Obca_Karta_Platnicza,
    CASE k.Knt_Osoba
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Osoba AS VARCHAR) + ')'
    END                                                             AS Osoba_Fizyczna,
    CASE k.Knt_StanPostep
        WHEN 0 THEN 'Brak'
        WHEN 1 THEN 'W trakcie postępowania'
        ELSE 'Nieznane (' + CAST(k.Knt_StanPostep AS VARCHAR) + ')'
    END                                                             AS Stan_Postepowania,
    CASE k.Knt_DataPromocji
        WHEN 0 THEN 'Brak'
        WHEN 1 THEN 'Wg daty wystawienia'
        WHEN 2 THEN 'Wg daty realizacji'
        ELSE 'Nieznane (' + CAST(k.Knt_DataPromocji AS VARCHAR) + ')'
    END                                                             AS Promocja_Wg_Daty,
    CASE k.Knt_Powiazany
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(k.Knt_Powiazany AS VARCHAR) + ')'
    END                                                             AS Powiazany,

    -- === ATRYBUTY CRM ===
    k.Knt_Atrybut1                                                  AS CRM_Atrybut1,
    k.Knt_Wartosc1                                                  AS CRM_Wartosc1,
    k.Knt_Atrybut2                                                  AS CRM_Atrybut2,
    k.Knt_Wartosc2                                                  AS CRM_Wartosc2,
    k.Knt_Atrybut3                                                  AS CRM_Atrybut3,
    k.Knt_Wartosc3                                                  AS CRM_Wartosc3,
    k.Knt_Branza                                                    AS Branza,
    slw.SLW_WartoscS                                                AS Rodzaj_Kontrahenta,
    k.Knt_RolaPartnera                                              AS Rola_Partnera,
    CASE k.Knt_Dzialalnosc
        WHEN 0 THEN 'Nieokreślono'
        WHEN 1 THEN 'Spółka cywilna'
        WHEN 2 THEN 'Spółka z o.o.'
        WHEN 3 THEN 'Spółka akcyjna'
        WHEN 4 THEN 'Spółka jawna'
        WHEN 5 THEN 'Spółka komandytowa'
        WHEN 6 THEN 'Spółdzielnia'
        WHEN 7 THEN 'Przedsiębiorstwo Państwowe'
        WHEN 8 THEN 'Jednoosobowa działalność gospodarcza'
        WHEN 9 THEN 'Inna działalność'
        ELSE 'Nieznane (' + CAST(k.Knt_Dzialalnosc AS VARCHAR) + ')'
    END                                                             AS Dzialalnosc_Gospodarcza,

    -- === DOKUMENT TOŻSAMOŚCI ===
    k.Knt_DokumentTozsamosci                                       AS Dokument_Tozsamosci,
    CASE WHEN k.Knt_DataWydania > 0
        THEN DATEADD(d, k.Knt_DataWydania, '18001228') END         AS Data_Wydania_Dokumentu,
    k.Knt_OrganWydajacy                                            AS Organ_Wydajacy,

    -- === UMOWA / CRM ===
    k.Knt_Umowa                                                     AS Umowa,
    k.Knt_CechaOpis                                                AS Cecha_Opis,

    -- === KONTA KSIĘGOWE ===
    k.Knt_KontoDostawcy                                            AS Konto_Ksiegowe_Dostawcy,
    k.Knt_KontoOdbiorcy                                            AS Konto_Ksiegowe_Odbiorcy,

    -- === KARTA PŁATNICZA ===
    k.Knt_TypKarty                                                  AS Typ_Karty_Platniczej,
    k.Knt_NumerKarty                                               AS Numer_Karty_Platniczej

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
LEFT JOIN CDN.KntGrupyDom kgd
    ON kgd.KGD_GIDNumer = k.Knt_GIDNumer
    AND kgd.KGD_GIDTyp = 32
LEFT JOIN Sciezka_Grup sg
    ON sg.KGD_GIDNumer = kgd.KGD_GrONumer
LEFT JOIN (
    SELECT TCN_RodzajCeny, MIN(TCN_Nazwa) AS Nazwa_Cennika
    FROM CDN.TwrCenyNag
    GROUP BY TCN_RodzajCeny
) tcn ON tcn.TCN_RodzajCeny = k.Knt_Cena AND k.Knt_Cena > 0
LEFT JOIN CDN.Slowniki slw
    ON slw.SLW_ID = k.Knt_Rodzaj
    AND k.Knt_Rodzaj > 0
