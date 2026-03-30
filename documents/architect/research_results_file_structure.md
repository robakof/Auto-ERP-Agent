# Research: File Structure Convention Patterns

**Data:** 2026-03-30
**Metoda:** 2 sub-agenty (monorepo patterns, file ownership)

## Wnioski

### Potwierdzone (draft ok)
- Per-role directory ownership to wlasciwy model (nie per-user — agenci nie maja kont GitHub)
- Hybrid approach (per-team + shared) skaluje najlepiej przy 10+ zespolach
- tmp/ jako single scratch directory z .gitignore — standard
- Hook-based enforcement > convention-only (juz mamy w pre_tool_use.py)

### Do dodania w draft
- **Automated tmp/ cleanup** — research potwierdza brak TTL jako gap
- **Policy Engine jako enforcement** — CODEOWNERS zbedny, Policy Engine lepszy
- **Mrowisko jest pionerem** — brak standardowych multi-agent filesystem conventions

### Zrodla
- Monorepo: nx, turborepo, bazel patterns, Google/Uber/Airbnb
- Ownership: CODEOWNERS, CI gates, pre-commit hooks
- Multi-agent: AutoGPT, CrewAI, MetaGPT — brak conventions (my jesteśmy pierwsi)
