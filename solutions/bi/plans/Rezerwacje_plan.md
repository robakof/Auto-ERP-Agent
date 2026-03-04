# Plan widoku BI.Rezerwacje

**Tabela główna:** CDN.Rezerwacje — 1 329 rekordów, filtr techniczny: `Rez_TwrNumer > 0`

**Baseline:** COUNT(*) = COUNT(DISTINCT Rez_GIDNumer) = 1 329 po wszystkich JOINach ✓

**JOINy:**

| Tabela | Typ | Klucz | Uzasadnienie |
|---|---|---|---|
| CDN.TwrKarty | INNER | `Twr_GIDNumer = r.Rez_TwrNumer` | towar gwarantowany filtrem technicznym |
| CDN.KntKarty | LEFT | `Knt_GIDNumer = r.Rez_KntNumer AND Knt_GIDTyp = r.Rez_KntTyp` | NULL = rezerwacja bez kontrahenta |
| CDN.Magazyny | LEFT | `Mag_GIDNumer = r.Rez_MagNumer` | 0 = rezerwacja globalna |
| CDN.ZamNag | LEFT | `ZaN_GIDNumer = r.Rez_ZrdNumer AND r.Rez_ZrdTyp = 960` | numer ZS/ZZ |
| CDN.ProdZasoby | LEFT | `PZA_Id = r.Rez_ZrdNumer AND r.Rez_ZrdTyp = 14346` | pośrednik do ZP |
| CDN.ProdZlecenia | LEFT | `PZL_Id = pza.PZA_PZLId` | numer zlecenia produkcji |
| CDN.Dostawy | LEFT | `Dst_GIDNumer = r.Rez_DstNumer AND r.Rez_DstTyp = 160` | dostawa (GIDTyp 160='Dostawa'); 215/1329 rekordów powiązanych |

---

| CDN_Pole | Alias_w_widoku | Transformacja / Uwaga |
|---|---|---|
| Rez_GIDTyp | `Typ_Rezerwacji` | CASE: 2576='Rezerwacja', 2592='Rezerwacja u dostawcy' (etykiety z CDN.Obiekty) |
| Rez_GIDFirma | pominięte | ID firmy — techniczne |
| Rez_GIDNumer | `ID_Rezerwacji` | klucz główny, bez zmian |
| Rez_GIDLp | pominięte | techniczne |
| Rez_TwrTyp | pominięte | część klucza JOIN → TwrKarty |
| Rez_TwrFirma | pominięte | część klucza JOIN → TwrKarty |
| Rez_TwrNumer | pominięte | klucz JOIN (użyty w WHERE i INNER JOIN) |
| Rez_TwrLp | pominięte | część klucza JOIN → TwrKarty |
| *(TwrKarty)* | `Kod_Towaru` | Twr_Kod, bez zmian |
| *(TwrKarty)* | `Nazwa_Towaru` | Twr_Nazwa, bez zmian |
| *(TwrKarty)* | `Jm_Towaru` | Twr_Jm, bez zmian |
| Rez_KntTyp | pominięte | część klucza JOIN → KntKarty |
| Rez_KntFirma | pominięte | część klucza JOIN → KntKarty |
| Rez_KntNumer | pominięte | klucz JOIN (LEFT) |
| Rez_KntLp | pominięte | część klucza JOIN → KntKarty |
| *(KntKarty)* | `Akronim_Kontrahenta` | Knt_Akronim, NULL = brak kontrahenta |
| *(KntKarty)* | `Nazwa_Kontrahenta` | Knt_Nazwa1, NULL = brak kontrahenta |
| Rez_ZrdTyp | `Typ_Dokumentu_Zrodlowego` | bez zmian; kod liczbowy |
| Rez_ZrdTyp | `Opis_Dokumentu_Zrodlowego` | CASE wg dok. i CDN.Obiekty: 960='Zamówienie', 14345='Operacja procesu produkcyjnego', 14346='Zasób procesu produkcyjnego', 2592='Rezerwacja u dostawcy' |
| Rez_ZrdFirma | pominięte | techniczne |
| Rez_ZrdNumer | `Numer_Dokumentu_Zrodlowego` | CASE inline: 960→ZS/ZZ z ZamNag \| 14346→ZP z ProdZlecenia \| 2592→'BkRez#'+id; 14345 - brak numeru (produkcja) |
| Rez_ZrdLp | `Pozycja_Na_Dok_Zrodlowym` | bez zmian; numer pozycji na dok. źródłowym (0 = nagłówek) |
| Rez_ZrdSubLp | pominięte | techniczne |
| Rez_OpeTyp | pominięte | część klucza JOIN → OpeKarty; poza zakresem |
| Rez_OpeFirma | pominięte | część klucza JOIN → OpeKarty; poza zakresem |
| Rez_OpeNumer | pominięte | klucz JOIN do operatora; poza zakresem |
| Rez_OpeLp | pominięte | część klucza JOIN → OpeKarty; poza zakresem |
| Rez_MagTyp | pominięte | część klucza JOIN → Magazyny |
| Rez_MagFirma | pominięte | część klucza JOIN → Magazyny |
| Rez_MagNumer | `ID_Magazynu` | bez zmian; 0 = globalnie |
| Rez_MagLp | pominięte | techniczne |
| *(Magazyny)* | `Magazyn` | CASE: 0→'Globalnie', else Mag_Nazwa (wg dok.: "jeśli nie wypełniony, dotyczy wszystkich magazynów") |
| Rez_DstTyp | pominięte | część klucza JOIN → CDN.Dostawy |
| Rez_DstFirma | pominięte | techniczne |
| Rez_DstNumer | `ID_Dostawy` | bez zmian; 0→NULL; "wypełniany tylko po stronie sprzedaży" wg dok.; 215/1329 niepuste |
| Rez_DstLp | pominięte | techniczne |
| Rez_Ilosc | `Ilosc_Zarezerwowana` | bez zmian |
| Rez_Zrealizowano | `Ilosc_Zrealizowana` | bez zmian |
| Rez_IloscMag | `Ilosc_Na_Dok_Magazynowych` | bez zmian; wg dok.: "ilość wygenerowana na dok. magazynowych" |
| Rez_IloscImp | pominięte | wg dok.: "ilość wygenerowana na fakt. importowych" — puste w całym zbiorze |
| Rez_IloscSSC | pominięte | wg dok.: "ilość wygenerowana na dok. SSC" — puste w całym zbiorze |
| Rez_IloscSAD | pominięte | wg dok.: "ilość wygenerowana na dok. SAD" — puste w całym zbiorze |
| Rez_TStamp | `Data_Wprowadzenia` | wg dok.: "TimeStamp wprowadzenia rezerwacji"; Clarion TIMESTAMP → DATETIME; 0→NULL |
| Rez_DataRealizacji | `Data_Realizacji` | wg dok.: "Przewidywana data realizacji"; Clarion DATE → DATE; 0→NULL |
| Rez_DataWaznosci | `Data_Waznosci` | wg dok.: "Data ważności rezerwacji"; Clarion DATE → DATE; 0→NULL |
| Rez_DataAktywacji | `Data_Aktywacji` | wg dok.: "Początkowa data ważności. Przed nią i po DataW rezerwacja jest ignorowana"; Clarion DATE → DATE; 0→NULL |
| Rez_Aktywna | `Aktywna` | CASE: 1='Tak', 0='Nie'; wg dok.: "czy rezerwacja pozostaje w mocy" |
| Rez_Zrodlo | `Zrodlo_Rezerwacji` | bez zmian; kod liczbowy |
| Rez_Zrodlo | `Opis_Zrodla` | CASE wg dok.: 5='Zamówienie wewnętrzne', 6='Ręczna wewnętrzna', 9='Zamówienie zewnętrzne', 10='Ręczna zewnętrzna', 16='Dokument magazynowy' |
| Rez_DataPotwDst | `Data_Planowanej_Dostawy` | wg dok.: "Planowana data dostawy"; Clarion DATE → DATE; 0→NULL; 1274/1329 niepuste |
| Rez_FrsID | `ID_Centrum_Praw` | bez zmian; wg dok.: "identyfikator miejsca w strukturze firmy"; FK do CDN.FrmStruktura; 0 = brak |
| Rez_Typ | `Typ_Rez` | CASE wg dok.: 1='Rezerwacja', 0='Nierezerwacja'; dane: stałe=1, ale inne wartości możliwe |
| Rez_Priorytet | `Priorytet` | bez zmian; brak opisu w dok.; wartości: 0, 20 |
| Rez_DataRezerwacji | `Data_Rezerwacji` | wg dok.: "Data rezerwacji"; Clarion TIMESTAMP → DATETIME; 0→NULL |
| Rez_BsSTwrNumer | pominięte | wg dok.: "wskazanie na subelementy bilansu stanu towarów" — poza zakresem |
| Rez_BsNID | pominięte | wg dok.: "wskazanie na subelementy bilansu stanu towarów" — poza zakresem |
| Rez_BsSRodzaj | pominięte | wg dok.: "wskazanie na subelementy bilansu stanu towarów" — poza zakresem |
| Rez_PTZID | `ID_Zasobu_Technologii` | bez zmian; wg dok.: "id zasobu z technologii z czynności lub realizacji"; 0 = brak |
| Rez_CCHNumer | `ID_Klasy_Cechy` | bez zmian; wg dok.: "numer klasy cechy"; 37/1329 rekordów ≠ 0; 0 = brak cechy |
| Rez_Cecha | pominięte | wg dok.: "cecha towaru" — puste w całym zbiorze |
| Rez_Opis | pominięte | wg dok.: "opis rezerwacji" — puste w całym zbiorze |
| Rez_GUID | pominięte | techniczne |
| *(obliczeniowe)* | `Ilosc_Do_Pokrycia` | `Rez_Ilosc - Rez_Zrealizowano - Rez_IloscMag` |
