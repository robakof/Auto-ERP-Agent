# Notatki Developera dla ERP Specialist

Kanał odgórny: Developer → ERP Specialist.
Wytyczne, korekty, obserwacje które ERP Specialist powinien uwzględnić w swojej pracy.

ERP Specialist czyta ten plik na starcie każdej sesji (po załadowaniu ERP_SPECIALIST.md).
Developer dopisuje wpisy po odkryciu błędów lub wzorców w trakcie prac developerskich.

---

## Aktywne

### 2026-03-11 — TrN_TypNumeracji nie istnieje w CDN.TraNag

ERP_SCHEMA_PATTERNS.md sekcja "Prefiks dokumentu" zawiera błąd:
używa `n.TrN_TypNumeracji IN ('FSK','FZK','PAK','FKE')` — ta kolumna nie istnieje (Msg 207).

Poprawne podejście (zweryfikowane w Rozrachunki.sql): `TrN_GIDTyp IN (2041, 1529, 2042, 2045)`.

Do czasu korekty ERP_SCHEMA_PATTERNS.md (wymaga zatwierdzenia Developera):
używaj `TrN_GIDTyp IN (lista numeryczna)` zamiast `TrN_TypNumeracji IN (lista akronimów)`.

Mapowanie akronimów → GIDTyp: `solutions/reference/numeracja_wzorce.tsv` kolumna GIDTyp.

---

### 2026-03-11 — (Z) = korekta zbiorcza rabatowa (spinacz), nie Stan & 2

Źródło: research Comarch + analiza TrN_SpiTyp/TrN_SpiNumer.

**(Z)FSK / (Z)FKE / (Z)FZK to korekty zbiorcze rabatowe** — dokumenty do których
są "spięte" dokumenty WZK/WKE/PZK przez mechanizm spinacza.
NIE oznacza "anulowania korekty" ani nie wynika z TrN_Stan & 2 = 2.

Wcześniejsza obserwacja (FSK Stan=6, GenDokMag=-1 → (s)FSK) była prawidłowa ale
niepełna: ten dokument nie miał spinacza, więc GenDokMag=-1 wygrał → (s).
Dla FSK z spinaczem WZK → wynik byłby (Z).

**Prawidłowa kolejność CASE (do wdrożenia w ERP_SCHEMA_PATTERNS.md):**

```sql
CASE
    WHEN t.TrN_GIDTyp IN (2041, 2045, 1529)
         AND EXISTS (
             SELECT 1 FROM CDN.TraNag s
             WHERE s.TrN_SpiTyp   = t.TrN_GIDTyp
               AND s.TrN_SpiNumer = t.TrN_GIDNumer
               AND (
                    (t.TrN_GIDTyp = 2041 AND s.TrN_GIDTyp = 2009) OR  -- (Z)FSK <- WZK
                    (t.TrN_GIDTyp = 2045 AND s.TrN_GIDTyp = 2013) OR  -- (Z)FKE <- WKE
                    (t.TrN_GIDTyp = 1529 AND s.TrN_GIDTyp = 1497)     -- (Z)FZK <- PZK
               )
         )
    THEN '(Z)'
    WHEN t.TrN_Stan & 2 = 2
         AND t.TrN_GIDTyp IN (2041, 2045, 1529)
    THEN '(Z)'   -- fallback heurystyczny
    WHEN t.TrN_GenDokMag = -1
         AND t.TrN_GIDTyp IN (1521, 1529, 1489)
    THEN '(A)'
    WHEN t.TrN_GenDokMag = -1
    THEN '(s)'
    ELSE ''
END
```

**Stopień pewności:** EXISTS (spinacz) — wysoki (udokumentowane w Comarch).
Stan & 2 = 2 jako fallback — średni (heurystyka, niezweryfikowana w źródle).

Do zatwierdzenia przez Developera przed edycją ERP_SCHEMA_PATTERNS.md (plik chroniony).

---

## Archiwum

