# Plan stabilizacji systemu Mrowisko

Data: 2026-03-27 | Autor: Dyspozytor | Status: DRAFT — do zatwierdzenia przez człowieka

---

## Diagnoza

System rozwijał się w szybkim tempie. Architektura koncepcyjna wyprzedziła wdrożenie.
Poniżej mapa problemów uporządkowana od najbardziej do najmniej krytycznych.

---

## P1: Dashboard pokazuje fałszywy stan (bug techniczny)

**Objaw:** Dashboard w Mrowisko.md wyświetla 4 aktywne sesje. Faktycznie działa 1.

**Przyczyna:**
- `render_dashboard.py` liczy sesje z `session_log` (kto miał "session started" w ostatnich 24h)
  zamiast sprawdzać `sessions.ended_at IS NULL` lub tabelę `live_agents`.
- 7 rekordów `workflow_execution` w statusie "running" z 25-26 marca nigdy nie zamknięto
  (`workflow-end`). Funkcja `_session_status()` widzi je i pokazuje status "Praca".
- Tabela `sessions.role` jest zawsze NULL (backlog #197).

**Naprawa (Developer):**
1. `render_dashboard.py` — zmienić źródło na `live_agents` (status IN starting/active)
   lub `sessions` z filtrem `ended_at IS NULL`.
2. Zamknąć 7 stale workflow_execution (IDs 8, 9, 10, 13, 15, 24, 27) jako `abandoned`.
3. Backlog #197 (session heartbeat + role w sessions) — zrealizować.

**Effort:** maly-sredni | **Value:** wysoka (fundament operacyjny Dyspozytora)

---

## P2: Inboxy zaśmiecone — 91 nieprzeczytanych wiadomości

**Objaw:** Każda rola ma inbox pełen wiadomości, które nigdy nie zostały oznaczone jako przeczytane.
Mechanizm mark-as-read nie działał lub nie był używany.

**Rozkład:**

| Kategoria | ~Ilość | Opis |
|-----------|--------|------|
| Historyczne/zakończone | ~50 | Cykle review BI (TraElem, ZamElem, MagNag, MagElem) — praca dawno ukończona |
| Broadcasty informacyjne | ~18 | Ogłoszenia Developer o nowych narzędziach (3 broadcasty x 6 ról) |
| Actionable | ~17 | Wymagają decyzji lub pracy (PE: 10, Metodolog: 7, Architect: 4) |
| Cancelled/noise | ~5 | Anulowane handoffy (git_commit.py gate) |
| Stale (>1 tydzień) | 1 | Metodolog msg #3 z 13 marca |

**Naprawa (Dyspozytor — ja):**
1. Przygotować listę wiadomości do bulk mark-as-read (historyczne + broadcasty + cancelled).
2. Wydzielić z 17 actionable te, które mają już pokrycie w backlogu.
3. Dla actionable bez pokrycia — dodać backlog items lub oznaczyć jako resolved.
4. Potrzebuję narzędzia `mark-read` w agent_bus_cli. **Czy istnieje?** Jeśli nie — backlog item.

**Effort:** sredni (triażowanie wymaga czytania treści) | **Value:** wysoka

---

## P3: Agenci nie przestrzegają workflow (problem systemowy)

**Objaw:** Agenci nie wchodzą w workflow (`workflow-start`), nie logują kroków (`step-log`),
pomijają fazy. Udokumentowane naruszenie: sesja Architekta 2026-03-25 (pominięcie Fazy 2,
błędna interpretacja handoff point).

**Stan wątku:**
- Research compliance (prompt-level): DONE — `documents/researcher/research/workflow_compliance.md`
- Konwencja: DONE — `documents/conventions/CONVENTION_WORKFLOW.md` v1.4 (13 reguł, HANDOFF_POINT)
- Diagnoza: DONE — `documents/human/reports/workflow_violation_diagnosis_2026_03_25.md`
- Research enforcement (runtime-level): PROMPT ISTNIEJE, ale WYNIKI NIE POWSTAŁY
  (`documents/researcher/prompts/research_workflow_enforcement.md` — brak pliku wynikowego)
- Backlog #153 (workflow tracking w DB): zaprojektowany, niezaplanowany
- Arch Uplift Faza 7 (strict enforcement): zależna od Fazy 4 (Dyspozytor) — Faza 4 w trakcie

**Timeline wątku (z wczorajszej sesji 2026-03-26):**
1. PE (#405) udokumentował 6 nieudanych prób wzmocnienia promptów → klasyfikacja: `outside_prompt_layer`
2. Architect wybrał opcję 2 (git_commit.py gate) → **człowiek odrzucił**: "gate na końcu jest za późno,
   agent zrobi 2h pracy bez workflow, potem backfilluje step-logi byle jak"
3. Architect zgodził się: "facade compliance, zero value" → **anulował opcje 1-2**
4. Wspólna decyzja: **potrzeba research enforcement (opcja 3)** — jak wymusić compliance
   tak żeby nie było: za wcześnie (blok narzędzi), za późno (blok commitu), fasadowo (agent loguje PASS byle jak)
5. PE utworzył prompt: `documents/researcher/prompts/research_workflow_enforcement.md`
6. **Research NIE ZOSTAŁ WYKONANY** — brak pliku wynikowego, nikt nie spawał Researchera

**Dodatkowe research prompts (też niewykonane):**
- `research_mission_control.md` (msg #412) — interfejsy kontroli swarmu AI
- prompt z msg #413 — "czego nie wiemy że nie wiemy" (complex systems, cybernetics, HRO)

**Naprawa:**
1. **Teraz:** Spawać Researchera z `research_workflow_enforcement.md` (kluczowy blocker)
2. **Po researchu:** Architect/Developer budują rozwiązanie programistyczne na podstawie wyników
3. Prompt-level enforcement się nie sprawdził — nie powtarzać (6 prób, 6 porażek)

**Effort:** duzy | **Value:** krytyczna (bez tego system nie jest wiarygodny)

---

## P4: Backlog — 5 pozycji "in_progress" bez aktywnych agentów

| ID | Tytuł | Area | Od kiedy | Rekomendacja |
|----|-------|------|----------|--------------|
| 115 | Domain Model Refactor (ADR-001) | Arch | 22 mar | ADR "Accepted", M1-M4 complete → **done** ✓ |
| 150 | Convention Registry META_CONVENTION | Arch | 24 mar | 6 konwencji + META + README istnieje → **done** ✓ |
| 158 | CLI-API sync guard | Dev | 26 mar | Plan napisany, brak implementacji → **planned** ✓ |
| 171 | CONVENTION_CODE rozszerzenie | Arch | 25 mar | CONVENTION_PYTHON v1.3 pokrywa scope → **done** ✓ |
| 179 | CONVENTION_DB_SCHEMA | Arch | 26 mar | Plik v1.0 istnieje, active → **done** ✓ |

**Status: ZREALIZOWANE** — backlog zaktualizowany 2026-03-27.

---

## P5: Prompt Engineer — bottleneck (10 actionable)

PE ma najwięcej otwartych zadań. Kluczowe:

| Priorytet | Msg ID | Temat |
|-----------|--------|-------|
| 1 | #396 | Developer nie loguje step-logów — patching promptu |
| 2 | #425 | Workflow splitting (1 ID per scenariusz) |
| 3 | #412, #413 | Dwa research prompts (coordination patterns, workflow compliance) |
| 4 | #370 | CONVENTION_DB_SCHEMA |
| 5 | #424 | context_usage w promptach |
| 6 | #427 | Dashboard guidance w Dispatcher prompt |
| 7 | #337 | Post-implementation steps w Developer workflow |
| 8 | #394 | session_start review |

**Naprawa:** Spawać PE z priorytetowym taskiem (#396 → #425 → reszta w kolejności).
Ale najpierw — oczyścić inbox PE z resolved/cancelled.

---

## P6: Metodolog — rola nieaktywna, 12 wiadomości, 5 planned items

Metodolog nie miał sesji od co najmniej 13 marca. Akumulacja:
- 2 taski od Architekta: dodanie zasad do SPIRIT.md (#160 "Agent jako rewolucjonista", #162 "Projektuj na porządek")
- 3 propozycje od PE: #173, #264, #269 (zasady metodologiczne)
- 2 pytania procesowe: #278 (kto zmienia status na review), #282 (L1-L7 code maturity)
- 1 stara wiadomość #3 (13 marca, prawdopodobnie nieaktualna)

**Decyzja potrzebna od człowieka:**
- Czy rola Metodologa jest nadal potrzebna?
- Jeśli tak — spawać sesję z backlogiem powyżej.
- Jeśli nie — przenieść SPIRIT.md do Architekta, zasady procesowe do PE.
- Wariant pośredni: Metodolog uruchamiany ad-hoc (nie regularnie), a proste taski (dodaj zasadę do SPIRIT.md) delegować do PE.

---

## P7: Pending handoffy — 5 czeka na dostarczenie

| ID | Od | Do | Temat | Rekomendacja |
|----|----|----|-------|-------------|
| 416 | architect | architect | Self-handoff: 10 otwartych wątków | Spawn Architect z tym kontekstem |
| 414 | architect | developer | Dispatcher tools | **DONE** — Developer dostarczył, mark-read |
| 406 | architect | developer | git_commit.py gate | **CANCELLED** — msg #410 anuluje |
| 387 | architect | developer | PM tools | **DONE** — Developer dostarczył, mark-read |
| 384 | architect | prompt_engineer | PM v1 prompt | **DONE** — PE napisał DISPATCHER.md, mark-read |

Efektywnie: 4 z 5 handoffów to resolved/cancelled. Jedyny żywy to #416 (Architect self-handoff).

---

## P8: 7 stale workflow_execution w DB

Workflow IDs 8, 9, 10, 13, 15, 24, 27 mają status "running" z 25-26 marca.
Nikt ich nie zamknął przez `workflow-end`. To zaśmieca dashboard i statystyki.

**Naprawa:** Zamknąć jako `abandoned` — skrypt lub ręcznie per ID.

---

## Proponowana kolejność realizacji

| Faza | Co | Kto | Zależności |
|------|----|-----|-----------|
| S1 | Zamknąć stale workflow_execution (P8) | Dyspozytor/Developer | brak |
| S2 | Naprawić dashboard (P1) | Developer | S1 poprawia symptom |
| S3 | Wyczyścić inboxy (P2) — bulk mark-read historyczne | Dyspozytor | potrzeba narzędzia mark-read |
| S4 | Zaktualizować backlog statusy (P4) | Dyspozytor | brak |
| S5 | Oczyścić handoffy resolved (P7) | Dyspozytor | brak |
| S6 | Decyzja o Metodologu (P6) | Człowiek | brak |
| S7 | Spawn PE z priorytetami (P5) | Dyspozytor → PE | S3 (czysty inbox) |
| S8 | Wzmocnić workflow compliance (P3) | PE → Developer | S7 |

Fazy S1-S5 to porządkowanie — mogę je zacząć realizować natychmiast.
S6 wymaga decyzji człowieka.
S7-S8 to faza operacyjna — spawanie specjalistów.

---

## Pytania do człowieka

1. **Metodolog** — zachować, zawiesić, czy przenieść kompetencje do PE/Architect?
2. **Mark-read tool** — czy istnieje w agent_bus_cli? Jeśli nie, mam dodać backlog item?
3. **Stale workflow_execution** — mogę zamknąć 7 rekordów jako `abandoned`?
4. **Backlog #115 (ADR-001)** — mogę oznaczyć jako `done`?
5. **Kolejność** — zgadzasz się z S1→S8 czy chcesz zmienić priorytety?
