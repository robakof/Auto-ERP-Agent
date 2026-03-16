# Research: Wymuszanie reguł behawioralnych na agentach LLM

## Kontekst

Agenci Claude Code mają w CLAUDE.md i dokumentach ról zakaz używania pewnych komend:
- `cat`/`head`/`tail` → zamiast tego `Read`
- `grep`/`rg` → zamiast tego `Grep`
- `find`/`ls` → zamiast tego `Glob`
- `python -c "..."` z wieloliniowym kodem → zamiast tego plik tymczasowy

Mimo wielokrotnego dokumentowania, agenci nagminnie łamią te reguły.
Dokumentacja (CLAUDE.md) nie wystarcza — agent "wie" ale nie "robi".

## Pytanie badawcze

Jak skutecznie wymusić ograniczenia behawioralne na agencie LLM działającym w pętli tool-use?
Jakie mechanizmy są skuteczne, a które zawodzą i dlaczego?

## Obszary do zbadania

1. **Dlaczego prompt-level reguły zawodzą?**
   - Czy to problem "salience" (reguła zakopana w długim prompcie)?
   - Czy to problem kontekstu (agent nie widzi reguły gdy jej potrzebuje)?
   - Czy to pattern matching w pretrainingu jest silniejszy niż instrukcja?
   - Badania: "instruction following degradation", "context window salience"

2. **Hook-level enforcement (PreToolUse)**
   - Czy blokowanie na poziomie systemu (hook) jest skuteczniejsze niż prompt?
   - Jakie są ograniczenia podejścia hook-based?
   - Czy `permissionDecision: deny` z komunikatem powoduje że agent uczy się w sesji?

3. **Alternatywne podejścia z literatury / praktyki**
   - "Constitutional AI" — czy auto-krytyka przed akcją pomaga?
   - "Tool scaffolding" — czy można usunąć zakazane narzędzia ze schematu zamiast zakazywać?
   - Prompt engineering: czy "zawsze używaj Read zamiast cat" jest skuteczniejsze niż "nie używaj cat"?
   - Pozycja reguły w prompcie: header vs footer vs inline przy definicji narzędzia

4. **Praktyczne rozwiązania do oceny**
   - Usunięcie `Bash` z allowed tools całkowicie i wymuszenie tylko dedykowanych narzędzi
   - PreToolUse hook który przy `cat`/`grep`/`find` w komendzie zwraca deny + "użyj Read/Grep/Glob"
   - Reguła w formacie "jeśli chcesz X → wywołaj Y" zamiast "nie rób X"
   - Powtórzenie reguły w kilku miejscach (CLAUDE.md + dokument roli + inline w sekcji narzędzi)

## Oczekiwany wynik

Raport `research_results_agent_rule_enforcement.md` zawierający:
1. Diagnozę dlaczego dokumentacja nie wystarcza (mechanizm psychologiczny/architektoniczny)
2. Ranking podejść enforcement: od najbardziej do najmniej skutecznego
3. Konkretna rekomendacja dla tego projektu (co wdrożyć w PreToolUse lub CLAUDE.md)
