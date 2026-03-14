TrN_TypNumeracji nie istnieje w CDN.TraNag

ERP_SCHEMA_PATTERNS.md sekcja "Prefiks dokumentu" zawiera błąd:
używa `n.TrN_TypNumeracji IN ('FSK','FZK','PAK','FKE')` — ta kolumna nie istnieje (Msg 207).

Poprawne podejście (zweryfikowane w Rozrachunki.sql): `TrN_GIDTyp IN (2041, 1529, 2042, 2045)`.

Używaj `TrN_GIDTyp IN (lista numeryczna)` zamiast `TrN_TypNumeracji IN (lista akronimów)`.
Mapowanie: solutions/reference/numeracja_wzorce.tsv kolumna GIDTyp.
