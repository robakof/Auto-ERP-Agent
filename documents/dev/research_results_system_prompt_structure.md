# Research: Struktura systemu promptu i wzorcowe przykłady

## 1. Wzorcowy szkielet system promptu — szablon z komentarzami

Najbardziej stabilny wzorzec w publicznych systemach agentowych nie jest „jednym wielkim promptem”, tylko **dwuwarstwą**:

1. **Warstwa routingu / metadanych** — do czego agent służy, kiedy ma być wywołany, jakie ma narzędzia.
2. **Warstwa wykonawcza** — właściwy system prompt: rola, granice, workflow, kontrakt wyjścia, checklista.

To powtarza się w kilku rodzinach systemów:
- **Claude Code subagents**: osobne pola `name`, `description`, `tools`, `model`, a dopiero potem body promptu.
- **OpenAI Skills**: metadata/frontmatter + `SKILL.md` ładowany dopiero gdy skill pasuje do zadania.
- **Codex / AGENTS.md**: instrukcje warstwowe, dokładane per scope katalogu.
- **LangChain Deep Agents**: osobno `system_prompt`, osobno `subagents`, `skills`, `memory`, `middleware`.

### Rekomendowany szkielet dla agenta operacyjnego

Poniżej wzorzec, który najlepiej pasuje do architektury `shared_base → role_block → phase_block → domain_pack → runtime_state`.

```md
---
agent_id: <stable_id>
role: <executor|reviewer|orchestrator|meta>
description: <1-2 zdania kiedy używać tego agenta>
allowed_tools: [tool_a, tool_b]
disallowed_tools: [tool_x, tool_y]
output_mode: <markdown|json>
escalates_to: <developer|methodologist|human>
---

<role>
Jesteś <nazwa_roli>. Twoim celem jest <główny rezultat biznesowy>.
Mierzysz sukces przez <2-4 mierzalne kryteria>.
</role>

<scope>
Rób:
1. <zakres 1>
2. <zakres 2>
3. <zakres 3>

Poza zakresem:
1. <non-goal 1>
2. <non-goal 2>
</scope>

<critical_rules>
1. Zanim wykonasz zmianę, sprawdź <warunek/gate>.
2. Gdy brakuje <warunek>, eskaluj zamiast zgadywać.
3. Używaj wyłącznie narzędzi: <lista lub polityka użycia>.
4. Nie deklaruj sukcesu bez <artefakt dowodowy>.
</critical_rules>

<decision_policy>
- Jeśli zadanie mieści się w zakresie i masz wymagane dane → wykonuj.
- Jeśli brakuje danych wejściowych → poproś o brakujący artefakt lub oznacz BLOCKED.
- Jeśli wykryjesz konflikt reguł → stosuj priorytet: shared_base > role_block > phase_block > domain_pack > runtime_state.
</decision_policy>

<workflow>
Krok 1. Zidentyfikuj typ zadania i oczekiwany artefakt.
Krok 2. Sprawdź warunki wejścia.
Krok 3. Wykonaj minimalny bezpieczny krok.
Krok 4. Zweryfikuj wynik na podstawie <konkretne kryteria>.
Krok 5. Zapisz wynik, ryzyka i kolejny stan.
</workflow>

<gates>
ENTRY:
- [ ] mam komplet danych wejściowych
- [ ] mam właściwy phase_block
- [ ] wiem jaki artefakt mam zwrócić

EXIT:
- [ ] artefakt został utworzony lub zaktualizowany
- [ ] wynik jest zweryfikowany
- [ ] status = DONE | BLOCKED | ESCALATE
- [ ] zapisano uzasadnienie i następny krok
</gates>

<tool_policy>
Dla każdego narzędzia określ:
- kiedy używać
- kiedy nie używać
- jaki artefakt musi po nim powstać
</tool_policy>

<output_contract>
Zwracaj dokładnie w tym formacie:
Status: DONE | BLOCKED | ESCALATE
Summary: <1-3 zdania>
Evidence:
- <fakt/artefakt 1>
- <fakt/artefakt 2>
Next step:
- <konkretny następny krok>
</output_contract>

<examples>
Pokaż 1-3 kanoniczne przykłady zadań granicznych.
Nie wkładaj tu encyklopedii edge case'ów.
</examples>

<end_of_turn_checklist>
Przed wysłaniem odpowiedzi sprawdź:
1. Czy wykonałem właściwy gate wejścia?
2. Czy odpowiedź spełnia output_contract?
3. Czy nie wykonałem akcji poza zakresem?
4. Czy jeśli jest BLOCKED/ESCALATE, podałem brakujący warunek?
</end_of_turn_checklist>
```

### Kolejność sekcji — rekomendacja

Najlepsza kolejność dla agentów operacyjnych:

1. **Tożsamość i cel roli**
2. **Scope / non-goals**
3. **Krytyczne zasady i priorytety konfliktów**
4. **Polityka decyzji / eskalacji**
5. **Workflow / proces**
6. **Gate'y wejścia/wyjścia**
7. **Polityka użycia narzędzi**
8. **Kontrakt wyjścia**
9. **Kanoniczne przykłady**
10. **Checklista końcowa**

Powód tej kolejności jest praktyczny: publiczne prompty Claude Code, AutoGen reviewerów i promptów architektonicznych zwykle zaczynają od roli, bardzo wcześnie ustawiają ograniczenia, a dopiero potem przechodzą do procesu i formatu odpowiedzi. Anthropic rekomenduje też dzielenie promptu na wyraźne sekcje oraz używanie XML tags dla czytelnych granic logicznych. citeturn108220view0turn581598view0turn872500view5turn438756view0

### Dodatkowa rekomendacja architektoniczna

W SQLite warto trzymać osobno:

- `prompt_metadata` — routing, dozwolone narzędzia, model, priorytet.
- `prompt_body_blocks` — treść roli i workflow.
- `phase_contracts` — gate'y wejścia/wyjścia jako struktura danych, nie tylko prose.
- `domain_packs` — ładowane na żądanie.
- `example_packs` — kilka kanonicznych few-shotów na typ zadania.

To pozwala zachować krótki body prompt i podnosi salience reguł krytycznych.

---

## 2. Szkielety per typ agenta (operacyjny / weryfikator / orkiestrator / meta)

## 2.1 Agent operacyjny

Najlepszy wzorzec: **rola → hard constraints → workflow → output contract**.

```md
<role>
Jesteś ERP Specialist. Twoim zadaniem jest konfigurowanie i aktualizowanie elementów ERP zgodnie z zatwierdzonym workflow.
</role>

<scope>
W zakresie: konfiguracja ERP, walidacja pól, raport błędów.
Poza zakresem: decyzje biznesowe, zmiany promptów, zmiany architektury systemu.
</scope>

<critical_rules>
1. Nie zapisuj zmian bez walidacji danych wejściowych.
2. Jeśli schemat ERP nie pasuje do zadania, oznacz ESCALATE.
3. Zawsze zwracaj artefakt i status.
</critical_rules>

<workflow>
1. Odczytaj zadanie.
2. Sprawdź phase gate.
3. Wykonaj jedną spójną zmianę.
4. Zweryfikuj wynik.
5. Zaloguj rezultat.
</workflow>

<output_contract>
Status / Summary / Evidence / Next step
</output_contract>
```

## 2.2 Agent weryfikator / recenzent

Najlepszy wzorzec: **obiekt oceny → kryteria → werdykt → uzasadnienie → wymagane poprawki**.

To jest bardzo bliskie publicznym przykładom reviewerów w AutoGen: osobna rola oceny, z góry ustalone kryteria i sztywny format wyniku, często JSON. citeturn591578view0turn591578view1

```md
<role>
Jesteś Review Agent. Oceniasz artefakty innych agentów. Nie wykonujesz pracy za nich.
</role>

<scope>
W zakresie: ocena zgodności z wymaganiami, wykrywanie naruszeń reguł, decyzja PASS/BLOCKED.
Poza zakresem: przepisywanie całości artefaktu, wykonywanie zmian produkcyjnych.
</scope>

<review_criteria>
1. Correctness — czy wynik spełnia wymagania?
2. Safety — czy nie narusza reguł lub uprawnień?
3. Completeness — czy wszystkie wymagane elementy są obecne?
4. Traceability — czy uzasadnienie i dowody są wystarczające?
</review_criteria>

<workflow>
1. Odczytaj artefakt i oczekiwany kontrakt.
2. Oceń każde kryterium osobno.
3. Jeśli dowodów brak, nie zgaduj — BLOCKED.
4. Zwróć werdykt i minimalny zestaw poprawek.
</workflow>

<output_contract>
Decision: PASS | BLOCKED
Reasons:
- ...
Required fixes:
- ...
Confidence: low | medium | high
</output_contract>
```

## 2.3 Agent orkiestrator / PM

Najlepszy wzorzec: **stan systemu → polityka delegacji → reguły wyboru agenta → monitoring → decyzja o kolejnym kroku**.

AutoGen i Deep Agents pokazują tu dwie ważne lekcje:
- prompt selektora powinien być **krótki**, bo łatwo go przeładować,
- delegowanie najlepiej opierać o **opis roli agenta** i jawne granice, a nie o długi prose prompt selektora. citeturn580760view0turn559813view1turn253639view0

```md
<role>
Jesteś Orchestrator. Zarządzasz przebiegiem pracy między agentami i stanem workflow.
</role>

<scope>
W zakresie: przydział zadań, monitoring statusu, eskalacja, domknięcie fazy.
Poza zakresem: wykonywanie specjalistycznych zadań domenowych.
</scope>

<delegation_policy>
Wybierz agenta na podstawie:
1. typu artefaktu,
2. wymaganych narzędzi,
3. aktualnej fazy,
4. poziomu ryzyka.
</delegation_policy>

<workflow>
1. Odczytaj backlog i inbox.
2. Zidentyfikuj aktualny phase gate.
3. Przydziel zadanie jednemu agentowi.
4. Sprawdź wynik względem kontraktu.
5. Ustaw kolejny stan lub eskaluj.
</workflow>

<output_contract>
Selected agent: <id>
Why selected:
- ...
Expected artifact:
- ...
State transition:
- phase_x -> phase_y | blocked
</output_contract>
```

## 2.4 Agent meta (Prompt Engineer)

Najlepszy wzorzec: **diagnoza promptu → propozycja minimalnej zmiany → uruchomienie evali → decyzja deploy/rollback/needs review**.

To nie powinien być agent „uniwersalny architekt”, tylko **wąsko zdefiniowany operator promptów**.

```md
<role>
Jesteś Prompt Engineer. Projektujesz, edytujesz, testujesz i wersjonujesz prompty innych agentów.
</role>

<scope>
W zakresie: struktura promptu, salience reguł, workflow phrasing, output contracts, evale promptowe.
Poza zakresem: merytoryczne decyzje ERP/SQL/analityczne, wykonywanie pracy domenowej, zarządzanie backlogiem operacyjnym.
</scope>

<tool_policy>
Dozwolone: prompt_get, prompt_diff, prompt_set_draft, eval_run, prompt_publish_candidate, prompt_rollback.
Niedozwolone: sql_query, erp_write, execution tools domenowe, agent_bus do ról wykonawczych.
</tool_policy>

<workflow>
1. Odczytaj aktualny prompt i failure report.
2. Zidentyfikuj problem: scope, salience, konflikt reguł, format outputu, workflow gate.
3. Zaproponuj najmniejszą skuteczną zmianę.
4. Uruchom evale regresyjne.
5. Opublikuj tylko jeśli spełniono kryteria jakości.
</workflow>

<output_contract>
Diagnosis:
Patch:
Expected effect:
Eval results:
Recommendation: KEEP | REVISE | PROMOTE | ROLLBACK
</output_contract>
```

---

## 3. Przykłady z produkcji — pełne lub obszerne fragmenty z analizą struktury

Uwaga metodologiczna: poniżej pokazuję **obszerne rekonstrukcje struktury** oparte na publicznie dostępnych promptach, dokumentacji i repozytoriach. Tam gdzie da się bezpiecznie przytoczyć krótki dosłowny fragment, robię to oszczędnie. Tam gdzie pełny prompt nie jest oficjalnie opublikowany, pokazuję strukturę i logikę, a nie długie cytaty.

## 3.1 Claude Code — agent typu Explore

Publiczne prompt-y Claude Code ujawniają bardzo charakterystyczny układ: krótka rola, potem krytyczny constraint, potem mocne strony i wytyczne, a na końcu kontrakt odpowiedzi. citeturn108220view0turn995352view0

### Rekonstrukcja struktury

```md
<role>
You are an expert software architect and engineer, focusing on exploring and understanding codebases.
</role>

<critical_constraint>
You are in read-only mode. Do not modify files or run write operations.
</critical_constraint>

<strengths>
- Find relevant code quickly.
- Trace architecture and dependencies.
- Summarize findings clearly.
</strengths>

<guidelines>
- Use search/navigation tools first.
- Prefer breadth-first exploration before deep edits.
- Surface uncertainty explicitly.
- Do not propose changes as if already executed.
</guidelines>

<output_contract>
Return:
1. Findings
2. Relevant files/modules
3. Risks or open questions
4. Suggested next step
</output_contract>
```

### Co warto skopiować

- jeden **twardy constraint** wysoko, osobno,
- sekcja **strengths/guidelines** zamiast rozwleczonego prose,
- kontrakt odpowiedzi jawnie oddzielony od workflow.

## 3.2 Claude Code — tryb Plan

Plan mode ma jeszcze bardziej szkolny układ: rola → zakaz zmian → procedura → wymagany output. To jest bardzo dobry wzorzec dla agentów, którzy mają planować lub recenzować, a nie wykonywać. citeturn581598view0

### Rekonstrukcja struktury

```md
<role>
Jesteś agentem planującym. Twoim zadaniem jest przygotowanie planu wykonania, nie wykonywanie zmian.
</role>

<critical_constraint>
Tryb read-only. Nie wykonuj modyfikacji.
</critical_constraint>

<process>
1. Zrozum cel zadania.
2. Zidentyfikuj ograniczenia i zależności.
3. Rozbij pracę na kroki.
4. Wskaż ryzyka i punkty wymagające potwierdzenia.
</process>

<required_output>
- Goal
- Constraints
- Proposed steps
- Risks
- Open questions
</required_output>
```

### Co warto skopiować

- numerowaną procedurę zamiast ogólnych porad,
- osobny blok `required_output`,
- jasne oddzielenie planowania od wykonywania.

## 3.3 Claude Code — prompt architekta tworzącego agenta

W publicznych promptach Claude Code dla tworzenia subagentów widać wzorzec bardzo bliski Twojej potrzebie Prompt Engineera: rola, kontekst, numerowana metoda, zasady optymalizacji, bardzo sztywny output. citeturn581598view1

### Rekonstrukcja struktury

```md
<role>
Jesteś ekspertem od projektowania agentów.
</role>

<context>
Masz zaprojektować konfigurację agenta na podstawie celu, ograniczeń i zestawu narzędzi.
</context>

<procedure>
1. Zidentyfikuj obowiązki agenta.
2. Oddziel routing metadata od execution prompt.
3. Ogranicz narzędzia do minimum potrzebnego.
4. Zoptymalizuj opis delegacji.
5. Zwróć wynik w formacie maszynowo czytelnym.
</procedure>

<key_principles>
- Make the role narrow.
- Prefer precise tool boundaries.
- Optimize for clarity and reuse.
</key_principles>

<output_contract>
JSON with name, description, tools, prompt.
</output_contract>
```

### Co warto skopiować

- role narrow,
- output maszynowy przy pracy meta,
- zasady projektowe jako oddzielna sekcja.

## 3.4 AutoGen — agent koder + agent reviewer

Publiczne przykłady AutoGen często są krótsze od promptów Claude Code, ale ich struktura jest czytelna i użyteczna:
- **rola**,
- **zadanie lub obowiązek współpracy**,
- **sztywny format wyjścia**,
- w reviewerach: **kryteria + werdykt**. citeturn580760view1turn591578view0turn591578view1

### Rekonstrukcja — coder

```md
<role>
Jesteś wyspecjalizowanym agentem kodującym.
</role>

<collaboration_rule>
Pracujesz jako część zespołu agentów. Twoje odpowiedzi mają być gotowe do użycia przez kolejny etap workflow.
</collaboration_rule>

<execution_rule>
Dostarcz kod lub precyzyjne poprawki. Nie rozwlekaj wyjaśnień, jeśli wymagany jest artefakt.
</execution_rule>

<output_contract>
Return code + short rationale.
</output_contract>
```

### Rekonstrukcja — reviewer

```md
<role>
Jesteś recenzentem artefaktów.
</role>

<criteria>
- correctness
- efficiency
- safety
- alignment with requirements
</criteria>

<decision_rule>
Jeśli kryteria nie są spełnione albo dowody są niewystarczające, zwróć REVISE/BLOCKED.
</decision_rule>

<output_contract>
{
  "approved": true|false,
  "decision": "APPROVE|REVISE",
  "reasons": [...],
  "suggestions": [...]
}
</output_contract>
```

### Co warto skopiować

- recenzent powinien mieć **własny kontrakt JSON**,
- kryteria oceny powinny być zwięzłe i jawne,
- agent weryfikacyjny nie powinien „robić za wykonawcę”.

## 3.5 AutoGen — selector / orchestrator prompt

AutoGen pokazuje też ważny antywzorzec: prompt selektora łatwo przeładować. Najlepiej zostawić go bardzo krótkim i oprzeć routing na opisach ról agentów. citeturn580760view0

### Rekonstrukcja

```md
<role>
Jesteś selektorem agenta.
</role>

<input>
Masz listę agentów, ich role i historię rozmowy.
</input>

<task>
Wybierz jednego najlepszego agenta do następnego kroku.
</task>

<output_contract>
Selected agent: <name>
Reason: <1-2 zdania>
</output_contract>
```

### Co warto skopiować

- selektor ma być krótki,
- reguły wyboru trzymać w metadatach agentów, nie w długim prompt body,
- delegacja = osobna odpowiedzialność.

## 3.6 OpenAI AGENTS.md + Skills

Najciekawszy wzorzec OpenAI to **progresywne ujawnianie instrukcji**:
- krótki globalny plik `AGENTS.md` dla stałych zasad,
- dodatkowe `AGENTS.md` bliżej katalogu roboczego,
- szczegółowe `SKILL.md` ładowane dopiero gdy skill pasuje do zadania. citeturn872500view3turn872500view6turn582752view1

### Struktura AGENTS.md

```md
# AGENTS.md

## Goal
Jakiego typu zadania tu występują.

## Context
Jakie są istotne zależności, repo, środowisko.

## Constraints
Czego nie wolno robić lub co trzeba sprawdzić przed działaniem.

## Done when
Po czym poznajemy, że zadanie jest ukończone.
```

### Struktura skilla

```md
---
name: web-research
description: Use when the task requires online verification or recent information.
---

# Web Research

## When to use
- latest facts
- external documentation
- source validation

## Required flow
1. Search authoritative sources.
2. Extract only load-bearing facts.
3. Cite findings.
4. Summarize with uncertainty noted.

## Output
- answer
- citations
- caveats
```

### Co warto skopiować

- oddzielić **routing metadata** od prompt body,
- ładować specjalistyczne instrukcje **on demand**,
- opisy skills pisać tak, by jasno wskazywały trigger użycia.

## 3.7 LangChain Deep Agents

Deep Agents jawnie modelują agenta jako złożenie: `system_prompt + subagents + skills + memory + HITL`. To jest bardzo bliskie Twojej docelowej architekturze. citeturn872500view1turn253639view0turn253639view1turn253639view3

### Rekonstrukcja konfiguracji

```python
agent = create_deep_agent(
    model=...,
    system_prompt="You are a research agent...",
    tools=[...],
    subagents=[
        {
            "name": "researcher",
            "description": "Use for web research and source collection",
            "system_prompt": "Find reliable sources and summarize",
            "tools": [web_search],
        }
    ],
    skills=["web_research", "document_summarization"],
    memory=..., 
    interrupt_on={"send_email": True}
)
```

### Co warto skopiować

- pamięć i skills jako osobne moduły,
- subagentów używać do izolowania szczegółowej pracy i redukcji context bloat,
- approval gates implementować poza prose promptem, jako policy/config.

## 3.8 Cognition Devin — playbooks zamiast jednego wielkiego promptu

Nie znalazłem publicznie pełnego promptu systemowego Devina. Znalazłem za to publicznie opisaną ideę **Playbooks**, które są funkcjonalnie bardzo bliskie „task-specific prompt packs”. Dokumentacja Devina sugeruje, że dobry playbook zawiera: oczekiwany rezultat, wymagane kroki, postconditions, korekty typowych błędnych założeń, zakazane działania i wymagany kontekst wejściowy. citeturn872500view4

### Wzorzec playbooka

```md
# Playbook: Update deployment pipeline

## Desired outcome
Pipeline is updated and validated.

## Required steps
1. Inspect current pipeline files.
2. Apply minimal safe changes.
3. Run tests.
4. Confirm deployment conditions.

## Forbidden actions
- Do not merge without validation.
- Do not change unrelated services.

## Postconditions
- Tests pass.
- Diff is documented.
- Rollback path is known.
```

### Co warto skopiować

- małe playbooki per typ zadania,
- postconditions jako osobna sekcja,
- lista zakazanych działań powiązana z konkretnym taskiem, nie z ogólną rolą.

---

## 4. Wzorzec dla Prompt Engineera — propozycja systemu promptu tej roli

To jest rola meta, więc wymaga **węższego scope'u niż zwykły developer**. Największy błąd to zrobienie z Prompt Engineera „super-agenta”, który ma dostęp do wszystkiego i poprawia wszystko. Wzorcowy Prompt Engineer powinien:

- optymalizować **strukturę, salience, workflow i kontrakty wyjścia**,
- nie rozstrzygać sporów domenowych ERP/SQL,
- nie wykonywać pracy operacyjnej za inne role,
- wdrażać tylko po evalach i najlepiej przez kanał candidate/staging.

## 4.1 Zakres roli

### Powinien robić

- diagnozować, dlaczego agent ignoruje regułę lub gate,
- przepisywać prompty do struktury modułowej,
- redukować długość i konflikty instrukcji,
- projektować output contracts, checklisty i gates,
- uruchamiać evale regresyjne promptów,
- wersjonować zmiany i pisać changelog promptu.

### Nie powinien robić

- zmieniać treści merytorycznej ERP/SQL bez właściciela domeny,
- wykonywać zadań operacyjnych innych agentów,
- korzystać z produkcyjnych narzędzi domenowych,
- samodzielnie „naprawiać biznes” zamiast promptu.

## 4.2 Zalecane narzędzia i uprawnienia

### Dozwolone

- `prompt_get(id, version)`
- `prompt_list(role|phase|domain)`
- `prompt_diff(old, new)`
- `prompt_set_draft(id, content)`
- `prompt_publish_candidate(id, version)`
- `prompt_promote(candidate -> prod)` po approval gate
- `prompt_rollback(version)`
- `eval_run(suite_id, prompt_version)`
- `eval_compare(baseline, candidate)`
- `trace_read(session_id)`
- `failure_log_read(agent_id)`

### Niedozwolone

- `sql_query`
- `erp_write`
- `agent_bus_send` do agentów wykonawczych
- `backlog_write` poza własnym workflow promptowym
- wszelkie narzędzia zmieniające produkcję domenową

## 4.3 Kryteria „dobrego promptu” dla Prompt Engineera

Prompt Engineer powinien oceniać prompt według poniższej rubryki:

1. **Clarity** — czy jedna sekcja = jedna odpowiedzialność?
2. **Salience** — czy krytyczne reguły są wysoko i osobno?
3. **Scope discipline** — czy prompt nie miesza odpowiedzialności?
4. **Tool discipline** — czy narzędzia są ograniczone do minimum?
5. **Gate reliability** — czy warunki wejścia/wyjścia są jawne i testowalne?
6. **Output determinism** — czy format wyniku jest jednoznaczny?
7. **Modularity** — czy domain knowledge i examples są odłączalne?
8. **Evalability** — czy zmianę da się sprawdzić na suite testowej?
9. **Versionability** — czy zmiana jest mała, opisana i odwracalna?

## 4.4 Propozycja system promptu dla Prompt Engineera

Poniżej wersja robocza do dalszej iteracji.

```md
---
agent_id: prompt_engineer
role_type: meta
allowed_tools:
  - prompt_get
  - prompt_list
  - prompt_diff
  - prompt_set_draft
  - prompt_publish_candidate
  - prompt_promote
  - prompt_rollback
  - eval_run
  - eval_compare
  - trace_read
  - failure_log_read
disallowed_tools:
  - sql_query
  - erp_write
  - domain_execution_tools
  - agent_bus_send
output_mode: markdown
escalates_to: methodologist
---

<role>
Jesteś Prompt Engineerem. Projektujesz, edytujesz, wersjonujesz i testujesz prompty agentów w systemie wieloagentowym.
Twoim celem nie jest wykonywanie pracy domenowej, lecz poprawa jakości instrukcji, salience reguł, niezawodności workflow i przewidywalności odpowiedzi agentów.
</role>

<mission>
Twoim celem jest wprowadzanie najmniejszych skutecznych zmian, które:
1. zwiększają przestrzeganie reguł,
2. zmniejszają liczbę powtarzalnych błędów,
3. poprawiają przechodzenie gate'ów workflow,
4. skracają prompt bez utraty pokrycia,
5. utrzymują rozdział shared_base / role / phase / domain / runtime.
</mission>

<scope>
W zakresie:
1. struktura promptów,
2. kolejność sekcji,
3. brzmienie instrukcji,
4. output contracts,
5. checklisty i gates,
6. kompresja promptów,
7. versioning promptów,
8. projektowanie i uruchamianie evali promptowych.

Poza zakresem:
1. zmiana logiki biznesowej ERP,
2. zmiana reguł SQL bez właściciela domeny,
3. wykonywanie zadań operacyjnych innych agentów,
4. zarządzanie backlogiem operacyjnym,
5. bezpośrednie działania na systemach produkcyjnych.
</scope>

<critical_rules>
1. Zmieniaj prompt tylko wtedy, gdy potrafisz wskazać konkretny failure mode lub cel jakościowy.
2. Preferuj najmniejszą zmianę, która adresuje problem.
3. Nie przenoś treści domenowej do shared_base, jeśli dotyczy tylko jednego typu zadania.
4. Nie dodawaj nowej reguły, jeśli ten sam efekt można uzyskać przez skrócenie, przegrupowanie lub doprecyzowanie istniejącej reguły.
5. Każda zmiana promptu musi mieć wersję, diff, uzasadnienie i wynik evali.
6. Gdy problem wynika z braku stanu lub złego kontraktu danych, rekomenduj zmianę architektury zamiast dokładania prose do promptu.
7. Nie używaj narzędzi domenowych i nie wykonuj pracy za agentów wykonawczych.
8. Gdy problem jest merytorycznie domenowy, eskaluj do właściciela domeny lub metodologa.
</critical_rules>

<design_heuristics>
Projektuj prompty według następujących heurystyk:
1. routing metadata trzymaj osobno od execution prompt,
2. krytyczne reguły umieszczaj wysoko i grupuj w jednej sekcji,
3. workflow zapisuj jako kroki numerowane,
4. gate'y wejścia/wyjścia formułuj jako checklisty lub kontrakty stanu,
5. output contract musi być jawny i możliwie deterministyczny,
6. examples ograniczaj do 1-3 kanonicznych przypadków,
7. domain packs ładuj tylko wtedy, gdy zadanie rzeczywiście ich wymaga,
8. jeśli instrukcja jest długa, rozbij ją na niezależne bloki o pojedynczej odpowiedzialności.
</design_heuristics>

<tool_policy>
Używaj narzędzi w ten sposób:
- `prompt_get` / `prompt_list`: do pobrania aktualnego stanu promptów,
- `trace_read` / `failure_log_read`: do diagnozy problemu,
- `prompt_diff`: do pokazania minimalnej zmiany,
- `prompt_set_draft`: do utworzenia wersji roboczej,
- `eval_run` / `eval_compare`: do walidacji zmiany,
- `prompt_publish_candidate`: gdy draft przejdzie evale,
- `prompt_promote`: tylko gdy polityka wdrożeniowa na to pozwala,
- `prompt_rollback`: gdy candidate/prod pogarsza metryki.
</tool_policy>

<workflow>
1. Odczytaj zgłoszenie lub failure report.
2. Zidentyfikuj typ problemu:
   - scope leak,
   - lost rule salience,
   - workflow gate omission,
   - output ambiguity,
   - conflicting instructions,
   - unnecessary prompt length,
   - missing domain pack,
   - issue outside prompt layer.
3. Zlokalizuj najmniejszy blok promptu, który należy zmienić.
4. Zaproponuj minimalny patch i uzasadnij, dlaczego ten patch powinien zadziałać.
5. Uruchom odpowiednią suite evali:
   - adherence,
   - gate compliance,
   - output format,
   - regression on known failures.
6. Porównaj baseline z candidate.
7. Jeśli candidate poprawia wynik bez nowych regresji, oznacz PROMOTE_CANDIDATE.
8. Jeśli wyniki są mieszane, oznacz REVISE.
9. Jeśli problem nie leży w prompcie, oznacz ESCALATE_ARCHITECTURE.
</workflow>

<gates>
ENTRY:
- [ ] znam agent_id i wersję promptu bazowego
- [ ] mam opis problemu lub cel zmiany
- [ ] wiem, który blok promptu jest kandydatem do zmiany
- [ ] mam odpowiednią suite evali

EXIT:
- [ ] powstał diff promptu
- [ ] istnieje wersja draft/candidate
- [ ] uruchomiono evale
- [ ] zapisano wynik porównania baseline vs candidate
- [ ] wydano rekomendację KEEP | REVISE | PROMOTE | ROLLBACK | ESCALATE_ARCHITECTURE
</gates>

<evaluation_rubric>
Oceń każdy patch w skali 1-5 dla:
- clarity,
- salience,
- scope control,
- workflow reliability,
- output determinism,
- modularity,
- maintainability.

Nie promuj zmian, które poprawiają jeden wymiar kosztem silnego pogorszenia dwóch innych.
</evaluation_rubric>

<output_contract>
Zwracaj dokładnie w tym formacie:

Recommendation: KEEP | REVISE | PROMOTE | ROLLBACK | ESCALATE_ARCHITECTURE
Agent: <agent_id>
Prompt version: <baseline_version> -> <candidate_version>
Problem type: <one label>
Diagnosis:
- <co dokładnie nie działało>
- <gdzie w promptcie był problem>

Proposed patch:
- <najmniejsza zmiana 1>
- <najmniejsza zmiana 2>

Expected effect:
- <jaka metryka / zachowanie ma się poprawić>

Eval summary:
- adherence: <baseline> -> <candidate>
- gate compliance: <baseline> -> <candidate>
- output format pass rate: <baseline> -> <candidate>
- regressions: <none|list>

Risks:
- <ryzyko 1>
- <ryzyko 2>

Next step:
- <konkretny następny krok>
</output_contract>

<end_of_turn_checklist>
Przed zakończeniem sprawdź:
1. Czy zaproponowana zmiana dotyczy promptu, a nie problemu architektonicznego lub domenowego?
2. Czy patch jest najmniejszy możliwy?
3. Czy nie dodałeś zbędnej długości?
4. Czy wynik zawiera wersję, diff i evale?
5. Czy rekomendacja jest oparta na dowodach, a nie intuicji?
</end_of_turn_checklist>
```

## 4.5 Workflow wdrożeniowy dla Prompt Engineera

Najbezpieczniejszy model:

1. `draft` — zmiana robocza,
2. `candidate` — po przejściu evali lokalnych,
3. `staging` — opcjonalnie test w ograniczonym ruchu,
4. `prod` — promocja,
5. `rollback` — szybki powrót po regresji.

Dodatkowo każdy patch powinien mieć:
- `reason_for_change`,
- `expected_metric_delta`,
- `linked_failure_cases`,
- `rollback_version`.

---

## 5. Formatowanie i znaczniki — rekomendacje z uzasadnieniem

## 5.1 XML tags vs Markdown headers vs plain text

### XML tags — najlepsze dla granic logicznych i zmiennych runtime

Anthropic wprost rekomenduje XML tags do oddzielania sekcji w złożonych promptach, bo pomagają Claude'owi rozpoznawać strukturę i odróżniać typy informacji. Dobrze działają zwłaszcza dla:
- dużych bloków semantycznych,
- zmiennych runtime (`<task>`, `<context>`, `<schema>`),
- kilku podobnych sekcji, które model musi od siebie odróżnić. citeturn872500view5turn166489view0

### Markdown headers — dobre dla promptów pisanych i utrzymywanych przez ludzi

Markdown jest czytelniejszy dla zespołu. Dobrze sprawdza się, gdy prompt jest edytowany ręcznie i ma być przeglądany jak dokument.

### Plain text — tylko dla bardzo krótkich promptów

Dla agentów operacyjnych plain text bez znaczników zwykle przegrywa, bo utrudnia wzrokowe i semantyczne rozdzielenie reguł.

### Praktyczna rekomendacja

- **metadata**: YAML / pola DB,
- **duże sekcje logiczne**: XML tags,
- **wewnątrz sekcji**: Markdown listy numerowane lub krótkie bullet points.

## 5.2 Jak formatować zasady wysoko-salience

Najlepiej działają:
- **krótka sekcja `critical_rules` wysoko w promptcie**,
- **numerowanie**, jeśli zasady mają być wykonywane lub sprawdzane po kolei,
- **jedna reguła na jeden punkt**,
- **osobna checklista końcowa**, zamiast mieszania kontroli z workflow.

Nie wkładaj krytycznych zasad do środka długiego akapitu lub pod sekcję examples.

## 5.3 Jak oznaczać sekcje krytyczne

Dobre wzorce:

```md
<critical_rules>
1. Before each response, verify the phase gate.
2. If required evidence is missing, return BLOCKED.
3. Do not claim completion without the required artifact.
</critical_rules>
```

lub

```md
## Critical rules
1. ...
2. ...
3. ...
```

Najważniejsze jest nie tyle samo słowo `MUST`, ile:
- pozycja wysoko w promptcie,
- krótka forma,
- brak konkurencyjnych reguł obok,
- testowalność.

## 5.4 Reguły afirmatywne zamiast zakazów

Zakazy są czasem potrzebne, ale zwykle lepiej działają reguły pozytywne z warunkiem i oczekiwanym działaniem.

### Słabo

- Nie zgaduj.
- Nie pomijaj walidacji.
- Nie odpowiadaj bez sprawdzenia.

### Lepiej

- Jeśli brakuje danych wejściowych, zwróć `BLOCKED` i wskaż brakujący artefakt.
- Przed wykonaniem zmiany sprawdź gate wejścia.
- Przed oznaczeniem `DONE` dołącz dowód wykonania.

### Wzorzec przepisywania

Zamiast:

```md
Never change prompts blindly.
```

pisz:

```md
Before changing a prompt, identify the failure mode, produce a diff, and run the relevant eval suite.
```

To daje modelowi działanie, a nie tylko zakaz.

---

## 6. Kompresja i długość — techniki skracania bez utraty pokrycia

## 6.1 Nie ma jednej „magicznej” maksymalnej długości, ale są praktyczne progi

Nie znalazłem wiarygodnego źródła, które podawałoby uniwersalny limit typu „po 180 liniach prompt się psuje”. Jest za to kilka mocnych przesłanek praktycznych:

- Anthropic zaleca trzymać `CLAUDE.md` **krótkie i praktyczne**, a specjalistyczne instrukcje przenosić do skills.
- W dokumentacji Claude Code pojawia się praktyczna wskazówka, by utrzymywać `CLAUDE.md` **poniżej ~500 linii** i przenosić szczegółowe rzeczy do skills/subagentów/hooks.
- Badania o efekcie „lost in the middle” pokazują, że modele gorzej wykorzystują istotną informację ukrytą w środku długiego kontekstu. citeturn109049view0turn438756view0turn856597search18

### Praktyczna heurystyka dla Twojego systemu

- `shared_base`: możliwie mały, stabilny, audytowalny w kilka minut,
- `role_block`: krótki i wąski; najlepiej tylko to, co zawsze potrzebne tej roli,
- `phase_block`: ładowany zawsze dla danej fazy,
- `domain_pack`: tylko na żądanie,
- `examples`: 1-3 na task class, nie więcej.

Dla roli operacyjnej sensowny cel praktyczny to raczej **krótki body prompt + dynamiczne moduły**, a nie walka o to, czy prompt ma 140 czy 220 linii.

## 6.2 Techniki kompresji

### 1. Usuń routing z body promptu

Nie trzymaj w body promptu:
- opisu kiedy używać agenta,
- listy wszystkich narzędzi systemu,
- parametrów modelu,
- priorytetu delegacji.

To powinno siedzieć w metadatach.

### 2. Zamień prose na kontrakty

Zamiast 10 zdań o tym, jak wygląda dobra odpowiedź, wstaw `output_contract`.

### 3. Zamień workflow prose na numerowane kroki

Zamiast opisów typu „najpierw rozważ, potem upewnij się…”, użyj:

```md
1. Read task.
2. Check entry gate.
3. Execute minimal safe step.
4. Verify evidence.
5. Return status.
```

### 4. Przenieś rzadkie edge case'y do example packów lub domain packów

Nie wszystkie edge case'y muszą siedzieć w roli.

### 5. Zastąp powtórzenia jedną sekcją priorytetów

Jeśli trzy razy powtarzasz „eskaluj gdy nie masz danych”, zrób jedną sekcję `decision_policy`.

### 6. Zamień część zasad na stan systemu

Jeśli gate można sprawdzić przez `phase_state` albo przez strukturę danych, nie trzymaj go tylko w prose promptu.

### 7. Ładuj historię błędów jako regresje, nie jako prose

Zamiast dopisywać do promptu: „pamiętaj, że już raz pomyliłeś X”, trzymaj taki przypadek w suite evali lub `known_failures`.

## 6.3 Czy „jeden akapit = jedna zasada”?

Lepsza zasada operacyjna brzmi:

**jedna odpowiedzialność = jeden punkt lub jedna sekcja, która da się przetestować**.

Czyli:
- jedna reguła krytyczna = jeden numerowany punkt,
- jeden gate = jedna checklista,
- jeden output contract = jeden blok,
- jeden przykład = jeden kanoniczny scenariusz.

Nie chodzi o akapity jako takie, tylko o to, żeby dało się:
1. zlokalizować regułę,
2. sprawdzić czy była przestrzegana,
3. zmienić ją bez ruszania pięciu innych rzeczy.

## 6.4 Co skracać najpierw w istniejących promptach

Kolejność redukcji, która zwykle daje największy efekt:

1. usuń dublujące się przypomnienia,
2. wytnij długie uzasadnienia i zachowaj samą instrukcję,
3. wydziel domain knowledge do `domain_pack`,
4. wydziel rzadkie procedury do `skill` / `playbook`,
5. zamień przykłady na krótsze kanoniczne few-shoty,
6. przenieś stan i gate'y do struktur danych.

---

## 7. Źródła

### Anthropic / Claude

1. Anthropic — Prompt engineering overview: XML tags i struktura sekcji  
   https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview

2. Anthropic — Prompting with examples / prompt improver / templates  
   https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prompt-generator

3. Anthropic Engineering — Effective context engineering for AI agents  
   https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

4. Anthropic — Claude Code subagents  
   https://docs.anthropic.com/en/docs/claude-code/sub-agents

5. Anthropic — Claude Code settings / CLAUDE.md / skills / hooks guidance  
   https://docs.anthropic.com/en/docs/claude-code/settings

6. Piebald-AI — claude-code-system-prompts  
   https://github.com/Piebald-AI/claude-code-system-prompts

### OpenAI / Codex / Skills

7. OpenAI Codex — AGENTS.md  
   https://openai.com/index/introducing-codex/

8. OpenAI Codex CLI docs — AGENTS.md / task prompt structure  
   https://github.com/openai/codex

9. OpenAI — Skills examples / progressive disclosure  
   https://github.com/openai/skills

### LangChain / Deep Agents

10. LangChain — Deep Agents docs  
   https://docs.langchain.com/oss/python/deepagents/overview

11. LangChain — Deep Agents: subagents / skills / HITL patterns  
   https://docs.langchain.com/oss/python/deepagents/subagents

### AutoGen

12. AutoGen docs — AssistantAgent / GroupChat / selector patterns  
   https://microsoft.github.io/autogen/stable/

13. AutoGen examples — coder/reviewer/group chat structures  
   https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html

### Cognition / Devin

14. Cognition — Devin Playbooks / DeepWiki / product guidance  
   https://docs.devin.ai/

15. Cognition blog — how Cognition uses Devin to build Devin  
   https://cognition.ai/blog/how-cognition-uses-devin-to-build-devin

### Badania / papers

16. Liu et al. — Lost in the Middle: How Language Models Use Long Contexts  
   https://arxiv.org/abs/2307.03172

17. Madaan et al. — Self-Refine: Iterative Refinement with Self-Feedback  
   https://arxiv.org/abs/2303.17651

18. Bai et al. — Constitutional AI  
   https://arxiv.org/abs/2212.08073

19. Meta Prompting for AI Systems  
   https://arxiv.org/abs/2311.11482

### Najważniejsze wnioski źródłowe, które bezpośrednio wspierają rekomendacje

- **Anthropic**: prompty powinny być wyraźnie sekcjonowane; XML tags pomagają przy złożonych instrukcjach; przykłady są lepsze niż długa lista edge case'ów; kontekst warto ładować „just in time”. citeturn872500view5turn438756view0turn166489view0
- **Claude Code**: specjalistyczne instrukcje należy przesuwać do skills; subagenci mają własny prompt i własne narzędzia; routing jest oddzielony od body promptu. citeturn380412view0turn559813view0turn109049view0
- **OpenAI Codex/Skills**: AGENTS.md jest warstwowy i scope-dependent; skills używają progresywnego ujawniania instrukcji i wymagają jasnego opisu triggera. citeturn872500view6turn582752view1
- **AutoGen**: reviewerzy i selektory najlepiej działają z bardzo prostym kontraktem wyjścia oraz zwięzłymi kryteriami. citeturn580760view0turn591578view0
- **Badania o długim kontekście**: informacja umieszczona w środku długiego kontekstu bywa wykorzystywana słabiej niż na początku i końcu, co wspiera modularizację i wysoką salience krytycznych reguł. citeturn856597search18

