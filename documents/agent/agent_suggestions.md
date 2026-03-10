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

### 2026-03-10 — bi_catalog_add.py — uzupełnienie

Narzędzie aktualizuje tylko `columns`. Przy każdym nowym widoku agent nadal musi ręcznie
uzupełnić `description`, `example_questions` i `notes` w catalog.json.
Rozważyć: czy `--all` przy starcie sesji bota powinno być częścią weryfikacji (jak `bi_verify`)?

---

## Archiwum

### 2026-03-10 — Sesja BI.Rozrachunki (Faza 2 → Faza 4)

**CDN.UpoNag — Nota odsetkowa (typ 2832)**

Typ 2832 (NO) NIE jest w CDN.TraNag — jest w CDN.UpoNag (tabela upomnień/not odsetkowych).
JOIN: `upo.UPN_GIDNumer = r.ROZ_TrpNumer/KAZNumer` przy `ROZ_TrpTyp/KAZTyp = 2832`.
Format numeru (zweryfikowany przez CDN.NazwaObiektu):
`'NO-' + RIGHT(CAST(UPN_Rok AS VARCHAR(4)), 2) + '/' + CAST(UPN_Numer AS VARCHAR(10))`
Wzorzec: NO-25/3 (YY/Numer — ODWROTNIE niż intuicja sugeruje).

Typ 2832 należy wykluczyć z NOT IN dla TraNag: `NOT IN (784, 4144, 435, 2832)`.

**Artefakt wyścigu czasowego**

Baza produkcyjna rośnie podczas wykonywania zapytania. Małe liczby NULLi w Nr_Dok (2–4)
przy eksporcie to nowe rekordy dodane między zapytaniem a eksportem — nie błąd SQL.
Weryfikacja: osobny `SELECT WHERE COALESCE(...) IS NULL` zwróci 0 gdy SQL jest poprawny.

**Widok BI.Rozrachunki — zakończony**

`solutions/bi/views/Rozrachunki.sql`, `catalog.json` zaktualizowany.
22 kolumny, ~170k wierszy. Pełne tłumaczenia typów dokumentów na PL.

**Refleksje końcowe — walidacja i deployment**

Walidacja widoku przez sql_query nie zadziała na pliku z CREATE OR ALTER VIEW — narzędzie
blokuje słowo CREATE. Jedyna opcja weryfikacji SQL przed wdrożeniem to wyciągnięcie samego
SELECT z brudnopisu (który jest osobnym plikiem). To dobry powód żeby nigdy nie porzucać
brudnopisu przed Fazą 4 — jest jedynym plikiem który można przetestować bez DBA.

Widok na bazie istnieje dopiero po ręcznym uruchomieniu pliku SQL przez DBA w SSMS.
Agent nie może tego zrobić (brak uprawnień DDL). Następna instancja powinna zawsze sprawdzić
`SELECT COUNT(*) FROM AIBI.NazwaWidoku` zanim założy że widok działa.

Schema BI → AIBI: user zmienił nazwę schematu ręcznie w catalog.json i KntKarty.sql.
Rozrachunki.sql i Rezerwacje.sql mają już AIBI (zapisane przez solutions_save_view.py
z aktualną nazwą). Wszystkie trzy pliki views/ są spójne z AIBI.
Przy każdej zmianie schematu: sprawdź grep "CREATE OR ALTER VIEW" solutions/bi/views/*.sql.

**Refleksje końcowe

Progress log z poprzedniej sesji był kompletny — wejście w Fazę 2 zajęło minuty zamiast
godzin. To dowód że warto go pisać dokładnie. Zasada potwierdzona.

Najmniejszy wyjątek (3 rekordy NO spośród 170k) wymagał odkrycia nowej tabeli (UpoNag)
i weryfikacji formatu przez usera. Koszt: dwa zapytania do bazy i jedna wiadomość do usera.
Opłacalne — NULL w widoku produkcyjnym jest gorszy niż jeden krok weryfikacyjny.

Feedback usera po bi_verify był konkretny i jednorazowy — usunięcie 6 kolumn i poprawa
tłumaczeń to zmiana w 10 minut. Wzorzec "pokaż eksport, zbierz feedback en bloc"
działa lepiej niż pytanie o każdą kolumnę osobno.

Co można było zrobić inaczej: przy budowaniu planu (Faza 1 — poprzednia sesja)
warto od razu zaproponować pełne nazwy typów zamiast skrótów. Skróty (PA, FS, FSK)
są naturalne dla ERP-owca, ale widok BI służy też osobom spoza systemu.
Następnym razem: w planie kolumna Typ_Dok domyślnie z pełną nazwą, nie skrótem.

**REGUŁA: komponenty GID w widokach BI (potwierdzona przez usera)**

- GIDFirma → pomijamy
- GIDTyp   → tłumaczymy przez CASE (to jest typ obiektu ERP — niesie sens biznesowy)
- GIDNumer → zostawiamy (klucz do ad-hoc zapytań i JOINów z innych tabel)
- GIDLp    → pomijamy

Agent tej reguły nie wyabstrahował sam — wyciągnął ją dopiero po feedbacku usera
który kazał usunąć GIDFirma/GIDLp z gotowego widoku. Następnym razem: stosować od Fazy 1.

---

### 2026-03-10 — Sesja BI.Rozrachunki (Faza 0 + Faza 1)

**Kluczowe odkrycia — dla następnej instancji**

CDN.Rozrachunki to tabela rozliczeń (matchingów między dokumentami). Każde rozliczenie = 2 wiersze
(GIDLp=1 i GIDLp=2) które są lustrami z zamienionymi TRP/KAZ i różną walutą. Widok bierze GIDLp=1.

TRP = strona 1 (najczęściej faktura/paragon), KAZ = strona 2 (najczęściej płatność KB).
Dominujący wzorzec: PA(2034) → KB(784) — 135 027 wierszy.

**JOINy dla numerów dokumentów:**
- TraNag typy → CDN.TraNag (TrN_GIDTyp + TrN_GIDNumer)
- KB (784) → CDN.Zapisy — kolumna KAZ_NumerDokumentu zawiera gotowy string numeru
- NM (4144) → CDN.MemNag (MEN_GIDNumer)
- RK (435) → CDN.RozniceKursowe (RKN_ID)
- Operator → CDN.OpeKarty (Ope_GIDNumer = ROZ_OpeNumerRL)

**Formuła prefiksu numeru TraNag (zweryfikowana 99.999%):**
```
(Z) → TrN_Stan & 2 = 2 AND typ korekty (FSK/FZK/PAK/FKE)
(A) → TrN_GenDokMag = -1 AND typ zakupowy (FZ/FZK/PZ)
(s) → TrN_GenDokMag = -1 AND pozostałe
brak → standard
```
Miesiąc z wiodącym zerem: `RIGHT('0' + CAST(MM AS VARCHAR(2)), 2)`.
Znany wyjątek: FSK GIDNumer=6394119 dostaje (Z) mimo Stan=5 — nierozkodowane,
prompt dla researchera w Rozrachunki_researcher_prompt.md.

**Co zajęło niepotrzebnie dużo czasu:**

Dwa rundy weryfikacji numerów przez SSMS (user musiał uruchamiać zapytania) zamiast jednej.
Gdybym od razu zaproponował zapytanie porównujące NumerSystemowy vs NumerInline,
nie byłoby potrzeby kolejki: objects.sql → objects_FS.sql → objects_verify.sql v1 → v2.
Następnym razem: od razu zbudować verify query po pierwszym odczycie formatów z objects.sql.

**Co działało dobrze:**

bi_discovery na starcie dał bardzo dobry obraz tabeli w jednym wywołaniu — bez niego
odkrycie struktury GIDLp=1/2 i identyfikacja stałych zajęłoby wiele oddzielnych zapytań.
Sprawdzenie pary wierszy (SELECT gdzie GIDNumer IN TOP 5) natychmiast ujawniło strukturę lustrzaną.

Równoległe zapytania (4-5 naraz) przy zbieraniu danych o JOINach bardzo skróciło czas.

**Dla następnej instancji — przed SQL:**

1. Progress log jest kompletny i gotowy — przeczytaj go zanim cokolwiek zrobisz.
2. Plan Excel zatwierdzony przez usera — przeczytaj excel_read_rows z --columns CDN_Pole,Uwzglednic,Komentarz_Usera.
3. Sprawdź czy COUNT(*) z GIDLp=1 = 170 480 przed pisaniem SQL.
4. Przy każdym nowym LEFT JOIN sprawdzaj COUNT(*) vs COUNT(DISTINCT ROZ_GIDNumer) — Zapisy
   może mieć wiele wierszy na jeden KAZ_GIDNumer (różne raporty kasowe?).
5. Format NM (MemNag) NIE był weryfikowany przez CDN.NazwaObiektu — user musi potwierdzić.
6. CEiM_Reader też nie ma dostępu do CDN.NazwaObiektu (error 229) — do weryfikacji zawsze SSMS.

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
