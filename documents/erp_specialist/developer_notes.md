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

## Archiwum

