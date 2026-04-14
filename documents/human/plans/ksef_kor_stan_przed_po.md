# Plan: KSeF KOR — model StanPrzed/StanPo

**Data:** 2026-04-14
**Owner:** Developer
**Powód:** KSeF odrzuca obecny XML ("plik zawiera błąd"). Generator produkuje wiersze różnicowe (jeden `<FaWiersz>` per pozycja z samą różnicą), a FA(3) dla korekt ilościowych/cenowych oczekuje modelu "przed/po" — dwa wiersze per pozycja (oryginał z `<StanPrzed>1</StanPrzed>` + stan po korekcie z `<P_6A>`).

Wzorzec: `documents/Wzory plików/korekta Bolsius example.xml` (SmartKSeF, przyjęty przez KSeF).

---

## Zakres

### 1. SQL — `solutions/ksef/ksef_fsk_draft.sql`
Dziś zwraca wiersze z TrN korekty (różnice). Musi zwrócić parę wierszy per pozycja:
- **StanPrzed:** dane z oryginału (ilość/cena/wartość przed korektą) — z TrN faktury korygowanej
- **StanPo:** dane po korekcie (oryginał + różnica z korekty)

Wymaga JOIN TrN (korekta) → TrN (oryginał) po relacji faktura↔korekta w Comarch XL.

**To nie jest moja domena — zadanie dla ERP Specialist.**

Input dla ERP Specialist:
- Kolumny do zwrócenia per wiersz: `Wiersz_NrPozycji, Wiersz_StanPrzed (0/1), Wiersz_DataKorekty (dla wierszy "po"), P_7_Nazwa, Indeks, PKWiU, P_8A_JM, P_8B_Ilosc, P_9B_CenaBrutto, P_11A_WartoscNetto, P_11Vat, P_12_StawkaVAT`
- Pozostałe pola nagłówkowe — bez zmian (już działają)

### 2. Generator XML — `tools/ksef_generate_kor.py`

Funkcja `build_fa_wiersze(fa, rows)`:
- dla każdej pozycji wygeneruj 2 elementy `<FaWiersz>`:
  - wiersz "przed": `<StanPrzed>1</StanPrzed>`, bez `<P_6A>`
  - wiersz "po": z `<P_6A>` (data korekty), bez `<StanPrzed>`

Zmiana pól wiersza (dostosowanie do FA(3) KOR):
| Było (nasz)     | Ma być            |
|-----------------|-------------------|
| `P_9A` (netto)  | `P_9B` (brutto)   |
| `P_11` (netto)  | `P_11A`           |
| —               | `P_11Vat`         |
| —               | `Indeks` (opt.)   |
| —               | `PKWiU` (opt.)    |

Funkcja `build_fa_korekta`:
- Usunąć `<TypKorekty>2</TypKorekty>` (Bolsius go nie dodaje; KSeF przy StanPrzed nie wymaga). Docelowo zweryfikować XSD.
- `<NrKSeFN>1</NrKSeFN>` zostaje (oryginały poza KSeF).

### 3. Testy — `tests/test_ksef_generate_kor.py`
Update pod nowy schemat danych (2 wiersze per pozycja, nowe nazwy pól).

### 4. Walidacja end-to-end
- Wygenerować XML dla konkretnej korekty ilościowej (user wskaże GID).
- Walidacja XSD `output/schemat_FA3.xsd` = PASS.
- Wysyłka do KSeF sandbox/prod = accepted.

---

## Kolejność prac

1. **Developer → ERP Specialist:** handoff z opisem wymaganej struktury SQL (kolumny powyżej).
2. **ERP Specialist:** nowy SQL, testuje na próbce, commit.
3. **Developer:** refaktor `build_fa_wiersze` + `build_fa_korekta` pod nowe kolumny.
4. **Developer:** update testów.
5. **Walidacja:** XSD + próba w KSeF.

## Ryzyka

- SQL join korekta↔oryginał w Comarch XL może być nietrywialny (różne ścieżki: TrN_KorektaDoId? Elementy.ElK_ZrodloId?). ERP Specialist rozstrzygnie.
- Próbka Bolsius ma `P_9B` (brutto) — w ERP XL cena jednostkowa dla FSK netto vs brutto może wymagać przeliczenia. Do ustalenia z ERP Specialist.
- `TypKorekty` — jeśli XSD wymaga, zostawiamy. Próbka Bolsius nie ma, więc chyba nie — potwierdzić przez walidację XSD po zmianach.

## Otwarte pytania do usera

- Czy jest próbka Waszej korekty która **przeszła** już KSeF (inny wzorzec niż Bolsius)? Byłby lepszym targetem niż obcy XML.
- NrKSeFFaKorygowanej — trzymacie w ERP numery KSeF oryginałów? Jeśli tak — dodamy je zamiast `NrKSeFN=1`.
