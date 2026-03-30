# Architecture Review: planowanie_produkcji

Date: 2026-03-30
Status: NEEDS REVISION
Code maturity level: L2 Mid — kod lokalnie poprawny, ale brak design na poziomie modułu.
Chaotyczny rozrost bez spójnego planu.

---

## Summary

**Overall assessment: NEEDS REVISION**

Projekt składa się z 4 artefaktów które nie tworzą spójnej całości:
- `tools/planowanie_produkcji.py` — CLI eksport do Excel
- `solutions/erp_specialist/planowanie_produkcji_zamowienia_niepotwierdzone.sql` — zamówienia ZaN_Stan=2
- `solutions/erp_specialist/planowanie_produkcji_stany_mag_otorowo_surowce.sql` — stany surowców (ORPHANED)
- `tmp/test_planowanie_produkcji.py` — testy poza suite'm

Fundamentalny problem: **cel modułu (planowanie produkcji = zamówienia vs stany) nie jest zaimplementowany.**
Mamy narzędzie eksportu zamówień, a nie planowanie produkcji.

---

## Findings

### Critical Issues (must fix)

#### C1. Duplikacja filtrów: SQL + Python — naruszenie Single Source of Truth

SQL (`planowanie_produkcji_zamowienia_niepotwierdzone.sql`) ma w WHERE:
```sql
AND ze.ZaE_TwrKod LIKE 'CZNI%'
AND CAST(op.ZnO_Opis AS NVARCHAR(500)) LIKE 'Zamówienie%'
```

Python (`filter_rows()`) powtarza te same filtry:
```python
if not (r.get("Towar_Kod") or "").startswith("CZNI"):  # już w SQL
    continue
if not opis.startswith("Zamówienie"):                   # już w SQL
    continue
```

**Efekt:** Dwa miejsca definiują tę samą regułę. Zmiana w SQL nie zmieni Pythona i odwrotnie.
Dopuszczalny byłby tylko filtr roku (który faktycznie jest tylko w Pythonie — SQL ma go zakomentowanego).

**Fix:** Usuń z `filter_rows()` filtry Towar_Kod i Opis. Zostaw tylko filtr roku.

---

#### C2. Testy w `tmp/` — poza suite'm, nie są uruchamiane

Plik `tmp/test_planowanie_produkcji.py` zawiera 5 solidnych testów filtrów.
`tmp/` to scratch — testy tam nie są częścią `pytest tests/`.
**Skutek:** Zero coverage w CI, ktoś zmieni logikę, testy nie zareagują.

**Fix:** Przenieść do `tests/test_planowanie_produkcji.py`. Usunąć z `tmp/`.

---

### Warnings (should fix)

#### W1. Orphaned SQL — stany magazynowe bez integracji

`planowanie_produkcji_stany_mag_otorowo_surowce.sql` istnieje, ma komentarz
"Developer używa tego jako drugiego wejścia" — ale żaden kod Python go nie wczytuje.
To dead artifact. Albo integracja z Python, albo jawna decyzja "to osobny raport".

**Fix:** Decyzja: (a) zintegrować z CLI jako drugi arkusz / komenda, (b) udokumentować jako
standalone SQL bez integracji, (c) usunąć jeśli niepotrzebny.

---

#### W2. Brak workflow — process ad-hoc

Nie istnieje `workflows/workflow_planowanie_produkcji.md`.
Komentarz w SQL mówi "Developer filtruje dalej wg potrzeb" — to nie jest workflow.
Każda sesja odkrywa reguły na nowo. Dlatego jest chaos.

**Fix:** PE formalizuje workflow. Architect definiuje kontrakt modułu (patrz W3).

---

#### W3. Cel modułu nie jest zaimplementowany

"Planowanie produkcji" semantycznie oznacza: **co produkować** = zamówienia CZNI (popyt) vs stany surowców (podaż).
Obecne narzędzie robi tylko **eksport zamówień**. Stany surowców istnieją w SQL ale nie są połączone.

Brakująca logika:
- Która pozycja z zamówień ma wystarczające surowce?
- Które surowce są brakujące (gap = demand - stock)?
- Priorytetyzacja produkcji

To nie jest bug — to niedomknięta funkcjonalność. Ale dopóki tego nie ma,
moduł powinien nazywać się "eksport_zamowien_czni", nie "planowanie_produkcji".

**Fix (krótkoterminowy):** Rename lub rename komentarza. Nie nazywaj eksportu planowaniem.
**Fix (docelowy):** Zintegrować stany surowców jako drugi arkusz lub tabelę porównawczą.

---

### Suggestions (nice to have)

#### S1. Rok filtru powinien być w SQL, nie tylko w Pythonie

Komentarz w SQL: `-- filtr roku: po stronie Developera`. Ale filtr w SQL (zakomentowany) istnieje.
Lepiej: SQL przyjmuje parametr `{year}` i filtruje na bazie — mniejszy transfer danych.
Aktualnie pobieramy ~1022 pozycji i filtrujemy rok w Pythonie.

#### S2. `output/planowanie/` akumuluje pliki bez retencji

Każde uruchomienie dodaje nowy plik z datą. Brak mechanizmu czyszczenia.
Przy codziennym użyciu: 365 plików rocznie.

---

## Root Cause — skąd chaos

Moduł rósł inkrementalnie bez design up-front:

```
ERP Specialist   → SQL zamówienia         (poprawny artefakt)
ERP Specialist   → SQL stany surowców     (poprawny artefakt, orphaned)
Developer        → Python CLI eksport     (ad-hoc, bez specyfikacji modułu)
Developer        → testy w tmp/           (scratch, nie suite)
```

Nie ma decyzji architektonicznej: co robi ten moduł, jakie ma wejścia/wyjścia,
co łączy SQL zamówień z SQL stanów. Każdy agent działał lokalnie — całość nie powstała.

---

## Recommended Actions

Priorytet 1 (Developer, natychmiast):
- [ ] Przenieść `tmp/test_planowanie_produkcji.py` → `tests/test_planowanie_produkcji.py`
- [ ] Usunąć z `filter_rows()` filtry Towar_Kod i Opis (zostaw rok) — SQL już je robi
- [ ] Uruchomić `pytest tests/test_planowanie_produkcji.py` — 5/5 PASS

Priorytet 2 (Architect + PE, ta sesja):
- [ ] Decyzja: co robimy ze stanami surowców (integracja / standalone / usunąć)
- [ ] PE formalizuje workflow dla tego modułu
- [ ] Zmiana nazwy: jeśli to eksport, nie planowanie — rename lub zmiana scope

Priorytet 3 (Developer, kolejna sesja):
- [ ] Jeśli integracja ze stanami: nowy CLI `--mode plan` = zamówienia + stany jako dwa arkusze
- [ ] Filtr roku przenieść do SQL (parametr `{year}`) — mniejszy transfer danych

---

## Architecture Decision Required

**Pytanie do użytkownika:**

Czy `planowanie_produkcji` ma docelowo:

**A)** Tylko eksport zamówień CZNI (obecna funkcjonalność — rename to "eksport_zamowien_czni")

**B)** Eksport zamówień + stany surowców jako dwa osobne arkusze w jednym pliku Excel
   (wymaga: integracji `planowanie_produkcji_stany_mag_otorowo_surowce.sql`)

**C)** Pełne planowanie: zamówienia vs stany → gap analysis → co brakuje do produkcji
   (wymaga: nowej logiki łączącej oba SQL + BOM jeśli dostępny)

Odpowiedź determinuje scope Developera.
