# Research: Najlepsze praktyki pisania promptów w systemach wieloagentowych

## Kontekst dla Researchera

Buduję mrowisko autonomicznych agentów LLM (Claude Code / Claude API) które wspólnie prowadzą firmę produkcyjną — zaczyna od konfiguracji ERP, docelowo zarządza operacjami. Architektura:

- **3 poziomy ról:** Wykonawcy (ERP Specialist, Analityk) → Developer → Metodolog
- **Komunikacja przez DB** (SQLite: inbox, backlog, suggestions, session log)
- **3 typy promptów dziś:**
  1. Prompt roli — kim agent jest, jakie ma zasady, kiedy eskaluje (300–500 linii .md)
  2. Prompt workflow — jak wykonać konkretne zadanie krok po kroku (100–200 linii)
  3. Prompt wytycznych — zasady dziedzinowe (SQL syntax, schema patterns) ładowane na żądanie
- **Plan architektury (Faza 3):** prompty migrują do DB, session_init.py dobiera i składa tylko bloki potrzebne do bieżącej fazy zadania — zamiast ładować cały dokument roli w każdej sesji

**Konkretny ból:** agenci z czasem "degradują" — ignorują reguły zakopane w połowie 400-liniowego promptu, gubią gate'y w workflow, powtarzają błędy które były już naprawione. Monolityczne .md ładowane w całości do kontekstu.

---

## Pytania badawcze

### 1. Struktura i modularność

- Jakie są uznane wzorce dekompozycji promptów systemowych w systemach wieloagentowych? (np. system prompt + task prompt + tool descriptions + examples jako osobne warstwy)
- Czy istnieje literatura/prakseologia dotycząca "prompt jako kod" — modułowość, dziedziczenie, kompozycja?
- Jak duże firmy (Anthropic, OpenAI, Cognition, LangChain) strukturyzują prompty dla długo działających agentów?

### 2. Salience — co agent faktycznie "widzi"

- Jakie jest empiryczne ryzyko degradacji w długich promptach systemowych? Gdzie Agent zaczyna ignorować reguły? (pozycja w kontekście — primacy/recency effect)
- Czy istnieją techniki zwiększające salience konkretnych reguł (np. formatowanie, powtórzenia, "memory anchors")?
- Jak formatować gate'y workflow (warunki wejścia/wyjścia z fazy) żeby agent nie pomijał ich pod presją kontekstu?

### 3. Dynamiczne prompty per zadanie/faza

- Jakie są wzorce "prompt injection per task phase" — ładowania tylko fragmentu wiedzy potrzebnego do bieżącego kroku?
- Czy istnieje literatura o "retrieval-augmented prompting" dla agentów (pobieranie fragmentów z bazy per kontekst vs pełny dokument)?
- Jakie są trade-offy między: (a) jeden duży prompt z całą wiedzą vs (b) wiele małych promptów składanych dynamicznie?

### 4. Wytyczne dziedzinowe (domain knowledge injection)

- Jak efektywnie wstrzykiwać wiedzę dziedzinową (np. reguły SQL, wzorce schematu bazy) do agenta który ma jedno zadanie?
- Czy lepiej: (a) w system prompt, (b) jako oddzielna wiadomość user/assistant przed zadaniem, (c) jako "few-shot examples" inline?
- Jak unikać "prompt pollution" gdy agent ma dużo reguł dziedzinowych (30+ zasad SQL)?

### 5. Multi-agent prompt consistency

- Jak utrzymywać spójność zachowań gdy wiele agentów działa na tych samych zasadach bazowych (np. eskalacja, logowanie, format odpowiedzi)?
- Wzorce shared prompt inheritance w roich agentów — co powinno być w "shared base" a co per-rola?
- Jak wersjonować prompty agentów gdy reguły się zmieniają między sesjami (agent nie ma pamięci)?

### 6. Ewaluacja promptów

- Jak mierzyć jakość promptu systemowego bez ręcznego testowania każdej sesji?
- Czy istnieją automatyczne metody wykrywania "prompt decay" (agent coraz gorzej trzyma się reguł)?
- Jakie metryki stosować dla agentów operacyjnych (nie chatbotów) — rule adherence, escalation rate, task completion?

---

## Kontekst techniczny

- Model: Claude (Sonnet/Opus), wywoływany przez CLI (Claude Code) i API
- Sesje: 50–200 tur, context window ~200k tokenów, ale agent degraduje wcześniej
- Prompty dziś: pliki .md ładowane przez session_init.py do `doc_content`
- Cel: migracja do tabeli `prompts` w SQLite, session_init komponuje prompt z bloków per: rola × faza_workflow × zadanie
- Stack: Python 3.12, SQLite, SQL Server (ERP), Telegram bot

---

## Oczekiwany output

Plik: `documents/methodology/research_results_multiagent_prompts.md`

Struktura:

```
## 1. Kluczowe wzorce (top 5-7 praktyk z uzasadnieniem)
## 2. Salience i degradacja — co mówi literatura/prakseologia
## 3. Dynamiczne prompty — wzorce i trade-offy
## 4. Wytyczne dziedzinowe — najskuteczniejszy sposób wstrzykiwania
## 5. Multi-agent consistency — shared base vs per-rola
## 6. Ewaluacja — jak mierzyć jakość promptu
## 7. Implikacje dla architektury (co zmienić w obecnym systemie)
## 8. Źródła (linki do dokumentacji, artykułów, repozytoriów)
```

Dla każdej sekcji: konkretne zalecenie + uzasadnienie empiryczne lub z doświadczenia branżowego.
Unikaj ogólników — interesują mnie konkretne wzorce implementacyjne, nie teoria.

Jeśli znajdziesz repozytoria z przykładami (LangChain system prompts, AutoGen role definitions,
Cognition Devin prompts) — przeanalizuj je pod kątem wzorców struktury.
