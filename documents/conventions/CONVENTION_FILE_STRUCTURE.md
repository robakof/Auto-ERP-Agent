---
convention_id: file-structure
version: "1.0"
status: active
created: 2026-03-30
updated: 2026-03-30
author: architect
owner: architect
approver: dawid
reviewer: [developer]
audience: [architect, developer, prompt_engineer, erp_specialist, analyst, dispatcher, metodolog]
scope: "Struktura katalogow i nazewnictwo plikow w repo Mrowisko"
---

# CONVENTION_FILE_STRUCTURE

## TL;DR

- Struktura per koncept, nie per rola: `roles/`, `architecture/`, `workspace/`, `config/`
- Kazdy katalog top-level ma jedno zadanie — jesli robi dwa, rozdziel
- Agent pisze do `workspace/` (artefakty) i `tmp/` (scratch) — nie do cudzych `roles/`
- Artefakty organizowane per TYP (plan, raport, research) — nie per tworca
- `config/` = jedno miejsce na konfiguracje systemu (policy.json, settings)

---

## Zakres

**Pokrywa:**
- Struktura katalogow top-level i ich przeznaczenie
- Gdzie trafiaja artefakty per typ
- Nazewnictwo plikow
- Ownership katalogow

**NIE pokrywa:**
- Zawartosc plikow (konwencje per typ: CONVENTION_PROMPT, CONVENTION_WORKFLOW)
- Wewnetrzna struktura `src/` (CONVENTION_PYTHON, CONVENTION_TYPESCRIPT)
- Struktura bazy danych (CONVENTION_DB_SCHEMA)

---

## Reguly

### 01R: Katalogi top-level — jedno zadanie na katalog

```
roles/              Instrukcje agentow (prompty, onboarding)
architecture/       Decyzje systemowe (ADR, PATTERNS.md)
conventions/        Reguly projektu (CONVENTION_*.md)
workflows/          Definicje procesow (workflow_*.md)
workspace/          Artefakty pracy (plany, raporty, research, rozwiazania)
tools/              CLI narzedzia Python + hooki
core/               Domain model (entities, repositories, mappers)
bot/                Telegram bot
extensions/         Rozszerzenia VS Code
tests/              Testy automatyczne
config/             Konfiguracja systemu (policy.json)
business/           Dokumenty biznesowe czlowieka (nie-agentowe)
tmp/                Scratch agentow (kasowalne)
_loom/              Template projektu (seed)
archive/            Dokumenty historyczne / deprecated
```

**Docelowo:** Dokumentacja (roles/, architecture/, conventions/, workflows/) zostanie
przeniesiona do DB. Filesystem bedzie sluzyc jako warstwa renderowania .md dla czlowieka.
Struktura katalogow musi byc DB-ready — parsowalna i mapowalna na rekordy.

Nie twórz nowych katalogow top-level bez zatwierdzenia Architekta.

### Pliki root (poza katalogami)

```
CLAUDE.md             System prompt (wymog Claude Code — zostaje w root)
README.md             Opis projektu (standard git)
INSTALL.md            Instrukcja instalacji
.gitignore            Git ignore rules
.env.example          Template zmiennych srodowiskowych
pyproject.toml        Python project config (dependencies, build)
pytest.ini            Pytest config
requirements.txt      Python dependencies (pip)
mrowisko.db           SQLite database (runtime, .gitignore)
```

**Katalogi systemowe (nieruszalne):**
```
.git/                 Git repo
.claude/              Claude Code config + worktrees
```

**Katalogi cache (generated, .gitignore):**
```
.pytest_cache/        Pytest cache
.mypy_cache/          MyPy type checker cache
.ruff_cache/          Ruff linter cache
mrowisko.egg-info/    Python package metadata
```

**Whitelist — TYLKO te pliki i katalogi moga istniec w root.**
Cokolwiek spoza listy = do przegladu i usuniecia lub przeniesienia.
Nowy plik/katalog w root wymaga zatwierdzenia Architekta i aktualizacji tej listy.

### 02R: roles/ — instrukcje agentow

```
roles/
  erp_specialist/     ERP_SPECIALIST.md + workflow guides + schema patterns
  developer/          DEVELOPER.md + CODE_STANDARDS.md + TECHSTACK.md
  architect/          ARCHITECT.md
  prompt_engineer/    PROMPT_ENGINEER.md + WORKFLOW_CONVENTION.md
  dispatcher/         DISPATCHER.md + onboarding
  analyst/            ANALYST.md
  metodolog/          METHODOLOGY.md + SPIRIT.md
  shared/             LIFECYCLE_TOOLS.md (cross-role)
```

To sa pliki instrukcji — agent czyta swoja role na starcie sesji.
NIE sa to katalogi robocze agentow (artefakty ida do `workspace/`).

### 03R: architecture/ — wiedza systemowa

```
architecture/
  ADR-001-domain-model.md
  ADR-003-event-listener-system.md
  ADR-004-policy-engine.md
  PATTERNS.md
```

Trwale decyzje architektoniczne. Owner: Architect.
Osobny katalog bo to wiedza systemowa, nie artefakt pracy ani instrukcja roli.

### 04R: workspace/ — artefakty pracy (per typ, nie per rola)

```
workspace/
  plans/              Plany implementacyjne, refaktory
  reports/            Raporty, audyty, diagnozy
  research/           Wyniki researchow
    prompts/          Prompty do uruchomienia w zewnetrznym narzedziu
    results/          Wyniki researchow
  solutions/          SQL, eksporty, rozwiazane zadania ERP
  dashboard/          Dashboard pliki
```

**Kluczowa zmiana:** artefakty organizowane per TYP, nie per tworca.
Plan Architekta i plan Developera leza w tym samym `workspace/plans/`.
Kto stworzyl widac z nazwy pliku lub git blame — nie z katalogu.

### 05R: Kod — flat top-level per modul

```
tools/                CLI narzedzia Python
  lib/                Wspolne biblioteki (agent_bus.py, output.py)
  hooks/              Hooki Claude Code (pre_tool_use.py)
core/                 Domain model (entities, repositories, mappers)
bot/                  Telegram bot
extensions/           Rozszerzenia VS Code
tests/                Testy automatyczne
```

Kod zostaje w root jako osobne katalogi (nie w `src/`).
Uzasadnienie: `tools/` gleboko osadzony w promptach, hookach i CLAUDE.md.
Migracja do `src/tools/` = breaking change bez proporcjonalnej wartosci.

### 06R: config/ — konfiguracja systemu

```
config/
  policy.json         Policy Engine config (ADR-004)
```

Jedno miejsce na konfiguracje. Nie rozpraszaj po katalogu tools/ czy documents/.

### 07R: business/ — dokumenty czlowieka (nie-agentowe)

```
business/
  templates/          Wzory plikow (oferty, brandbook)
  ar/                 Dokumenty biznesowe (wyceny, etykiety, skrypty)
```

Dokumenty biznesowe czlowieka nie mieszaja sie z praca agentow.
Agenci NIE pisza do `business/`.

### 08R: tmp/ — scratch, TTL 7 dni

- Pliki tymczasowe agentow (wiadomosci, logi, draft)
- Kasowalne bez ostrzezenia (docelowo: automatyczny cleanup > 7 dni)
- Nigdy nie referencuj jako trwale zrodlo danych
- NIE w git (.gitignore)

### 09R: Nazewnictwo plikow

| Typ | Pattern | Przyklad |
|-----|---------|---------|
| Konwencja | `CONVENTION_{ZAKRES}.md` | `CONVENTION_FILE_STRUCTURE.md` |
| ADR | `ADR-{NNN}-{tytul}.md` | `ADR-004-policy-engine.md` |
| Workflow | `workflow_{nazwa}.md` | `workflow_convention_creation.md` |
| Prompt roli | `{ROLA}.md` | `DEVELOPER.md` |
| Plan | `plan_{temat}[_v{N}].md` | `plan_dispatcher_rebuild_v2.md` |
| Raport | `{temat}_{data}.md` | `dispatcher_startup_diagnosis_2026_03_29.md` |
| Research prompt | `research_{temat}.md` | `research_runner_patterns.md` |
| Research results | `research_results_{temat}.md` | `research_results_policy_engine_patterns.md` |
| Narzedzie | `{nazwa}.py` | `agent_bus_cli.py` |
| Test | `test_{modul}.py` | `test_agent_bus.py` |
| Config | `{nazwa}.json` | `policy.json` |
| Plik tymczasowy | `{typ}_{kontekst}.md` | `msg_dev_f0_tasks.md` |

### 10R: Ownership — kto pisze gdzie

| Katalog | Kto pisze | Kto czyta |
|---------|-----------|-----------|
| `roles/<rola>/` | PE (prompty), owner roli | Agent danej roli |
| `architecture/` | Architect | Wszyscy |
| `conventions/` | Architect | Wszyscy |
| `workflows/` | PE | Wszyscy |
| `workspace/plans/` | Kazdy agent | Czlowiek + agenci |
| `workspace/reports/` | Kazdy agent | Czlowiek + agenci |
| `workspace/research/` | Kazdy agent | Zlecajacy + agenci |
| `workspace/solutions/` | ERP Specialist | Czlowiek + Analyst |
| `workspace/dashboard/` | Dispatcher (render) | Czlowiek |
| `tools/` | Developer | Wszyscy |
| `core/` | Developer | Wszyscy |
| `bot/` | Developer | Wszyscy |
| `extensions/` | Developer | Wszyscy |
| `tests/` | Developer | Wszyscy |
| `archive/` | Architect (decyzja) | Nikt (deprecated) |
| `_loom/` | Architect | Nowe instancje |
| `config/` | Architect (design), Developer (impl) | Wszyscy (hooks, tools) |
| `business/` | Czlowiek | Czlowiek + agenci (read-only) |
| `tmp/` | Kazdy agent | Agent ktory stworzyl |

Enforcement docelowo przez Policy Engine (ADR-004).
Do wdrozenia: konwencja + code review.

---

## Przyklady

### Przyklad 1: Gdzie plan refaktoru

```
Stara struktura: documents/human/plans/plan_dispatcher_rebuild_v2.md
Nowa struktura:  workspace/plans/plan_dispatcher_rebuild_v2.md

Dlaczego workspace/plans/: plan to artefakt pracy, nie instrukcja roli.
```

### Przyklad 2: Gdzie ADR

```
Stara struktura: documents/architecture/ADR-004-policy-engine.md
Nowa struktura:  architecture/ADR-004-policy-engine.md

Dlaczego top-level: ADR to wiedza systemowa, zasuguje na wlasny namespace.
```

### Przyklad 3: Gdzie prompt roli

```
Stara struktura: documents/dev/DEVELOPER.md
Nowa struktura:  roles/developer/DEVELOPER.md

Dlaczego roles/: to instrukcja, nie dokument roboczy.
```

### Przyklad 4: Gdzie research results

```
Stara struktura: documents/architect/research_results_policy_engine_patterns.md
Nowa struktura:  workspace/research/results/research_results_policy_engine_patterns.md

Dlaczego workspace/research/: research to artefakt pracy, nie instrukcja.
Organizowany per typ, nie per rola tworzaca.
```

### Przyklad 5: Gdzie wyceny biznesowe

```
Stara struktura: documents/human/ar/wyceny/Wycena AUCHAN.xlsm
Nowa struktura:  business/ar/wyceny/Wycena AUCHAN.xlsm

Dlaczego business/: dokumenty czlowieka oddzielone od pracy agentow.
```

---

## Antywzorce

### 01AP: documents/ robi 6 rzeczy

**Zle:** Jeden katalog `documents/` zawiera prompty rol, ADR-y, konwencje,
workspace czlowieka, research, dokumenty biznesowe.
**Dlaczego:** Brak jasnego wlasciciela, trudno znalezc pliki, brak skalowalnoci.
**Dobrze:** Osobne katalogi per koncept: `roles/`, `architecture/`, `workspace/`.

### 02AP: Artefakty organizowane per rola zamiast per typ

**Zle:** `documents/architect/research_results_X.md` (research w katalogu roli)
**Dlaczego:** Plan architekta i plan developera leza w roznych miejscach mimo ze oba sa planami.
**Dobrze:** `workspace/research/results/research_results_X.md` (per typ)

### 03AP: Dokumenty biznesowe mieszane z praca agentow

**Zle:** `documents/human/ar/wyceny/` obok `documents/human/plans/`
**Dlaczego:** Wyceny nie sa artefaktem agenta — to dokumenty firmy.
**Dobrze:** `business/ar/wyceny/` — osobny namespace.

### 04AP: Config rozproszony po repo

**Zle:** Policy w `documents/architecture/`, settings w `.claude/`, config w `tools/`
**Dlaczego:** Agent nie wie gdzie szukac konfiguracji.
**Dobrze:** `config/policy.json` — jedno miejsce.

---

## Migracja z obecnej struktury

Obecna struktura (`documents/` all-in-one) dziala ale nie skaluje.
Migracja = osobne zadanie (backlog), nie czesc tej konwencji.

Orientacyjne mapowanie:
```
documents/<rola>/          → roles/<rola>/          (instrukcje)
documents/architecture/    → architecture/          (ADR, patterns)
documents/conventions/     → conventions/           (bez zmian)
documents/human/plans/     → workspace/plans/
documents/human/reports/   → workspace/reports/
documents/human/dashboard/ → workspace/dashboard/
documents/researcher/      → workspace/research/
documents/<rola>/research_*→ workspace/research/results/
documents/human/ar/        → business/ar/
documents/Wzory plików/    → business/templates/
documents/shared/          → roles/shared/
documents/archive/         → archive/ (lub usunac)
handoffs/                  → archive/ (legacy, handoffy teraz w DB)
tools/                     → tools/              (bez zmian)
core/                      → core/               (bez zmian)
bot/                       → bot/                (bez zmian)
extensions/                → extensions/          (bez zmian)
tests/                     → tests/              (bez zmian)
solutions/                 → workspace/solutions/
```

---

## References

- Research formalny: `documents/researcher/research/research_results_file_structure.md`
- Research sub-agenty: `documents/architect/research_results_file_structure.md`
- Nx, Turborepo, Bazel — per-project/package organizacja, nie per-team
- Google monorepo paper — blast radius i enforcement jako kluczowe przy skali
- LangGraph, AutoGen, ChatDev, MetaGPT — brak standardu multi-agent filesystem (pionierski teren)
- Kubernetes staging — model shared areas z wyzsza kontrola

**Kluczowy wniosek z researchu:** Struktura katalogow BEZ enforcement narzediowego
nie skaluje sie. Konwencja jest fundamentem, ale Policy Engine (ADR-004) jest
niezbednym uzupelnieniem do egzekwowania na skale 100 agentow.

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-30 | Clean start — struktura per koncept, nie per rola. Separation: roles / architecture / workspace / src / config / business. Research: formalny + sub-agenty potwierdzaja kierunek. |
