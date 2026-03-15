## Status: Faza 2 — draft SQL gotowy, eksport wykonany

**Tabela główna:** CDN.TraNag (naglowki dokumentow handlowych)
**Baseline:** COUNT(*) = 223 984, COUNT(DISTINCT TrN_GIDNumer) = 223 984
(baza urosla o 48 rekordow od czasu discovery — poprzedni baseline: 223 936)

---

## Typy dokumentow (TrN_GIDTyp — wszystkie zweryfikowane w CDN.Obiekty)

| GIDTyp | Skrot | Nazwa PL | n |
|--------|-------|----------|---|
| 2034 | PA | Paragon | 137367 |
| 2033 | FS | Faktura sprzedazy | 19405 |
| 1617 | PW | Przychod wewnetrzny | 19014 |
| 2001 | WZ | Wydanie zewnetrzne | 11349 |
| 1521 | FZ | Faktura zakupu | 10674 |
| 2009 | WZK | Korekta wydania zewnetrznego | 5467 |
| 1603 | MMW | Przesuniecie miedzymagazynowe wydanie | 4628 |
| 1604 | MMP | Przesuniecie miedzymagazynowe przyjecie | 4590 |
| 1616 | RW | Rozchod wewnetrzny | 3747 |
| 2041 | FSK | Korekta faktury sprzedazy | 3413 |
| 2003 | KK | Korekta kosztu | 1367 |
| 1489 | PZ | Przyjecie zewnetrzne | 1141 |
| 1497 | PZK | Korekta przyjecia zewnetrznego | 828 |
| 1625 | PWK | Korekta przychodu wewnetrznego | 250 |
| 1529 | FZK | Korekta faktury zakupu | 229 |
| 2042 | PAK | Korekta paragonu | 204 |
| 2037 | FSE | Faktura eksportowa | 70 |
| 2013 | WKE | Korekta wydania eksportowego | 57 |
| 2005 | WZE | Wydanie zewnetrzne eksportowe | 57 |
| 1624 | RWK | Korekta rozchodu wewnetrznego | 34 |
| 2039 | RS | Raport sprzedazy | 14 |
| 2045 | FKE | Korekta faktury eksportowej | 13 |
| 2035 | RA | Faktura do paragonu | 9 |
| 2004 | DP | Deprecjacja | 5 |
| 1232 | KDZ | Koszt dodatkowy zakupu | 4 |

## JOINy ustalone

- CDN.KntKarty knt — LEFT JOIN na TrN_KntNumer + TrN_KntTyp + KntNumer>0
- CDN.KntKarty knd — LEFT JOIN na TrN_KnDNumer + TrN_KnDTyp + KnDNumer>0
- CDN.KntKarty akw_knt — LEFT JOIN gdy TrN_AkwTyp=32 (dominujacy typ)
- CDN.PrcKarty akw_prc — LEFT JOIN gdy TrN_AkwTyp=944 (2 rekordy)
- CDN.Magazyny mag_z — LEFT JOIN na TrN_MagZNumer>0
- CDN.Magazyny mag_d — LEFT JOIN na TrN_MagDNumer>0
- CDN.OpeKarty ope_w/z/r/m — LEFT JOIN na TrN_OpeNumerX>0
- CDN.PrcKarty prc_opi — LEFT JOIN gdy TrN_OpiTyp=944 + TrN_OpiNumer>0

## Odchylenie od planu (zatwierdzone przez usera 2026-03-15)

Plan zakladal: Akwizytor_Login z CDN.OpeKarty gdy TrN_AkwTyp=128
Dane rzeczywiste: TrN_AkwTyp IN (0=175520, 32=48461, 944=2) — typ 128 nie wystepuje
Implementacja: Akwizytor_Akronim = COALESCE(akw_knt.Knt_Akronim, akw_prc.Prc_Akronim)

## Weryfikacja eksportu (2026-03-15)

| Kolumna | Distinct | Null | OK |
|---------|----------|------|----|
| Typ_Dok | 25 | 0 | tak |
| Stan_Dok | 6 | 0 | tak |
| Aktywny_Dok | 2 | 0 | tak |
| Numer_Dokumentu | 223605 | 0 | tak* |
| Data_Wystawienia | 1052 | 3 | tak |
| Forma_Platnosci | 3 | 33606 | tak |
| Waluta | 3 | 0 | tak |
| Rejestr_VAT | 2 | 190723 | tak |
| VAT_Od | 2 | 0 | tak |
| Kontrahent_Akronim | 2856 | 171091 | tak |
| Login_Operatora_Wyst | 33 | 0 | tak |
| Mag_Zrodlowy_Symbol | 20 | 8039 | tak |
| Opiekun_Akronim | 6 | 207359 | tak |
| Akwizytor_Akronim | 16 | 175829 | tak |
| Kurs_Walutowy | 44 | 223929 | tak |

*Numer_Dokumentu: 379 duplikatow (223984 - 223605) — zjawisko danych (ten sam numer
 w roznych typach dokumentow), nie blad SQL.

## Typy FK (CDN.Obiekty)

- 864 = Adres kontrahenta (podstawowy)
- 896 = Adres kontrahenta (inny)
- 944 = Pracownik
- 32 = Kontrahent (KntKarty)
- 208 = Magazyn
- 128 = Operator (OpeKarty)

## Pola datowe

| Kolumna | Typ | Sentinel | OK |
|---------|-----|----------|----|
| TrN_Data2 | Clarion DATE | BETWEEN 1 AND 109211 | tak |
| TrN_Data3 | Clarion DATE | BETWEEN 1 AND 109211 | tak |
| TrN_Termin | Clarion DATE | BETWEEN 1 AND 109211 | tak |
| TrN_DataMag | Clarion DATE | BETWEEN 1 AND 109211 | tak |
| TrN_DataRoz | Clarion DATE | BETWEEN 1 AND 109211 | tak |
| TrN_DataPO | Clarion DATE | BETWEEN 1 AND 109211 | tak |
| TrN_DataWplywu | Clarion DATE | BETWEEN 1 AND 109211 | tak |
| TrN_DataWysylki | Clarion DATE | BETWEEN 1 AND 109211 | tak |
| TrN_DataOdprawyPotwierdzenia | Clarion DATE | 0=NULL | tak |
| TrN_DataWystOrg | Clarion DATE | 0=NULL | tak |
| TrN_DataSprOrg | Clarion DATE | 0=NULL | tak |
| TrN_DataOdKor | Clarion DATE | 0=NULL | tak |
| TrN_DataDoKor | Clarion DATE | 0=NULL | tak |
| TrN_LastMod | Clarion TIMESTAMP | DATEADD(ss,...'1990-01-01') | tak |

## Pliki

- Brudnopis: solutions/bi/TraNag/TraNag_draft.sql
- Plan: solutions/bi/TraNag/TraNag_plan.xlsx
- Eksport: solutions/bi/TraNag/TraNag_export.xlsx (aktualizacja 2026-03-15)

## Nastepny krok

Analityk recenzuje eksport (Faza 3). Po zatwierdzeniu → solutions_save_view.py → DBA.
