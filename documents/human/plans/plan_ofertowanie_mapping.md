# Plan: Projekt Ofertowanie — mapowanie kolumn z ERP

Data: 2026-03-27

## Cel

Eksport produktów z ERP Comarch XL do Excel z kolumnami zdefiniowanymi przez użytkownika.
Plik Excel ma być źródłem danych do dalszego ofertowania (cenniki, PDF, itp.).

---

## Mapowanie kolumn — status

### ✓ Potwierdzone — można pobrać z ERP

| Kolumna | Źródło | Tabela / AtK_ID |
|---|---|---|
| Nazwa | Twr_Nazwa | CDN.TwrKarty |
| Kod EAN | Twr_Ean | CDN.TwrKarty |
| CZAS PALENIA / DZIAŁANIA | Atr_Wartosc | CDN.Atrybuty, AtK_ID=9 |
| GRAMATURA WKŁADU | Atr_Wartosc | CDN.Atrybuty, AtK_ID=10 |
| SZEROKOŚĆ NETTO PRODUKTU | Atr_Wartosc | CDN.Atrybuty, AtK_ID=11 |
| WYSOKOŚĆ NETTO PRODUKTU | Atr_Wartosc | CDN.Atrybuty, AtK_ID=12 |
| SZEROKOŚĆ BRUTTO OPAKOWANIA | Atr_Wartosc | CDN.Atrybuty, AtK_ID=13 |
| opak. | TwJ_PrzeliczL | CDN.TwrJM, JmZ='opak.' |
| karton | TwJ_PrzeliczL | CDN.TwrJM, JmZ='karton' |
| warstwa | TwJ_PrzeliczL | CDN.TwrJM, JmZ='warstwa'|
| paleta | TwJ_PrzeliczL | CDN.TwrJM, JmZ='paleta' |
| Cena 100 | TwC_Wartosc | CDN.TwrCeny, TwC_TcnId=1 |
| ZAKUP | TwZ_KsiegowaNetto/TwZ_Ilosc | CDN.TwrZasoby (ostatnia cena) |

### ✓ Obliczane w Python (nie z bazy ERP)

| Kolumna | Logika |
|---|---|
| Zdjęcie | Nazwa pliku z katalogu D:\UdzialySieciowe\ZDJECIA\...\{Kod}.jpg/.png |
| Czy zdjęcie załadowane do systemu | os.path.exists({Kod}.jpg lub .png) → Tak/Nie |
| Czy zdjęcie zrobione png | os.path.exists({Kod}.png) → Tak/Nie |

---

## Pytania do użytkownika — WYMAGANE przed implementacją

### 1. Akronim vs Kod — co to za różnica?

W bazie ERP jest jedna kolumna `Twr_Kod` (np. "CWKZ0041").
W liście kolumn masz zarówno **Akronim** jak i **Kod** — co oznacza każde z nich?

- Czy Akronim = prefiks Twr_Kod (np. "CWKZ")?
- Czy Kod = pełny Twr_Kod (np. "CWKZ0041")?
- Czy to dwa różne pola z ERP?

### 2. Transport TIR, Transport paleta, Konfekcja

Brak tych pól w bazie ERP:
- Nie ma ich w atrybutach towarów (CDN.AtrybutyKlasy — sprawdzone wszystkie 57 atrybutów).
- Nie ma ich w CDN.TwrKarty.

Skąd mają pochodzić dane?
- Czy to nowe atrybuty do dodania w ERP?
- Czy obliczane na podstawie istniejących danych (np. z wymiarów/wagi)?
- Czy uzupełniane ręcznie w Excelu?

### 3. Marża — jak liczyć?

Wzór marży zależy od definicji. Proponowane opcje:
- `(Cena_100 - Zakup) / Cena_100 * 100%`
- `(Cena_100 - Zakup) / Zakup * 100%` (narzut)
- Inny wzór?

Który cennik traktujemy jako "cena sprzedaży" do liczenia marży?

### 4. Cena max upust i Cena upust — który cennik?

Mamy 65 cenników w systemie (CDN.TwrCenyNag). Które TCN_Id odpowiadają:
- **Cena max upust** = ?
- **Cena upust** = ?

Główne cenniki w systemie:
```
TCN_Id=1   → CENA 100
TCN_Id=2   → CMENTARZ
TCN_Id=7   → FRANOWO
TCN_Id=8   → BRICO
TCN_Id=9   → INTER
TCN_Id=10  → MRÓWKA
```

---

## Proponowana architektura skryptu

Plik: `tools/ofertowanie_export.py`

1. Pobiera wszystkie aktywne towary (Twr_Archiwalny=0) LUB tylko z wybranej grupy
2. Jedno zapytanie SQL z JOINami do TwrJM + Atrybuty + TwrCeny
3. Sprawdza zdjęcia przez os.path
4. Eksportuje do Excel przez openpyxl
5. Kolumny odporne na zmianę kolejności (mapowanie po nazwie)

---

## Zakres potrzebny od użytkownika

Czy eksport ma obejmować:
- [ ] Wszystkie aktywne towary
- [ ] Tylko towary z określonej grupy (TwrGrupy)
- [ ] Tylko towary z aktywnym statusem ofertowym (AtK_ID=59)
