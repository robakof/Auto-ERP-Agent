# Research: Struktura systemu promptu i wzorcowe przykłady

## Kontekst

Buduję system wieloagentowych LLM (Claude). Planuję migrację promptów ról z monolitycznych .md
do modularnej bazy (SQLite) gdzie `session_init.py` składa prompt z bloków per `rola × faza × zadanie`.

Powołuję nową rolę: **Prompt Engineer** — agent który projektuje, edytuje, wersjonuje i testuje
prompty innych agentów w systemie. Sam jego prompt musi być wzorcowy.

Dotychczasowy research potwierdził architekturę warstw:
`shared_base → role_block → phase_block → domain_pack → runtime_state`

Teraz potrzebuję: **konkretnej struktury** systemu promptu i **rzeczywistych przykładów**
z produkcyjnych systemów agentowych.

---

## Pytania badawcze

### 1. Szkielet systemu promptu — co i w jakiej kolejności

- Jaki jest uznany schemat sekcji systemu promptu dla agenta operacyjnego (nie chatbota)?
  Interesuje mnie kolejność: tożsamość roli → zasady → narzędzia → workflow → przykłady → output?
- Jak Claude Code, LangChain Deep Agents, AutoGen i Cognition Devin strukturyzują swoje
  system prompty — jakie sekcje, w jakiej kolejności, jak oznaczają granice?
- Czy istnieją różne szkielety dla różnych typów agentów:
  (a) agent operacyjny wykonujący zadania krok po kroku,
  (b) agent weryfikujący/recenzujący,
  (c) agent orkiestrujący innych agentów,
  (d) agent specjalistyczny z wiedzą dziedzinową?

### 2. Rzeczywiste przykłady — pokaż, nie opisuj

Szukam **pełnych lub prawie pełnych przykładów** system promptów z produkcji lub uznanych
open-source projektów, dla następujących typów agentów:

- Agent operacyjny (wykonuje konkretne zadanie z narzędziami i workflow)
- Agent recenzent/weryfikator (ocenia artefakty innych agentów, zwraca PASS/BLOCKED z uzasadnieniem)
- Agent orkiestrator/PM (deleguje zadania, monitoruje stan, prowadzi workflow)
- Agent z rolą metapoziomową (np. Prompt Engineer, który edytuje prompty innych agentów)

Źródła do sprawdzenia:
- `Piebald-AI/claude-code-system-prompts` — repozytorium z wyekstrahowanymi promptami Claude Code
- Cognition Devin — opublikowane fragmenty system promptu
- AutoGen AssistantAgent i jej bazowy system prompt
- LangChain Deep Agents customization examples
- OpenAI AGENTS.md wzorce z Codex

### 3. Prompt Engineer — jak zdefiniować agenta który edytuje prompty innych agentów

To jest specyficzna rola metapoziomowa. Potrzebuję odpowiedzi na:

- Jak zdefiniować scope Prompt Engineera żeby nie wchodził w domenę innych ról?
  (edytuje strukturę i brzmienie, nie treść merytoryczną ERP/SQL/analityczną)
- Jakie narzędzia/uprawnienia powinien mieć? (prompt_get, prompt_set, prompt_diff,
  eval runner — ale nie: sql_query, agent_bus do ról wykonawczych)
- Jak powinien rozumieć "dobry prompt" — jakie kryteria oceny?
- Jak powinien wersjonować i testować zmiany zanim wdrożą się na produkcję?
- Czy istnieją przykłady "prompt that writes prompts" z produkcji lub badań?
  (meta-prompting, constitutional AI, self-refinement wzorce)

### 4. Formatowanie i znaczniki

- XML tags vs Markdown headers vs plain text — kiedy co stosować i dlaczego?
  Czy Claude preferuje konkretny format granic sekcji?
- Jak formatować listy zasad żeby były wysoko-salience (numerowane, bullety, bloki kodu)?
- Jak oznaczać sekcje krytyczne ("YOU MUST", "NEVER", "BEFORE EACH RESPONSE CHECK")?
- Jak pisać reguły afirmatywnie zamiast zakazami — konkretne wzorce przepisywania?

### 5. Długość i gęstość

- Jaka jest empirycznie uzasadniona maksymalna długość bloku roli żeby nie degradował?
- Jak skracać istniejące prompty bez utraty pokrycia — techniki kompresji?
- Zasada "jeden akapit = jedna zasada" czy coś innego?

---

## Oczekiwany output

Plik: `documents/dev/research_results_system_prompt_structure.md`

Struktura:
```
## 1. Wzorcowy szkielet system promptu — szablon z komentarzami
## 2. Szkielety per typ agenta (operacyjny / weryfikator / orkiestrator / meta)
## 3. Przykłady z produkcji — pełne lub obszerne fragmenty z analizą struktury
## 4. Wzorzec dla Prompt Engineera — propozycja systemu promptu tej roli
## 5. Formatowanie i znaczniki — rekomendacje z uzasadnieniem
## 6. Kompresja i długość — techniki skracania bez utraty pokrycia
## 7. Źródła
```

Dla sekcji 3 i 4: priorytet na **pokazanie kodu/treści promptu**, nie opis.
Dla sekcji 4: zaproponuj wersję roboczą system promptu dla Prompt Engineera —
nawet jeśli niepełna, jako punkt startowy do dalszej pracy.
