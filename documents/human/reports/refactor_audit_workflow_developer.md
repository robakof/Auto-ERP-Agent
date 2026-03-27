## Audyt refaktoru: workflow_developer.md → 4 pliki

**Data:** 2026-03-27
**Oryginał:** workflows/archive_pre_refactor/workflow_developer.md (248 linii)
**Nowe pliki:** workflow_developer_tool.md, workflow_developer_bugfix.md, workflow_developer_patch.md, workflow_developer_suggestions.md

## Mapowanie reguł

| # | Reguła (oryginał) | Status | Lokalizacja (nowy) |
|---|---|---|---|
| R1 | Małe/średnie zadania. Duże → PROJECT_START | zachowana | developer_tool.md: opis na górze |
| R2 | Routing table per typ | przeniesiona | DEVELOPER.md: sekcja workflow routing |
| R3 | Sprawdź czysty working tree | zachowana | developer_tool.md: Faza 1, krok 1 |
| R4 | Plan do pliku documents/human/plans/ | zachowana | developer_tool.md: Faza 1, krok 2 |
| R5 | Plan review do Architekta — HANDOFF | zachowana | developer_tool.md: Faza 2, krok 1 |
| R6 | REJECT → popraw, APPROVE → dalej | zachowana | developer_tool.md: Faza 2, krok 2-3 |
| R7 | TDD preferowane | zachowana | developer_tool.md: Faza 3, krok 1 |
| R8 | Integration + unit tests, mockuj | zachowana | developer_tool.md: Faza 3, krok 1.1 |
| R9 | Test checkpoint po metodzie/funkcji | zachowana | developer_tool.md: Faza 3, krok 2 |
| R10 | Raportuj explicit: test_X.py::TestY | zachowana | developer_tool.md: Faza 3, krok 2 |
| R11 | Blast radius check | zachowana | developer_tool.md: Faza 3, krok 3 |
| R12 | Commit per działająca zmiana | zachowana | developer_tool.md: Faza 3, krok 4 |
| R13 | Nieomnawiane kwestie → pytaj usera | zachowana | developer_tool.md: Faza 4, krok 1 |
| R14 | Pokaż, zapytaj o feedback, iteruj | zachowana | developer_tool.md: Faza 4, krok 2-3 |
| R15 | Code review do Architekta — HANDOFF | zachowana | developer_tool.md: Faza 5, krok 1 |
| R16 | NEEDS REVISION → popraw, PASS → dalej | zachowana | developer_tool.md: Faza 5, krok 2-3 |
| R17 | Checklist publikacji | zachowana | developer_tool.md: Faza 6, krok 1-3 |
| F1 | Pliki robocze nie w root | zachowana | developer_tool.md: Faza 3 Forbidden |
| F2 | Kod bez testów nie jest gotowy | zachowana | developer_tool.md: Faza 3 Forbidden |
| R18 | Diagnoza przyczyny, nie objawu | zachowana | developer_bugfix.md: Faza 1, krok 1 |
| R19 | Blind spot query | zachowana | developer_bugfix.md: Faza 1, krok 2 |
| R20 | Oceń skalę | zachowana | developer_bugfix.md: Faza 1, krok 3 |
| R21 | Przedstaw diagnozę użytkownikowi | zachowana | developer_bugfix.md: Faza 1, krok 4 |
| R22 | Test checkpoint po zmianie, explicit | zachowana | developer_bugfix.md: Faza 2, krok 1-2 |
| R23 | Blast radius check po fixie | zachowana | developer_bugfix.md: Faza 2, krok 3 |
| R24 | Commit z przyczyny (nie objawu) | zachowana | developer_bugfix.md: Faza 2, krok 4 |
| F3 | Nie naprawiaj jednej instancji z 10 | zachowana | developer_bugfix.md: Faza 2 Forbidden |
| F4 | Nie obchód zamiast naprawy | zachowana | developer_bugfix.md: Faza 2 Forbidden |
| R25 | ≤5 linii, 1 plik, nie zmienia interfejsu | zachowana | developer_patch.md: Zakres |
| R26 | Read → Edit → smoke → commit | zachowana | developer_patch.md: Faza 1, krok 1-3 |
| R27 | Zmiana docs → notyfikacja PE | zachowana | developer_patch.md: Faza 2, krok 2 |
| F5 | Nie zmieniaj interfejsu w Patch | zachowana | developer_patch.md: Faza 1 Forbidden |
| F6 | >5 linii = oceń czy nie nowe narzędzie | zachowana | developer_patch.md: Faza 1 Forbidden |
| R28 | Przeczytaj suggestions (render.py) | zachowana | developer_suggestions.md: Faza 1, krok 1 |
| R29 | Oceń: warto/nie warto/dyskusja | zachowana | developer_suggestions.md: Faza 1, krok 2 |
| R30 | Sprawdź czy nie istnieje przed backlogiem | zachowana | developer_suggestions.md: Faza 2, krok 1 |
| R31 | backlog-add + suggest-status implemented | zachowana | developer_suggestions.md: Faza 2, krok 2-3 |
| R32 | arch_check.py przy zmianach ścieżek | przeniesiona | DEVELOPER.md: guideline Zamknięcie sesji |
| R33 | Commit + push przez git_commit.py | przeniesiona | DEVELOPER.md: guideline Zamknięcie sesji |
| R34 | Log sesji | przeniesiona | DEVELOPER.md: guideline Zamknięcie sesji |
| R35 | Mockup outputu przed kodem | przeniesiona | DEVELOPER.md: guideline Mockup outputu |

## Podsumowanie

- **Zachowane w workflow:** 31 reguł + 6 forbidden = 37/41
- **Przeniesione do DEVELOPER.md:** 4 (R32-R35: Zamknięcie + Mockup — guidelines)
- **Usunięte:** 0
- **Zgubione:** 0

**Verification:** 37 + 4 = 41 = total. ✓ Pokrycie 100%.
