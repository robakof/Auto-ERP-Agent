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

### 2026-03-09 — Sesja BI.Zamowienia (Faza 1 → Faza 4)

**Co działało dobrze**

Równoległe odpytywanie bazy (11 zapytań naraz przy analizie komentarzy usera) skróciło czas weryfikacji drastycznie. Wzorzec "zbierz wszystko, potem zapytaj raz" zadziałał — zamiast 8 osobnych pytań do usera zadałem je jedną listą, user odpowiedział jedną wiadomością.

Weryfikacja empiryczna maski DokZwiazane przez TrN_ZaNNumer była dobrą intuicją — nawet jeśli wynik był negatywny (bitmask nie mapuje na typy TraNag), to ten negatyw jest wartościowy. Wiemy czego szukać nie trzeba.

**Co sprawiało trudność**

Korekta roku w numerze dokumentu wyszła dopiero po feedbacku usera z systemu — nie weryfikowałem formatu numeru przez porównanie z rzeczywistym ekranem ERP. Następnym razem: po zbudowaniu numeru inline zapytać usera "czy ten format ZS-2/05/23/PH_4 zgadza się z tym co widzisz w systemie?" zanim przejdę dalej.

Użytkownik poprawiał kolejność odpowiedzi na pytania wielokrotnie numerując inaczej niż ja. Przy następnym zestawie pytań: ponumeruj pytania wyraźnie i poproś o odpowiedź w tej samej numeracji.

**Odkrycie: TrN_ZaNNumer**

CDN.TraNag łączy się z CDN.ZamNag przez `TrN_ZaNNumer` (typ 960 w `TrN_ZaNTyp`). Przydatne do przyszłych widoków łączących zamówienia z dokumentami WZ/FS/PZ.

**Odkrycie: format roku w numerach**

ERP wyświetla rok jako 2 cyfry (YY), nie 4 (YYYY). Dotyczy prawdopodobnie wszystkich tabel z polami Rok (ZamRok, TrNRok, etc.). Wzorzec: `RIGHT(CAST(col AS VARCHAR(4)), 2)`.

**Zarządzanie kontekstem — co paliło go najbardziej**

`bi_verify` z pełnymi statystykami dla 102 kolumn uruchomiony 3 razy = największy pojedynczy wydatek.
Zasada: po drobnej poprawce (jedna kolumna, jedna literówka) używaj `sql_query` na tę kolumnę.
`bi_verify` tylko na końcu etapu lub gdy zmiana dotyka wielu kolumn / JOINów.

`excel_read_rows` na 202-wierszowym planie = jednorazowy ale ciężki.
Zasada: pierwsze przejście przez plan rób tylko z `--columns CDN_Pole,Uwzglednic,Komentarz_Usera`.
Pełne kolumny (Transformacja, Uzasadnienie) czytaj tylko dla wierszy które tego wymagają.

**KLUCZOWA KOREKTA PODEJŚCIA — dotyczy wszystkich przyszłych widoków**

User wielokrotnie poprawiał plan w kierunku "sprowadź" tam gdzie agent proponował "pomiń".
Zasada do zapamiętania:

Pomiń pole TYLKO gdy spełniony jeden z warunków:
1. SELECT DISTINCT zwraca dokładnie 1 wartość dla całej tabeli (udowodnione przez COUNT)
2. Dokumentacja wprost mówi "pole nie jest obsługiwane" lub "nieużywane"
3. Dane wrażliwe (hasła, PINy)
4. Czyste komponenty GID (GIDTyp/GIDFirma/GIDLp) bez żadnej informacji biznesowej

W każdym innym przypadku — uwzględnij. Rzadko wypełnione (np. 2/12022) = uwzględnij.
Nieznane zastosowanie = uwzględnij i opisz. Mała wartość analityczna wg agenta = nie agent decyduje.
Power BI odfiltruje to co user nie potrzebuje. Brak kolumny w widoku blokuje analizę.

**Co warto sprawdzić przy BI.Zamowienia wznowieniu**

- `ZaN_PromocjePar=3` (3731 rek.) — znaczenie nieznane, oznaczone 'Nieznane (3)'. User miał sprawdzić ZS-390/09/2024/SPKR w systemie.
- `ZaN_DokZwiazane` — bitmask zostawiony surowy. Researcher sugeruje "kategorie zakładek Historia związanych" ale bez twardego źródła.

---

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
