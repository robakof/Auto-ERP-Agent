-- =============================================================================
-- JAS export — WZ oczekujące na wysłanie do JAS
-- Zwraca wszystkie wiersze z AILO.wz_jas_export (jeden wiersz = jeden typ palety)
-- Grupowanie po wz_id po stronie Pythona (jas_mapper.py)
-- =============================================================================
--
-- Opcjonalne filtry (podstawiane przez jas_export.py):
--   {filter_wz_id}   → AND wz_id = <id>     (jedna WZ)
--   {filter_numer}   → AND numer_wz = '<nr>' (po numerze)
--

SELECT
    numer_wz,
    data_wystawienia,
    data_sprzedazy,
    data_realizacji_zs,
    opis,
    odbiorca_nazwa,
    odbiorca_ulica,
    odbiorca_nr_domu,
    odbiorca_kod_pocztowy,
    odbiorca_miasto,
    odbiorca_kraj,
    typ_opakowania,
    ilosc,
    dlugosc_cm,
    szerokosc_cm,
    wysokosc_cm,
    waga_kg_max,
    magazyn_id,
    wz_id

FROM AILO.wz_jas_export

{where_clause}

ORDER BY wz_id, typ_opakowania;
