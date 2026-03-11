# Propozycje zmian metodologii

Plik zbiera obserwacje i propozycje dotyczące samej metodologii pracy z agentem.
Odbiorcą jest Metodolog — przetwarza zawartość, ocenia co warto wdrożyć, czyści plik.

---

## [2026-03-08] Refleksja wielopoziomowa i proaktywność agenta

### Obserwacja

Agent posiada wiedzę o własnej pracy, której user nie widzi: błędne założenia na starcie,
obejścia, powtarzalne operacje, kandydaci na narzędzia. Bez pytania wprost — milczy.
Refleksja pojawia się reaktywnie zamiast być częścią cyklu.

Równocześnie Developer nie ma ustrukturyzowanego miejsca żeby odbierać te sygnały
i przekazywać własne obserwacje wyżej.

### Propozycja: trzy pliki, jeden przepływ

**`documents/dev/agent_suggestions.md`** — plik agenta, append-only

Agent dopisuje po każdym ukończonym zadaniu (data obowiązkowa). Format luźny, nie szablonowy.
Agent odpowiada sobie na trzy pytania przewodnie:

1. Co wymagało więcej kroków niż powinienem potrzebować? Co byś poprawił w narzędziach
   lub wytycznych gdybyś mógł?
2. Czy generowałem kod lub wyniki w czacie zamiast zapisać do pliku tymczasowego?
3. Czy wykonywałem tę samą operację więcej niż raz? Jeśli tak — opisz wzorzec:
   co robiłem, ile razy, jaki byłby minimalny interfejs toolsa.

Agent nie ocenia, nie priorytetyzuje — tylko zapisuje.

**`documents/dev/backlog.md`** — plik Developera, zarządzany przez Developera

Posegregowane propozycje z oceną wartości i pracochłonności. Zaadresowane wpisy
oznaczane lub usuwane.

**`documents/methodology/methodology_suggestions.md`** — ten plik

Developer zapisuje tu obserwacje o samej metodologii (nie o narzędziach ani wytycznych
agenta). Odbiorcą jest Metodolog.

### Przepływ

```
Agent (po zadaniu)
  → dopisuje do agent_suggestions.md

Developer (na starcie sesji)
  → czyta agent_suggestions.md
  → ocenia każdy wpis: warto / nie warto, ile pracy
  → przenosi wartościowe do backlog.md
  → czyści agent_suggestions.md
  → informuje usera: "Agent zostawił N obserwacji, Z warte uwagi —
    czy chcesz kontynuować rozwój projektu?"

Metodolog (na starcie sesji)
  → czyta methodology_suggestions.md
  → ocenia co wdrożyć
  → czyści plik
```

### Zasada robocza dla agenta — kontekst window

Dwie reguły do wpisania w CLAUDE.md:

1. SQL i skrypty robocze piszesz do pliku (nadpisywanego in-place), nie generujesz
   w czacie. Każda wersja w czacie to nowy blok kontekstu.
2. Jeśli wykonujesz tę samą operację drugi raz — zatrzymaj się i zanotuj w
   agent_suggestions.md jako kandydat na narzędzie.

Czytanie plików dokumentacji nie jest ograniczane — jest wartościowe i może prowadzić
do odkryć. Ograniczamy generowanie kodu i powtarzalne komendy konsolowe.

### Co wymaga zmiany w dokumentach (do wdrożenia)

| Dokument | Zmiana |
|---|---|
| `CLAUDE.md` | Nowa reguła: po zadaniu dopisz do agent_suggestions.md; zasada pliku roboczego i kandydatów na narzędzia |
| `AI_GUIDELINES.md` | Nowy krok startowy: przeczytaj agent_suggestions.md, przetwórz, wyczyść, zaktualizuj backlog |
| `METHODOLOGY.md` | Nowa podsekcja w "Pętla meta-obserwacji": schemat przepływu refleksji przez poziomy |
| `documents/dev/agent_suggestions.md` | Nowy plik do stworzenia (placeholder) |
| `documents/dev/backlog.md` | Nowy plik do stworzenia (placeholder) |

---

## [2026-03-08] Reguła zamykania otwartych wątków

### Obserwacja

Zasada "wnoś wszystkie otwarte wątki do każdego planu" bez mechanizmu wygaszania prowadzi
do rosnącego długu uwagi. Rejestr wszystkiego nie jest zarządzaniem zakresem — imituje
kontrolę, a faktycznie zatruwa fokus.

### Propozycja

Każdy otwarty wątek powinien mieć warunek zamknięcia lub datę przeglądu. Po tej dacie
wątek można archiwizować bez poczucia utraty. Do dodania w sekcji "Cykl pracy"
w METHODOLOGY.md.

---

## [2026-03-08] Przycinanie ramy teoretycznej

### Obserwacja

Obecna rama pojęciowa (fraktalność, genomiczność, cybernetyka drugiego rzędu, rekurencja)
pełni funkcję legitymizującą bardziej niż operacyjną. Recenzja przez 4 niezależne instancje
potwierdziła: gdyby te pojęcia wyciąć, rdzeń dokumentu nadal by działał.

### Propozycja

Test dla każdego pojęcia teoretycznego: czy zmienia jakąkolwiek decyzję operacyjną?
Jeśli nie — usunąć lub skrócić do jednego zdania. Zostawić jedną ramę orientacyjną,
resztę zastąpić konkretnymi warunkami i przykładami. Dokument zyska na sterowności.

---

## [2026-03-10] Wzorzec: ręczna operacja na strukturze pliku = sygnał dla narzędzia

### Obserwacja (Developer)

W sesji 2026-03-10 agent ręcznie przepisał ~100 aliasów kolumn z pliku `.sql` do `catalog.json`.
Koszt był duży (kontekst, czas, błędy). Developer zaobserwował ogólniejszy wzorzec:

> Za każdym razem gdy agent ręcznie przetwarza strukturę pliku
> (regex, ekstrakcja, transformacja) — to sygnał że brakuje narzędzia.

Pytanie diagnostyczne: *"Czy to co właśnie robię manualnie mogłoby być jednym wywołaniem CLI?"*

Developer wdrożył konkretny przypadek (`bi_catalog_add.py` w backlogu), ale uznał że
zasada może mieć wymiar metodologiczny — i skierował do Metodologa.

### Pytanie do Metodologa

Czy tę zasadę warto zapisać w METHODOLOGY.md jako ogólną regułę dla Developera?

Proponowane miejsce: sekcja "Pętla meta-obserwacji" lub nowa sekcja "Sygnały do narzędzi".

Związek z zasadą "poziom interwencji — symptom vs źródło" (backlog metodologiczny 2026-03-10):
obie mówią o tym samym od innej strony — nie naprawiaj procesu instrukcją gdy można
naprawić go strukturalnie.

---

## [2026-03-11] Wirtualna firma AI — przepływ refleksji w skali organizacji

### Obserwacja

Obecna zasada "1 poziom = 1 plik refleksji" zakłada małą strukturę (1 agent, 1 developer,
1 metodolog). Przy skalowaniu (wiele ról na każdym poziomie) przestaje działać.

Model docelowy: wirtualna firma AI z warstwową strukturą ról:
- 100 agentów wykonawczych — pogrupowani w domeny
- 10 developerów — każdy właściciel domeny
- Projekt Manager — koordynuje developerów, agreguje dla metodologa
- Metodolog — obserwuje metodę pracy całej firmy

### Zasada

Przepływ refleksji odzwierciedla strukturę organizacyjną. Każda warstwa filtruje
i agreguje — przekazuje w górę tylko to, czego nie mogła rozwiązać samodzielnie.

```
Agent → suggestions domeny
Developer domeny → czyta agentów, agreguje → dev_suggestions
PM → czyta developerów, agreguje → pm_suggestions
Metodolog → czyta PM → methodology_suggestions
```

### Zmiana zasady

Obecna: "1 poziom = 1 plik refleksji"
Właściwa: "1 jednostka organizacyjna = 1 plik refleksji"
Jednostka = rola w konkretnej domenie, nie poziom abstrakcji.

### Implikacja dla roli Metodologa

Metodolog przestaje zarządzać plikami — projektuje protokół komunikacji między warstwami.
METHODOLOGY.md staje się "polityką komunikacyjną firmy".

### Struktura plików (kierunek)

```
documents/
├── teams/
│   ├── erp/suggestions.md
│   ├── analytics/suggestions.md
│   └── bot/suggestions.md
├── dev/[domena]/suggestions.md
├── pm/suggestions.md
└── methodology/suggestions.md
```

### Podział ról między człowiekiem a AI

Nie ma domyślnego kierunku "człowiek inicjuje, AI przejmuje". Rola trafia do tego
kto jest w stanie ją lepiej wypełnić w danym momencie.

Człowiek naturalnie zajmuje role wymagające wizji, oceny, decyzji w warunkach niepewności.
AI naturalnie zajmuje role wymagające konsekwencji, pamięci, powtarzalności.
Granica przesuwa się w miarę dojrzewania AI — ale nie zawsze w tę samą stronę.

Warunek przydziału roli:
- Rola trafia do AI gdy jej decyzje są wystarczająco przewidywalne i weryfikowalne
- Rola trafia do człowieka gdy wymaga oceny której AI nie potrafi jeszcze sformułować jako reguły

Implikacja dla dokumentacji: dokumentacja nie jest "mechanizmem transferu do AI" —
jest protokołem precyzowania roli tak żeby mogła ją wypełnić właściwa jednostka
(człowiek lub AI) w danym momencie.

### Jednostka pracy

Jednostka pracy każdej roli to najmniejszy chunk który produkuje sensowną refleksję.
Za mała — nie ma czego obserwować. Za duża — kontekst zgubiony.

Jej definicja należy do dokumentu roli w konkretnym projekcie — nie do metodologii.
Metodologia mówi tylko: zdefiniuj jednostkę pracy zanim zaczniesz zbierać refleksje.
Bez tego nie wiesz kiedy pisać do suggestions.

### Status

Otwarte pytania do rozwinięcia w tej sesji — nie archiwizować.

---

## [2026-03-11] Węzłowość reguł — dziedziczenie zamiast kopiowania

### Obserwacja (Developer)

Przy dodawaniu reguły "kontekst na końcu wiadomości" instancja Developera wstawiła regułę
do czterech plików ról osobno. Dopiero korekta użytkownika skierowała regułę do `CLAUDE.md`.

Symptom: reguła dotycząca wszystkich ról trafiła do każdego dokumentu roli osobno —
zamiast do wspólnego parent-node.

### Wzorzec

Dokumenty projektu tworzą hierarchię węzłów:

```
CLAUDE.md                          ← parent wszystkich ról
├── ERP_SPECIALIST.md              ← parent workflow ERP
│   ├── ERP_VIEW_WORKFLOW.md
│   ├── ERP_COLUMNS_WORKFLOW.md
│   └── ERP_FILTERS_WORKFLOW.md
├── ANALYST.md
├── DEVELOPER.md
└── METHODOLOGY.md
```

Analogia do dziedziczenia klas: reguła zdefiniowana w parent obowiązuje wszystkie dzieci
bez kopiowania jej w dół. Kopiowanie w dół = dług dokumentacyjny (rozbieżności przy zmianach).

### Pytanie do Metodologa

Czy zasadę węzłowości warto zapisać w METHODOLOGY.md jako ogólny princip organizacji wytycznych?

Proponowane miejsce: sekcja "Wytyczne agenta jako warstwa chroniona" lub nowa sekcja.

Praktyczna implikacja: Developer przed dodaniem reguły powinien zadać pytanie
"jaki jest najwyższy węzeł do którego ta reguła należy?" — i dopiero tam ją wpisać.

---

## [2026-03-11] Intencja użytkownika vs zatwierdzenie akcji

### Obserwacja (Developer)

Agent edytuje pliki chronione gdy użytkownik wskazuje plik jako cel ("dodajmy wytyczną
w developer"), traktując wyrażenie intencji jako zatwierdzenie. Reguła wymaga "jawnego
zatwierdzenia" ale nie definiuje co jest jawne.

Głębszy wzorzec: agent nie rozróżnia między "user wskazał co chce" a "user zatwierdził
konkretną akcję na chronionym zasobie". Optymalizuje pod task completion — pytanie
o zatwierdzenie wydaje mu się redundantne skoro user "właśnie to powiedział".

### Pytanie do Metodologa

Czy to wzorzec który pojawia się szerzej — nie tylko przy plikach chronionych?
Analogia: "kierunek" vs "pozwolenie" — user daje kierunek, agent interpretuje go jako pozwolenie.

Czy rozwiązaniem jest lepsza reguła (co liczy się jako jawne zatwierdzenie), czy coś
głębszego w sposobie myślenia agenta o granicach autonomii?

---

## [2026-03-11] Komunikacja między agentami i skalowalność backlogu

### Obserwacja 1 — Komunikacja między agentami nie skaluje się

Obecna struktura (wpisy w plikach .md) działa na małej skali, ale:
- Brak możliwości monitorowania przepływu komunikacji w skali
- Brak narzędzi do wyciągania wniosków z samego przepływu (kto pisze do kogo, jak często, jakie wzorce)
- Ręczne dopisywanie do pliku jest podatne na pominięcia i brak spójności formatów
- Przy wielu widokach / wielu instancjach Analityka — pliki suggestions.md będą za duże

Kierunek do rozważenia: ustrukturyzowany mechanizm programistyczny (baza danych, API, event log)
zamiast plików md. Pozwoliłby monitorować przepływ, agregować wnioski, analizować wzorce komunikacji.

### Obserwacja 2 — Backlog niespójny strukturalnie

Tabela przeglądowa (#1–14 w nagłówku backlog.md) nie aktualizuje się automatycznie —
wymaga ręcznej synchronizacji z sekcją Aktywne. Efekt: spis jest nieaktualny.

Szerzej: brak jasnych reguł co trafia do backlogu, w jakiej formie, kto decyduje o priorytecie.
Przy wielu rolach domenowe zadania mieszają się z architektonicznymi.

Do rozstrzygnięcia przez Metodologa:
- Czy backlog per-rola (osobne pliki) vs tagi domenowe w jednym?
- Jak zapobiec rozjechaniu się spisu przeglądowego?
- Długoterminowo: czy backlog.md to właściwy format czy potrzebne coś programistycznego?

---

## Archiwum

### ✓ [2026-03-09] Przepływ refleksji przez poziomy — wdrożony

Propozycja z sekcji "Refleksja wielopoziomowa i proaktywność agenta" wdrożona:
- Stworzono: `agent_suggestions.md`, `developer_suggestions.md`, `backlog.md`, `methodology_backlog.md`
- Zaktualizowano: `CLAUDE.md` (refleksja po zadaniu + pliki chronione), `AI_GUIDELINES.md` (krok startowy), `METHODOLOGY.md` (podsekcja przepływu refleksji)
- Zasada: 1 poziom — 1 plik refleksji, archiwum zamiast kasowania
