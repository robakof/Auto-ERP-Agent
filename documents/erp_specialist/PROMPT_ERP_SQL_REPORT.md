# Prompt dla ERP Specialist — raport SQL do automatyzacji wysyłek JAS

---

## Kontekst

Budujemy system automatycznego zlecania wysyłek do spedytora JAS na podstawie zatwierdzonych dokumentów WZ z ERP XL. System działa w pętli co 30 sekund: odpytuje bazę ERP o nowe zatwierdzone WZ, pobiera ich dane, przekazuje do agenta AI który interpretuje opis i ustala datę dostawy, a następnie automatycznie składa zlecenie w API JAS.

Potrzebujemy zapytania SQL (widok lub procedura składowana), które zwróci wszystkie dane potrzebne do tego procesu.

---

## Warunki filtrowania

| Kryterium | Wartość |
|-----------|---------|
| Status dokumentu | tylko `Zatwierdzone` |
| Magazyn źródłowy | tylko **Buszewo** — wszystkie pozostałe magazyny odrzucamy (w tym AUCHAN, korekty WZK, inne oddziały) |

---

## Wymagane pola

### Identyfikacja WZ

| Pole | Opis |
|------|------|
| `numer_wz` | Numer dokumentu WZ (np. WZ-3/01/26/SPKR) |
| `data_wystawienia` | Data utworzenia dokumentu WZ |
| `data_sprzedazy` | Planowana data wysyłki z magazynu |
| `opis` | Notatka handlowca — może być pusta |

### Adres dostawy (z karty klienta / nagłówka WZ)

Używany jako domyślny adres odbiorcy gdy opis nie wskazuje innego adresu.

| Pole | Opis |
|------|------|
| `odbiorca_nazwa` | Nazwa firmy lub klienta |
| `odbiorca_ulica` | Ulica |
| `odbiorca_nr_domu` | Numer domu |
| `odbiorca_kod_pocztowy` | Kod pocztowy (format: XX-XXX) |
| `odbiorca_miasto` | Miasto |
| `odbiorca_kraj` | Kraj (domyślnie PL) |

### Pozycje cargo (opakowania)

Każda pozycja WZ to osobna paczka w zleceniu JAS. Potrzebujemy dla każdej pozycji:

| Pole | Opis |
|------|------|
| `typ_opakowania` | Typ opakowania w formacie JAS: `EPN`, `EFN`, `MB`, `PPN`, `KRT` lub odpowiednik z ERP |
| `ilosc` | Liczba sztuk danego typu |
| `dlugosc_cm` | Długość w cm |
| `szerokosc_cm` | Szerokość w cm |
| `wysokosc_cm` | Wysokość w cm |
| `waga_kg` | Waga w kg |

---

## Uwagi

- Jeśli jeden WZ ma wiele pozycji cargo — zwracamy wiele wierszy (jeden wiersz = jedna pozycja), pola nagłówkowe WZ powtarzają się.
- Jeśli ERP przechowuje typy opakowań inaczej niż kody JAS (`EPN`, `EFN`, `MB`, `PPN`, `KRT`) — prosimy o mapowanie lub o informację jakie wartości są dostępne, ustalimy mapowanie wspólnie.
- Wymiary i waga: jeśli ERP ich nie przechowuje na poziomie pozycji WZ — prosimy o informację; ustalimy podejście (np. dane z karty towaru).
- Kod magazynu Buszewo w ERP XL — prosimy o potwierdzenie dokładnej wartości używanej w bazie.

---

## Format odpowiedzi

Prosimy o:
1. Zapytanie SQL zwracające opisane pola
2. Potwierdzenie nazw tabel z których korzysta zapytanie
3. Informację o ewentualnych brakujących polach (np. brak wymiarów w ERP)

---

## Przykładowy oczekiwany wynik (jeden WZ, jedna pozycja)

| numer_wz | data_wystawienia | data_sprzedazy | opis | odbiorca_nazwa | odbiorca_miasto | ... | typ_opakowania | ilosc | waga_kg |
|----------|-----------------|----------------|------|----------------|-----------------|-----|----------------|-------|---------|
| WZ-3/01/26 | 2026-01-07 | 2026-01-07 | null | Sklep XYZ | Warszawa | ... | EPN | 1 | 25 |
