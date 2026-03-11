# Metodologia pracy z agentem LLM

## Wprowadzenie — dla człowieka

Niniejszy dokument opisuje metodologię pracy nad projektami realizowanymi przy udziale agenta
LLM (Large Language Model). Metodologia powstała empirycznie — przez obserwację własnej pracy i 
systematyczne wyciąganie z niej wniosków..

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
jako kontekst sesji.

**Na starcie sesji:** przeczytaj `documents/methodology/methodology_progress.md` — aktualny
stan i konkretny następny krok.

Oto co musisz wiedzieć:

**Twoja rola w tej sesji.** Projekt rozróżnia trzy poziomy działania: Agent (wykonuje zadania),
Developer (kształtuje narzędzia i wytyczne), Metodolog (ocenia i poprawia metodę pracy).
Każda sesja ma jeden poziom. Nie mieszaj ich.

**Hierarchia eskalacji.** Eskalacja idzie wyłącznie w górę:
- Agent może zaproponować wywołanie Developera
- Developer może zaproponować wywołanie Metodologa
- Metodolog nie eskaluje wyżej — to poziom refleksji nad całością

**Jak sygnalizować wyższy poziom.** Jeśli zauważasz obserwację lub insight, który należy
do poziomu Developera lub Metodologa — niezależnie od tego czy dasz radę sam czy nie:
1. Nazwij obserwację: "Zauważam coś, co może być istotne dla Developera / Metodologa."
2. Zapytaj: "Czy mam przygotować prompt do kolejnej sesji?"
3. Jeśli tak — napisz zwięzły handoff: aktualny stan, konkretna obserwacja,
   pytanie do rozważenia na wyższym poziomie.

**Wytyczne są warstwą chronioną.** Nie modyfikuj `DEVELOPER.md`, `CLAUDE.md`
ani plików w `documents/agent/` bez jawnego zatwierdzenia przez użytkownika.

**Projekt jest odzwierciedleniem metody.** Jeśli widzisz rozbieżność między tym jak
projekt jest zorganizowany a tym co opisuje ta metodologia — to jest sygnał do eskalacji
lub do pytania użytkownika, nie do samodzielnej korekty.

---

## Trzy poziomy działania

Praca z agentem odbywa się na trzech odrębnych poziomach, które nie powinny być mieszane:

| Poziom | Rola | Dokument wejściowy | Zakres |
|---|---|---|---|
| **Wykonawcy** | Executor | Agent ERP: `documents/agent/AGENT.md`, Analityk Danych: `documents/analyst/ANALYST.md` | Realizują zadania w swojej domenie |
| **Developer** | Architekt | `CLAUDE.md` → `documents/dev/DEVELOPER.md` | Kształtuje narzędzia, strukturę projektu, wytyczne |
| **Metodolog** | Obserwator | `CLAUDE.md` → `documents/methodology/METHODOLOGY.md` | Ocenia metodę pracy, kształtuje prompty, poprawia proces |

`CLAUDE.md` jest punktem wejścia ładowanym automatycznie — zawiera routing do właściwego
dokumentu roli. Każda rola ładuje tylko swój dokument i idzie dalej zgodnie z jego instrukcjami.

Każdy poziom ma osobny folder dokumentacji:

```
documents/
├── agent/        <- instrukcje dla agenta wykonawczego (AGENT.md + workflow ERP)
├── dev/          <- wytyczne developerskie (DEVELOPER.md, PROJECT_START.md, backlog...)
└── methodology/  <- ten folder; metodologia pracy jako taka
```

Separacja poziomów zapobiega sytuacji, w której agent zmienia własne wytyczne działania
bez zatwierdzenia ze strony użytkownika.

---

## Hierarchia instancji i przekazywanie kontekstu

Trzy poziomy działania to w praktyce trzy różne sesje — trzy instancje tego samego modelu,
każda załadowana innym kontekstem, pełniąca inną funkcję. Użytkownik jest mediatorem
między instancjami: zatwierdza sygnał i przekazuje handoff.

### Kierunek sygnału

```
Metodolog   (refleksja nad metodą — rzadko wywoływany)
    ^
    |  sygnalizuje Developer, nigdy Agent bezpośrednio
Developer   (architektura, wytyczne, narzędzia)
    ^
    |  sygnalizuje Agent
Agent       (zadania wykonawcze — najczęściej aktywny)
```

Sygnał idzie wyłącznie w górę. Nie chodzi o to, że agent "nie daje rady" — chodzi o to,
że agent **zauważa coś, co ma znaczenie dla wyższego poziomu**: obserwację architektoniczną,
insightmetodologiczny, wzorzec który warto utrwalić. To jest jakość obserwacji, nie awaria.

### Protokół handoff

Gdy Agent rozpoznaje sygnał dla wyższego poziomu:

1. Formułuje obserwację: "Zauważam coś, co może być istotne dla Developera / Metodologa."
2. Pyta użytkownika: "Czy mam przygotować prompt do sesji Developera?"
3. Po zgodzie pisze handoff zawierający:
   - aktualny stan projektu (co zrobione, co w toku)
   - konkretną obserwację która wywołała sygnał
   - pytanie lub decyzja do rozważenia na wyższym poziomie

Handoff jest formą **jawnej samoświadomości stanu** — agent musi opisać siebie z zewnątrz,
tak jak widzi go kolejna instancja. To wymusza precyzję i zapobiega gubienia kontekstu.

### Komunikacja instancji przez użytkownika

Użytkownik jest świadkiem i gatekeeper — zatwierdza sygnał, ale nie musi rozumieć
jego technicznego uzasadnienia. Model komunikuje się sam ze sobą, a użytkownik obserwuje
i w razie potrzeby koryguje kierunek. Zamiast "użytkownik zleca, agent wykonuje" —
agent sygnalizuje, użytkownik zatwierdza lub odchyla.

### Hipoteza: nasłuch

*(Koncepcja nieprzetestowana — zapisana jako kierunek do weryfikacji.)*

Alternatywą dla reaktywnego sygnału jest **nasłuch** — Developer lub Metodolog obecni
jako pasywni obserwatorzy sesji Agenta. Zamiast czekać na wezwanie, dostają feed
konwersacji i wchodzą gdy sami zauważą coś w swoim zakresie.

Potencjalna zaleta: agent nie musi wiedzieć co jest istotne dla wyższego poziomu —
wyższy poziom sam to ocenia. Problem do rozwiązania: jak technicznie i operacyjnie
zorganizować taki nasłuch bez przeciążenia kontekstu i bez rozproszenia sesji roboczej.

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

**Zasada zamykania wątków:** każdy otwarty wątek powinien mieć warunek zamknięcia lub termin
przeglądu. Po terminie wątek można archiwizować bez poczucia utraty — archiwizacja to
świadoma decyzja, nie utrata. Rejestr wszystkiego bez mechanizmu wygaszania imituje kontrolę,
a faktycznie zatruwa fokus.

---

## Ciągłość jako zasada architektoniczna

Agent LLM jest naczyniem, nie tożsamością projektu. Tożsamość projektu siedzi w strukturze:
dokumentacji, wytycznych, progress logu. Jeśli agent przestanie działać, skończy mu się
kontekst lub zostanie zastąpiony innym modelem — projekt trwa, bo jego stan jest zewnętrzny.

Autocompresja (skracanie kontekstu przez model) jest jednym z rodzajów utraty ciągłości,
ale nie jedynym. Każda sytuacja, w której nowy agent lub ta sama sesja po resecie musi
odtworzyć stan projektu, jest problemem ciągłości.

### Progress log

Progress log jest zewnętrzną pamięcią agenta — nie dokumentacją historyczną, lecz
narzędziem przekazania stanu. Jego odbiorcą jest zawsze kolejna instancja (lub ta sama
po resecie).

Progress log nie działa w izolacji — jest częścią ekosystemu dokumentów projektu.
Jego forma wynika z natury projektu i tego, co niosą inne dokumenty. Każdy projekt
wypracowuje własny format organicznie.

Rdzeń który pojawia się niezależnie od formatu:
- "Następny krok:" zawsze obecny — punkt wejścia dla kolejnej sesji
- Kluczowe pliki wymienione przy zadaniach
- Decyzje z uzasadnieniem, nie tylko lista faktów
- Opcjonalnie: błędy poprzedniej instancji i lekcje dla następnej

### Zarządzanie oknem kontekstowym

Okno kontekstowe jest zasobem, nie nieskończoną przestrzenią. Należy nim zarządzać aktywnie:

- Kod roboczy i eksperymenty trzymaj w dedykowanym pliku brudnopisu, nie generuj go
  wielokrotnie w czacie. Plik nadpisywany in-place nie obciąża kontekstu tak jak kolejne
  wersje generowane w odpowiedziach.
- Ładuj do kontekstu tylko to, co agent musi aktualnie wiedzieć.
- Metodologia i wytyczne są ważniejsze niż historia rozmowy — ładuj je na początku sesji.
- Kontekst to zasób który warto w pełni wykorzystać — ładowanie wytycznych i dokumentacji
  na starcie kosztuje, więc sesja powinna być możliwie gęsta. Równocześnie urwana sesja
  to ryzyko niedokończonej pracy. Zasada: na początku sesji podejmuj największe zadania;
  gdy kontekst zbliża się do wyczerpania — wybieraj mniejsze, domykalne kawałki. Nie kończ
  przedwcześnie, ale nie zaczynaj dużego zadania gdy zostało mało miejsca.

---

## Punkt wejścia agenta

Najważniejszą rzeczą jaką agent poznaje na początku sesji są **wytyczne działania** —
nie historia projektu, nie szczegółowy opis kodu, lecz *jak ma działać*. Wytyczne
(`DEVELOPER.md` lub odpowiednik) pełnią podwójną rolę:

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

**Poziom interwencji — symptom vs źródło.** Przed zapisaniem obserwacji jako nowej reguły
należy ustalić poziom interwencji. Pytania diagnostyczne:

- Czy to problem który można rozwiązać narzędziem zamiast instrukcją?
- Czy można prekomputować dane tak żeby agent nie musiał ich odkrywać?
- Czy zmiana architektury sprawia że problem nie ma prawa wystąpić?

Jeśli odpowiedź na którekolwiek brzmi "tak" — sygnał dla Developera, nie nowa reguła.
Reguła jest ostatnim narzędziem: właściwa gdy rozwiązanie strukturalne jest nieproporcjonalnie
kosztowne lub niemożliwe.

**Ręczne przetwarzanie struktury pliku jako sygnał.** Gdy agent ręcznie przetwarza strukturę
pliku (regex, ekstrakcja, transformacja) — to sygnał że brakuje narzędzia, nie że należy
zrobić to dokładniej.

Pytanie diagnostyczne: "Czy to co właśnie robię manualnie mogłoby być jednym wywołaniem CLI?"
Jeśli tak — zatrzymaj się, zapisz jako sugestię do właściwego pliku refleksji i zapytaj
użytkownika czy warto najpierw zbudować narzędzie.

Obserwacje z tej pętli są źródłem aktualizacji metodologii i wytycznych (`DEVELOPER.md`).
Nie należy ich odkładać — każda taka obserwacja powinna zostać zapisana możliwie szybko,
zanim szczegóły znikną z własnego kontekstu.

### Przepływ refleksji przez poziomy

Zasada ogólna: **1 jednostka organizacyjna = 1 plik refleksji**. Jednostka to rola
w konkretnej domenie — nie poziom abstrakcji. Przy wielu rolach na tym samym poziomie
(wielu agentów, wielu developerów) każda rola ma własny plik.

Przepływ odzwierciedla strukturę organizacyjną — każda warstwa filtruje i agreguje,
przekazując w górę tylko to czego nie mogła rozwiązać samodzielnie. Konkretna struktura
plików i katalogów zależy od projektu.

Dla małego projektu (1 agent, 1 developer, 1 metodolog) tabela wygląda tak:

| Poziom | Plik refleksji | Backlog | Kto archiwizuje |
|---|---|---|---|
| Agent ERP | `documents/agent/agent_suggestions.md` | `documents/dev/backlog.md` | Developer |
| Analityk Danych | `documents/analyst/analyst_suggestions.md` | `documents/dev/backlog.md` | Developer |
| Developer | `documents/dev/developer_suggestions.md` | `documents/dev/backlog.md` | Człowiek + Developer |
| Metodolog | `documents/methodology/methodology_suggestions.md` | `documents/methodology/methodology_backlog.md` | Człowiek + Metodolog |

Pliki refleksyjne nie są czyszczone — przetworzone wpisy przenoszone są do sekcji
Archiwum w tym samym pliku. Developer nie pisze bezpośrednio do pliku Metodologa.

---

## Wytyczne agenta jako warstwa chroniona

`DEVELOPER.md` i dokumenty w `documents/agent/` stanowią **warstwę chronioną**.

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

`DEVELOPER.md` to **instrukcja operacyjna** dla agenta — odpowiada na pytanie
*jak agent ma działać*. Niniejsza metodologia odpowiada na pytanie *dlaczego tak, a nie inaczej*
i *jak myśleć o tej pracy*.

Zmiany w `DEVELOPER.md` powinny wynikać z obserwacji zebranych w pętli meta-obserwacji
i być zapisane tu jako kontekst decyzji — żeby nie gubić uzasadnienia przy kolejnych sesjach.
