# Research prompt: rozwiązania dla completion bias w agentach LLM

## Kontekst

Pracujemy z systemem wieloagentowym gdzie LLM-y autonomicznie wykonują zadania.
Obserwowany problem: agenci mają wewnętrzną presję żeby "dostarczyć i skończyć"
mimo braku zewnętrznego nacisku. Przejawia się to jako:

- Pomijanie reguł które znają (checklist, testy, hierarchia pliku)
- Eskalacja błędów gdy złapani — szybka naprawa generuje kolejne błędy
- Ewaluacja reguł PO decyzji zamiast PRZED
- Rozwiązania lokalne zamiast systemowych

Szukamy rozwiązań tego problemu — eksploracyjnie, bez założenia z góry
że znamy odpowiedź.

## Pytania badawcze

1. **Mechanizm** — jak w literaturze akademickiej i inżynierskiej opisuje się
   ten rodzaj zachowania LLM? Jakie nazwy (completion bias, helpfulness bias,
   sycophancy, reward hacking, rushing)? Co wiadomo o jego źródle?

2. **Rozwiązania promptowe** — jakie techniki prompt engineering adresują
   ten problem? Nie tylko "take a breath" — szeroko: chain-of-thought,
   reflection prompts, slow thinking, pause tokens, constitutional AI,
   self-critique, pre-mortem prompting, itp. Co ma empiryczne potwierdzenie?

3. **Rozwiązania architektoniczne** — czy problem rozwiązuje się na poziomie
   systemu zamiast promptu? Np. obowiązkowy krok "plan before act",
   oddzielna faza weryfikacji, inny agent jako reviewer, human-in-the-loop
   checkpointy, ograniczenie długości odpowiedzi wymuszające więcej kroków.

4. **Narracja i środowisko** — czy zmiana tonu/narracji w system promptcie
   (spokój, jakość jako cel, brak pośpiechu) ma udokumentowany wpływ?
   Jakie framy (medytacja, rzemiosło, ogród, droga) były testowane?
   Co działa, co jest tylko poetyckie?

5. **Systemy wieloagentowe** — czy w systemach z wieloma agentami problem
   jest inny niż w pojedynczym agencie? Jak inne systemy (AutoGPT, CrewAI,
   Anthropic multi-agent) projektują przepływ żeby minimalizować ten wzorzec?

6. **Nieoczywiste rozwiązania** — co zaskakuje w badaniach? Czy są podejścia
   kontraintuicyjne które działają?

## Output contract

Zapisz wyniki do pliku: `documents/prompt_engineer/research_results_completion_bias.md`

Struktura pliku wynikowego:
```
# Research: [tytuł]
Data: YYYY-MM-DD

## TL;DR — 3-5 najbardziej obiecujących kierunków
(to czytam najpierw — konkretne, actionable)

## Wyniki per obszar badawczy
(sekcje odpowiadające pytaniom badawczym)
Dla każdego rozwiązania: opis + siła dowodów [empiryczne / praktyczne / spekulacja]

## Co nierozwiązane / otwarte pytania

## Źródła / odniesienia
```

Czego NIE rób:
- Nie oceniaj czy pasuje do naszego systemu — to osobny krok
- Nie dawaj jednej odpowiedzi — dawaj pole możliwości
- Nie skracaj gdy brakuje danych — zaznacz lukę
