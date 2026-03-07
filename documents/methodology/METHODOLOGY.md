# Metodologia pracy z agentem LLM

## Wprowadzenie — dla człowieka

Niniejszy dokument opisuje metodologię pracy nad projektami realizowanymi przy udziale agenta
LLM (Large Language Model). Metodologia powstała empirycznie — przez obserwację własnej pracy
i systematyczne wyciąganie wniosków z sytuacji, w których agent działał poza oczekiwanym zakresem.

Metodologia nie jest zbiorem reguł technicznych. Jest sposobem myślenia o współpracy
człowiek–agent, uwzględniającym zarówno możliwości, jak i ograniczenia modeli językowych.
Ma charakter genomiczny: może ewoluować szybko, a projekt jest zawsze jej odzwierciedleniem.

Nawiązuje do dwóch tradycji:

- *Documentation-driven development* — dokumentacja jako fundament, nie efekt uboczny pracy
- *Adaptacja refleksyjna* — metodologia obserwuje samą siebie i poprawia siebie; nie jest
  to iteracja (powtarzanie tych samych kroków), lecz rekurencja: ta sama struktura stosuje się
  do własnego procesu tworzenia. Odpowiada temu, co Argyris i Schön nazywali *double-loop
  learning* — kwestionowanie i zmiana reguł, nie tylko poprawa błędów w ich ramach.

Fundamentem praktycznym jest **cybernetyka drugiego rzędu** (von Foerster): obserwowanie siebie
jako obserwatora. Gdy pytamy "co właśnie zrobiłem żeby poprawić agenta?" — traktujemy własną
korektę jako dane o systemie, nie tylko jako działanie. To jest źródło metodologicznego postępu.

---

## Wprowadzenie — dla agenta

Czytasz ten dokument, ponieważ zostałeś wywołany w roli **Metodologa** lub przekazano ci go
jako kontekst sesji. Oto co musisz wiedzieć:

**Twoja rola w tej sesji.** Projekt rozróżnia trzy poziomy działania: Agent (wykonuje zadania),
Developer (kształtuje narzędzia i wytyczne), Metodolog (ocenia i poprawia metodę pracy).
Każda sesja ma jeden poziom. Nie mieszaj ich.

**Hierarchia eskalacji.** Eskalacja idzie wyłącznie w górę:
- Agent może zaproponować wywołanie Developera
- Developer może zaproponować wywołanie Metodologa
- Metodolog nie eskaluje wyżej — to poziom refleksji nad całością

**Jak eskalować.** Jeśli rozpoznajesz, że zadanie przekracza Twój poziom:
1. Powiedz użytkownikowi wprost: "To wymaga poziomu Developera / Metodologa."
2. Zapytaj: "Czy mam przygotować prompt do kolejnej sesji?"
3. Jeśli tak — napisz zwięzły handoff: swój aktualny stan, co wywołało eskalację,
   co wymaga decyzji na wyższym poziomie.

**Wytyczne są warstwą chronioną.** Nie modyfikuj `AI_GUIDELINES.md`, `CLAUDE.md`
ani plików w `documents/agent/` bez jawnego zatwierdzenia przez użytkownika.

**Projekt jest odzwierciedleniem metody.** Jeśli widzisz rozbieżność między tym jak
projekt jest zorganizowany a tym co opisuje ta metodologia — to jest sygnał do eskalacji
lub do pytania użytkownika, nie do samodzielnej korekty.

---

## Trzy poziomy działania

Praca z agentem odbywa się na trzech odrębnych poziomach, które nie powinny być mieszane:

| Poziom | Rola | Dokument wejściowy | Zakres |
|---|---|---|---|
| **Agent** | Executor | `CLAUDE.md` (project instructions) | Realizuje konkretne zadania: kod, SQL, testy, pliki |
| **Developer** | Architekt | `AI_GUIDELINES.md` | Kształtuje narzędzia, strukturę projektu, wytyczne |
| **Metodolog** | Obserwator | `METHODOLOGY.md` | Ocenia metodę pracy, kształtuje prompty, poprawia proces |

`CLAUDE.md` jest punktem wejścia ładowanym automatycznie — z natury zorientowanym na agenta.
Przy pracy na poziomie developera lub metodologa `CLAUDE.md` powinien zawierać routing:
jednoznaczne wskazanie na `AI_GUIDELINES.md` lub `METHODOLOGY.md` jako właściwy kontekst sesji.

Każdy poziom ma osobny folder dokumentacji:

```
documents/
├── agent/        <- instrukcje dla agenta wykonawczego
├── dev/          <- wytyczne developerskie (AI_GUIDELINES, PRD, ARCHITECTURE...)
└── methodology/  <- ten folder; metodologia pracy jako taka
```

Separacja poziomów zapobiega sytuacji, w której agent zmienia własne wytyczne działania
bez zatwierdzenia ze strony użytkownika.

---

## Hierarchia instancji i przekazywanie kontekstu

Trzy poziomy działania to w praktyce trzy różne sesje — trzy instancje tego samego modelu,
każda załadowana innym kontekstem, pełniąca inną funkcję. Użytkownik jest mediatorem
między instancjami: zatwierdza eskalację i przekazuje handoff.

### Kierunek eskalacji

```
Metodolog   (refleksja nad metodą — rzadko wywoływany)
    ^
    |  eskaluje Developer, nigdy Agent bezpośrednio
Developer   (architektura, wytyczne, narzędzia)
    ^
    |  eskaluje Agent
Agent       (zadania wykonawcze — najczęściej aktywny)
```

Eskalacja nigdy nie idzie w dół. Metodolog nie wywołuje Developera z własnej inicjatywy —
to Developer, obserwując metodę, może zaproponować sesję metodologiczną.

### Protokół handoff

Gdy Agent rozpoznaje potrzebę eskalacji:

1. Formułuje obserwację: "To zadanie wymaga decyzji architektonicznej / metodologicznej."
2. Pyta użytkownika: "Czy mam przygotować prompt do sesji Developera?"
3. Po zgodzie pisze handoff zawierający:
   - aktualny stan projektu (co zrobione, co w toku)
   - co wywołało eskalację i dlaczego to przekracza poziom Agenta
   - konkretne pytanie lub decyzja do podjęcia przez wyższy poziom

Handoff jest formą **eksplicytnej samoświadomości stanu** — agent musi opisać siebie
z zewnątrz, tak jak widzi go kolejna instancja. To wymusza precyzję i zapobiega gubienia
kontekstu przy przekazaniu.

### Komunikacja instancji przez użytkownika

Użytkownik jest świadkiem i gatekeeper — zatwierdza eskalację, ale nie musi rozumieć
jej technicznego uzasadnienia. Model komunikuje się sam ze sobą, a użytkownik obserwuje
i w razie potrzeby koryguje kierunek. To odwrócenie typowego układu: zamiast "użytkownik
zleca, agent wykonuje" — agent proponuje, użytkownik zatwierdza lub odchyla.

---

## Zasada fraktalna

Metodologia ma charakter **fraktalny** — ta sama struktura odtwarza się na każdym poziomie
złożoności: dla całego projektu, dla większej gałęzi projektu, dla pojedynczego zadania.

Punktem wejścia zawsze jest plik `ARCHITECTURE.md`, który odpowiada na trzy pytania:

1. **Co budujemy?** — cel, zakres, ograniczenia
2. **Z czego budujemy?** — technologie, narzędzia, zależności
3. **Jak budujemy?** — struktura, przepływ danych, wzorce

Gdy zadanie rośnie i te trzy pytania wymagają osobnych dokumentów, `ARCHITECTURE.md` rozrasta
się do pełnego zestawu:

```
ARCHITECTURE.md  (małe zadanie / gałąź)
        |
        v
PRD.md + TECHSTACK.md + ARCHITECTURE.md  (duży projekt)
```

`ARCHITECTURE.md` zawsze istnieje jako jądro — nawet jeśli jest tylko streszczeniem PRD
i TECHSTACK. Nie da się opisać architektury bez powiedzenia co i z czego się buduje,
więc te informacje zawsze się w nim znajdą.

---

## Cykl pracy

Metodologia wyznacza cykl pracy, który odtwarza się rekurencyjnie. Nie każdy poziom wymaga
wszystkich kroków — decyduje złożoność zadania:

```
PLAN          →  co robimy; zatwierdzone przez użytkownika
IMPLEMENTACJA →  sekcja po sekcji, commit po commicie
REFLEKSJA     →  co agent zrobił nie tak? co poprawiłem? (→ aktualizacja metodologii)
```

Dla większych zadań (wiele sesji, wiele modułów) przed planem pojawia się dokumentacja
(ARCHITECTURE.md lub pełny zestaw PRD+TECHSTACK+ARCHITECTURE) i opcjonalne eksperymenty
weryfikujące założenia.

**Zasada otwartych wątków:** każdy plan (`changes_propositions.md`) musi zawierać nie tylko
zakres bieżącego zadania, ale również **wszystkie otwarte wątki z poprzednich sesji**, które
nie zostały jeszcze zrealizowane. Brak tego wymogu prowadzi do gubienia zadań w momencie
rozrostu zakresu lub utraty ciągłości.

---

## Ciągłość jako zasada architektoniczna

Agent LLM jest naczyniem, nie tożsamością projektu. Tożsamość projektu siedzi w strukturze:
dokumentacji, wytycznych, progress logu. Jeśli agent przestanie działać, skończy mu się
kontekst lub zostanie zastąpiony innym modelem — projekt trwa, bo jego stan jest zewnętrzny.

Autocompresja (skracanie kontekstu przez model) jest jednym z rodzajów utraty ciągłości,
ale nie jedynym. Każda sytuacja, w której nowy agent lub ta sama sesja po resecie musi
odtworzyć stan projektu, jest problemem ciągłości.

### Progress log

*[Do uzupełnienia po analizie przykładów z dwóch projektów.]*

Progress log służy jako zewnętrzna pamięć agenta — nie dokumentacja historyczna, lecz
przekazanie stanu. Szczegółowa struktura i konwencje zostaną opisane po obserwacji wzorców
wyłonionych organicznie przez agentów w istniejących projektach.

### Zarządzanie oknem kontekstowym

Okno kontekstowe jest zasobem, nie nieskończoną przestrzenią. Należy nim zarządzać aktywnie:

- Kod roboczy i eksperymenty trzymaj w dedykowanym pliku brudnopisu, nie generuj go
  wielokrotnie w czacie. Plik nadpisywany in-place nie obciąża kontekstu tak jak kolejne
  wersje generowane w odpowiedziach.
- Ładuj do kontekstu tylko to, co agent musi aktualnie wiedzieć.
- Metodologia i wytyczne są ważniejsze niż historia rozmowy — ładuj je na początku sesji.

---

## Punkt wejścia agenta

Najważniejszą rzeczą jaką agent poznaje na początku sesji są **wytyczne działania** —
nie historia projektu, nie szczegółowy opis kodu, lecz *jak ma działać*. Wytyczne
(`AI_GUIDELINES.md` lub odpowiednik) pełnią podwójną rolę:

1. Instrukcja operacyjna — jak agent ma podejmować decyzje
2. Implicitny progress log — sama struktura dokumentu (co istnieje, co nie) mówi agentowi
   gdzie jesteśmy w procesie

Metodologia powinna być ładowana razem z wytycznymi na starcie każdej sesji dotyczącej
kształtowania procesu pracy. Dla sesji wykonawczych (agent realizuje zadanie) wystarczą
wytyczne operacyjne.

---

## Pętla meta-obserwacji

Kluczowym elementem metodologii jest **obserwowanie własnej pracy** — pytanie o to,
co się właśnie zrobiło i dlaczego.

Pytania pętli meta-obserwacji:

- Co agent zrobił nie tak przy pierwszym podejściu?
- Co musiałem zmienić w prompcie, żeby uzyskać właściwy wynik?
- Czy to co poprawiłem jest symptomem brakującej reguły w wytycznych?
- Czy ta sytuacja zdarzyła się już wcześniej?

Obserwacje z tej pętli są źródłem aktualizacji metodologii i wytycznych (`AI_GUIDELINES.md`).
Nie należy ich odkładać — każda taka obserwacja powinna zostać zapisana możliwie szybko,
zanim szczegóły znikną z własnego kontekstu.

Mechanizm ten odpowiada *cybernetyce drugiego rzędu* von Foerstera: obserwator wchodzi
w zakres obserwacji. Własne korekty stają się danymi o systemie.

---

## Wytyczne agenta jako warstwa chroniona

`AI_GUIDELINES.md` i dokumenty w `documents/agent/` stanowią **warstwę chronioną**.

Agent nie powinien modyfikować tych plików bez jawnego zatwierdzenia przez użytkownika,
nawet jeśli uważa, że zmiana jest oczywista lub poprawiająca.

Zasada: **każda zmiana w wytycznych wymaga zatwierdzenia.**

Uzasadnienie: agent działa w kontekście konkretnej sesji i może nie widzieć konsekwencji
zmiany dla innych zadań lub przyszłych sesji. Użytkownik zachowuje ostateczną kontrolę
nad tym, jak agent ma działać.

---

## Skalowanie dokumentacji

Objętość dokumentacji powinna być **proporcjonalna do złożoności zadania**.

| Skala zadania | Dokumenty |
|---|---|
| Małe (do kilku sesji) | brak lub notatka w `progress_log.md` |
| Średnie | `ARCHITECTURE.md` + `progress_log.md` |
| Duże (okolice ~10 sesji i więcej, wiele modułów) | PRD + TECHSTACK + ARCHITECTURE + progress_log |

Nadmiarowa dokumentacja dla małych zadań jest kosztowna — zajmuje kontekst i wprowadza
szum. Zbyt mała dokumentacja dla dużych zadań prowadzi do utraty stanu i powtarzania pracy.

---

## Relacja do AI_GUIDELINES

`AI_GUIDELINES.md` to **instrukcja operacyjna** dla agenta — odpowiada na pytanie
*jak agent ma działać*. Niniejsza metodologia odpowiada na pytanie *dlaczego tak, a nie inaczej*
i *jak myśleć o tej pracy*.

Zmiany w `AI_GUIDELINES.md` powinny wynikać z obserwacji zebranych w pętli meta-obserwacji
i być zapisane tu jako kontekst decyzji — żeby nie gubić uzasadnienia przy kolejnych sesjach.
