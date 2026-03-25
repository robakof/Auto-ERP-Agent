# Research: Konwencje kodowania Python w projektach multi-tool CLI

## Kontekst

Projekt Mrowisko ma 55+ narzędzi Python CLI w katalogu tools/ i biblioteki w lib/. Obecny CODE_STANDARDS.md (88 linii) jest zbyt ogólnikowy. Potrzebujemy konwencji kodowania specyficznej dla tego typu projektu (wiele CLI tools w jednym repo, output JSON, agenci LLM jako konsumenci).

## Pytania badawcze

1. **Python CLI conventions w dużych projektach:** Jak projekty z wieloma CLI tools (np. httpie, aws-cli, gcloud, gh) standaryzują interfejs? Jakie reguły dotyczą: output format, error handling, argument parsing, exit codes?

2. **JSON output contract:** Jakie są best practices dla unified JSON output z CLI tools? (np. zawsze {ok, data, error} vs inne wzorce). Jak projekty zapewniają spójność JSON output między 50+ toolami?

3. **Code conventions dla AI-generated code:** Jakie reguły kodowania są najważniejsze gdy kod jest generowany/modyfikowany przez LLM? Co wymuszać żeby output LLM był spójny? (np. mandatory type hints, strict naming, explicit imports)

4. **Minimum viable code convention (Pareto):** Jakie 20% reguł daje 80% spójności kodu w projekcie? Które reguły mają największy impact na czytelność i utrzymywalność?

5. **Error handling w CLI tools:** Jakie wzorce error handling stosują dojrzałe projekty Python CLI? (try/except vs raise, structured errors, user-friendly vs machine-readable errors)

## Output contract

Zapisz wyniki do: `documents/researcher/research/convention_code.md`

Struktura:
- TL;DR — 3-5 kluczowych wniosków
- Wyniki per pytanie (z siłą dowodów)
- Otwarte pytania / luki
- Źródła
