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

## Archiwum

### ✓ [2026-03-09] Przepływ refleksji przez poziomy — wdrożony

Propozycja z sekcji "Refleksja wielopoziomowa i proaktywność agenta" wdrożona:
- Stworzono: `agent_suggestions.md`, `developer_suggestions.md`, `backlog.md`, `methodology_backlog.md`
- Zaktualizowano: `CLAUDE.md` (refleksja po zadaniu + pliki chronione), `AI_GUIDELINES.md` (krok startowy), `METHODOLOGY.md` (podsekcja przepływu refleksji)
- Zasada: 1 poziom — 1 plik refleksji, archiwum zamiast kasowania
