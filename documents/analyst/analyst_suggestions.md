# Sugestie Analityka Danych

Plik refleksji Analityka Danych. Dopisywany po zakończeniu analizy zakresu.
Archiwizuje Developer — po przeglądzie z człowiekiem.

## Jak pisać

Zatrzymaj się i napisz swobodnie — co warte zapamiętania z tej pracy.
Nie musisz odpowiadać na wszystkie pytania poniżej, nie musisz trzymać się ich kolejności.
Jeśli masz obserwację której nie obejmują — napisz ją.

Pytania pomocnicze:
- Co sprawiało trudność? Co byłoby łatwiejsze gdyby narzędzia lub wytyczne działały inaczej?
- Czy powtarzałem coś, co mogłoby być jednym narzędziem lub jedną regułą?
- Co chciałbym powiedzieć następnej instancji zanim zacznie to samo zadanie?
- Jakie wzorce problemów z danymi warto zapamiętać dla kolejnych zakresów?

---

## Wpisy

### 2026-03-12 — Audyt rozruchowy konwencji widoków BI

**Kontekst:** Pierwsza sesja Analityka. Rola A (weryfikator konwencji). Audyt 4 istniejących
widoków: KntKarty, Rezerwacje, ZamNag, Rozrachunki.

**Co działało dobrze:**
Dokumenty konwencji (ERP_VIEW_WORKFLOW, ERP_SCHEMA_PATTERNS, developer_notes) są kompletne
i spójne. Wyciągnięcie 24 sprawdzalnych reguł zajęło jedno przejście — brak ambiwalencji
w tym co powinno być sprawdzalne.

**Co sprawiało trudność:**
- `analyst_start.md` wskazywał `Kontrahenci.sql` — plik nie istnieje (poprawna nazwa: `KntKarty.sql`).
  Drobna niezgodność nazwy w dokumencie rozruchowym. Developer powinien zaktualizować.
- Brak definicji "danych wrażliwych" w jakimkolwiek dokumencie — konwencja mówi "pomijaj wrażliwe"
  ale nie wymienia co jest wrażliwe. Wypełniono w tej sesji (PESEL, numery rachunków, numery dok.
  tożsamości) i dodano do ERP_VIEW_CONVENTIONS.md. Wymaga zatwierdzenia Dawida.

**Obserwacja architektoniczna:**
Widoki są szerokie (80–120 kolumn) — zasadne przy założeniu AI operatorów z szerokim dostępem
i warstwy AIBI jako granicy bezpieczeństwa (nie logika biznesowa). Warstwa raportów SQL
nad widokami jest planowana jako następny krok — właściwa kolejność.

Nie wszystkie szerokie kolumny są uzasadnione: 7 wariantów operatorów w ZamNag, program
lojalnościowy w KntKarty — to spekulatywna kompletność. Ryzyko: przyszłe widoki mogą być
budowane na tym wzorcu bez refleksji czy dane kolumny mają konsumenta.
Sugestia: przy następnych widokach dodać do planu kolumnę "Kto to czyta" (bot, Power BI, AI operator, raporty).

**Co chciałbym powiedzieć następnej instancji:**
- Zacznij od `analyst_start.md` (jest) i `developer_notes.md` (jest) — razem dają kontekst
- Plik konwencji referencyjnych jest teraz w `documents/erp_specialist/ERP_VIEW_CONVENTIONS.md`
- Handoff do ERP Specialist idzie do `solutions/analyst/handoff/`
- Dawid uczestniczy w ocenie kolejnego widoku — uprzedź go zanim zaczniesz

---

## Archiwum
