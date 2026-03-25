# Audyt reformatu: PROMPT_CONVENTION.md

Data: 2026-03-25
Źródło: `documents/prompt_engineer/PROMPT_CONVENTION.md` (278 linii, 8 sekcji)
Wynik: `documents/prompt_engineer/PROMPT_CONVENTION.md` (v1.0 CONVENTION_META format)

## Mapowanie reguł: oryginał → nowy format

| # | Oryginał (sekcja / treść) | Nowy format | Status |
|---|---|---|---|
| 1 | §1 Warstwy systemu promptowego (diagram + zasady) | 01R | ✓ zachowane |
| 2 | §2 Znaczniki sekcji: XML tags + Markdown | 02R | ✓ zachowane |
| 3 | §2 Hierarchia ważności w dokumencie | 03R | ✓ zachowane |
| 4 | §2 Numeracja (fazy + litery) | 04R | ✓ zaktualizowane (dodano 01R/01AP format) |
| 5 | §2 Styl pisania (afirmatywne, bez emoji) | 05R | ✓ zachowane + dodano "bez narracji przyspieszającej" z PE critical_rules |
| 6 | §3 Szablon promptu roli (pełny template) | 06R | ✓ zachowane |
| 7 | §3 Sekcje opcjonalne (persona, behavior_examples, gates...) | 07R | ✓ zachowane + dodano code_maturity_levels |
| 8 | §4 Co gdzie trafia (tabela + test przynależności) | 08R | ✓ zachowane |
| 9 | §5 Szablon workflow | Usunięty — redundantny | ✓ CONVENTION_WORKFLOW.md jest osobną konwencją |
| 10 | §6 Zasady zmian (failure mode, patch vs refaktor) | 09R | ✓ zachowane |
| 11 | §6 Wymiary oceny promptu (6 wymiarów) | 10R | ✓ zachowane |
| 12 | §7 Prompty badawcze (output contract, lokalizacje) | 11R | ✓ zachowane, ścieżki zaktualizowane do researcher/ |
| 13 | §8 Czego unikać (6 punktów) | 01AP-06AP | ✓ rozpisane jako Antywzorce z "Źle/Dlaczego/Dobrze" |

## Dodane (nowe w stosunku do oryginału)

| Element | Źródło |
|---|---|
| YAML frontmatter | CONVENTION_META wymóg |
| TL;DR | CONVENTION_META wymóg |
| Zakres (Pokrywa / NIE pokrywa) | CONVENTION_META wymóg |
| Changelog | CONVENTION_META wymóg |
| Przykład 1: Minimalny prompt roli | Nowy — ilustracja 06R |
| Przykład 2: Test przynależności | Nowy — ilustracja 08R |
| 05R: "bez narracji przyspieszającej" | Z PE critical_rules (reguła 9) |
| 07R: code_maturity_levels | Z ARCHITECT.md (istniejąca sekcja opcjonalna) |

## Usunięte

| Element | Powód |
|---|---|
| §5 Szablon workflow (pełny template) | Przeniesiony do CONVENTION_WORKFLOW.md. Konwencja prompt nie powinna duplikować konwencji workflow. |

## Wynik audytu

- Reguły oryginału: 13 elementów merytorycznych
- Zachowane: 12 (mapowane do 01R-11R + 01AP-06AP)
- Usunięte: 1 (§5 szablon workflow — redundantny z CONVENTION_WORKFLOW)
- Zgubione: 0
