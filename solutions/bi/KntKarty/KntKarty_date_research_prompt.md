# Research: formaty dat w bazie Comarch ERP XL (Clarion)

## Kontekst

Pracuję z bazą SQL Server systemu Comarch ERP XL (wersja polska, baza ERPXL_CEIM).
System ERP XL jest oparty na środowisku Clarion — przechowuje daty jako liczby całkowite
w co najmniej dwóch formatach:

**Potwierdzony FORMAT A — Clarion DATE:**
- Liczba dni od 1800-12-28
- Zakres dla dat bieżących: ~70 000–100 000
- Konwersja SQL: `DATEADD(d, col, '18001228')`
- Przykłady z bazy: 70316, 81239, 82156, 82184

**Potwierdzony FORMAT B — Clarion TIMESTAMP:**
- Liczba sekund od 1990-01-01
- Zakres: ~10^9
- Konwersja SQL: `DATEADD(ss, col, '1990-01-01')`
- Przykłady z bazy: 1047823554, 1141724389

## Problem

W tabeli `CDN.KntKarty` pole `Knt_EFaVatDataDo` (Data ważności dla elektronicznego
przesyłania faktur VAT) ma wartości w zakresie **81169–150483**.

- Wartość 81169 → Format A → `1800-12-28 + 81169 dni` = ok. 2022-05-xx ✓ (sensowna)
- Wartość **150483** → Format A → `1800-12-28 + 150483 dni` = ok. **rok 2213** ✗ (podejrzane)

Pytania do wyjaśnienia:

1. **Czy w Comarch ERP XL / Clarion istnieje konwencja sentinel value** dla "data bez ograniczenia"
   (bezterminowo)? Jeśli tak — jaka to wartość i jak ją interpretować w SQL?

2. **Czy istnieje trzeci format daty** używany przez Comarch ERP XL — inne niż Clarion DATE
   i Clarion TIMESTAMP? Np. format oparty na innej epoce lub innej jednostce?

3. **Jak w dokumentacji Comarch ERP XL opisany jest format pola datowego** dla tabel takich
   jak KntKarty, ZamNag, TraNag — czy wszystkie pola INT/SMALLINT zawierające daty
   używają tych samych dwóch formatów?

4. **Czy wartość 150483 w kontekście daty ważności e-Faktury VAT** ma znane znaczenie?
   (Np. czy jest to standardowy sentinel w implementacji Comarch dla "ważne bezterminowo"?)

## Czego szukać

- Dokumentacja Clarion (TopSpeed/SoftVelocity): formaty przechowywania dat, sentinel values
- Forum Comarch: wątki o konwersji dat z bazy ERP XL do SQL
- Baza wiedzy Comarch / dokumentacja techniczna CDN.KntKarty lub podobnych tabel
- Artykuły o integracji Comarch ERP XL z SQL Server / Power BI / raportami

## Oczekiwany wynik

Odpowiedź powinna zawierać:
1. Wzorzec SQL do konwersji dla każdego zidentyfikowanego formatu
2. Sposób obsługi sentinel value (jeśli istnieje) — np. `CASE WHEN col > 130000 THEN NULL ELSE DATEADD(...)`
3. Źródło (link lub nazwa dokumentu)

Jeśli nie znajdziesz pewnej odpowiedzi — podaj najlepszą hipotezę z uzasadnieniem,
żebym mógł ją zweryfikować przez SELECT na realnych danych.
