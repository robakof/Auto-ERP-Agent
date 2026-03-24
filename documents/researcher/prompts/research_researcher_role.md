# Research: Wzorce projektowania roli Researcher w systemach agentowych

## Cel

Zebrać sprawdzone wzorce, praktyki i rekomendacje dotyczące projektowania agentów
wyspecjalizowanych w prowadzeniu researchu (web search, analiza źródeł, synteza wiedzy).

## Pytania badawcze

### 1. Struktura i workflow researchera

- Jakie są sprawdzone wzorce workflow dla agentów badawczych? (np. STORM, iteracyjne pogłębianie, drzewo pytań)
- Jak strukturyzować proces: szerokość vs głębokość? Kiedy iść szeroko, kiedy głęboko?
- Jak obsługiwać multi-hop reasoning (pytanie wymaga połączenia wielu źródeł)?
- Jakie są dobre praktyki dla research planning przed wykonaniem?

### 2. Jakość i wiarygodność źródeł

- Jak oceniać wiarygodność źródeł w trakcie researchu?
- Jak obsługiwać konfliktowe informacje między źródłami?
- Jakie są wzorce triangulacji (potwierdzanie faktu z wielu źródeł)?
- Jak oznaczać siłę dowodów (empiryczne / praktyczne / spekulacja)?

### 3. Synteza i output

- Jak strukturyzować wyniki researchu dla maksymalnej użyteczności?
- Jakie są wzorce TL;DR vs pełny raport?
- Jak prezentować trade-offy i alternatywy zamiast jednej odpowiedzi?
- Jak oznaczać luki w wiedzy i otwarte pytania?

### 4. Narzędzia i integracje

- Jakie narzędzia/API są najczęściej używane przez research agents?
- Jak łączyć web search z RAG (retrieval from local docs)?
- Jakie są wzorce cache'owania i unikania powtórnych wyszukiwań?

### 5. Persona i zachowania researchera

- Jaki styl myślenia jest optymalny dla researchera? (krytyczny, otwarty, sceptyczny?)
- Jak balansować między dokładnością a szybkością?
- Jak obsługiwać niepewność i brak danych?
- Jakie są anti-patterns (np. confirmation bias, over-reliance on first result)?

### 6. Przykłady implementacji

- Jak OpenAI, Anthropic, LangChain, CrewAI implementują research agents?
- Jakie są publiczne przykłady dobrze działających research agents?
- Co wyróżnia najlepsze implementacje od przeciętnych?

## Źródła do przeszukania

- Dokumentacja Anthropic (claude.ai/docs, cookbook)
- OpenAI Cookbook i dokumentacja Assistants API
- LangChain docs (agents, tools, research patterns)
- CrewAI docs (role definitions, research crew examples)
- AutoGPT, BabyAGI, STORM paper (Stanford)
- Artykuły o multi-agent research systems
- GitHub repos z implementacjami research agents

## Output contract

Zapisz wyniki do pliku: `documents/prompt_engineer/research_results_researcher_role.md`

Struktura pliku wynikowego:

```markdown
# Research: Wzorce projektowania roli Researcher

Data: YYYY-MM-DD

## TL;DR — 5 najważniejszych wzorców/kierunków

1. ...
2. ...

## Wyniki per obszar badawczy

### 1. Struktura i workflow
(opis + siła dowodów: empiryczne / praktyczne / spekulacja)

### 2. Jakość i wiarygodność źródeł
...

### 3. Synteza i output
...

### 4. Narzędzia i integracje
...

### 5. Persona i zachowania
...

### 6. Przykłady implementacji
...

## Otwarte pytania / luki w wiedzy

- ...

## Źródła / odniesienia

- [Tytuł](URL) — krótki opis co zawiera
```

## Czego NIE rób

- Nie oceniaj dopasowania do naszego systemu (Mrowisko) — to osobny krok po researchu
- Nie dawaj jednej odpowiedzi — dawaj pole możliwości
- Nie skracaj gdy brakuje danych — zaznacz lukę
- Nie cytuj bez źródła — każdy fakt z linkiem lub oznaczeniem źródła
