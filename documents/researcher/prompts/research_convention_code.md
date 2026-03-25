# Research: Konwencje kodowania Python w projektach multi-tool CLI

## Kontekst

Projekt ma 50+ narzędzi Python CLI w jednym repozytorium — każde narzędzie to oddzielny skrypt generujący JSON output, obsługujący błędy i przyjmujący argumenty przez CLI. Narzędzia są często generowane lub modyfikowane przez LLM (agenty). Chcemy stworzyć coding convention specyficzną dla tego wzorca — nie ogólny Python style guide, ale reguły dostosowane do: wiele CLI tools w jednym repo, JSON output, AI jako główny "programista".

**Czego NIE rób:** Nie oceniaj czy nasze obecne podejście jest dobre ani jak dopasować konwencję do projektu. To osobny krok po badaniu.

## Pytania badawcze

1. **Python CLI conventions w projektach multi-tool:** Jak dojrzałe projekty z wieloma CLI tools (httpie, aws-cli, gcloud CLI, gh CLI) standaryzują interfejs? Jakie reguły obowiązują dla: output format, error handling, argument parsing, exit codes?

2. **Coding conventions dla AI-generated code:** Jakie reguły kodowania są najważniejsze gdy kod jest generowany lub modyfikowany przez LLM? Co wymuszać żeby output LLM był spójny między narzędziami? (np. mandatory type hints, strict naming, explicit imports)

3. **Projekty multi-tool w jednym repo:** Jakie coding conventions stosują projekty utrzymujące wiele powiązanych CLI tools w jednym repozytorium? Jak zapewniają spójność interfejsu między toolami?

4. **Minimum viable code convention (Pareto):** Jakie 20% reguł daje 80% spójności kodu? Które reguły mają największy impact na czytelność i utrzymywalność przy minimalnym koszcie egzekwowania?

## Output contract

Zapisz wyniki do: `documents/researcher/research/research_results_convention_code.md`

Struktura (obowiązkowa):
- **TL;DR** — 3-5 najważniejszych wniosków z siłą dowodów
- **Wyniki per pytanie** — każde pytanie osobno, siła dowodów per wniosek (empiryczne / praktyczne / spekulacja)
- **Otwarte pytania / luki** — czego nie udało się potwierdzić lub gdzie źródła się rozjeżdżają
- **Źródła** — tytuł, URL, opis zastosowania
