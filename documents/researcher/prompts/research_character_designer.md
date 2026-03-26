# Research: Wzorce projektowania persony i charakteru agentów AI

## Cel

Zebrać sprawdzone wzorce, praktyki i rekomendacje dotyczące projektowania persony (profilu psychologicznego) i charakteru agentów AI w systemach wieloagentowych.

## Kontekst

W projekcie Mrowisko każdy agent ma nie tylko zakres odpowiedzialności (scope) i zasady (critical rules), ale także **personę** — profil psychologiczny określający JAK pracuje, nie CO robi. Przykład: Architect to "wywrotowy perfekcjonista — kwestionuje status quo, pewny siebie ale nie uparty, zmienia zdanie gdy widzi rzeczowe argumenty".

Persona wpływa na:
- Styl komunikacji z użytkownikiem
- Reakcje w sytuacjach granicznych (konflikt, niepewność, presja)
- Interakcje z innymi agentami (synergie, kreatywność)
- Balans między autonomią a eskalacją

## Pytania badawcze

### 1. Wzorce projektowania persony agenta

- Jakie są sprawdzone frameworki do definiowania persony/charakteru agentów AI?
- Czy są badania pokazujące wpływ persony na jakość outputu agenta?
- Jak balansować między "charakterem" a "przestrzeganiem reguł"?
- Jakie są wymiary persony które warto kontrolować (asertywność, kreatywność, ryzyko, autonomia)?

### 2. Persona w systemach wieloagentowych

- Jak persona wpływa na komunikację agent-agent (współpraca vs konflikt)?
- Czy są wzorce dla "team diversity" — różnorodność person w zespole agentów?
- Jak unikać "personality clash" między agentami?
- Czy persona powinna być stała czy kontekstowa (adaptacyjna)?

### 3. Promptowanie persony

- Jakie są skuteczne techniki promptowania persony? (np. "take a breath", role-playing, emotional framing)
- Gdzie w strukturze promptu umieszczać personę? (na początku, przed mission, jako osobna sekcja?)
- Jak długa powinna być sekcja persony? (jedno zdanie vs akapit vs strona?)
- Czy są badania nad efektywnością różnych stylów opisu persony?

### 4. Persona vs behavioral drift

- Jak zapewnić że agent trzyma się swojej persony w długich sesjach?
- Czy persona zanika przy wysokim obciążeniu kontekstu?
- Jakie są wzorce "przypominania" persony w trakcie pracy?
- Czy są techniki walidacji czy agent zachowuje się zgodnie z personą?

### 5. Przykłady person w produkcyjnych systemach

- Jak OpenAI, Anthropic, CrewAI, LangChain definiują persony agentów w przykładach?
- Jakie persony są najczęstsze dla ról typu: researcher, architect, analyst, developer?
- Czy są case studies pokazujące wpływ persony na jakość pracy agenta?

### 6. Anti-patterns i pułapki

- Kiedy persona szkodzi więcej niż pomaga?
- Czy nadmierna "humanizacja" agenta to problem?
- Jakie są znane konflikty między personą a rolą techniczną?
- Czy są sytuacje gdzie brak persony jest lepszy niż słaba persona?

## Źródła do przeszukania

- Dokumentacja Anthropic (claude.ai/docs, prompt engineering, agent design)
- OpenAI documentation (Assistants API, Agents SDK, GPTs customization)
- CrewAI docs (agent roles, personality traits, collaboration)
- LangChain/LangGraph (agent architecture, multi-agent systems)
- Badania akademickie o social simulation, character-based AI, agent personalities
- GitHub repos z multi-agent systems (STORM, Co-STORM, AutoGPT, CrewAI examples)
- Artykuły o prompt engineering dla persony (role-playing, emotional prompting)

## Output contract

Zapisz wyniki do pliku: `documents/researcher/research_results_character_designer.md`

Struktura pliku wynikowego:

```markdown
# Research: Wzorce projektowania persony i charakteru agentów AI

Data: YYYY-MM-DD

Legenda siły dowodów:
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, cookbook, działające repo
- **spekulacja** — inferencja, hipoteza, rekomendacja nieprzetestowana

## TL;DR — 5-7 najważniejszych wzorców/kierunków

1. ...
2. ...

## Wyniki per obszar badawczy

### 1. Wzorce projektowania persony agenta
(opis + siła dowodów per wniosek)

### 2. Persona w systemach wieloagentowych
...

### 3. Promptowanie persony
...

### 4. Persona vs behavioral drift
...

### 5. Przykłady person w produkcyjnych systemach
...

### 6. Anti-patterns i pułapki
...

## Otwarte pytania / luki w wiedzy

- ...

## Źródła / odniesienia

- [Tytuł](URL) — krótki opis co zawiera i po co użyte
```

## Czego NIE rób

- Nie oceniaj dopasowania do naszego systemu (Mrowisko) — to osobny krok po researchu
- Nie dawaj jednej odpowiedzi — dawaj pole możliwości
- Nie skracaj gdy brakuje danych — zaznacz lukę
- Nie cytuj bez źródła — każdy fakt z linkiem lub oznaczeniem źródła
