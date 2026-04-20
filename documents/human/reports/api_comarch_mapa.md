# Mapa API Comarch ERP XL — pełne mapowanie możliwości

## Podsumowanie

| Warstwa | Funkcji | Opis |
|---|---|---|
| Core API (.NET DLL) | ~210 | Pełne CRUD na wszystkich obiektach ERP |
| AI_ChatERP (SQL proc) | 44 | Gotowe endpointy read/write dla AI agentów |
| AI_PP (SQL proc) | 6 | Prognozowanie popytu (ML) |
| Hydra (C# callbacks) | framework | Rozszerzenia UI desktopowego |
| **Razem** | **~260** | |

---

## Grupa 1: LOGOWANIE I SESJA (4 funkcje)

| Funkcja | Typ | Opis |
|---|---|---|
| XLLogin | Connect | Rozpoczęcie sesji API |
| XLLogout | Connect | Zamknięcie sesji |
| XLLogoutEx | Connect | Zamknięcie sesji (rozszerzone) |
| XLSprawdzWersje | Read | Sprawdzenie wersji ERP |

---

## Grupa 2: DOKUMENTY HANDLOWE (20 funkcji)

Faktury sprzedaży, zakupu, korekty, paragony.

| Funkcja | Typ | Opis |
|---|---|---|
| XLNowyDokument | Create | Nowy dokument handlowy |
| XLOtworzDokument | Read | Otwarcie istniejącego do edycji |
| XLZamknijDokument | Update | Zamknięcie/zatwierdzenie dokumentu |
| XLDodajPozycje | Create | Dodanie pozycji (towaru) |
| XLModyfikujPozycje | Update | Zmiana pozycji |
| XLUsunPozycje | Delete | Usunięcie pozycji |
| XLDodajSubPozycje | Create | Dodanie sub-pozycji (komplety) |
| XLUsunSubPozycje | Delete | Usunięcie sub-pozycji |
| XLDodajPlatnosc | Create | Dodanie płatności |
| XLModyfikujPlatnosc | Update | Zmiana płatności |
| XLDodajVAT | Create | Dodanie pozycji VAT |
| XLModyfikujVAT | Update | Zmiana VAT |
| XLModyfikujNaglowek | Update | Edycja nagłówka (kontrahent, daty) |
| XLDokumentyZwiazane | Read | Pobranie dokumentów powiązanych |
| XLZepnijDokumenty | Update | Powiązanie dokumentów |
| XLDodajDoSpinacza | Update | Dodanie do spinacza |
| XLUsunZeSpinacza | Update | Usunięcie ze spinacza |
| XLKosztyDodDok | Create | Koszty dodatkowe dokumentu |
| XLRozbijKDZ | Process | Rozbicie kosztów dodatkowych |
| XLDodajKodJPKV7 / XLUsunKodJPKV7 | CRUD | Kody JPK_V7 |

---

## Grupa 3: DOKUMENTY MAGAZYNOWE (15 funkcji)

PZ, WZ, MM, PW, RW — ruchy magazynowe.

| Funkcja | Typ | Opis |
|---|---|---|
| XLNowyDokumentMag | Create | Nowy dokument magazynowy |
| XLOtworzDokumentMag | Read | Otwarcie do edycji |
| XLZamknijDokumentMag | Update | Zamknięcie dokumentu |
| XLDodajPozycjeMag | Create | Dodanie pozycji |
| XLModyfikujPozycjeMag | Update | Zmiana pozycji |
| XLUsunPozycjeMag | Delete | Usunięcie pozycji |
| XLDodajSubPozycjeMag / XLUsunSubPozycjeMag | CRUD | Sub-pozycje |
| XLDodajSubPozycjeMap / XLUsunSubPozycjeMap | CRUD | Mapowanie multi-magazyn |
| XLDodajOpiekunaDoMag | Create | Przypisanie opiekuna |
| XLDodajZasobDoMag | Create | Dodanie zasobu |
| XLRealizujPozycjeMag | Process | Realizacja (picking) |
| XLUsunRealizacjeMag | Delete | Anulowanie realizacji |
| XLZamknijRealizacjeMag | Update | Zamknięcie partii realizacji |

---

## Grupa 4: KONTRAHENCI (13 funkcji)

Dostawcy, odbiorcy, adresy, zgody RODO.

| Funkcja | Typ | Opis |
|---|---|---|
| XLNowyKontrahent | Create | Nowy kontrahent (legacy) |
| XLNowyKontrahentSQL | Create | Nowy kontrahent (nowoczesne SQL) |
| XLOtworzKontrahentaSQL | Read | Otwarcie do edycji |
| XLZmienPoleKntSQL | Update | Zmiana pojedynczego pola |
| XLZamknijKontrahenta / SQL | Update | Archiwizacja |
| XLNowyAdres / XLZmienAdres / XLZamknijAdres | CRUD | Adresy |
| XLNowaGrupaKnt | Create | Grupa kontrahentów |
| XLNowaZgoda / XLModyfikujZgode | CRUD | Zgody RODO |
| XLDodajOsobeKontrahenta | Create | Osoba kontaktowa |

---

## Grupa 5: TOWARY I CENY (10 funkcji)

Kartoteki towarowe, cenniki, EAN, partie.

| Funkcja | Typ | Opis |
|---|---|---|
| XLNowyTowar | Create | Nowa kartoteka towaru |
| XLZamknijTowar | Update | Archiwizacja towaru |
| XLNowaGrupaTwr | Create | Nowa grupa towarów |
| XLPartia | Create | Nowa partia/lot |
| XLDodajCene | Create | Dodanie ceny do cennika |
| XLZmienCene | Update | Zmiana ceny |
| XLNowyCennik | Create | Nowy cennik |
| XLZamknijCennik | Update | Archiwizacja cennika |
| XLDodajDostawce | Create | Dodanie dostawcy towaru |
| XLGenerujEAN | Process | Generowanie kodu EAN |

---

## Grupa 6: ZAMÓWIENIA (7 funkcji)

Zamówienia zakupu i sprzedaży.

| Funkcja | Typ | Opis |
|---|---|---|
| XLNowyDokumentZam | Create | Nowe zamówienie |
| XLOtworzDokumentZam | Read | Otwarcie do edycji |
| XLDodajPozycjeZam | Create | Dodanie pozycji |
| XLModyfikujPozycjeZam | Update | Zmiana pozycji |
| XLUsunPozycjeZam | Delete | Usunięcie pozycji |
| XLDodajPlatnoscZam | Create | Dodanie płatności |
| XLZamknijDokumentZam | Update | Zamknięcie zamówienia |

---

## Grupa 7: PRODUKCJA (39 funkcji)

Technologie, zlecenia produkcyjne, realizacja, kontrola jakości.

### Zlecenia produkcyjne (8)
| Funkcja | Typ | Opis |
|---|---|---|
| XLNoweZlecenieProd | Create | Nowe zlecenie produkcyjne |
| XLDodajDoZleceniaProd | Create | Dodanie do zlecenia |
| XLZamknijZlecenieProd | Update | Zamknięcie zlecenia |
| XLNowyDokumentZlc | Create | Nowy dokument zlecenia |
| XLDodajPozycjeZlc | Create | Dodanie pozycji |
| XLZamknijDokumentZlc | Update | Zamknięcie |
| XLOtworzDokumentZlc | Read | Otwarcie |
| XLRealizujZlc | Process | Realizacja zlecenia |

### Technologie i routing (7)
| Funkcja | Typ | Opis |
|---|---|---|
| XLNowaTechnologia | Create | Nowa technologia |
| XLNowaCzynnoscTechnologia | Create | Nowa czynność |
| XLNowaFunkcjaCzynnoscTechnologia | Create | Przypisanie funkcji do czynności |
| XLNowyZasobCzynnoscTechnologia | Create | Przypisanie zasobu |
| XLNowaFunkcjaProd | Create | Nowa funkcja produkcyjna |
| XLNowyObiektProd | Create | Nowy obiekt produkcyjny |
| XLNowyObiektFunkcjaProd | Create | Powiązanie obiekt-funkcja |

### Realizacja i śledzenie (15+)
| Funkcja | Typ | Opis |
|---|---|---|
| XLDodajCzynnoscDoProcesuProd | Create | Dodanie operacji do planu |
| XLDodajZasobDoCzynnosciProd | Create | Przypisanie zasobu |
| XLDodajObiektDoCzynnosciProd | Create | Przypisanie obiektu |
| XLDodajTerminDoCzynnosciProd | Create | Termin operacji |
| XLDodajRealizacjeOperacjiProd | Create | Rejestracja realizacji |
| XLProdZmienIloscRealizacji | Update | Zmiana ilości |
| XLRejestrujUzycieNarzedzia | Create | Rejestracja użycia narzędzia |
| XLProdRedukujIlosciZasobow | Process | Zużycie surowców |
| XLProdGenerujDokumentyDlaObiektow | Process | Auto-generowanie dokumentów |
| XLProdSpinajZasobyZDokumentami | Process | Powiązanie zasobów z dokumentami |
| XLNowyZabiegProd | Create | Nowy zabieg produkcyjny |
| XLProdDodajPauze / Zmien / Zakoncz | CRUD | Przestoje produkcyjne |
| XLRejestrujPominiecieOperacji | Create | Rejestracja pominięcia |

### Kontrola jakości (13)
| Funkcja | Typ | Opis |
|---|---|---|
| XLNowyParametrKJ | Create | Parametr kontroli |
| XLNowyWzorzecKJ | Create | Wzorzec KJ |
| XLNowyDokumentPKJ | Create | Dokument kontroli |
| XLGenerujPKJDlaObiektow | Process | Auto-generowanie KJ |
| XLZmienWynikKJDlaParametru | Update | Wynik kontroli |
| XLOdblokujDostaweNaPKJ / XLZablokujDostaweNaPKJ | Process | Blokada/zwolnienie dostaw |

---

## Grupa 8: LOGISTYKA — Paczki i Wysyłki (12 funkcji)

| Funkcja | Typ | Opis |
|---|---|---|
| XLNowaPaczka | Create | Nowa paczka |
| XLDodajDokumentDoPaczki / Usun | CRUD | Dokumenty w paczce |
| XlOtworzPaczke / XLZamknijPaczke | Read/Update | Zarządzanie paczką |
| XLNowaWysylka | Create | Nowa wysyłka |
| XLDodajPaczkeDoWysylki / Usun | CRUD | Paczki w wysyłce |
| XLDodajKosztDoWysylki / Usun | CRUD | Koszty wysyłki |
| XLOtworzWysylke / XLZamknijWysylke | Read/Update | Zarządzanie wysyłką |

---

## Grupa 9: KSIĘGOWOŚĆ I FINANSE (15 funkcji)

| Podgrupa | Funkcje | Opis |
|---|---|---|
| Dekrety księgowe (6) | XLDodajDekret*, XLZamknijDekret*, XLKasujDekret | Zapisy na kontach |
| Bilans otwarcia (6) | XLNowyDokumentBO, XLDodajPozycjeBO... | BO na początek roku |
| Rozliczenia (2) | XLRozliczaj, XLKasujRozliczenie | Rozliczanie płatności |
| Rozrachunki (1) | XLRozrachuj | Bilansowanie rozrachunków |
| Księgowanie (1) | XLKsiegujDokument | Dekretacja automatyczna |
| Noty memoriałowe (5) | XLDodajNote, XLDodajPozycjeNoty... | Noty |

---

## Grupa 10: SERWIS I NAPRAWY (27 funkcji)

### Serwis podstawowy (4)
XLNoweZlecenieSR, XLDodajPozycjeZleceniaSR, XLZamknijZlecenieSR, XLOtworzZlecenieSR

### Serwis zaawansowany — Nowy Serwis (23)
Urządzenia, czynności, części zamienne, parametry, przeglądy.

---

## Grupa 11: KSeF — e-Faktury (14 funkcji)

| Funkcja | Typ | Opis |
|---|---|---|
| XLKSeFOtworzSesje | Connect | Otwarcie sesji KSeF |
| XLKSeFZamknijSesje | Connect | Zamknięcie sesji |
| XLKSeFUwierzytelnienie | Auth | Uwierzytelnienie |
| XLKSeFDodajDokumentyDoWyslania | Create | Dodanie do kolejki |
| XLKSeFWyslijDokumenty | Process | Wysyłka do KSeF |
| XLKSeFPobierzUPO | Read | Pobranie UPO |
| XLKSeFPobierzDokumenty | Read | Pobranie dokumentów |
| XLKSeFUstalStatusDokumentu | Read | Sprawdzenie statusu |
| XLKSeFZmienStatusDokumentu | Update | Zmiana statusu |
| XLKSeFUsunStatusDokumentu | Delete | Usunięcie statusu |
| XLKSeFSpinajZDokumentem | Update | Powiązanie z dokumentem |
| XLKSeFRozlaczZDokumentem | Update | Odpięcie |
| XLKSeFDodajKntDoImportu | Create | Import kontrahenta |
| XLKSeFSprawdzCzyIstniejeFaktura | Read | Czy faktura istnieje |

---

## Grupa 12: POZOSTAŁE

| Podgrupa | Funkcje | Opis |
|---|---|---|
| Atrybuty (7) | XLDodajAtrybut, XLAtrNowaKlasa... | Cechy towarów/dokumentów |
| Promocje (9) | XLNowaPromocja, XLDodajKontrahentaDoPromocji... | Zarządzanie promocjami |
| Receptury (3) | XLNowaReceptura, XLDodajSkladnikReceptury... | BOM |
| Leasing/UML (11) | XLNowyDokumentUML, XLDodajRateUML... | Umowy leasingowe |
| Środki trwałe (6) | XLNowySrt, XLDodajDokumentSrt... | Ewidencja ŚT |
| Rezerwacje (4) | XLDodajRezerwacje, XLDodajZasobDoRezerwacji... | Rezerwacje towarów |
| Inwentaryzacja (6) | XLNowyOdczytInw, XLDodajPozycjeOdczytuInw... | Spis z natury |
| Bony (2) | XLDodajBon, XLModyfikujBon | Karty podarunkowe |
| Opis analityczny (5) | XLNowyOpis, XLDodajLinieOpisu... | MPK/centra kosztów |
| Pracownicy (2) | XLNowyPracownik, XLNowyOperator | Kadry i operatorzy |

---

## Grupa 13: AI_ChatERP — GOTOWE ENDPOINTY DLA AGENTÓW (44 procedury SQL)

To najważniejsza warstwa dla naszego projektu — procedury SQL zaprojektowane
przez Comarch dla integracji z AI/chatbotami.

### Sprzedaż i analityka (10)
| Procedura | Typ | Opis |
|---|---|---|
| AI_ChatERP_PodajSprzedaz | Read | Sprzedaż per kontrahent/produkt |
| AI_ChatERP_PodajNajwiecejSprzedawane | Read | Bestsellery |
| AI_ChatERP_PodajNajwiecejKupowane | Read | Najczęściej kupowane |
| AI_ChatERP_PodajWzrostSprzedazyNarastajaco | Read | Trend sprzedaży |
| AI_ChatERP_PodajTowaryNajwyzszaWartoscSprzedazy | Read | Najwyższy obrót |
| AI_ChatERP_PodajTowaryNajnizszaWartoscSprzedazy | Read | Najniższy obrót |
| AI_ChatERP_PodajKupcow | Read | Lista kupców |
| AI_ChatERP_PodajNajwiekszychOdbiorcow | Read | Top odbiorcy |
| AI_ChatERP_PodajNajwiekszychDostawcow | Read | Top dostawcy |
| AI_ChatERP_PodajNajtanszegoDostawce | Read | Najtańszy dostawca towaru |

### Kontrahenci i ryzyko (10)
| Procedura | Typ | Opis |
|---|---|---|
| AI_ChatERP_PodajDaneKontrahenta | Read | Dane kontrahenta (NIP, tel, email) |
| AI_ChatERP_PodajDaneOsobyKontrahenta | Read | Osoby kontaktowe |
| AI_ChatERP_PodajStanKontrahenta | Read | Saldo rozrachunków |
| AI_ChatERP_PodajRabatKontrahenta | Read | Rabaty |
| AI_ChatERP_PodajPromocjeKontrahenta | Read | Aktywne promocje |
| AI_ChatERP_PodajNajwiekszychDluznikow | Read | Top dłużnicy |
| AI_ChatERP_PodajNajwiekszychWierzycieli | Read | Top wierzyciele |
| AI_ChatERP_PodajPrzeterminowaneFaktury | Read | Przeterminowane FV |
| AI_ChatERP_PodajKwoteZaleglychPlatnosciKnt | Read | Kwota zaległości |
| AI_ChatERP_PodajPozostalyLimitKredytowyDlaKnt | Read | Dostępny limit |

### Towary i magazyn (6)
| Procedura | Typ | Opis |
|---|---|---|
| AI_ChatERP_PodajCeneTowaru | Read | Cena netto/brutto/marża |
| AI_ChatERP_PodajDostepnaIloscTowaru | Read | Dostępna ilość na magazynie |
| AI_ChatERP_PodajZalegajaceTowary | Read | Towary zalegające |
| AI_ChatERP_PodajZalegajaceTowaryNaMagazynie | Read | Zalegające per magazyn |
| AI_ChatERP_PodajZamiennikiTowaru | Read | Zamienniki |
| AI_ChatERP_PodajPromocjeTowaru | Read | Promocje na towar |

### Produkcja i zamówienia (8)
| Procedura | Typ | Opis |
|---|---|---|
| AI_ChatERP_PodajZPDoZamkniecia | Read | Zlecenia do zamknięcia |
| AI_ChatERP_PokazZPZaplanowaneNaDzien | Read | Plan produkcji na dzień |
| AI_ChatERP_PodajZPZBrakami | Read | Zlecenia z brakami |
| AI_ChatERP_PodajNiezrealizowaneZamowieniaPrzeterminowane | Read | Zaległe zamówienia |
| AI_ChatERP_PodajOstaniePNZDlaKnt | Read | Ostatnie PNZ kontrahenta |
| AI_ChatERP_PodajOstatnioDodanePNZ | Read | Nowe PNZ |
| AI_ChatERP_PodajUruchomioneOperacje | Read | Uruchomione operacje |
| AI_ChatERP_PodajZrealizowaneOperacje | Read | Zrealizowane operacje |

### Informacje o dokumentach (4)
| Procedura | Typ | Opis |
|---|---|---|
| AI_ChatERP_PodajInfoODokumencie | Read | Szczegóły dokumentu |
| AI_ChatERP_PodajNajczesciejUzywaneTP | Read | Najczęstsze technologie |
| AI_ChatERP_PodajOstatnioModyfikowaneTP | Read | Ostatnio zmieniane tech. |
| AI_ChatERP_SprawdzUprawnienia | Read | Sprawdzenie uprawnień operatora |

### Operacje WRITE (6)
| Procedura | Typ | Opis |
|---|---|---|
| AI_ChatERP_UstawLimitKredytowyDlaKnt | Write | Ustawienie limitu kredytowego |
| AI_ChatERP_UstawNieograniczonyLimitKredytowyDlaKnt | Write | Limit nieograniczony |
| AI_ChatERP_UstawDozwolonePrzeterminowaniePlatnosciDlaKnt | Write | Dozwolone opóźnienie |
| AI_ChatERP_WstrzymajTransakcjeDlaKontrahenta | Write | Blokada transakcji |
| AI_ChatERP_WstrzymajTransakcjeZDluznikamiIlosc | Write | Blokada wg ilości |
| AI_ChatERP_WstrzymajTransakcjeZDluznikamiKwota | Write | Blokada wg kwoty |
| AI_ChatERP_UstawOpeWyrazilZgodeNaRODO | Write | Zgoda RODO |

---

## Grupa 14: AI_PP — PROGNOZOWANIE POPYTU (6 procedur SQL)

| Procedura | Typ | Opis |
|---|---|---|
| AI_PP_PobierzModel | Read | Pobranie modelu ML |
| AI_PP_PobierzCenyTowarow | Read | Dane treningowe — ceny |
| AI_PP_PobierzIlosciTowarow | Read | Dane treningowe — ilości |
| AI_PP_PobierzParametryTowarow | Read | Parametry towarów |
| AI_PP_ZalogujOperacje | Write | Log operacji |
| AI_PP_ZapiszPrognoze | Write | Zapis prognozy |

---

## Grupa 15: NARZĘDZIA I DIAGNOSTYKA (16 funkcji)

| Funkcja | Typ | Opis |
|---|---|---|
| XLOpisBledu | Read | Opis błędu po kodzie |
| XLPobierzNumerDokumentu | Read | Następny numer dokumentu |
| XLPobierzIloscZdarzen | Read | Liczba zdarzeń |
| XLPobierzZdarzenie | Read | Szczegóły zdarzenia |
| XLPolaczenie | Diag | Test połączenia |
| XLSprawdzKluczHasp | Diag | Sprawdzenie klucza licencji |
| XLSprawdzLicencje | Diag | Dostępne moduły |
| XLPrzeliczRabat | Process | Kalkulacja rabatu |
| XLZmianaKontekstuOperatora | Auth | Zmiana operatora |
| XLZmienHaslo | Auth | Zmiana hasła |
| XLTransakcja | Process | Begin/commit transakcji |
| XLUruchomFormatkeWgGID | UI | Otwarcie formatki po GID |
| XLWykonajPodanyWydruk | Process | Wydruk |
| XLWykonajZapytanie | Process | Wykonanie dowolnego zapytania |
| XLNowyRachunek | Create | Nowy rachunek bankowy |

---

## Priorytetyzacja dla automatyzacji CEiM

### Szybkie wygrane (AI_ChatERP — gotowe do użycia)
1. Sprawdzanie cen i stanów magazynowych
2. Analiza sprzedaży i trendów
3. Monitoring dłużników i zaległości
4. Zarządzanie limitami kredytowymi

### Średni termin (Core API — wymaga wrappera .NET)
1. Automatyczne tworzenie dokumentów handlowych (FV, PZ, WZ)
2. Zarządzanie zamówieniami
3. Aktualizacja cenników
4. KSeF — pełna automatyzacja e-faktur

### Długi termin (Produkcja + Logistyka)
1. Planowanie produkcji i realizacja zleceń
2. Kontrola jakości
3. Logistyka — paczki i wysyłki
4. Prognozowanie popytu (ML)
