WITH Sciezka_Grup_Twr AS (
    -- Anchor: grupy poziomu 0 (korzeń GrONumer=0)
    SELECT
        TGD_GIDNumer,
        CAST(TGD_Kod AS NVARCHAR(4000)) AS Sciezka,
        0 AS Poziom
    FROM CDN.TwrGrupyDom
    WHERE TGD_GIDTyp = -16 AND TGD_GrONumer = 0
    UNION ALL
    SELECT
        g.TGD_GIDNumer,
        CAST(p.Sciezka + '\' + RTRIM(g.TGD_Kod) AS NVARCHAR(4000)),
        p.Poziom + 1
    FROM CDN.TwrGrupyDom g
    INNER JOIN Sciezka_Grup_Twr p ON p.TGD_GIDNumer = g.TGD_GrONumer
    WHERE g.TGD_GIDTyp = -16 AND g.TGD_GrONumer > 0
      AND p.Poziom < 20
)

SELECT
    -- === IDENTYFIKATOR ===
    t.Twr_GIDNumer                                              AS ID_Towaru,

    -- === TYP ===
    CASE t.Twr_Typ
        WHEN 1 THEN 'Towar'
        WHEN 2 THEN 'Produkt'
        WHEN 3 THEN 'Koszt'
        WHEN 4 THEN 'Usługa'
        ELSE 'Nieznane (' + CAST(t.Twr_Typ AS VARCHAR) + ')'
    END                                                         AS Typ,

    -- === PODSTAWOWE DANE ===
    t.Twr_Kod                                                   AS Kod,
    t.Twr_Nazwa                                                 AS Nazwa,
    t.Twr_Nazwa1                                                AS Nazwa1,
    t.Twr_Ean                                                   AS EAN,
    t.Twr_Jm                                                    AS JM,
    t.Twr_JmFormat                                              AS JM_Miejsca_Po_Przecinku,

    -- === KANAŁ SPRZEDAŻY (domyślny cennik) ===
    t.Twr_CenaSpr                                               AS Kanal_Sprzedazy_Nr,
    CASE t.Twr_CenaSpr
        WHEN 1 THEN 'CENA 100'
        WHEN 2 THEN 'CMENTARZ'
        WHEN 3 THEN 'FRANOWO'
        WHEN 4 THEN 'BRICO'
        WHEN 5 THEN 'INTER'
        WHEN 6 THEN 'MRÓWKA'
        WHEN 7 THEN 'CHATA POLSKA'
        WHEN 8 THEN 'AT'
        WHEN 9 THEN 'PRYZMAT'
        ELSE 'Nieznane (' + CAST(t.Twr_CenaSpr AS VARCHAR) + ')'
    END                                                         AS Kanal_Sprzedazy,

    -- === DOMYŚLNA JM (TwrJm; Lp=0 → baza JM z Twr_Jm) ===
    t.Twr_JmDomyslna                                            AS JM_Domyslna_Id,
    COALESCE(twj.TwJ_JmZ, t.Twr_Jm)                           AS JM_Domyslna_Symbol,

    -- === DOMYŚLNY DOSTAWCA (TwrDost + KntKarty) ===
    t.Twr_DstDomyslny                                           AS Dostawca_Domyslny_Nr,
    knt_dst.Knt_Akronim                                         AS Dostawca_Domyslny_Akronim,
    knt_dst.Knt_Nazwa1                                          AS Dostawca_Domyslny_Nazwa,

    -- === VAT ZAKUP ===
    t.Twr_GrupaPod                                              AS Grupa_VAT_Zakup,

    -- === OPERATOR TWORZĄCY ===
    t.Twr_OpeNumer                                              AS ID_Operatora_Tworzacego,
    op1.Ope_Ident                                               AS Operator_Tworzacy,

    -- === KATALOG ===
    t.Twr_Katalog                                               AS Katalog,

    -- === FLAGI WIDOCZNOŚCI / HANDLOWE ===
    CASE t.Twr_WCenniku
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_WCenniku AS VARCHAR) + ')'
    END                                                         AS W_Cenniku,
    CASE t.Twr_EdycjaNazwy
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_EdycjaNazwy AS VARCHAR) + ')'
    END                                                         AS Edycja_Nazwy,
    CASE t.Twr_BezRabatu
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_BezRabatu AS VARCHAR) + ')'
    END                                                         AS Bez_Rabatu,

    -- === DATY MODYFIKACJI (Clarion TIMESTAMP; LastModO usunięty — ≈ duplikat DataUtworzenia) ===
    CASE WHEN t.Twr_LastModL = 0 THEN NULL
         ELSE DATEADD(ss, t.Twr_LastModL, '1990-01-01') END    AS Data_Modyfikacji_L,
    CASE WHEN t.Twr_LastModC = 0 THEN NULL
         ELSE DATEADD(ss, t.Twr_LastModC, '1990-01-01') END    AS Data_Modyfikacji_C,

    -- === ZAKUP ===
    CASE t.Twr_ZakupAutoryz
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_ZakupAutoryz AS VARCHAR) + ')'
    END                                                         AS Zakup_Autoryzowany,

    -- === MAGAZYN DOMYŚLNY (Magazyny) ===
    t.Twr_MagNumer                                              AS ID_Magazynu,
    mag.MAG_Kod                                                 AS Magazyn_Kod,
    mag.MAG_Nazwa                                               AS Magazyn_Domyslny,

    -- === KOSZT USŁUGI ===
    CASE t.Twr_KosztUTyp
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_KosztUTyp AS VARCHAR) + ')'
    END                                                         AS Koszt_Uslugi_Typ,

    -- === KLASA CECHY (CechyKlasy GIDTyp=192) ===
    CASE WHEN t.Twr_CCKNumer = 0 THEN 'Brak'
         ELSE cck.CCK_Nazwa
    END                                                         AS Klasa_Cechy,

    -- === PRODUCENT (KntKarty GIDTyp=32) ===
    t.Twr_PrdNumer                                              AS ID_Producenta,
    knt_prd.Knt_Akronim                                         AS Producent_Akronim,
    knt_prd.Knt_Nazwa1                                          AS Producent_Nazwa,

    -- === OPERATOR MODYFIKUJĄCY ===
    t.Twr_OpeNumerM                                             AS ID_Operatora_Modyfikujacego,
    op2.Ope_Ident                                               AS Operator_Modyfikujacy,

    -- === VAT (pełny zestaw) ===
    t.Twr_StawkaPod                                             AS Stawka_VAT_Zakup,
    CASE t.Twr_FlagaVat
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_FlagaVat AS VARCHAR) + ')'
    END                                                         AS Flaga_VAT_Zakup,
    t.Twr_GrupaPodSpr                                           AS Grupa_VAT_Sprzedaz,
    t.Twr_StawkaPodSpr                                          AS Stawka_VAT_Sprzedaz,
    CASE t.Twr_FlagaVatSpr
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_FlagaVatSpr AS VARCHAR) + ')'
    END                                                         AS Flaga_VAT_Sprzedaz,

    -- === STATUS AKTYWNOŚCI ===
    CASE t.Twr_Archiwalny
        WHEN 1 THEN 'Archiwalny' WHEN 0 THEN 'Aktywny'
        ELSE 'Nieznane (' + CAST(t.Twr_Archiwalny AS VARCHAR) + ')'
    END                                                         AS Archiwalny,

    -- === JM (dodatkowe) ===
    CASE t.Twr_JMCalkowita
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_JMCalkowita AS VARCHAR) + ')'
    END                                                         AS JM_Calkowita,
    t.Twr_JmDomyslnaZak                                         AS JM_Domyslna_Zakup,
    COALESCE(twj_zak.TwJ_JmZ, t.Twr_Jm)                       AS JM_Domyslna_Zakup_Symbol,
    t.Twr_WymJm                                                 AS JM_Wymiarow,
    CASE t.Twr_JMBlokujZmiane
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_JMBlokujZmiane AS VARCHAR) + ')'
    END                                                         AS JM_Blokuj_Zmiane,

    -- === KRAJ I DATA UTWORZENIA ===
    t.Twr_KrajPoch                                              AS Kraj_Pochodzenia,
    CASE WHEN t.Twr_DataUtworzenia = 0 THEN NULL
         ELSE DATEADD(ss, t.Twr_DataUtworzenia, '1990-01-01')
    END                                                         AS Data_Utworzenia,

    -- === DOSTAWA ===
    CASE t.Twr_DostawaEAN
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_DostawaEAN AS VARCHAR) + ')'
    END                                                         AS Dostawa_EAN,

    -- === MOBILE / SKLEP ===
    CASE t.Twr_MobSpr
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_MobSpr AS VARCHAR) + ')'
    END                                                         AS Mobile_Sprzedaz,
    CASE t.Twr_JMiSklep
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_JMiSklep AS VARCHAR) + ')'
    END                                                         AS JM_Sklep,
    CASE t.Twr_JMPulpitKnt
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_JMPulpitKnt AS VARCHAR) + ')'
    END                                                         AS JM_Pulpit_Knt,
    t.Twr_JMMobSpr                                              AS JM_Mobile_Sprzedaz_Id,
    COALESCE(twj_mob.TwJ_JmZ, t.Twr_Jm)                       AS JM_Mobile_Sprzedaz_Symbol,

    -- === PIA (bitmask: 2=Pulpit Knt, 4=e-Sklep, 8=Mob.Sprz., 16=Mob.Mag.) ===
    CASE t.Twr_PIADostepnoscFlaga
        WHEN 0 THEN 'Brak'
        WHEN 8 THEN 'Mobilny Sprzedawca'
        ELSE 'Kombinacja (' + CAST(t.Twr_PIADostepnoscFlaga AS VARCHAR) + ')'
    END                                                         AS PIA_Dostepnosc,

    t.Twr_JMDopelnianiaMobSpr                                   AS JM_Dopelniania_Mobile_Id,
    COALESCE(twj_dop.TwJ_JmZ, t.Twr_Jm)                       AS JM_Dopelniania_Mobile_Symbol,

    -- === ANALIZA ===
    CASE t.Twr_AnalizaABCXYZ
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_AnalizaABCXYZ AS VARCHAR) + ')'
    END                                                         AS Analiza_ABCXYZ,

    -- === TECHNICZNA / MRP ===
    -- Techniczna_Dec1: dokumentacja ERP mówi "wyłącznie wewnętrzne, powinno być puste";
    -- w bazie: 13 distinct wartości — anomalia, eksponujemy as-is dla transparentności
    t.Twr_TechnicznaDec1                                        AS Techniczna_Dec1,
    CASE WHEN t.Twr_MrpId = 0 THEN NULL ELSE t.Twr_MrpId END  AS MRP_Id,
    CASE WHEN t.Twr_MrpId = 0 THEN NULL
         ELSE DATEADD(dd, pok.POK_DataOd - 1, '1800-12-28')
    END                                                         AS MRP_Okres_Data,

    -- === AUTONUMERACJA ===
    t.Twr_AutonumeracjaLiczba                                   AS Autonumeracja_Liczba,

    -- === MOBILE (partie) ===
    CASE t.Twr_WysylaniePartiiMobSpr
        WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_WysylaniePartiiMobSpr AS VARCHAR) + ')'
    END                                                         AS Wysylanie_Partii_Mobile,

    -- === ZESTAW ===
    CASE t.Twr_DodEleZez
        WHEN 0 THEN 'Nie'
        ELSE 'Nieznane (' + CAST(t.Twr_DodEleZez AS VARCHAR) + ')'
    END                                                         AS Dod_Elementy_Zezwolenia,

    -- === GRUPY DOMOWE — pełna ścieżka (TwrGrupyDom, rekurencyjnie) ===
    tgd.TGD_GrONumer                                            AS ID_Grupy,
    ISNULL(sg.Sciezka, 'Brak grupy')                           AS Sciezka_Grupy

FROM CDN.TwrKarty t

-- Operator tworzący
LEFT JOIN CDN.OpeKarty op1
    ON op1.Ope_GIDNumer = t.Twr_OpeNumer

-- Operator modyfikujący
LEFT JOIN CDN.OpeKarty op2
    ON op2.Ope_GIDNumer = t.Twr_OpeNumerM

-- Magazyn domyślny
LEFT JOIN CDN.Magazyny mag
    ON mag.MAG_GIDNumer = t.Twr_MagNumer
    AND t.Twr_MagNumer > 0

-- Producent (KntKarty, GIDTyp=32)
LEFT JOIN CDN.KntKarty knt_prd
    ON knt_prd.Knt_GIDNumer = t.Twr_PrdNumer
    AND knt_prd.Knt_GIDTyp  = t.Twr_PrdTyp
    AND t.Twr_PrdNumer > 0

-- Klasa cechy (GIDTyp=192)
LEFT JOIN CDN.CechyKlasy cck
    ON cck.CCK_GIDNumer = t.Twr_CCKNumer
    AND cck.CCK_GIDTyp  = 192
    AND t.Twr_CCKNumer  > 0

-- Grupy domowe — przypisanie towar→grupa (GIDTyp=16)
LEFT JOIN CDN.TwrGrupyDom tgd
    ON tgd.TGD_GIDTyp   = 16
    AND tgd.TGD_GIDNumer = t.Twr_GIDNumer

-- Grupy domowe — ścieżka z CTE
LEFT JOIN Sciezka_Grup_Twr sg
    ON sg.TGD_GIDNumer = tgd.TGD_GrONumer

-- Domyślna JM sprzedaży (TwrJm; Lp > 0)
LEFT JOIN CDN.TwrJm twj
    ON twj.TwJ_TwrNumer = t.Twr_GIDNumer
    AND twj.TwJ_TwrLp   = t.Twr_JmDomyslna
    AND t.Twr_JmDomyslna > 0

-- Domyślna JM zakupu (TwrJm)
LEFT JOIN CDN.TwrJm twj_zak
    ON twj_zak.TwJ_TwrNumer = t.Twr_GIDNumer
    AND twj_zak.TwJ_TwrLp   = t.Twr_JmDomyslnaZak
    AND t.Twr_JmDomyslnaZak > 0

-- JM mobile sprzedaży (TwrJm)
LEFT JOIN CDN.TwrJm twj_mob
    ON twj_mob.TwJ_TwrNumer = t.Twr_GIDNumer
    AND twj_mob.TwJ_TwrLp   = t.Twr_JMMobSpr
    AND t.Twr_JMMobSpr > 0

-- JM dopełniania mobile (TwrJm)
LEFT JOIN CDN.TwrJm twj_dop
    ON twj_dop.TwJ_TwrNumer = t.Twr_GIDNumer
    AND twj_dop.TwJ_TwrLp   = t.Twr_JMDopelnianiaMobSpr
    AND t.Twr_JMDopelnianiaMobSpr > 0

-- Okres MRP (ProdOkresy)
LEFT JOIN CDN.ProdOkresy pok
    ON pok.POK_Id = t.Twr_MrpId
    AND t.Twr_MrpId > 0

-- Domyślny dostawca — pozycja (TwrDost)
LEFT JOIN CDN.TwrDost dst
    ON dst.TWD_TwrNumer = t.Twr_GIDNumer
    AND dst.TWD_TwrLp   = t.Twr_DstDomyslny
    AND t.Twr_DstDomyslny > 0

-- Domyślny dostawca — dane kontrahenta
LEFT JOIN CDN.KntKarty knt_dst
    ON knt_dst.Knt_GIDNumer = dst.TWD_KntNumer
    AND knt_dst.Knt_GIDTyp  = dst.TWD_KntTyp

WHERE t.Twr_GIDNumer > 0
