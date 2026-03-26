# Rewizja dokumentów vs konwencje

Data: 2026-03-26
Autor: Prompt Engineer

Konwencje powstały 24-25.03.2026. Dokumenty poniżej nie były aktualizowane pod kątem
zgodności z konwencjami (CONVENTION_META, CONVENTION_WORKFLOW, CONVENTION_PROMPT, CONVENTION_PYTHON).

---

## Legenda

- **Last update** — data ostatniej zmiany w git
- **Konwencja** — która konwencja dotyczy tego dokumentu
- **Gap** — co potencjalnie nie jest zgodne

---

## Prompty ról — kandydaci do rewizji

| # | Dokument | Last update | Dotyczy konwencji | Gap |
|---|---|---|---|---|
| 1 | `documents/erp_specialist/ERP_SPECIALIST.md` | 26.03 (audit) | CONVENTION_PROMPT | Audit dodał narzędzia, ale struktura promptu nie była weryfikowana vs CONVENTION_PROMPT |
| 2 | `documents/analyst/ANALYST.md` | 26.03 (tests) | CONVENTION_PROMPT | Zmiana kosmetyczna (tests), struktura nie weryfikowana |
| 3 | `documents/methodology/METHODOLOGY.md` | 26.03 (tests) | CONVENTION_PROMPT | j.w. |
| 4 | `documents/methodology/SPIRIT.md` | 21.03 | — | Dokument strategiczny, nie prompt — konwencje go nie dotyczą |

**Uwaga:** DEVELOPER.md, ARCHITECT.md, PROMPT_ENGINEER.md — aktualizowane 25-26.03 w kontekście konwencji. Mogą wymagać drobnej rewizji ale były świadomie edytowane.

---

## Dokumenty domenowe ERP — kandydaci do rewizji

| # | Dokument | Last update | Dotyczy konwencji | Gap |
|---|---|---|---|---|
| 5 | `documents/erp_specialist/ERP_COLUMNS_WORKFLOW.md` | 11.03 | CONVENTION_WORKFLOW | Stary format — brak YAML header, brak outline, brak strict steps |
| 6 | `documents/erp_specialist/ERP_FILTERS_WORKFLOW.md` | 11.03 | CONVENTION_WORKFLOW | j.w. |
| 7 | `documents/erp_specialist/ERP_SCHEMA_PATTERNS.md` | 24.03 | — | Domain pack, nie workflow/prompt — konwencja nie wymaga zmian |
| 8 | `documents/erp_specialist/ERP_SQL_SYNTAX.md` | 11.03 | — | Domain pack, nie workflow/prompt |
| 9 | `documents/erp_specialist/PROMPT_ERP_SQL_REPORT.md` | 16.03 | CONVENTION_PROMPT | Prompt dla raportu SQL — nie weryfikowany vs CONVENTION_PROMPT |
| 10 | `documents/analyst/analyst_start.md` | 15.03 | — | Stary plik startowy — sprawdzić czy nadal potrzebny |

---

## Workflow — kandydaci do rewizji

| # | Dokument | Last update | Dotyczy konwencji | Gap |
|---|---|---|---|---|
| 11 | `workflows/workflow_bi_view_creation.md` | 24.03 | CONVENTION_WORKFLOW | Refaktor v3.0 z 24.03 — ale CONVENTION_WORKFLOW v1.0 też z 24.03. Sprawdzić zgodność |
| 12 | `workflows/workflow_prompt_refactor.md` | 25.03 | CONVENTION_WORKFLOW | Utworzony 25.03 — powinien być zgodny, ale brak jawnej weryfikacji |
| 13 | `workflows/workflow_workflow_creation.md` | 24.03 | CONVENTION_WORKFLOW | Utworzony 24.03 pre-convention — prawdopodobnie niezgodny |

**Workflow OK (tworzone/aktualizowane PO konwencjach):**
- workflow_developer.md (26.03)
- workflow_plan_review.md (25.03)
- workflow_code_review.md (25.03)
- workflow_convention_creation.md (25.03)
- workflow_suggestions_processing.md (25.03)
- workflow_research_prompt_creation.md (25.03)

---

## Inne dokumenty

| # | Dokument | Last update | Dotyczy konwencji | Gap |
|---|---|---|---|---|
| 14 | `documents/prompt_engineer/PROMPT_CONVENTION.md` | 25.03 | CONVENTION_META | Starszy format — sprawdzić czy CONVENTION_META go subsumuje |

---

## Priorytetyzacja

### Wysoki priorytet (stare, niezgodne z konwencjami)

| # | Dokument | Problem | Effort |
|---|---|---|---|
| **5** | ERP_COLUMNS_WORKFLOW.md | Brak YAML header, outline, strict steps. Format sprzed konwencji | średni |
| **6** | ERP_FILTERS_WORKFLOW.md | j.w. | średni |
| **13** | workflow_workflow_creation.md | Pre-convention, prawdopodobnie niezgodny format | mały |

### Średni priorytet (wymagają weryfikacji)

| # | Dokument | Problem | Effort |
|---|---|---|---|
| **1** | ERP_SPECIALIST.md | Struktura promptu vs CONVENTION_PROMPT — nie weryfikowana | średni |
| **2** | ANALYST.md | j.w. | średni |
| **3** | METHODOLOGY.md | j.w. | średni |
| **9** | PROMPT_ERP_SQL_REPORT.md | Prompt vs CONVENTION_PROMPT | mały |
| **11** | workflow_bi_view_creation.md | Zgodność z CONVENTION_WORKFLOW v1.4 | mały |
| **12** | workflow_prompt_refactor.md | Weryfikacja zgodności | mały |
| **14** | PROMPT_CONVENTION.md | Czy CONVENTION_META go subsumuje? | mały |

### Niski priorytet / do oceny

| # | Dokument | Problem |
|---|---|---|
| **10** | analyst_start.md | Czy nadal potrzebny? session_init zastąpił? |
| **7,8** | ERP_SCHEMA_PATTERNS, ERP_SQL_SYNTAX | Domain packs — konwencje ich nie dotyczą, chyba że chcemy CONVENTION_DOMAIN_PACK |
