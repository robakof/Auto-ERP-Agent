# Research: Konwencje pisania promptów ról w systemach multi-agent

## Kontekst

Budujemy system wieloagentowy z 6 wyspecjalizowanymi rolami (np. Architect, Developer, Analyst). Każda rola ma własny prompt systemowy definiujący misję, zakres, reguły krytyczne i workflow. Chcemy sformalizować "jak pisać te prompty" jako wewnętrzną konwencję — analogicznie do coding style guide. Mamy wstępny dokument konwencji i chcemy go oprzeć na sprawdzonych wzorcach.

**Czego NIE rób:** Nie oceniaj czy nasza obecna konwencja jest dobra ani jak ją dopasować do projektu. To osobny krok po badaniu.

## Pytania badawcze

1. **Struktura promptów ról w frameworkach agentowych:** Jak wiodące frameworki (LangChain, CrewAI, AutoGen, Semantic Kernel) strukturyzują prompty systemowe dla wyspecjalizowanych ról? Jakie sekcje uznają za obowiązkowe?

2. **Best practices Anthropic dla promptów systemowych:** Jakie są udokumentowane rekomendacje Anthropic dla struktury złożonych promptów systemowych? (Constitutional AI, Model Spec, oficjalne guides)

3. **Prompt convention w dużych projektach multi-agent:** Czy istnieją przykłady projektów lub firm które sformalizowały "jak pisać prompty ról" jako standard? Jaka jest struktura takich standardów?

4. **Empirycznie udokumentowane anti-patterns:** Jakie błędy w pisaniu promptów systemowych są udokumentowane empirycznie jako powodujące konkretne failure modes? (np. zakopanie krytycznych reguł, sprzeczne instrukcje, brak gate'ów)

## Output contract

Zapisz wyniki do: `documents/researcher/research/research_results_convention_prompt.md`

Struktura (obowiązkowa):
- **TL;DR** — 3-5 najważniejszych wniosków z siłą dowodów
- **Wyniki per pytanie** — każde pytanie osobno, siła dowodów per wniosek (empiryczne / praktyczne / spekulacja)
- **Otwarte pytania / luki** — czego nie udało się potwierdzić lub gdzie źródła się rozjeżdżają
- **Źródła** — tytuł, URL, opis zastosowania
