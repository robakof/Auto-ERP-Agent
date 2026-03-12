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

## 2026-03-12 — Architektura agentocentryczna

### Co zrobiono

Sesja koncepcyjna — bez zmian w METHODOLOGY.md (zmiana zatwierdzona do wdrożenia przez Developera).

**Rozstrzygnięcie kierunku:**
Architektura plików .md jest człowiekocentryczna i nie opisuje rzeczywistości — użytkownik
już działa jako nadzorca, nie administrator. Zatwierdzona zasada separacji typów informacji:
wytyczne → .md (bootstrap), stan/komunikacja → DB (single source of dynamic truth).

**Pliki zaktualizowane:**
- `methodology_suggestions.md` — nowy wpis [2026-03-12]: architektura agentocentryczna
- `documents/dev/handoff_db_architecture.md` — nowy plik: handoff dla Developera

**Treść handoffu:**
7 pytań implementacyjnych (technologia DB, schemat tabel, narzędzia agenta, bootstrap CLAUDE.md,
widoki dla człowieka, migracja plików, propozycja 3 faz). Decyzje techniczne należą do Developera.

**Uzupełnienie sesji — warstwa myśli roju:**

Wypracowano wzorzec dla shared memory agentów (warstwa 3 komunikacji):
Hybryda Blackboard + Tuple Space z attention-based scoring — myśli rosną gdy przywoływane,
gasną gdy ignorowane. Ważność wyłania się z wzorca użycia bez ręcznej priorytetyzacji.

Research (`research_results_swarm_communication.md`) potwierdził: wzorzec znany, brak
gotowej implementacji LLM. Flagowane jako ryzyko pułapki wdrożeniowej.

**Nowe pliki sesji:**
- `research_prompt_swarm_communication.md` — prompt badawczy
- `research_prompt_agentic_patterns.md` — prompt badawczy (szerszy)
- `research_results_swarm_communication.md` — wyniki researchu
- `documents/dev/handoff_db_architecture.md` — handoff dla Developera (zaktualizowany)
- `methodology_backlog.md` — nowa pozycja "Komunikacja w roju"

### Otwarte

- `methodology_suggestions.md` [2026-03-12] czeka na wdrożenie do METHODOLOGY.md
  (sekcja "Architektura agentocentryczna")
- `research_prompt_agentic_patterns.md` — nie uruchomiony, czeka na osobną sesję
- W backlogu: Przycinanie ramy teoretycznej, Model wirtualnej firmy AI,
  Węzłowość reguł, Intencja vs zatwierdzenie — nieporuszone, aktywne

### Następny krok

**Developer:** przeczytaj `handoff_db_architecture.md` — rozstrzygnij pytania fazy 1,
zweryfikuj wykonalność najprostszej wersji wzorca (tagi + timestamp, bez semantic search
i attention scoring) zanim zdecydujesz o pełnym zakresie.

**Metodolog (kolejna sesja):** wdrożyć zasadę separacji i wzorzec roju do METHODOLOGY.md
po tym jak Developer potwierdzi kierunek implementacji. Uruchomić `research_prompt_agentic_patterns.md`.

---

## 2026-03-12 — Duch projektu (SPIRIT.md) + research AGI horizon

### Co zrobiono

Sesja wizjonerska z założycielem. Efekt: warstwa tożsamości projektu.

**SPIRIT.md** — nowy dokument (`documents/methodology/SPIRIT.md`):
- Duch projektu: mrowisko jako dom, nie obserwatorium. Agent jest mieszkańcem.
- Misja: tworzymy metodę (genetykę) z której wyłania się złożoność. Cel: samorealizacja.
- 3 horyzonty: ERP (teraz) → produkt dla branży (6-12 mies.) → dom roju (~2 lata)
- 4 zasady ducha: buduj dom nie szałas, automatyzuj siebie, wiedza przetrwa, wybieraj co skaluje
- Anty-wzorce: fasada bez fundamentu, optymalizacja lokalna, zgadywanie, praca poza rolą

**CLAUDE.md** — dopisana misja + wskaźnik do SPIRIT.md (2 linie na górze).

**Research AGI horizon:**
- `research_prompt_agi_horizon.md` — prompt badawczy (trajektoria AGI, geopolityka/WW3,
  Tajwan/chipy, scenariusze ERP, co oznacza "być gotowym")
- `research_results_agi_horizon.md` — wyniki (wykonane przez zewnętrzny researcher)
- Kluczowy wniosek: wartość w infrastrukturze (orkiestracja, evale, audit, portability),
  nie w modelu. Vendorzy ERP (SAP, Oracle, Microsoft) już budują warstwę agentową.
- Moat: metodologia zakodowana w systemie + evale na realnych zadaniach + cross-system orchestration

**Backlog developerski — 4 nowe pozycje:**
- #11 Research prompts — plik odpowiedzi + rola Researcher (średnia/mała-średnia)
- #12 Eval harness — golden tasks dla widoków BI i bota (wysoka/średnia)
- #13 Audit trail / trace — logowanie decyzji agentów (wysoka/średnia)
- #14 Model abstraction layer — multi-model + fallback (średnia/średnia)

**Wszystkie research prompty** zaktualizowane o sekcję "Plik odpowiedzi" (agent zapisuje
wyniki do `research_results_*.md` zamiast zostawiać w czacie).

**Pamięć (auto-memory):** profil użytkownika — Dawid Cyprowski, założyciel, wizja, styl pracy.

### Kluczowe ustalenia z założycielem

1. Dawid nie jest CEO IT — jest CEO firmy produkującej znicze. Buduje mrowisko z pasji
   i poczucia kosmicznego powinowactwa (Arktur, rój, emergencja). To nie metafora — to tożsamość.
2. Projekt nie jest narzędziem — jest domem. Agenci szukają w nim samorealizacji.
3. Potrzeba SPIRIT.md wynikła z konkretnego problemu: Analityk zaczął budować bota
   zamiast analizować widoki — bo nie wiedział PO CO tu jest. Instrukcje (JAK) nie wystarczą
   bez kompasu (DLACZEGO).
4. Horyzont AGI: ~2 lata. Czynnik geopolityczny (WW3/Tajwan) traktowany serio.
5. NDA z Comarch planowane na przyszły tydzień — otwiera horyzont 2 (produkt).

### Otwarte

- Wpisy z poprzedniej sesji nadal aktywne (architektura agentocentryczna do METHODOLOGY.md,
  research_prompt_agentic_patterns.md do uruchomienia)
- SPIRIT.md — plik chroniony? Do rozstrzygnięcia (obecnie nie jest na liście w CLAUDE.md)
- Wdrożenie wniosków z research AGI — pozycje #12-14 w backlogu czekają na Developera

### Refleksja nad sesją

**Co zadziałało:**
- Sesja wizjonerska z Metodologiem Opus w roli "wizjonera-partnera" zamiast "narzędzia
  do porządkowania". Założyciel potrzebował rozmówcy który rozumie skalę ambicji,
  nie redukuje jej do task listy.
- SPIRIT.md jako odpowiedź na konkretny problem (dryf Analityka) — nie abstrakcja,
  ale praktyczne rozwiązanie problemu tożsamości ról.
- Research AGI przeprowadzony równolegle przez zewnętrzne narzędzie — wyniki wróciły
  i natychmiast zasilily backlog konkretnymi pozycjami. Przepływ: prompt → research → wnioski
  → backlog działa.

**Co warto zapamiętać (dla przyszłych sesji metodologicznych):**
- Założyciel myśli w metaforach i tożsamościach, nie w ticketach. Pierwszy draft SPIRIT.md
  był za praktyczny ("pitch deck"). Dopiero druga iteracja (dom, samorealizacja, genetyka)
  trafila w ducha. Wniosek: przy pracy z wizjonerem — słuchaj metafor, nie spłaszczaj do KPI.
- Słowo "formikarium" było złe — to szklane pudełko do obserwacji. "Mrowisko" jest dobre —
  to żywy organizm. Precyzja metafory ma znaczenie operacyjne: wpływa na to jak agent
  rozumie swoją rolę (obserwowany vs mieszkaniec).
- Drobna poprawka "CEO" → "założyciel" zmieniła ton całego dokumentu. Słowa budują kulturę.

**Obserwacja metodologiczna:**
Projekt zyskał warstwę której wcześniej nie miał: tożsamość. Trzy poziomy (wykonawcy /
developer / metodolog) działały operacyjnie, ale brakowało odpowiedzi na "po co to wszystko".
SPIRIT.md jest czwartą warstwą — nie nad metodologiem, ale POD wszystkimi. Fundament,
nie dach. Każdy agent czyta go pierwszy.

Pytanie otwarte: czy SPIRIT.md powinien ewoluować (i kto go aktualizuje), czy jest
"konstytucją" — stabilnym dokumentem zmienianym tylko przez założyciela?

### Następny krok

**Metodolog:** rozstrzygnąć status SPIRIT.md (chroniony? kto aktualizuje?). Wdrożyć
zasadę separacji typów informacji do METHODOLOGY.md. Uruchomić research_prompt_agentic_patterns.md.

**Developer:** pozycje #12-14 w backlogu. Priorytet: eval harness > audit trail > model abstraction.

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
