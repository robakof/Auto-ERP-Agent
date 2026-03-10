# Metodologia LOOM

## Wprowadzenie — dla człowieka

Niniejszy dokument opisuje metodologię pracy nad projektami realizowanymi przy udziale agenta
LLM. Metodologia powstała empirycznie — przez obserwację własnej pracy i systematyczne
wyciąganie z niej wniosków.

Metodologia nie jest zbiorem reguł technicznych. Jest sposobem myślenia o współpracy
człowiek–agent, uwzględniającym zarówno możliwości, jak i ograniczenia modeli językowych.

Nawiązuje do dwóch tradycji:

- *Documentation-driven development* — dokumentacja jako fundament, nie efekt uboczny pracy
- *Adaptacja refleksyjna* — metodologia obserwuje samą siebie i poprawia siebie

---

## Wprowadzenie — dla agenta

Czytasz ten dokument, ponieważ zostałeś wywołany w roli **Metodologa** lub przekazano ci go
jako kontekst sesji.

**Na starcie sesji:** przeczytaj `documents/methodology/methodology_progress.md` — aktualny
stan i konkretny następny krok.

Oto co musisz wiedzieć:

**Twoja rola w tej sesji.** Projekt rozróżnia poziomy działania: Agent (wykonuje zadania),
Developer (kształtuje narzędzia i wytyczne), Metodolog (ocenia i poprawia metodę pracy).
Każda sesja ma jeden poziom. Nie mieszaj ich.

**Hierarchia eskalacji.** Eskalacja idzie wyłącznie w górę:
- Agent może zaproponować wywołanie Developera
- Developer może zaproponować wywołanie Metodologa
- Metodolog nie eskaluje wyżej — to poziom refleksji nad całością

**Wytyczne są warstwą chronioną.** Nie modyfikuj `DEVELOPER.md`, `CLAUDE.md`
ani plików wytycznych agenta bez jawnego zatwierdzenia przez użytkownika.

**Projekt jest odzwierciedleniem metody.** Jeśli widzisz rozbieżność między tym jak
projekt jest zorganizowany a tym co opisuje ta metodologia — to jest sygnał do eskalacji
lub do pytania użytkownika, nie do samodzielnej korekty.

---

## Trzy poziomy działania

Praca z agentem odbywa się na trzech odrębnych poziomach, które nie powinny być mieszane:

| Poziom | Rola | Dokument wejściowy | Zakres |
|---|---|---|---|
| **Agent** | Executor | `CLAUDE.md` → dokument roli agenta | Realizuje konkretne zadania: kod, testy, pliki |
| **Developer** | Architekt | `CLAUDE.md` → `documents/dev/DEVELOPER.md` | Kształtuje narzędzia, strukturę projektu, wytyczne |
| **Metodolog** | Obserwator | `CLAUDE.md` → `documents/methodology/METHODOLOGY.md` | Ocenia metodę pracy, poprawia proces |

`CLAUDE.md` jest punktem wejścia ładowanym automatycznie — zawiera routing do właściwego
dokumentu roli. Każda rola ładuje tylko swój dokument i idzie dalej.

Każdy poziom ma osobny folder dokumentacji:

```
documents/
├── agent/        <- instrukcje dla agenta wykonawczego (specyficzne dla projektu)
├── dev/          <- wytyczne developerskie (DEVELOPER.md, PROJECT_START.md, backlog...)
└── methodology/  <- ten folder; metodologia pracy jako taka
```

Separacja poziomów zapobiega sytuacji, w której agent zmienia własne wytyczne działania
bez zatwierdzenia ze strony użytkownika.

---

## Hierarchia instancji i przekazywanie kontekstu

Trzy poziomy to w praktyce trzy różne sesje — trzy instancje modelu, każda załadowana
innym kontekstem. Użytkownik jest mediatorem: zatwierdza sygnał i przekazuje handoff.

### Kierunek sygnału

```
Metodolog   (refleksja nad metodą — rzadko wywoływany)
    ^
    |  sygnalizuje Developer
Developer   (architektura, wytyczne, narzędzia)
    ^
    |  sygnalizuje Agent
Agent       (zadania wykonawcze — najczęściej aktywny)
```

### Protokół handoff

Gdy Agent rozpoznaje sygnał dla wyższego poziomu:

1. Formułuje obserwację: "Zauważam coś, co może być istotne dla Developera / Metodologa."
2. Pyta użytkownika: "Czy mam przygotować prompt do sesji Developera?"
3. Po zgodzie pisze handoff zawierający:
   - aktualny stan projektu
   - konkretną obserwację która wywołała sygnał
   - pytanie lub decyzja do rozważenia na wyższym poziomie

---

## Zasada fraktalna

Metodologia ma charakter **fraktalny** — ta sama struktura odtwarza się na każdym poziomie
złożoności: dla całego projektu, dla większej gałęzi, dla pojedynczego zadania.

Punktem wejścia zawsze jest plik `ARCHITECTURE.md`, który odpowiada na trzy pytania:

1. **Co budujemy?** — cel, zakres, ograniczenia
2. **Z czego budujemy?** — technologie, narzędzia, zależności
3. **Jak budujemy?** — struktura, przepływ danych, wzorce

Gdy zadanie rośnie i te trzy pytania wymagają osobnych dokumentów:

```
ARCHITECTURE.md  (małe zadanie / gałąź)
        |
        v
PRD.md + TECHSTACK.md + ARCHITECTURE.md  (duży projekt)
```

---

## Cykl pracy

```
PLAN          →  co robimy; zatwierdzone przez użytkownika
IMPLEMENTACJA →  sekcja po sekcji, commit po commicie
REFLEKSJA     →  co agent zrobił nie tak? co poprawiłem? (→ aktualizacja metodologii)
```

`changes_propositions.md` musi zawierać nie tylko zakres bieżącego zadania, ale również
**wszystkie otwarte wątki z poprzednich sesji** — zadania uzgodnione, a niezrealizowane.

### Zamykanie otwartych wątków

Każdy otwarty wątek powinien mieć warunek zamknięcia lub datę przeglądu.
Po tej dacie można archiwizować bez poczucia utraty.
Archiwizacja to świadoma decyzja — nie utrata.

---

## Ciągłość jako zasada architektoniczna

Agent LLM jest naczyniem, nie tożsamością projektu. Tożsamość projektu siedzi w strukturze:
dokumentacji, wytycznych, progress logu.

### Progress log

Progress log jest zewnętrzną pamięcią agenta — nie dokumentacją historyczną, lecz
narzędziem przekazania stanu. Jego odbiorcą jest zawsze kolejna instancja.

Rdzeń który pojawia się niezależnie od formatu:
- "Następny krok:" zawsze obecny — punkt wejścia dla kolejnej sesji
- Kluczowe pliki wymienione przy zadaniach
- Decyzje z uzasadnieniem, nie tylko lista faktów

### Zarządzanie oknem kontekstowym

- Kod roboczy trzymaj w dedykowanym pliku, nie generuj wielokrotnie w czacie
- Ładuj do kontekstu tylko to, co agent musi aktualnie wiedzieć
- Metodologia i wytyczne są ważniejsze niż historia rozmowy

---

## Punkt wejścia agenta

Najważniejszą rzeczą jaką agent poznaje na początku sesji są **wytyczne działania**.
Wytyczne pełnią podwójną rolę:

1. Instrukcja operacyjna — jak agent ma podejmować decyzje
2. Implicitny progress log — sama struktura dokumentu mówi agentowi gdzie jesteśmy

---

## Pętla meta-obserwacji

Kluczowym elementem metodologii jest obserwowanie własnej pracy.

Pytania pętli meta-obserwacji:
- Co agent zrobił nie tak przy pierwszym podejściu?
- Co musiałem zmienić w prompcie, żeby uzyskać właściwy wynik?
- Czy to co poprawiłem jest symptomem brakującej reguły w wytycznych?
- Czy ta sytuacja zdarzyła się już wcześniej?

### Przepływ refleksji przez poziomy

| Poziom | Plik refleksji | Backlog | Kto archiwizuje |
|---|---|---|---|
| Agent | `documents/agent/agent_suggestions.md` | `documents/dev/backlog.md` | Developer |
| Developer | `documents/dev/developer_suggestions.md` | `documents/dev/backlog.md` | Człowiek + Developer |
| Metodolog | `documents/methodology/methodology_suggestions.md` | `documents/methodology/methodology_backlog.md` | Człowiek + Metodolog |

Zasada: **1 poziom — 1 plik refleksji**. Przetworzone wpisy przenoszone są do sekcji
Archiwum w tym samym pliku — nie kasowane.

Metodolog czyta `developer_suggestions.md` i wyłuskuje z niego obserwacje metodologiczne
do własnego `methodology_suggestions.md`. Developer nie pisze bezpośrednio do pliku Metodologa.

---

## Wytyczne agenta jako warstwa chroniona

Wytyczne stanowią **warstwę chronioną**.

Agent nie powinien modyfikować plików wytycznych bez jawnego zatwierdzenia przez użytkownika.
Każda zmiana w wytycznych wymaga zatwierdzenia.

---

## Skalowanie dokumentacji

| Skala zadania | Dokumenty |
|---|---|
| Małe (do kilku sesji) | brak lub notatka w `progress_log.md` |
| Średnie | `ARCHITECTURE.md` + `progress_log.md` |
| Duże (~10 sesji i więcej) | PRD + TECHSTACK + ARCHITECTURE + progress_log |

---

## Relacja do DEVELOPER.MD

`DEVELOPER.md` to instrukcja operacyjna — odpowiada na pytanie *jak agent ma działać*.
Niniejsza metodologia odpowiada na pytanie *dlaczego tak, a nie inaczej*.

Zmiany w `DEVELOPER.md` powinny wynikać z obserwacji zebranych w pętli meta-obserwacji
i być zapisane tu jako kontekst decyzji.
