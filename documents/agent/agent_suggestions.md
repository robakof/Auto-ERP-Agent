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

*(brak aktywnych wpisów)*

---

## Archiwum

### 2026-03-09 — Sesja BI.Zamowienia (Faza 0 + próba Fazy 1)

Zarchiwizowane 2026-03-09. Technikalia naprawione (limit→1000, --useful-only usunięto, ERP_SCHEMA_PATTERNS poprawiono). bi_plan_generate i truncated przeniesione do backlogu. Odkrycia merytoryczne ZamNag — kontekst dla agenta ERP przy wznowieniu BI.Zamowienia (plik `solutions/bi/Zamowienia/Zamowienia_plan_src.sql`).

**Kluczowe odkrycia ZamNag do zapamiętania przy BI.Zamowienia:**
- `ZaN_ZrdNumer` = samoodniesienie (bezużyteczny); link ZZ→ZS przez `CDN.ZamZamLinki`
- `ZaN_OpiNumer` typ 944 = Pracownik → JOIN `CDN.PrcKarty` (8204/12022 wypełnione)
- `ZaN_KnPNumer` (płatnik) i `ZaN_KnDNumer` (odbiorca) — osobne encje, INCLUDE
- `ZaN_Stan` = bitmask: maska_archiw=16, maska_anulowane=32
- `ZaN_FormaNr`: 10=Gotówka, 20=Przelew, 30=Kredyt, 40=Czek, 50=Karta, 60=Inne
- `ZaN_CenaSpr` = numer cennika (0–9), JOIN przez CDN.TwrCenyNag
- Stan sesji: Faza 0 kompletna, Faza 1 niezakończona. Komentarze usera z pierwszego planu utracone.
