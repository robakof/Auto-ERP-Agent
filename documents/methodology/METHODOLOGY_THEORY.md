# Metodologia pracy z agentem LLM — uzasadnienia i teoria

Dokument referencyjny. Zawiera uzasadnienia decyzji metodologicznych, hipotezy
do weryfikacji i kontekst filozoficzny. Ładuj opcjonalnie — nie jest wymagany
do operacyjnej pracy Metodologa.

Instrukcje operacyjne Metodologa: `documents/methodology/METHODOLOGY.md`.

---

## Tradycje i fundamenty

Metodologia powstała empirycznie — przez obserwację własnej pracy i systematyczne
wyciąganie z niej wniosków.

Nie jest zbiorem reguł technicznych. Jest sposobem myślenia o współpracy
człowiek-agent, uwzględniającym zarówno możliwości, jak i ograniczenia modeli językowych.
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

## Trzy poziomy działania

Praca z agentem odbywa się na trzech odrębnych poziomach, które nie powinny być mieszane:

| Poziom | Rola | Zakres |
|---|---|---|
| **Wykonawcy** | Executor | Realizują zadania w swojej domenie (może być wiele ról wykonawczych) |
| **Developer** | Architekt | Kształtuje narzędzia, strukturę projektu, wytyczne |
| **Metodolog** | Obserwator | Ocenia metodę pracy, kształtuje prompty, poprawia proces |

*Aktualna lista ról i dokumentów wejściowych: `CLAUDE.md`. Tabela powyżej opisuje poziomy
koncepcyjnie — jest przykładem struktury, nie stanem konkretnego projektu.*

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
insight metodologiczny, wzorzec który warto utrwalić. To jest jakość obserwacji, nie awaria.

### Handoff jako samoświadomość stanu

Handoff jest formą jawnej samoświadomości stanu — agent musi opisać siebie z zewnątrz,
tak jak widzi go kolejna instancja. To wymusza precyzję i zapobiega gubieniu kontekstu.

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

---

## Cykl pracy

Metodologia wyznacza cykl pracy, który odtwarza się rekurencyjnie. Nie każdy poziom wymaga
wszystkich kroków — decyduje złożoność zadania:

```
PLAN          →  co robimy; zatwierdzone przez użytkownika
IMPLEMENTACJA →  sekcja po sekcji, commit po commicie
REFLEKSJA     →  co agent zrobił nie tak? co poprawiłem? (→ aktualizacja metodologii)
```

**Zasada otwartych wątków:** każdy plan musi zawierać nie tylko zakres bieżącego zadania,
ale również wszystkie otwarte wątki z poprzednich sesji. Brak tego wymogu prowadzi
do gubienia zadań przy rozroście zakresu lub utracie ciągłości.

**Zasada zamykania wątków:** każdy otwarty wątek powinien mieć warunek zamknięcia
lub termin przeglądu. Archiwizacja to świadoma decyzja, nie utrata.

---

## Ciągłość jako zasada architektoniczna

Agent LLM jest naczyniem, nie tożsamością projektu. Tożsamość projektu siedzi w strukturze:
dokumentacji, wytycznych, progress logu. Jeśli agent przestanie działać, skończy mu się
kontekst lub zostanie zastąpiony innym modelem — projekt trwa, bo jego stan jest zewnętrzny.

### Progress log

Progress log jest zewnętrzną pamięcią agenta — nie dokumentacją historyczną, lecz
narzędziem przekazania stanu. Jego odbiorcą jest zawsze kolejna instancja.

Rdzeń niezależny od formatu:
- "Następny krok:" zawsze obecny — punkt wejścia dla kolejnej sesji
- Kluczowe pliki wymienione przy zadaniach
- Decyzje z uzasadnieniem, nie tylko lista faktów

### Zarządzanie oknem kontekstowym

Okno kontekstowe jest zasobem, nie nieskończoną przestrzenią:

- Kod roboczy trzymaj w pliku brudnopisu, nie generuj wielokrotnie w czacie.
- Ładuj do kontekstu tylko to, co agent musi aktualnie wiedzieć.
- Metodologia i wytyczne ważniejsze niż historia rozmowy — ładuj na początku sesji.
- Na początku sesji podejmuj największe zadania; gdy kontekst się kończy — mniejsze,
  domykalne kawałki.

---

## Pętla meta-obserwacji — uzasadnienie

Pytania pętli meta-obserwacji:

- Co agent zrobił nie tak przy pierwszym podejściu?
- Co musiałem zmienić w prompcie, żeby uzyskać właściwy wynik?
- Czy to co poprawiłem jest symptomem brakującej reguły w wytycznych?
- Czy ta sytuacja zdarzyła się już wcześniej?

**Poziom interwencji — symptom vs źródło.** Przed zapisaniem obserwacji jako nowej reguły
należy ustalić poziom interwencji:

- Czy to problem który można rozwiązać narzędziem zamiast instrukcją?
- Czy można prekomputować dane tak żeby agent nie musiał ich odkrywać?
- Czy zmiana architektury sprawia że problem nie ma prawa wystąpić?

Reguła jest ostatnim narzędziem: właściwa gdy rozwiązanie strukturalne jest nieproporcjonalnie
kosztowne lub niemożliwe.

**Ręczne przetwarzanie jako sygnał.** Gdy agent ręcznie przetwarza strukturę pliku —
to sygnał że brakuje narzędzia, nie że należy zrobić to dokładniej.

---

## Skalowanie dokumentacji

Objętość dokumentacji powinna być proporcjonalna do złożoności zadania.

| Skala zadania | Dokumenty |
|---|---|
| Małe (do kilku sesji) | log sesji w DB |
| Średnie | `ARCHITECTURE.md` + log sesji w DB |
| Duże (~10+ sesji, wiele modułów) | PRD + TECHSTACK + ARCHITECTURE + log sesji w DB |

---

## Relacja do promptów ról

Prompty ról (`DEVELOPER.md`, `ERP_SPECIALIST.md` itp.) to instrukcje operacyjne —
odpowiadają na pytanie *jak agent ma działać*. Niniejsza metodologia odpowiada
na pytanie *dlaczego tak, a nie inaczej* i *jak myśleć o tej pracy*.

Zmiany w promptach ról powinny wynikać z obserwacji zebranych w pętli meta-obserwacji.
