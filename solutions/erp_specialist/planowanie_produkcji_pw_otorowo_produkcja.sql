-- Planowanie produkcji — przyjęta produkcja PW Otorowo (P_P Otorowo*)
-- Dokument: PW (Przychód wewnętrzny), GIDTyp = 1617
-- Seria: OTO (Otorowo) — odpowiada UI-nazwie "P_P Otorowo"
-- Filtr towaru: kody CZNI%
-- Filtr roku: po Data_Magazynowa (TrN_DataMag)
-- Źródło: CDN.TraNag + CDN.TraElem
-- Data: 2026-03-30
-- Autor: ERP Specialist
--
-- Output: Czni_Kod, Suma_Qty — gotowe do dict[czni_kod, suma_qty] w pp_produced.py
-- Rok przekazywany jako parametr (zastąp @year wartością lub przekaż z Python)

SELECT
    te.TrE_TwrKod                                          AS Czni_Kod,
    SUM(te.TrE_Ilosc)                                      AS Suma_Qty
FROM CDN.TraNag tn
JOIN CDN.TraElem te
    ON te.TrE_GIDNumer = tn.TrN_GIDNumer
WHERE
    tn.TrN_GIDTyp  = 1617           -- PW (Przychód wewnętrzny)
    AND tn.TrN_TrNSeria = 'OTO'     -- seria Otorowo
    AND te.TrE_TwrKod LIKE 'CZNI%'  -- tylko towary CZNI
    AND YEAR(CAST(DATEADD(d, tn.TrN_DataMag, '18001228') AS DATE)) = 2025  -- rok: zastąp 2025 parametrem
GROUP BY
    te.TrE_TwrKod
ORDER BY
    te.TrE_TwrKod;

-- Uwagi do implementacji pp_produced.py:
--   - Zastąp literalne 2025 zmienną year (inject do SQL przez format lub parametr)
--   - TrN_DataMag = data magazynowa (int, format Comarch: dni od 1800-12-28)
--   - JOIN: TrE_GIDNumer = TrN_GIDNumer (nie potrzeba GIDTyp/GIDFirma — GIDNumer unikalny w TraNag)
--   - Wynik 100+ kodów CZNI dla 2025 — zweryfikowano
