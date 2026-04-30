# xl_invoice — Architektura, PRD, Techstack

Moduł przyjmowania faktur zakupowych kosztowych surowcowych z KSeF XML do Comarch XL przez XL API.

---

## PRD — Wymagania produktowe

### 1. Wprowadzenie i cel

**Problem:** Ręczne wpisywanie faktur zakupowych od dostawców do ERP — czasochłonne, podatne na błędy.
**Rozwiązanie:** Automatyczny import z plików KSeF XML (FA(3)) do Comarch XL przez XL API.

**Input faza 1:** Katalog z plikami `.xml` od dostawców (format KSeF FA(3))
**Input faza 2:** Bezpośrednie połączenie z bazą KSeF (poza scope tej sesji)
**Output:** Faktury zakupowe kosztowe surowcowe (FZ-KS) w Comarch XL z pełnymi danymi

### 2. Użytkownicy

- Pracownicy biura (non-technical) — codzienne użycie, GUI
- Jeden katalog wejściowy plików XML od dostawców

### 3. Wymagania funkcjonalne

**F1 — Parser KSeF XML**
- Czyta pliki `.xml` z podanego katalogu (FA(3) format)
- Wyciąga: sprzedawca (NIP, nazwa), nabywca, nr faktury, data wystawienia, termin płatności,
  pozycje (nazwa, ilość, j.m., cena netto, stawka VAT, wartość VAT), suma netto, suma VAT, waluta

**F2 — Walidacja przed importem**
- Sprawdź czy kontrahent (NIP) istnieje w kartotece Comarch — jeśli nie: POMIŃ z komunikatem
- Sprawdź czy faktura o tym numerze obcym już istnieje — jeśli tak: POMIŃ (idempotentność)

**F3 — Tworzenie FZ w Comarch XL**
- XLNowyDokument → typ: FZ kosztowa surowcowa
- XLModyfikujNaglowek → nr dokumentu obcego, daty, kontrahent, termin
- XLDodajPozycje → każda pozycja faktury
- XLDodajVAT → stawki VAT
- XLZamknijDokument

**F4 — Przetwarzanie wsadowe**
- Przetwarza wszystkie pliki XML z katalogu
- Każdy plik = jedna faktura (lub błąd z opisem)

**F5 — Raport Excel**
- Plik `.xlsx` z wynikiem: plik, nr faktury, kontrahent, kwota, status (OK/BŁĄD/POMINIĘTO), komunikat

**F6 — GUI**
- Krok 1: Wybierz katalog z plikami XML
- Krok 2: Uruchom import
- Wynik: podsumowanie (dodanych / błędów / pominiętych) + przycisk "Otwórz raport"
- Ostrzeżenie: zamknij Comarch ERP przed uruchomieniem

### 4. Wymagania niefunkcjonalne

- Idempotentność: dwukrotne uruchomienie na tych samych plikach = brak duplikatów
- Brak danych hardcoded: ścieżki i config w `.env`
- Testy: każda funkcja z testem jednostkowym / integracyjnym
- Obsługa błędów: jeden błędny plik nie zatrzymuje przetwarzania pozostałych

### 5. Scope i ograniczenia

**W scope faza 1:**
- FZ kosztowe surowcowe
- Pliki XML z katalogu lokalnego
- Kontrahenci muszą istnieć w kartotece (brak auto-tworzenia)
- Waluta PLN (inne waluty: faza 2)

**Poza scope:**
- FZ kosztowe zwykłe (faza 2)
- Auto-tworzenie kontrahentów
- KSeF API (faza 2)
- Korekty faktur

### 6. Aspekty techniczne — otwarte pytania (→ eksperymenty)

- Jaka wartość `TrNTyp` dla `XLNowyDokument` tworzy FZ kosztową surowcową?
- Jakie pola `XLDodajPozycje` są wymagane dla pozycji kosztowej (brak towaru z kartoteki)?
- Jak podać kontrahenta przez XL API (GID czy kod NIP)?
- Czy `XLDodajVAT` jest wymagane czy obliczane automatycznie?

---

## Techstack

| Warstwa | Technologia | Uzasadnienie |
|---|---|---|
| Parser XML | `xml.etree.ElementTree` (stdlib) | Zero zależności, wystarczający dla FA(3) |
| XL API | XlProxy + XlClient (istniejące) | Gotowa infrastruktura, nie duplikujemy |
| Walidacja kontrahenta | SqlClient + CDN.Kontrahenci | Jak w xl_attribute_set.py |
| Raport | openpyxl (istniejące) | Spójność z atrybutami |
| GUI | tkinter (stdlib) | Spójność z xl_attribute_app.py |
| Config | python-dotenv + .env | Standard projektu |

---

## Architektura

### Struktura plików

```
tools/
  xl_invoice_parser.py      # KSeF XML → dataclass Invoice
  xl_invoice_set.py         # Invoice → XL API (jeden dokument)
  xl_invoice_bulk.py        # katalog XML → bulk + raport
  xl_invoice_app.py         # GUI (tkinter)
core/ksef/domain/
  invoice.py                # istniejący model (FS) — rozszerzymy lub dodamy FzInvoice
```

### Domain model

```python
@dataclass(frozen=True)
class FzInvoice:
    nr_obcy: str            # numer faktury dostawcy
    nip_sprzedawcy: str
    nazwa_sprzedawcy: str
    data_wystawienia: date
    termin_platnosci: date
    pozycje: list[FzPozycja]
    suma_netto: Decimal
    suma_vat: Decimal
    waluta: str             # PLN faza 1

@dataclass(frozen=True)
class FzPozycja:
    nazwa: str
    ilosc: Decimal
    jm: str
    cena_netto: Decimal
    wartosc_netto: Decimal
    stawka_vat: str         # "23", "8", "0", "ZW"
    wartosc_vat: Decimal
```

### Przepływ danych

```
katalog XML
    → xl_invoice_bulk.py (scan plików)
        → xl_invoice_parser.py (XML → FzInvoice)
        → xl_invoice_set.py (walidacja kontrahenta, check duplikatu, XL API)
            → XlClient.nowy_dokument(TrNTyp=FZ_KOSZTOWA_SUROWCOWA)
            → XlClient.invoke("XLModyfikujNaglowek", ...)
            → XlClient.dodaj_pozycje(...) × N
            → XlClient.invoke("XLDodajVAT", ...) × M stawek
            → XlClient.zamknij_dokument(...)
        → wynik per plik
    → raport Excel (openpyxl)
```

### Kamienie milowe

| M | Co | Zależność |
|---|---|---|
| M1 | xl_invoice_parser.py + testy | — |
| M2 | Eksperymenty XL API (TrNTyp, pola) | M1 |
| M3 | xl_invoice_set.py + testy | M2 |
| M4 | xl_invoice_bulk.py + raport | M3 |
| M5 | xl_invoice_app.py (GUI) | M4 |

---

## Wyniki eksperymentów (29.04.2026)

**E1 — TrNTyp dla FZ kosztowej surowcowej: ROZWIĄZANY**
- `XLNowyDokument`: Typ=1, Seria=ZSKR, RodzajZakupu=1
- FZ kosztowa zwykła: Typ=1, Seria=ZTHK, RodzajZakupu=1
- Epoch daty: liczba dni od 28 grudnia 1800 (ordinal 657433)
- Dla PLN: KursL/KursNr/KursM = puste
- TrybWsadowy=1 wymagane

**E2 — Pola XLDodajPozycje: ROZWIĄZANY**
- TowarNazwa wystarczy — nie trzeba TowarKod
- System auto-przypisuje kod "A-VISTA" dla pozycji bez towaru
- Wymagane: IDDokumentu, Ilosc, Cena, Vat, JmZ, TowarNazwa

**E3 — Identyfikacja kontrahenta: ROZWIĄZANY**
- KntTyp=32, KntFirma=1464833, KntNumer=Knt_GIDNumer z CDN.KntKarty
- Mapowanie NIP→GID: SELECT Knt_GIDNumer FROM CDN.KntKarty WHERE Knt_NIP=?

**E4 — XLDodajVAT: ROZWIĄZANY**
- Nie wymagane — VAT obliczany automatycznie przez ERP
