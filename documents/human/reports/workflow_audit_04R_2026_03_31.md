# Workflow Audit: Strict Format (04R) — 2026-03-31

## Wyniki auditu

**Przed konwersja:** 16/16 workflow w formacie 05R (human-readable). Zero 04R strict.

| # | Workflow | Format przed | Format po | Wersja |
|---|---------|-------------|----------|--------|
| 1 | suggestions_processing | 05R | **04R** | 3.0 → 4.0 |
| 2 | convention_creation | 05R | **04R** | 1.4 → 2.0 |
| 3 | code_review | 05R | **04R** | 1.0 → 2.0 |
| 4 | plan_review | 05R | 05R | 1.0 |
| 5 | bi_view_creation | 05R | 05R | 3.1 |
| 6 | research_prompt_creation | 05R | 05R | 1.0 |
| 7 | prompt_refactor | 05R | 05R | 1.1 |
| 8 | dispatcher | 05R | 05R | 1.0 |
| 9 | exploration | 05R | 05R | 1.0 |
| 10 | developer_tool | 05R | 05R | 1.0 |
| 11 | developer_bugfix | 05R | 05R | 1.0 |
| 12 | developer_patch | 05R | 05R | 1.0 |
| 13 | developer_suggestions | 05R | 05R | 1.0 |
| 14 | prompt_patch | 05R | 05R | 1.0 |
| 15 | workflow_creation | 05R | 05R | 1.2 |
| 16 | session_end | 05R | 05R | 1.0 |

## Konwersja top 3

Skonwertowane 3 workflow do formatu strict 04R (DB-ready):

### 1. suggestions_processing (v4.0)
- 17 stepow z pelnym step_id/action/tool/command/verification/on_failure/next_step
- 2 decision points (check_next_group, check_ratio)
- 3 HANDOFF_POINT (human_approve_groups, human_review_proposals, escalate_ratio)
- 5 exit gates z item_id
- Petla (loop) reprezentowana przez Decision Point

### 2. convention_creation (v2.0)
- 19 stepow z pelnym formatem strict
- 1 decision point (check_domain)
- 3 HANDOFF_POINT (send_to_pe, receive_research_prompt, human_approve_convention)
- 7 exit gates z item_id
- Petla research reprezentowana przez next_step → define_research_questions

### 3. code_review (v2.0)
- 13 stepow z pelnym formatem strict
- 2 decision points (review_assessment, re_review_assessment)
- 3 HANDOFF_POINT (send_review_request, send_needs_revision, send_pass)
- Faza 3c (BLOCKED) wyodrebniona jako osobna sciezka
- related_docs zaktualizowane (workflow_developer → rozbite pliki)

## Task 0.3: Rozbicie workflow_developer.md

Status: **juz zrobione** (przed ta sesja). Plik workflow_developer.md nie istnieje.
Istnieja 4 osobne pliki:
- workflow_developer_tool.md
- workflow_developer_bugfix.md
- workflow_developer_patch.md
- workflow_developer_suggestions.md

## Exit gate planu

- [x] >= 3 workflow w formacie strict (04R) z step_id, verification, next_step
- [x] workflow_developer.md rozbity na >= 2 osobne pliki
