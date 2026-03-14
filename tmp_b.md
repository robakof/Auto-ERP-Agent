(Z) = korekta zbiorcza rabatowa (spinacz), nie Stan & 2

(Z)FSK / (Z)FKE / (Z)FZK to korekty zbiorcze rabatowe — dokumenty do których są "spięte"
dokumenty WZK/WKE/PZK przez mechanizm spinacza. NIE oznacza "anulowania korekty".

Prawidłowa kolejność CASE (do wdrożenia w ERP_SCHEMA_PATTERNS.md gdy zatwierdzone):

1. EXISTS (spinacz) → '(Z)' — wysoka pewność
2. Stan & 2 = 2 → '(Z)' — fallback heurystyczny, średnia pewność
3. GenDokMag = -1 AND GIDTyp IN zakup → '(A)'
4. GenDokMag = -1 → '(s)'

Szczegóły SQL: przekaż do Developera jeśli potrzebujesz pełnego CASE do zatwierdzenia.
