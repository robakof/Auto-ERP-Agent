# ADR Index — Architecture Decision Records

Rejestr decyzji architektonicznych projektu Mrowisko.

---

## Format ADR

Każda decyzja architektoniczna dokumentowana jako osobny plik `ADR-NNN-<slug>.md`:

- **Status:** Draft → Proposed → Accepted → Deprecated
- **Decydent:** Architect (zatwierdzenie przez użytkownika)
- **Lokalizacja:** `documents/architect/ADR-*.md`

---

## Rejestr

| ID | Tytuł | Status | Data | Wpływ |
|----|-------|--------|------|-------|
| [ADR-001](ADR-001-domain-model.md) | Domain Model (refaktor na klasy) | Proposed | 2026-03-XX | Wysoki — zmiana architektury core/ |
| [ADR-002](ADR-002-language-policy.md) | Polityka językowa PL/EN | Accepted | 2026-03-22 | Średni — konwencja dokumentacji i promptów |
| ADR-003 | Runner architecture | Pending | — | Wysoki — wymaga eksperymentów (#114) |
| ADR-004 | Synchronizacja DB między maszynami | Pending | — | Średni — backlog #90 |
| [ADR-KSEF-001](ADR-KSEF-001-erp-feedback-strategy.md) | KSeF — strategia feedbacku do ERP Comarch XL (shadow DB, czekamy na update Comarch) | Accepted | 2026-04-16 | Średni — zamraża decyzję "zero modyfikacji schematu Comarch" |

---

## Decyzje oczekujące (bez ADR)

| Temat | Bloker | Backlog |
|-------|--------|---------|
| Odpinalność _loom od wykonawczej | Wymaga analizy | — |
| Folder dla człowieka (Obsidian-friendly) | Wymaga decyzji struktury | — |

---

*Utrzymuje: Architect*
