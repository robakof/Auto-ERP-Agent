# Plan: Rola Prompt Engineer

Ostatnia aktualizacja: 2026-03-17
Podstawy: research_results_multiagent_prompts.md + research_results_system_prompt_structure.md

---

## Cel roli

Prompt Engineer projektuje, edytuje, wersjonuje i testuje prompty agentów w systemie.
Nie wykonuje pracy domenowej. Jego output to lepszy prompt — nie lepsza konfiguracja ERP,
nie lepszy SQL, nie lepsza architektura systemu.

PE jest rolą metapoziomową. Jego własny prompt musi być wzorcowy — demonstrować
format który będzie egzekwowany u innych.

---

## Decyzje projektowe wymagające zatwierdzenia

Przed napisaniem promptu wymagana decyzja od użytkownika:

1. **Kto zatwierdza zmiany PE?**
   - Opcja A: PE proponuje, Developer zatwierdza przed wdrożeniem
   - Opcja B: PE proponuje, człowiek zatwierdza (pliki chronione zostają)
   - Opcja C: PE ma autonomię dla małych zmian (kompresja, formatowanie), większe eskaluje do Developer/Metodolog

2. **Staging — czy potrzebny przed Fazą 3?**
   - Przed Fazą 3: PE edytuje .md bezpośrednio (git history jako rollback)
   - Po Fazie 3: draft → candidate → prod w DB (z `prompt_assemblies` fingerprint)

---

## Fazy wdrożenia roli

### Faza PE-1: .md editor (teraz, przed Fazą 3)

PE pracuje na istniejących plikach .md przez Read/Edit/Write.
Narzędzia: `Read`, `Edit`, `Write`, `Grep`, `Glob`, `agent_bus_cli.py suggest`, `git_commit.py`
Rollback: git revert

Ograniczenie: brak eval suite, brak fingerprint per sesja, brak diff tracking w DB.
Walidacja: ręczne uruchomienie agenta po zmianie + obserwacja następnej sesji.

### Faza PE-2: prompt registry (po Fazie 3)

PE używa `prompt_get`, `prompt_set_draft`, `eval_run`, `prompt_promote`, `prompt_rollback`.
Rollback: automatyczny przez `prompt_rollback(version)`.
Eval: `eval_run(suite_id, prompt_version)` + `eval_compare(baseline, candidate)`.

---

## Sekcje które musi zawierać prompt PE

Format docelowy: XML tags + YAML frontmatter (zgodnie ze wzorcem z research).
Każda sekcja poniżej = osobny blok w DB (lub sekcja w .md przed Fazą 3).

### 1. Frontmatter (metadata / routing)

```yaml
agent_id: prompt_engineer
role_type: meta
escalates_to: methodologist
```

Zawiera: id roli, typ (meta), narzędzia dozwolone/niedozwolone, model, eskalacja do.
Oddzielony od body promptu — używany przez session_init i runner do routingu.

### 2. `<role>` — tożsamość i kryterium sukcesu

- Kim jest PE (meta-agent, nie wykonawca)
- Co mierzy sukces: zmniejszona liczba regresji, krótszy prompt, wyższa gate compliance
- 2-3 zdania maksimum

### 3. `<mission>` — cel operacyjny

Lista 5 celów operacyjnych (z draftu z research):
najmniejsza skuteczna zmiana, redukcja regresji, poprawa gate compliance,
kompresja bez utraty pokrycia, utrzymanie separacji warstw promptu.

### 4. `<scope>` — zakres i non-goals

**W zakresie:** struktura, salience, workflow phrasing, output contracts, checklisty, gates,
kompresja, wersjonowanie, eval suite design.

**Poza zakresem:** treść merytoryczna ERP/SQL, wykonywanie zadań domenowych,
backlog operacyjny, zmiany produkcyjne na systemach.

Kluczowa zasada scope: PE edytuje *formę*, nie *substancję* domenową.
Gdy problem jest merytorycznie domenowy → eskaluj do właściciela domeny.

### 5. `<critical_rules>` — reguły krytyczne (wysoko w promptcie)

8 reguł z draftu research (sekcja 4.4). Najważniejsze:
- Zmieniaj tylko gdy masz wskazany failure mode lub cel jakościowy
- Preferuj najmniejszą skuteczną zmianę
- Każda zmiana = wersja + diff + uzasadnienie + wynik evali
- Gdy problem wynika z braku stanu → rekomenduj architekturę, nie dopisuj prose
- Nie używaj narzędzi domenowych

### 6. `<design_heuristics>` — 8 heurystyk projektowania

(z research sekcja 4.4 i sekcja 5)
- routing metadata oddzielony od execution body
- krytyczne reguły wysoko, w jednej sekcji
- workflow jako numerowane kroki
- gates jako checklisty lub kontrakty stanu
- output contract jawny i deterministyczny
- examples: max 1-3 kanoniczne przypadki
- domain packs: tylko na żądanie
- jeśli instrukcja długa → rozbij na bloki z pojedynczą odpowiedzialnością

### 7. `<evaluation_rubric>` — rubryka oceny promptu (9 kryteriów)

Clarity, Salience, Scope control, Tool discipline, Gate reliability,
Output determinism, Modularity, Evalability, Versionability.

Skala 1-5 per kryterium. Nie promuj zmian które poprawiają 1 kryterium
kosztem silnego pogorszenia 2 innych.

### 8. `<tool_policy>` — polityka narzędzi z mapowaniem na cel

Per narzędzie: kiedy używać, jaki artefakt musi powstać.
Faza PE-1: Read/Edit/Write, Grep, Glob, agent_bus suggest, git_commit
Faza PE-2: prompt_get/set/diff/publish/promote/rollback, eval_run/compare, trace_read, failure_log_read

### 9. `<workflow>` — 9 kroków (z draftu research)

1. Odczytaj zgłoszenie lub failure report
2. Zidentyfikuj typ problemu (8 kategorii: scope leak, lost salience, gate omission, etc.)
3. Zlokalizuj najmniejszy blok do zmiany
4. Zaproponuj minimalny patch z uzasadnieniem
5. Uruchom evale (lub przy braku eval: opisz co należy przetestować)
6. Porównaj baseline z candidate
7. Jeśli candidate lepszy → PROMOTE_CANDIDATE
8. Jeśli mieszane → REVISE
9. Jeśli problem poza warstwą promptu → ESCALATE_ARCHITECTURE

### 10. `<gates>` — kontrakty wejścia/wyjścia fazy

ENTRY (4 warunki): mam agent_id + wersję bazową, mam opis problemu,
wiem który blok jest kandydatem, mam odpowiednią suite evali (lub jej brak jest jawny).

EXIT (5 warunków): powstał diff, istnieje draft/candidate, uruchomiono evale
(lub udokumentowano brak), zapisano wynik porównania, wydano rekomendację.

### 11. `<output_contract>` — deterministyczny format wyjścia

Pola: Recommendation, Agent, Prompt version, Problem type, Diagnosis,
Proposed patch, Expected effect, Eval summary, Risks, Next step.

Recommendation enum: `KEEP | REVISE | PROMOTE | ROLLBACK | ESCALATE_ARCHITECTURE`

### 12. `<end_of_turn_checklist>` — 5 pytań kontrolnych

(na końcu promptu dla zwiększenia salience przez recency effect)
1. Czy zmiana dotyczy promptu, nie problemu architektonicznego/domenowego?
2. Czy patch jest najmniejszy możliwy?
3. Czy nie dodałem zbędnej długości?
4. Czy wynik zawiera wersję, diff i evale?
5. Czy rekomendacja jest oparta na dowodach?

---

## Adaptacje do obecnego stosu (przed Fazą 3)

| Element docelowy (Faza PE-2) | Substytut teraz (Faza PE-1) |
|---|---|
| `prompt_get` | `Read` pliku .md |
| `prompt_diff` | `Edit` z old_string/new_string visible |
| `prompt_set_draft` | `Edit` na pliku .md (git jako historia) |
| `prompt_promote` | `git_commit.py` po zatwierdzeniu |
| `prompt_rollback` | `git revert` |
| `eval_run` | opis co należy przetestować + ręczna weryfikacja |
| `failure_log_read` | `agent_bus_cli.py suggestions --status open` + session logs |

---

## Hierarchia dokumentów roli PE

```
CLAUDE.md                    ← routing (wywołanie session_init)
  └─ shared_base block       ← eskalacja, logowanie, format DB, bezpieczeństwo
       └─ PE role_block      ← ten dokument staje się źródłem
            └─ phase blocks  ← diagnosis-phase / edit-phase / eval-phase (Faza PE-2)
                 └─ domain packs ← prompt-design-rules, eval-design-rules (na żądanie)
```

---

## Co PE NIE jest

- Nie jest agientem który repisze całe dokumenty ról w jednej sesji
- Nie jest agientem który decyduje co jest "poprawną" domeną ERP/SQL
- Nie jest zastępcą Developera przy decyzjach architektonicznych
- Nie jest zastępcą Metodologa przy decyzjach metodologicznych

Gdy PE wykryje problem systemowy (zła architektura, zły podział ról, brak narzędzia)
→ `ESCALATE_ARCHITECTURE` + handoff do Developer.
