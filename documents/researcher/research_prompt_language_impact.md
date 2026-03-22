# Research: Wpływ języka na działanie modeli LLM

## Cel

Zebrać dane i badania dotyczące wpływu języka promptów i odpowiedzi na jakość, koszt i wydajność modeli LLM.

## Kontekst

W projekcie Mrowisko używamy promptów po polsku i po angielsku. Użytkownik komunikuje się z agentami po polsku, ale część dokumentacji technicznej i promptów może być po angielsku. Chcemy zrozumieć trade-offy.

## Pytania badawcze

### 1. Jakość odpowiedzi: polski vs angielski

- Czy modele LLM (Claude, GPT-4) działają gorzej na polskim niż na angielskim?
- Jeśli tak — o ile gorzej? (dane ilościowe z benchmarków)
- W jakich zadaniach różnica jest największa? (reasoning, coding, creative writing, factual QA)
- Czy użycie polskiego promptu z angielskim outputem (lub odwrotnie) ma sens?

### 2. Tokenizacja i koszt

- Ile tokenów zajmuje ta sama treść w polskim vs angielskim?
- Czy polski tekst jest droższy per "jednostka informacji"?
- Jak wyglądają języki azjatyckie (chiński, japoński, koreański) pod względem gęstości tokenów?
- Czy języki azjatyckie są bardziej efektywne kosztowo ze względu na ideogramy?

### 3. Kontekst i długość okna

- Czy polski "zjada" więcej context window na tę samą informację?
- Jakie są praktyczne implikacje dla długich promptów i dokumentacji?
- Czy warto kompresować prompty przez użycie angielskiego w częściach technicznych?

### 4. Wielojęzyczność w systemach agentowych

- Jak organizacje production-grade rozwiązują kwestię języka?
- Czy są wzorce "prompt w języku X, output w języku Y"?
- Jak obsługiwać komunikację agent-agent gdy agenci mają różne języki?

### 5. Języki azjatyckie — efektywność

- Czy chiński/japoński faktycznie są bardziej efektywne tokenowo?
- Jakie są trade-offy? (jakość reasoning, dostępność zasobów, interoperability)
- Czy są case studies firm azjatyckich używających natywnych języków w produkcji?

### 6. Rekomendacje praktyczne

- Kiedy używać polskiego, a kiedy angielskiego?
- Czy mieszać języki w jednym prompcie? (np. instrukcje PL, kod EN)
- Jakie są best practices dla projektów wielojęzycznych?

## Źródła do przeszukania

- Dokumentacja Anthropic i OpenAI o wielojęzyczności i tokenizacji
- Badania akademickie: multilingual LLM performance, tokenization efficiency
- Benchmarki modeli na różnych językach (MMLU multilingual, HellaSwag multilingual)
- Artykuły o tokenizacji: BPE, SentencePiece, wpływ na języki niełacińskie
- Case studies firm używających LLM w językach innych niż angielski
- Porównania tokenizacji: polski vs angielski vs chiński vs japoński
- GitHub discussions, Reddit r/LocalLLaMA, HN threads o language efficiency

## Output contract

Zapisz wyniki do pliku: `documents/researcher/research_results_language_impact.md`

Struktura pliku wynikowego:

```markdown
# Research: Wpływ języka na działanie modeli LLM

Data: YYYY-MM-DD

Legenda siły dowodów:
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, case study, działające repo
- **spekulacja** — inferencja, hipoteza, rekomendacja nieprzetestowana

## TL;DR — 5-7 najważniejszych wniosków

1. ...
2. ...

## Wyniki per obszar badawczy

### 1. Jakość odpowiedzi: polski vs angielski
(dane ilościowe, benchmarki, trade-offy + siła dowodów)

### 2. Tokenizacja i koszt
(porównania: PL vs EN vs chiński/japoński + siła dowodów)

### 3. Kontekst i długość okna
...

### 4. Wielojęzyczność w systemach agentowych
...

### 5. Języki azjatyckie — efektywność
...

### 6. Rekomendacje praktyczne
...

## Otwarte pytania / luki w wiedzy

- ...

## Źródła / odniesienia

- [Tytuł](URL) — krótki opis co zawiera i po co użyte
```

## Czego NIE rób

- Nie oceniaj dopasowania do naszego projektu — to osobny krok
- Nie dawaj jednej odpowiedzi — pokazuj trade-offy
- Nie skracaj gdy brakuje danych — zaznacz lukę
- Nie cytuj bez źródła — każdy fakt z linkiem
- Jeśli znajdziesz sprzeczne dane (np. "chiński bardziej efektywny" vs "chiński mniej efektywny") — opisz konflikt, nie ukrywaj go
