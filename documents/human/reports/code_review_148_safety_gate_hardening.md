# Code Review: #148 Safety Gate Hardening

Date: 2026-03-25
Files: tools/hooks/pre_tool_use.py, tests/test_pre_tool_use.py

## Summary

**Overall assessment:** PASS
**Code maturity level:** Senior — funkcje ≤15 linii, single responsibility, shlex fallback na ValueError, frozenset dla lookupów, czytelny dispatch w validate_segment. Testy pokrywają granice.

## Warunki Architekta — spełnienie

| Warunek | Status | Implementacja |
|---------|--------|---------------|
| W1: mv walidacja | ✓ | check_mv() — target OR all sources in allowed |
| W2: parsowanie flag/wielu args | ✓ | extract_paths() — shlex + skip flags |
| W3: split && per segment | ✓ | split_chain() + pętla w main() |

## Architektura

Flow poprawny:
```
DANGEROUS_PATTERNS → DENY_WITH_REPAIR → validate_segment() [per && segment] → SAFE_PREFIXES
```

Nowe warstwy wstawione PRZED SAFE_PREFIXES — destrukcyjne komendy są walidowane nawet jeśli są na liście safe prefixes. Poprawna kolejność.

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

- **pre_tool_use.py:91** — `split_chain` dzieli tylko po `&&`. Komendy z `;` lub `||` omijają walidację per-segment. Przykład: `rm tmp/x ; rm core/y` → validate_segment dostaje pełny string, first_token to `rm`, extract_paths wyciągnie `tmp/x`, `;`, `rm`, `core/y` — ale `;` i `rm` nie są ścieżkami, więc... Actually `shlex.split("rm tmp/x ; rm core/y")` da `['rm', 'tmp/x', ';', 'rm', 'core/y']`, z czego extract_paths zwróci `['tmp/x', ';', 'rm', 'core/y']`. `path_in_allowed(';')` → False → DENY. Przypadkiem działa poprawnie, ale z niewłaściwego powodu. Dodaj split po `;` i `||` do `split_chain` dla jawnej poprawności.

- **pre_tool_use.py:101** — `extract_paths` nie obsługuje `--` (end-of-flags). `rm -- -dangerous-name.py` → `-dangerous-name.py` jest skipowane jako flaga. Agent mógłby skasować plik o nazwie zaczynającej się od `-` bez walidacji ścieżki. Ryzyko minimalne (taki plik musiałby istnieć), ale warto obsłużyć.

### Suggestions (nice to have)

- **pre_tool_use.py:146** — `check_execution`: `start . foo` pasuje do `startswith("start . ")`. Nie jest to problem bezpieczeństwa (start i tak otwiera explorer), ale jest to niezamierzone dopasowanie. Rozważ exact match zamiast startswith.

- **test_pre_tool_use.py** — Brak testu dla `rm` bez argumentów. `all_paths_allowed([])` zwraca False → DENY. Poprawne zachowanie, ale warto udokumentować testem.

- **test_pre_tool_use.py** — Brak testu dla chain z `;`. Dodaj test `rm tmp/x ; rm core/y` → DENY, żeby potwierdzić że obecna implementacja obsługuje ten case (nawet jeśli z niewłaściwego powodu).

## Recommended Actions

- [ ] Rozszerz `split_chain` o `;` i `||` (Warning 1)
- [ ] Obsłuż `--` w `extract_paths` (Warning 2)
- [ ] Dodaj 2-3 testy edge case (Suggestions)

Żadne z powyższych nie blokuje commitu — to ulepszenia. Implementacja jest solidna i bezpieczna.
