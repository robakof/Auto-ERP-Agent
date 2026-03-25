# Mapa konwencji — 100% pokrycia

Data: 2026-03-25
Autor: Architect
Status: draft — do dyskusji z Dawidem

---

## Legenda statusów

| Status | Znaczenie |
|---|---|
| **active** | Sformalizowana konwencja w formacie CONVENTION_META |
| **exists-informal** | Treść istnieje, ale nie w formacie konwencji |
| **implicit** | Reguły rozproszone w CLAUDE.md / role docs |
| **missing** | Brak jakiejkolwiek formalizacji |

## Priorytetyzacja

| Priorytet | Znaczenie |
|---|---|
| **P0** | Runner-blocking — bez tego agenci produkują śmieci |
| **P1** | Quality-critical — bez tego jakość jest niska, ale output jest użyteczny |
| **P2** | Consistency — porządkuje, ale nie blokuje pracy |
| **P3** | Nice-to-have — formalizacja istniejącej praktyki |

---

## Mapa konwencji

### Tier 0: Meta (jak tworzyć standardy)

| # | Konwencja | Owner | Status | Prio | Materiał źródłowy |
|---|---|---|---|---|---|
| 1 | **CONVENTION_META** — struktura konwencji | Architect | **active** | -- | `documents/conventions/CONVENTION_META.md` |
| 2 | **CONVENTION_WORKFLOW** — struktura workflow | PE | **active** | -- | `documents/conventions/CONVENTION_WORKFLOW.md` |

### Tier 1: DNA agenta (jak agent myśli i pisze)

| #   | Konwencja                                                                                | Owner     | Status              | Prio | Materiał źródłowy                                                                                                      |
| --- | ---------------------------------------------------------------------------------------- | --------- | ------------------- | ---- | ---------------------------------------------------------------------------------------------------------------------- |
| 3   | **CONVENTION_PROMPT** — pisanie promptów ról, workflow, domain packs                     | PE        | **exists-informal** | P0   | `documents/prompt_engineer/PROMPT_CONVENTION.md` (278 linii, bogata treść, wymaga przeformatowania na CONVENTION_META) |
| 4   | **CONVENTION_CODE** — Python: naming, struktura, error handling, logging, bezpieczeństwo | Architect | **exists-informal** | P0   | `documents/dev/CODE_STANDARDS.md` (88 linii, zbyt ogólnikowy, wymaga rozszerzenia i sformalizowania)                   |
| 5   | **CONVENTION_TESTING** — co testować, jak, coverage, fixtures, nazewnictwo               | Architect | **missing**         | P1   | 40+ testów w `tests/` jako implicit pattern, `conftest.py`                                                             |

### Tier 2: Jak agent pracuje (procesy i komunikacja)

| # | Konwencja | Owner | Status | Prio | Materiał źródłowy |
|---|---|---|---|---|---|
| 6 | **CONVENTION_COMMUNICATION** — format wiadomości agent-agent, sugestie, backlog, handoff | Architect | **implicit** | P0 | Reguły w CLAUDE.md (sekcja agent_bus), ale brak specyfikacji formatu treści wiadomości, severity, priorytetów |
| 7 | **CONVENTION_GIT** — commit message, branch naming, co commitować, kiedy push | Developer | **implicit** | P1 | `git_commit.py` + reguły w CLAUDE.md, ale rozproszone |
| 8 | **CONVENTION_FILE_STRUCTURE** — co gdzie żyje, nazewnictwo katalogów, ścieżki artefaktów | Architect | **implicit** | P1 | Częściowo w CLAUDE.md (documents/human/, tmp/, solutions/), ale niekompletne i niespójne |

### Tier 3: Wiedza domenowa (jak agent rozumie ERP)

| # | Konwencja | Owner | Status | Prio | Materiał źródłowy |
|---|---|---|---|---|---|
| 9 | **CONVENTION_SQL** — styl SQL, nazewnictwo widoków BI, deployment, walidacja | ERP Spec | **exists-informal** | P1 | `ERP_SQL_SYNTAX.md` + `ERP_SCHEMA_PATTERNS.md` (bogate, ale nie w formacie konwencji) |
| 10 | **CONVENTION_ERP_SOLUTIONS** — struktura katalogów solutions/, artefakty per widok, lifecycle | ERP Spec | **implicit** | P2 | Pattern w `solutions/bi/*/` (plan.xlsx, draft.sql, objects.sql, views/*.sql) |

### Tier 4: Tooling i infrastruktura

| # | Konwencja | Owner | Status | Prio | Materiał źródłowy |
|---|---|---|---|---|---|
| 11 | **CONVENTION_TOOL_CLI** — output JSON contract, argument parsing, error format, help text | Developer | **missing** | P2 | 55+ narzędzi w `tools/`, brak unified interface contract |
| 12 | **CONVENTION_DB_SCHEMA** — nazewnictwo tabel mrowisko.db, migracje, backwards compat | Architect | **missing** | P2 | ADR-001 (domain model), ale brak operacyjnej konwencji migracji |
| 13 | **CONVENTION_HOOKS** — pre/post tool use, on_stop, on_user_prompt — co mogą, czego nie | Developer | **missing** | P2 | 4 hooki w `tools/hooks/`, brak specyfikacji |

### Tier 5: Dokumentacja i review

| # | Konwencja | Owner | Status | Prio | Materiał źródłowy |
|---|---|---|---|---|---|
| 14 | **CONVENTION_REVIEW** — code review, prompt review, workflow review — format, severity, flow | Architect | **exists-informal** | P2 | `ARCHITECT.md` (code_maturity_levels, output_contract), ale tylko dla code review |
| 15 | **CONVENTION_RESEARCH** — research prompt structure, result format, evaluation | PE | **exists-informal** | P3 | `PROMPT_CONVENTION.md` sekcja 7, ale minimalna |
| 16 | **CONVENTION_LANGUAGE** — kiedy PL, kiedy EN, co w jakiej warstwie | Architect | **implicit** | P3 | ADR-002 + CLAUDE.md (konwencja językowa), wystarczy sformalizować |

---

## Podsumowanie

| Prio | Ilość | Status |
|---|---|---|
| -- (done) | 2 | active |
| P0 | 3 | exists-informal (2), implicit (1) |
| P1 | 4 | missing (1), implicit (2), exists-informal (1) |
| P2 | 5 | missing (3), implicit (1), exists-informal (1) |
| P3 | 2 | exists-informal (1), implicit (1) |
| **TOTAL** | **16** | 2 active, 14 do zrobienia |

---

## Rekomendowana kolejność realizacji

### Fala 1 — Runner-blocking (P0) — ~3-5 dni

Bez tych trzech runner produkuje śmieci:

| # | Konwencja | Effort | Dlaczego P0 |
|---|---|---|---|
| 3 | CONVENTION_PROMPT | **mały** (reformat istniejącego) | Agenci piszą/modyfikują prompty — muszą wiedzieć jak |
| 4 | CONVENTION_CODE | **średni** (rozszerzenie CODE_STANDARDS) | Agenci piszą Python — muszą znać standard |
| 6 | CONVENTION_COMMUNICATION | **średni** (nowy, ale scope jasny) | Agenci komunikują się — brak formatu = szum i duplikaty (root cause 176 suggestions) |

**CONVENTION_COMMUNICATION jest kluczowa.** To prawdopodobnie największy contributor do eksplozji sugestii — agenci nie wiedzą jak formułować obserwacje, więc każdy pisze po swojemu, duplikuje, nie kategoryzuje. Konwencja komunikacji = mniej szumu = mniej sugestii.

### Fala 2 — Quality-critical (P1) — ~5-7 dni

| # | Konwencja | Effort | Dlaczego P1 |
|---|---|---|---|
| 5 | CONVENTION_TESTING | średni | Zero failing tests to reguła — ale brak specyfikacji co testować |
| 7 | CONVENTION_GIT | mały (formalizacja istniejącego) | Spójność commitów między agentami |
| 8 | CONVENTION_FILE_STRUCTURE | średni | Agenci muszą wiedzieć gdzie kłaść pliki |
| 9 | CONVENTION_SQL | mały (reformat istniejącego) | ERP Specialist i BI view workflow |

### Fala 3 — Consistency (P2-P3) — iteracyjnie

10-16: formalizacja w miarę potrzeb, nie blokerzy.

---

## Obserwacja architektoniczna

**3 z 14 brakujących konwencji to reformat istniejącej treści** (PROMPT, SQL, LANGUAGE).
Nie trzeba pisać od zera — trzeba przeformatować na CONVENTION_META i ewentualnie rozszerzyć.

**CODE_STANDARDS.md (88 linii) jest zbyt ogólnikowy** na konwencję. To guideline, nie standard.
Wymaga rozszerzenia o: concrete examples, antywzorce, edge cases specyficzne dla mrowisko.

**CONVENTION_COMMUNICATION jest jedyną naprawdę nową konwencją w P0.**
To jednocześnie ta, która najbardziej zmniejszy eksplozję sugestii.

---

## Decyzje potrzebne od Dawida

1. Czy mapa jest kompletna? (Czy widzisz aspekt projektu bez konwencji na liście?)
2. Czy priorytetyzacja P0/P1/P2/P3 jest trafna?
3. Czy zgoda na Falę 1 (3 konwencje P0) jako pierwszy krok?
4. Kto pisze co:
   - CONVENTION_PROMPT → PE (reformat swojego dokumentu)?
   - CONVENTION_CODE → Architect (draft) + Developer (review)?
   - CONVENTION_COMMUNICATION → Architect (draft)?
