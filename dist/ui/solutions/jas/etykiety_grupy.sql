-- =============================================================================
-- Etykiety wysyłkowe — lista lat i klientów do wyboru w UI
-- Zwraca: rok_gid, rok_kod, klient_gid, klient_kod
-- Jeden wiersz = jeden klient (liść pod rokiem pod 10_OFERTY)
-- =============================================================================
--
-- Hierarchia: 10_OFERTY (9139) → rok → klient
-- GIDTyp = -16 dla grup towarowych
--

SELECT
    r.TwG_GIDNumer   AS rok_gid,
    r.TwG_Kod        AS rok_kod,
    k.TwG_GIDNumer   AS klient_gid,
    k.TwG_Kod        AS klient_kod

FROM CDN.TwrGrupy r          -- poziom roku
JOIN CDN.TwrGrupy k          -- poziom klienta
    ON  k.TwG_GrONumer = r.TwG_GIDNumer
    AND k.TwG_GIDTyp   = -16

WHERE r.TwG_GrONumer = 9139  -- bezpośrednie dzieci 10_OFERTY = lata
  AND r.TwG_GIDTyp   = -16

ORDER BY r.TwG_Kod, k.TwG_Kod;
