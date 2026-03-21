# Research: Software Architect role for AI agent system

Data: 2026-03-21
Researcher: External agent (WebSearch/WebFetch)

---

## Kontekst

Projektujemy nową rolę agenta: **Architekt** w systemie wieloagentowym do automatyzacji konfiguracji ERP. System ma już role: Developer (implementacja narzędzi), ERP Specialist (konfiguracja), Analyst (weryfikacja danych), Prompt Engineer (projektowanie promptów), Metodolog (metoda pracy).

Architekt będzie odpowiedzialny za:
- Projektowanie architektury systemu (długofalowe, strategiczne)
- Analizę researchów architektonicznych
- Ocenę kodu pod względem jakości (code review)
- Proponowanie refaktoryzacji do Developerów
- Badanie zgodności implementacji z zaplanowaną architekturą

Developer implementuje narzędzia, Architekt projektuje strukturę systemu i ocenia jakość.

---

## Pytania badawcze

### 1. Terminologia i słownictwo

Jakie słowa kluczowe, frazy i terminy są używane w promptach dla roli Software Architect / System Architect w kontekście AI agents?

Szukaj:
- Typowe sekcje promptów architektonicznych (architectural principles, design guidelines, trade-offs...)
- Język używany do definiowania odpowiedzialności architekta (design, evaluate, propose, review...)
- Rozróżnienie między "architect" a "developer" w promptach AI

### 2. Gotowe prompty — wzorce

Czy istnieją publicznie dostępne prompty dla roli Software Architect w systemach AI agents lub multi-agent systems?

Szukaj:
- Prompty z projektów open-source (AutoGPT, LangChain agents, CrewAI, innych frameworków agentowych)
- Prompty z dokumentacji Claude, OpenAI, Anthropic dotyczące architectural agents
- Case studies: jak inne zespoły definiują rolę architekta w systemach agentowych

### 3. Responsibility boundaries — Developer vs Architect

Jak w praktyce rozgranicza się odpowiedzialności między Developer a Architect w kontekście AI agents?

Szukaj:
- Kiedy Developer eskaluje do Architekta (decision triggers)
- Co należy do "architectural decision" vs "implementation detail"
- Przykłady: czy wybór biblioteki to Developer czy Architect? Czy struktura folderów? Czy naming conventions?

### 4. Code review workflows dla AI agents

Jakie są sprawdzone wzorce code review wykonywanych przez AI agents?

Szukaj:
- Checklista code review dla AI (co sprawdzać: security, performance, maintainability...)
- Format outputu code review (structured feedback, severity levels...)
- Jak agent przekazuje feedback — bezpośrednio modyfikuje kod czy pisze raport?
- Czy agent-reviewer powinien mieć dostęp do git history, PR context?

### 5. Architecture Decision Records (ADR) w kontekście agentów

Czy agenci architektoniczni powinni dokumentować decyzje jako ADR? Jaki format?

Szukaj:
- ADR templates używane w projektach z AI agents
- Czy ADR to output Architekta czy Developer implementuje po decyzji Architekta?
- Struktury dokumentów architektonicznych (diagrams, contracts, decision logs)

### 6. Anti-patterns — czego unikać

Jakie są typowe błędy przy definiowaniu roli Architect w systemach AI?

Szukaj:
- Overlap z Developer (zbyt duża duplikacja odpowiedzialności)
- Analysis paralysis (architekt blokuje development bez końca analizując)
- Ivory tower syndrome (projektuje bez kontaktu z rzeczywistością implementacji)
- Scope creep (architekt wchodzi w zadania innych ról)

---

## Output contract

Zapisz wyniki do pliku: `documents/architect/research_results_architect_role.md`

Struktura pliku wynikowego:

```markdown
# Research: Software Architect role for AI agents
Data: YYYY-MM-DD

## TL;DR — 3-5 najbardziej obiecujących kierunków

(Najważniejsze wnioski z researchu — co warto wdrożyć w naszym systemie)

## 1. Terminologia i słownictwo

(Typowe frazy, sekcje promptów, język używany w promptach architektonicznych)
Siła dowodów: [empiryczne / praktyczne / spekulacja]

## 2. Gotowe prompty — wzorce

(Linki do przykładowych promptów, opis struktury, kluczowe sekcje)
Siła dowodów: [empiryczne / praktyczne / spekulacja]

## 3. Responsibility boundaries — Developer vs Architect

(Jak rozgraniczać odpowiedzialności, decision triggers, przykłady)
Siła dowodów: [empiryczne / praktyczne / spekulacja]

## 4. Code review workflows dla AI agents

(Checklisty, formaty outputu, sposoby przekazywania feedback)
Siła dowodów: [empiryczne / praktyczne / spekulacja]

## 5. Architecture Decision Records (ADR)

(Formaty, templates, kto pisze, jak dokumentować decyzje arch)
Siła dowodów: [empiryczne / praktyczne / spekulacja]

## 6. Anti-patterns — czego unikać

(Typowe błędy, overlap z Developer, analysis paralysis, scope creep)
Siła dowodów: [empiryczne / praktyczne / spekulacja]

## Co nierozwiązane / otwarte pytania

(Luki w researchu, pytania które pozostają bez odpowiedzi)

## Źródła / odniesienia

(Linki do promptów, dokumentacji, case studies, artykułów)
```

---

## Czego NIE rób

- **Nie oceniaj dopasowania do naszego systemu** — to osobny krok, zrobimy po otrzymaniu wyników
- **Nie dawaj jednej odpowiedzi** — dawaj pole możliwości (różne podejścia, trade-offy)
- **Nie skracaj gdy brakuje danych** — zaznacz lukę w sekcji "Co nierozwiązane"
- **Nie mieszaj factów z opiniami** — oznacz siłę dowodów per sekcja

---

## Zakres wyszukiwania

Szukaj w:
- Dokumentacja frameworków multi-agent (AutoGPT, LangChain, CrewAI, AgentGPT, Claude Code SDK)
- GitHub repositories: prompts dla architect agents
- Anthropic documentation: architectural patterns for AI agents
- OpenAI documentation: system architect prompts
- Case studies: AI agents in software development (Devin, Cursor, Copilot Workspace)
- Blogs/articles: "AI software architect", "AI code reviewer", "multi-agent architecture"

Priorytet: praktyczne przykłady > teoretyczne rozważania.
