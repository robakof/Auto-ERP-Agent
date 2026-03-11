# Progress log — warstwa metodologiczna

Zewnętrzna pamięć sesji metodologicznych. Odbiorcą jest kolejna instancja Metodologa.

Rdzeń każdego wpisu: stan po sesji + konkretny następny krok.

---

## 2026-03-09 — Inicjalizacja systemu refleksji

### Co zrobiono

Wdrożono trójpoziomowy system refleksji (propozycja z `methodology_suggestions.md`):

**Nowe pliki:**
- `documents/agent/agent_suggestions.md` — refleksja agenta po etapie pracy
- `documents/dev/developer_suggestions.md` — refleksja developera
- `documents/dev/backlog.md` — priorytety developerskie (zasilony z `agent_reflections.md`)
- `documents/methodology/methodology_backlog.md` — priorytety metodologiczne
- `documents/methodology/methodology_progress.md` — ten plik

**Zaktualizowane pliki:**
- `CLAUDE.md` — sekcja "Refleksja po etapie pracy" + jawna lista plików chronionych
- `AI_GUIDELINES.md` — krok startowy "Agent Suggestions" z human in the loop
- `METHODOLOGY.md` — podsekcja "Przepływ refleksji przez poziomy"
- `methodology_suggestions.md` — sekcja Archiwum

**Zasady systemu:**
- 1 poziom = 1 plik refleksji (agent / developer / metodolog)
- Pliki refleksyjne: append + archiwum, nie kasowanie
- Developer archiwizuje `agent_suggestions.md` po przeglądzie z człowiekiem
- Metodolog wyłuskuje obserwacje metodologiczne z `developer_suggestions.md`

### Otwarte w backlogu metodologicznym

Dwie pozycje w `methodology_backlog.md`:
1. Reguła zamykania otwartych wątków (do METHODOLOGY.md)
2. Przycinanie ramy teoretycznej (do METHODOLOGY.md, niski priorytet)

### Następny krok

Wdrożenie pozycji z `methodology_backlog.md`:
- Zacznij od reguły zamykania wątków — dodaj do sekcji "Cykl pracy" w METHODOLOGY.md
- Oceń czy przycinanie teorii ma sens teraz czy odkłada się dalej

---

## 2026-03-11 — Wdrożenie zasad do METHODOLOGY.md + porządki backlogu

### Co zrobiono

**METHODOLOGY.md — nowe zasady:**
- Sekcja "Cykl pracy": Zasada zamykania wątków (termin przeglądu, archiwizacja jako świadoma decyzja)
- Sekcja "Zarządzanie oknem kontekstowym": zasada rytmu sesji (duże zadania na starcie, małe gdy kontekst się kończy)
- Sekcja "Pętla meta-obserwacji": Poziom interwencji — symptom vs źródło (pytania diagnostyczne przed nową regułą)
- Sekcja "Pętla meta-obserwacji": Ręczne przetwarzanie jako sygnał brakującego narzędzia

**Porządki:**
- `methodology_backlog.md`: 3 pozycje zarchiwizowane, 1 nowa (wielość ról wykonawczych)
- `backlog.md` (dev): LOOM przeniesiony z otwartych wątków metodologicznych
- `methodology_suggestions.md`: niezmieniony — "przycinanie ramy teoretycznej" nadal aktywne

### Otwarte

- Wielość ról wykonawczych — zasada 1 rola = 1 plik refleksji (methodology_backlog.md)
- Przycinanie ramy teoretycznej (methodology_backlog.md, niska pilność)

### Następny krok

Rozstrzygnąć kwestię wielości ról wykonawczych (Agent ERP, Analityk) przed kolejną sesją
developerską dotyczącą Analityka. Ref. dev backlog [Arch] Separacja pamięci.

---

## 2026-03-09 — Przebudowa architektury wytycznych + inicjalizacja LOOM

### Co zrobiono

**Przebudowa plików wytycznych (ERP projekt):**
- `CLAUDE.md` skrócony do routingu (~50 linii): opis projektu, tabela ról, pliki chronione, eskalacja
- Nowy `documents/agent/AGENT.md` — instrukcje operacyjne agenta ERP: walidacja środowiska, routing zadań, narzędzia, zasada prawdy, rozszerzona eskalacja (infrastruktura)
- `AI_GUIDELINES.md` → `DEVELOPER.md` (git mv) + routing header + reguła skali zadania
- Nowy `documents/dev/PROJECT_START.md` — workflow inicjalizacji, wyodrębniony z DEVELOPER.md
- `METHODOLOGY.md` — routing header, tabela ról zaktualizowana, referencje AI_GUIDELINES→DEVELOPER

**LOOM — metodologia jako osobne repo:**
- Folder `_loom/` z kompletem plików gotowych do wypchnięcia na GitHub
- `seed.md` — bootstrap nowego projektu (kopiuj jako CLAUDE.md, agent konfiguruje resztę)
- `CLAUDE_template.md` — szablon z placeholderami
- `DEVELOPER.md`, `PROJECT_START.md` — oczyszczone z ERP-specifiku
- `METHODOLOGY.md` — oczyszczona, z regułą zamykania wątków, bez ERP-referencji
- Szablony refleksji i backlogów — puste, gotowe do kopiowania przez seed

### Otwarte

- `_loom/` czeka na repo GitHub (`CyperCyper/loom` lub inna nazwa) i push
- URL w `seed.md` zawiera placeholder — do zaktualizowania po utworzeniu repo
- `methodology_backlog.md`: reguła zamykania wątków wdrożona w LOOM/METHODOLOGY.md; do przepisania w ERP METHODOLOGY.md
- Przycinanie ramy teoretycznej — odkłada się (niska pilność)

### Następny krok

Projekt transport: utwórz nowe repo → skopiuj `_loom/seed.md` jako `CLAUDE.md` → uruchom agenta.
