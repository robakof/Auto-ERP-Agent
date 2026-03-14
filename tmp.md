Prośba o wdrożenie poprawki widoku AIBI.Rozrachunki

Plik solutions/bi/views/Rozrachunki.sql został zaktualizowany — usunięto 2 linie fallback heurystyki Stan & 2 (z obu CASE: Dok1 i Dok2).

Proszę o uruchomienie pliku w SSMS na bazie ERPXL_CEIM:
  solutions/bi/views/Rozrachunki.sql

Zmiana: usunięcie linii:
  WHEN trn1.TrN_Stan & 2 = 2 AND trn1.TrN_GIDTyp IN (2041, 2045, 1529) THEN '(Z)'
  WHEN trn2.TrN_Stan & 2 = 2 AND trn2.TrN_GIDTyp IN (2041, 2045, 1529) THEN '(Z)'

Uzasadnienie: fallback redundantny (0 pokrycia ponad EXISTS spinacza), potencjalnie ryzykowny (Stan=3 to normalny dokument zatwierdzony). Zbadano i zatwierdzono przez Developera.

Po wdrożeniu przez DBA — proszę dać znać, wykonam commit.
