## Status: Faza 0 — Discovery PASS / Czeka na numerację od usera

**Tabela główna:** CDN.TraNag (nagłówki dokumentów handlowych)
**Baseline:** COUNT(*) = 223 936, COUNT(DISTINCT TrN_GIDNumer) = 223 936

---

## Typy dokumentów (TrN_GIDTyp — wszystkie zweryfikowane w CDN.Obiekty)

| GIDTyp | Skrót | Nazwa PL | n |
|--------|-------|----------|---|
| 2034 | PA | Paragon | 137367 |
| 2033 | FS | Faktura sprzedaży | 19405 |
| 1617 | PW | Przychód wewnętrzny | 19014 |
| 2001 | WZ | Wydanie zewnętrzne | 11349 |
| 1521 | FZ | Faktura zakupu | 10674 |
| 2009 | WZK | Korekta wydania zewnętrznego | 5467 |
| 1603 | MMW | Przesunięcie międzymagazynowe wydanie | 4628 |
| 1604 | MMP | Przesunięcie międzymagazynowe przyjęcie | 4590 |
| 1616 | RW | Rozchód wewnętrzny | 3747 |
| 2041 | FSK | Korekta faktury sprzedaży | 3413 |
| 2003 | KK | Korekta kosztu | 1367 |
| 1489 | PZ | Przyjęcie zewnętrzne | 1141 |
| 1497 | PZK | Korekta przyjęcia zewnętrznego | 828 |
| 1625 | PWK | Korekta przychodu wewnętrznego | 250 |
| 1529 | FZK | Korekta faktury zakupu | 229 |
| 2042 | PAK | Korekta paragonu | 204 |
| 2037 | FSE | Faktura eksportowa | 70 |
| 2013 | WKE | Korekta wydania eksportowego | 57 |
| 2005 | WZE | Wydanie zewnętrzne eksportowe | 57 |
| 1624 | RWK | Korekta rozchodu wewnętrznego | 34 |
| 2039 | RS | Raport sprzedaży | 14 |
| 2045 | FKE | Korekta faktury eksportowej | 13 |
| 2035 | RA | Faktura do paragonu | 9 |
| 2004 | DP | Deprecjacja | 5 |
| 1232 | KDZ | Koszt dodatkowy zakupu | 4 |

## Typy FK (CDN.Obiekty)

- 864 = Adres kontrahenta (podstawowy)
- 896 = Adres kontrahenta (inny)
- 944 = Pracownik
- 752 = Rejestr kasowy
- 449 = Schemat księgowania
- 32 = Kontrahent (KntKarty)
- 208 = Magazyn
- 128 = Operator (OpeKarty)

## Pola datowe

| Kolumna | Typ | Min | Max | Wzorzec |
|---------|-----|-----|-----|---------|
| TrN_Data2 | Clarion DATE | 74218 | 1908212 | BETWEEN 1 AND 109211 (sentinel) |
| TrN_Data3 | Clarion DATE | 74218 | 1908229 | BETWEEN 1 AND 109211 (sentinel) |
| TrN_Termin | Clarion DATE | 1 | 1908213 | BETWEEN 1 AND 109211 (sentinel) |
| TrN_DataMag | Clarion DATE | 81237 | 1908225 | BETWEEN 1 AND 109211 (sentinel) |
| TrN_DataRoz | Clarion DATE | >0 | 1908212 | BETWEEN 1 AND 109211 (sentinel) |
| TrN_DataPO | Clarion DATE | >0 | 1908229 | BETWEEN 1 AND 109211 (sentinel) |
| TrN_DataWplywu | Clarion DATE | 81237 | 1177607 | BETWEEN 1 AND 109211 (sentinel) |
| TrN_DataWysylki | Clarion DATE | >0 | 183153 | BETWEEN 1 AND 109211 (sentinel) |
| TrN_DataOdprawyPotwierdzenia | Clarion DATE | >0 | 99932 | CASE WHEN col=0 THEN NULL (brak sentinela) |
| TrN_DataWystOrg | Clarion DATE | >0 | 82247 | CASE WHEN col=0 THEN NULL |
| TrN_DataSprOrg | Clarion DATE | >0 | 82247 | CASE WHEN col=0 THEN NULL |
| TrN_DataOdKor | Clarion DATE | >0 | 82247 | CASE WHEN col=0 THEN NULL |
| TrN_DataDoKor | Clarion DATE | >0 | 82247 | CASE WHEN col=0 THEN NULL |
| TrN_LastMod | Clarion TIMESTAMP | ~10^9 | ~2*10^9 | DATEADD(ss, col, '1990-01-01') |

## TrN_Stan (zweryfikowane z dokumentacją)

0=edycja po dodaniu, 1=bufor, 2=po edycji w buforze, 3=zatwierdzona/nierozliczona,
4=po edycji płatności, 5=rozliczona, 6=anulowana

## TrN_TrNLp — WAŻNE

TrN_TrNLp = 127 → dokument aktywny; <>127 → anulowany (np. 1, 2, 3...)
Brak filtru WHERE na TrN_TrNLp w widoku — raportujemy wszystko, kolumna Aktywny_Dok.

## Numery dokumentów

CZEKA NA USERA — przekazano TraNag_objects.sql
Format: RTRIM(Seria) + '/' + Numer + '/' + Rok (YY czy YYYY — do potwierdzenia)
Prefiks (Z)/(A)/(s) — wzorzec z ERP_SCHEMA_PATTERNS.md (zweryfikowany wcześniej dla TraNag)

## Stałe (pomiń w widoku — distinct=1)

TrN_GIDFirma, TrN_GIDLp, TrN_ZwrLp, TrN_SpiLp, TrN_RelLp, TrN_KntLp, TrN_KnALp,
TrN_AkwLp, TrN_AdWLp, TrN_SchTyp/Firma/Numer/Lp, TrN_SaNTyp/Firma/Numer/Lp,
TrN_KonLp, TrN_TKTyp/Firma/Numer/Lp, TrN_Dziennik, TrN_FormaRabat, TrN_Zaokraglenie,
TrN_Zaksiegowano, TrN_DataKsiegowania, TrN_LicznikKopii, TrN_MagZLp, TrN_MagDLp,
TrN_OpeTypW, TrN_OpeFirmaW, TrN_OpeLpW/Z/R/M, TrN_OdoLp, TrN_Detal,
TrN_DokumentObcyCharset, TrN_RabatW, TrN_MiejsceZaladunku, TrN_MiejscePrzeznaczenia,
TrN_RodzajTransportu, TrN_InfoDlaUC, TrN_Waga, TrN_NumerSAD, TrN_OpeTypM, TrN_OpeFirmaM,
TrN_IncotermsMiejsce, TrN_WagaBrutto, TrN_DataOdb, TrN_OpiLp, TrN_KarLp, TrN_KnDLp,
TrN_Wyslano, TrN_Promocje, TrN_PotwierdzenieOdbioru, TrN_RabatPromocyjnyGlobalny,
TrN_ZwroconoCalaIlosc, TrN_TerminRozliczeniaKaucji, TrN_OddZakazPAFA, TrN_WsSCHNumer,
TrN_WsStosujSchemat, TrN_WsDziennik, TrN_WsStosujDziennik, TrN_PrjId, TrN_KnSTypD/Firma/Numer/Lp,
TrN_KnSTypP/Firma/Numer/Lp, TrN_FrmNumer, TrN_PrzywracajRezerwacje, TrN_FormatkaCyr,
TrN_WtrID, TrN_WtrProgID, TrN_RodzajKor, TrN_VatZDPeDNumer, TrN_VatZDPeDLp,
TrN_DataDostawy, TrN_WMS, TrN_VATNalOd, TrN_OpeTypZM/NumerZM/TStampZM,
TrN_OpeTypZFR/NumerZFR/TStampZFR, TrN_ZatwMerytorycznie, TrN_ZatwFormalnoRach,
TrN_DataWplywuFA, TrN_PodzialPlatNiePytaj, TrN_ProceduraUproszcz, TrN_MPP,
TrN_JestLimitCelowy, TrN_OplataSpozFlaga, TrN_UmNId, TrN_ProceduraOSS,
TrN_RozliczacVIU, TrN_KorektaVIU, TrN_KrajWydania, TrN_KrajWydIdentPod,
TrN_KrajWydIdentPodVAT, TrN_KSeFWyslij, TrN_KSeFNumerOrg, TrN_GodzinaWystawienia (is_useful=Nie)

## Pliki

- Brudnopis: solutions/bi/TraNag/TraNag_draft.sql
- Numeracja: solutions/bi/TraNag/TraNag_objects.sql → CZEKA NA USERA

## Następny krok

Po otrzymaniu wyniku TraNag_objects.sql od usera → budowanie planu (Faza 1a)
