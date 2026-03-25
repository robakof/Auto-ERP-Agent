# Self-Review: Konwencje P0 (PROMPT, CODE, COMMUNICATION)

Date: 2026-03-25
Reviewer: Architect (self-review, Faza 4 workflow convention_creation)

## Checklist CONVENTION_META (01R-05R)

### YAML Frontmatter (01R)

| Pole | PROMPT | CODE | COMMUNICATION |
|------|--------|------|---------------|
| convention_id | ✓ prompt-convention | ✓ code-convention | ✓ communication-convention |
| version | ✓ 1.1 | ✓ 1.1 | ✓ 1.1 |
| status | ✓ draft | ✓ draft | ✓ draft |
| created | ✓ | ✓ | ✓ |
| **updated** | ✓ | ✓ | **✗ BRAK** |
| author | ✓ architect | ✓ architect | ✓ architect |
| owner | ✓ prompt_engineer | ✓ architect | ✓ architect |
| approver | ✓ dawid | ✓ dawid | ✓ dawid |
| audience | ✓ | ✓ | ✓ |
| scope | ✓ | ✓ | ✓ |

**Finding W1 (Warning):** COMMUNICATION brakuje pola `updated` w YAML — naruszenie META 01R.
**Fix:** Dodaj `updated: 2026-03-25`.

### Wymagane sekcje (02R)

| Sekcja | PROMPT | CODE | COMMUNICATION |
|--------|--------|------|---------------|
| TL;DR | ✓ | ✓ | ✓ |
| Zakres | ✓ | ✓ | ✓ |
| Kontekst | ✓ (opcja) | ✗ brak | ✓ (opcja) |
| Reguły | ✓ 14R | ✓ 16R | ✓ 13R |
| Przykłady | ✓ 4 | ✓ 3 | ✓ 5 |
| Antywzorce | ✓ 8AP | ✓ 7AP | ✓ 7AP |
| Changelog | ✓ | ✓ | ✓ |

**Finding S1 (Suggestion):** CODE nie ma sekcji Kontekst. Opcjonalna per META, ale niespójna z pozostałymi dwoma. Nie blokuje.

### Status lifecycle (03R)
Wszystkie: `draft` ✓. Poprawny stan dla Fazy 4.

### Wersjonowanie (04R)
Wszystkie: changelog dokumentuje zmiany v1.0→v1.1 ✓.

### Lokalizacja (05R)
Wszystkie w `documents/conventions/` ✓. Nazwy `CONVENTION_{ZAKRES}.md` ✓.

---

## Zgodność z SPIRIT.md

| Zasada | PROMPT | CODE | COMMUNICATION |
|--------|--------|------|---------------|
| Buduj dom, nie szałas | ✓ Reużywalne wzorce, nie ad-hoc | ✓ Pareto reguły ze źródeł | ✓ Skalowalne kanały |
| Automatyzuj siebie | ✓ Szablon roli = mniej decyzji | ✓ Lint/type-check enforcement | ✓ Decision tree = autonomia |
| Wiedza przetrwa sesję | ✓ Plik, nie czat | ✓ Plik, nie czat | ✓ Plik, nie czat |
| Wybieraj to co skaluje | ✓ 5-warstwy skalują | ✓ Wspólny JSON schema skaluje | ✓ Korelacja/TTL skalują |

Brak konfliktów z SPIRIT.md.

---

## Spójność wewnętrzna i cross-convention

### W2 (Warning): CODE 08R vs 14R — ambiguity print()

**08R mówi:** "print() jest zakazany w kodzie produkcyjnym"
**14R mówi:** "print('WARNING...', file=sys.stderr)" — używa print() na stderr

08R zakazuje print() bez kwalifikacji. 14R wprowadza wyjątek (stderr). Te dwie reguły kolidują.

**Fix:** Uściślij 08R: "print() na stdout jest zakazany" lub "print() bez file=sys.stderr jest zakazany".

### S2 (Suggestion): COMMUNICATION 05R/13R — komendy CLI

05R referuje `suggest-status` do oznaczania sugestii. 13R referuje `suggest-status --id <id> --status rejected`.
Zweryfikować czy ta komenda istnieje w agent_bus_cli.py. Jeśli nie — to jest gap w toolingu, nie w konwencji. Konwencja może opisywać docelowe zachowanie.

### S3 (Suggestion): CODE 16R — undefined helper

Przykład testów kontraktowych używa `run_tool()` bez definicji. Drobne — to jest pattern, nie gotowy kod. Ale developer skopiuje dosłownie i dostanie NameError.

### Cross-convention consistency

- PROMPT 09R (workflow bez XML tags) ↔ CODE/COMMUNICATION (nie prompty roli, inny format) — spójne ✓
- PROMPT 01R (warstwy: CLAUDE.md → rola → workflow) ↔ CODE 09R (konfiguracja) — nie kolidują ✓
- COMMUNICATION 06R (max 500 zn w send) ↔ PROMPT (brak limitu w prompcie) — różne domeny, OK ✓
- CODE 02R (JSON schema) ↔ COMMUNICATION (agent_bus format) — agent_bus ma własny format, CODE dotyczy narzędzi CLI — spójne ✓

---

## Podsumowanie

| Severity | Count | Findings |
|----------|-------|----------|
| Critical | 0 | — |
| Warning | 2 | W1: COMMUNICATION brak `updated`, W2: CODE 08R/14R conflict |
| Suggestion | 3 | S1: CODE brak Kontekst, S2: suggest-status CLI, S3: run_tool() undefined |

**Decyzja: Naprawiam W1 i W2 (warnings) przed przekazaniem do review.**
Suggestions pozostawiamy — nie blokują.
