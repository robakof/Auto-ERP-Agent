# Research: Formalizacja konwencji pisania promptów w systemach multi-agent

## Kontekst

Projekt Mrowisko ma istniejący dokument PROMPT_CONVENTION.md (278 linii) opisujący jak pisać prompty ról. Chcemy go sformalizować jako konwencję. Mamy już researche o strukturze promptów (system_prompt_structure.md, multiagent_prompts.md) — nie powtarzaj tego.

## Pytania badawcze

1. **Formalizacja prompt standards:** Czy istnieją projekty/firmy które sformalizowały "jak pisać prompty" jako wewnętrzny standard (nie prompt engineering guide, ale konwencja/style guide dla promptów systemowych)? Jaką strukturę mają te standardy?

2. **Anti-patterns w prompt conventions:** Jakie błędy popełniają zespoły formalizując konwencje promptów? (np. za dużo reguł, za sztywna struktura, brak wersjonowania)

3. **Prompt linting / walidacja:** Czy istnieją narzędzia lub praktyki automatycznej walidacji promptów pod kątem zgodności z konwencją? (np. sprawdzanie obecności wymaganych sekcji, limity długości)

4. **Ewolucja konwencji promptów:** Jak konwencje promptów ewoluują w czasie? Jak zarządzać breaking changes gdy wiele agentów korzysta z jednej konwencji?

## Output contract

Zapisz wyniki do: `documents/researcher/research/convention_prompt.md`

Struktura:
- TL;DR — 3-5 kluczowych wniosków
- Wyniki per pytanie (z siłą dowodów: empiryczne / praktyczne / spekulacja)
- Otwarte pytania / luki
- Źródła
