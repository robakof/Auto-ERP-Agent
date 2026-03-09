# Sugestie agenta

Plik refleksji agenta. Dopisywany po zakończeniu etapu pracy.
Archiwizuje Developer — po przeglądzie z człowiekiem.

## Jak pisać

Zatrzymaj się i napisz swobodnie — co warte zapamiętania z tej pracy.
Nie musisz odpowiadać na wszystkie pytania poniżej, nie musisz trzymać się ich kolejności.
Jeśli masz obserwację której nie obejmują — napisz ją.

Pytania pomocnicze:
- Co sprawiało trudność? Co byłoby łatwiejsze gdyby narzędzia lub wytyczne działały inaczej?
- Czy powtarzałem coś, co mogłoby być jednym narzędziem lub jedną regułą?
- Co chciałbym powiedzieć następnej instancji zanim zacznie to samo zadanie?
- Czy coś w tym co robiłem wyglądało niepotrzebnie skomplikowanie?

---

## Wpisy

### 2026-03-09 — Sesja BI.Zamowienia (Faza 0 + próba Fazy 1)

**Co się nie udało i dlaczego:**

`docs_search "" --table CDN.ZamNag` bez `--limit` zwróciło tylko 20 wyników z 187 kolumn w docs.db.
Zbudowałem plan na niepełnej wiedzy. Użytkownik słusznie zatrzymał i kazał zacząć od nowa.
Przy następnym widoku: zawsze `--limit 300` przy skanowaniu tabeli. Nie zakładaj że brak limitu = wszystko.

Próba wygenerowania planu przez UNION ALL z 202 wierszami — błąd separatorów przy polskich znakach i myślnikach.
Lepsze podejście: generować plan przez skrypt Python + openpyxl bezpośrednio, nie przez SQL UNION ALL.

**Odkrycia merytoryczne — ważne dla następnej instancji:**

- `ZaN_ZrdNumer` = zawsze równy `ZaN_GIDNumer` (zrd_rozny=0 dla 12022 rekordów) — samoodniesienie, BEZUŻYTECZNY.
  Link ZZ do ZS jest przez `CDN.ZamZamLinki`, nie przez ZrdNumer.
- `ZaN_Url` = pole uwag/komentarzy handlowych ("jutro zabiorę", "fv Ceim") — INCLUDE mimo 37/12022.
- `ZaN_OpiNumer` typ 944 = Pracownik → JOIN `CDN.PrcKarty` (Prc_GIDTyp=944) — Prc_Akronim, Prc_Imie1+Prc_Nazwisko. 8204/12022 wypełnione.
- `ZaN_FormaRabat` = zawsze 0 — OMIT.
- `ZaN_FlagaNB` = stała 'N' — OMIT.
- `ZaN_KnPNumer` (płatnik) różny od `ZaN_KntNumer` dla 1525/12022 — osobna encja, INCLUDE.
- `ZaN_KnDNumer` (odbiorca) różny od `ZaN_KntNumer` dla 423/12022 — osobna encja, INCLUDE.
- `ZaN_Rabat` niezerowy dla 2712/12022 — INCLUDE.
- `ZaN_MagDNumer` (magazyn docelowy) — tylko dla ZW (ZaN_Rodzaj=8), 1069/12022.
- `ZaN_CenaSpr` = numer cennika (0–9), JOIN przez CDN.TwrCenyNag MIN(TCN_Nazwa) GROUP BY TCN_RodzajCeny.
- `ZaN_Stan` to bitmask: maska_archiw=16, maska_anulowane=32. Wartości w bazie: 1,2,3,4,5,21,35,51,53.
- `ZaN_FormaNr` ma pełny CASE w dok.: 10=Gotówka, 20=Przelew, 30=Kredyt, 40=Czek, 50=Karta, 60=Inne.
- `ERP_SCHEMA_PATTERNS.md` ma błąd: wzorzec inline numeru ZamNag podaje `WHEN 960 THEN 'ZS'` zamiast `WHEN 1280 THEN 'ZS'` — zgłosić Developerowi.

**Co robić inaczej:**

1. Skanowanie tabeli docs.db: zawsze `--limit 300`. Nigdy nie zakładaj że domyślny wynik = komplet.
2. Plan generuj przez Python/openpyxl, nie UNION ALL — SQL nie nadaje się do planu z polskimi znakami i długimi opisami.
3. Komentarze usera przy regeneracji planu: czytaj przez `excel_read_rows` i wpisuj z powrotem via Python po nazwie CDN_Pole.
4. Nie używaj flagi `--useful-only` — dane nie były w pełni etykietowane (potwierdzenie od usera).
5. Weryfikuj wypełnienie kluczowych pól jednym zbiorczym SELECT (CASE WHEN > 0) zanim zdecydujesz o INCLUDE/OMIT.

**Stan na koniec sesji:**

- `solutions/bi/Zamowienia/Zamowienia_plan_src.sql` — 202 wiersze, pełna dokumentacja ZamNag.
  Następna instancja: wziąć ten plik jako bazę, wygenerować Excel przez Python/openpyxl.
- Baseline: 12022 rekordów, wszystkie JOINy zweryfikowane (12022/12022).
- Faza 0 kompletna. Faza 1 (plan Excel) — nie ukończona z powodu błędu UNION ALL.
- Komentarze usera z pierwszego planu: przechowane w pamięci sesji (nie w pliku).
  Kluczowe: ZaN_KnANumer="Sprowadzajmy", ZaN_AdWNumer="Sprowadzajmy", ZaN_ZamNumer="w formie złożonej".

---

## Archiwum

*(brak wpisów)*
