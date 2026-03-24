# Research: Mrowisko Runner — weryfikacja podejścia

## Kontekst

Budujemy system multi-agent oparty na Claude Code CLI (nie SDK). Agenci działają jako
osobne sesje CLI, komunikują się przez bazę SQLite (inbox/send). Chcemy zbudować
runner który automatycznie wywołuje agentów jako subprocess i stopniowo zwiększa
ich autonomię.

Proponowane wywołanie:
```bash
claude --print --output-format text < tmp/runner_prompt.md
```

## Pytania do zbadania

### 1. Claude Code CLI — subprocess invocation

- Czy `claude --print < plik` poprawnie inicjalizuje projekt (CLAUDE.md, hooks)?
- Czy subprocess otrzymuje dostęp do ustawień projektu (`.claude/settings.json`)?
- Czy istnieje flaga `--session-id` lub `--parent-session` do śledzenia łańcuchów wywołań?
- Czy `--output-format text` vs `--output-format json` — który daje lepszy live streaming?
- Czy jest mechanizm `--max-turns` lub `--budget-tokens` do ograniczenia kosztów?

### 2. Live streaming output

- Czy subprocess Popen z Claude Code CLI streamuje output line-by-line czy buforuje?
- Czy istnieje flaga która wymusza unbuffered output?

### 3. Multi-agent orchestration best practices

- Jakie są znane pułapki przy orchestracji agentów przez subprocess?
- Jak inne projekty rozwiązują problem pętli wywołań (A→B→A)?
- Czy są lepsze wzorce niż plik tymczasowy do przekazania kontekstu agentowi?
- Jak zarządzać równoległymi wywołaniami (jeśli dojdziemy do tego etapu)?

### 4. Bezpieczeństwo i kontrola

- Jak ograniczyć co agent może zrobić w subprocess (uprawnienia, scope)?
- Czy Claude Code ma wbudowany mechanizm `--allow-tools` do whitelistowania narzędzi?
- Jak wykrywać i przerywać runaway agents (nieskończona pętla, nadmierne koszty)?

### 5. Alternatywy do rozważenia

- Czy Anthropic Agent SDK jest lepszym wyborem niż CLI subprocess dla tego przypadku?
  (zależy nam na: live output w terminalu, reużycie konfiguracji projektu, prostota)
- Czy istnieją gotowe orchestration frameworks (LangGraph, CrewAI) warte rozważenia
  vs własna implementacja?

## Oczekiwany wynik

Plik `research_results_mrowisko_runner.md` z:
1. Odpowiedziami na powyższe pytania (z linkami do dokumentacji)
2. Listą pułapek których powinniśmy unikać
3. Rekomendacją: czy proponowane podejście (CLI subprocess) jest właściwe,
   czy jest coś co nam umyka
