# Research: Kolejność schematu przy ekstrakcji informacji

---
research_id: extraction_order
requested_by: prompt_engineer
output_path: documents/researcher/research/research_results_extraction_order.md
base_prompt: documents/researcher/prompts/base_prompt_rigorous.md
---

## Mission

Zbadaj jak kolejność (schemat przed vs po) wpływa na jakość ekstrakcji informacji przez LLM.

**Kontekst:** PE tworzy workflow na podstawie konwersacji agenta. Dwa podejścia:
1. **Schema-first:** Przeczytaj CONVENTION_WORKFLOW → ekstrakcja (wiesz czego szukać)
2. **Data-first:** Ekstrakcja surowa → przeczytaj CONVENTION → formatowanie

## Research Questions

### 1. Confirmation bias w ekstrakcji

**Pytania:**
- Czy znajomość schematu przed ekstrakcją powoduje pomijanie informacji spoza schematu?
- Czy istnieją badania o "schema-induced blindness" w LLM?
- Jak anchoring effect wpływa na ekstrakcję?

**Expected output:**
- Dowody za/przeciw confirmation bias przy schema-first
- Badania o selective attention w LLM

### 2. Over-extraction bez schematu

**Pytania:**
- Czy brak schematu prowadzi do ekstrakcji nieistotnych informacji?
- Jak LLM radzi sobie z filtrowaniem bez kryteriów?
- Czy post-hoc filtering jest skuteczny?

**Expected output:**
- Porównanie precision/recall obu podejść
- Strategie post-hoc filtering

### 3. Praktyki w information extraction

**Pytania:**
- Jakie podejście stosują pipeline'y NLP/IE?
- Czy schema-guided extraction jest standardem?
- Jakie są best practices w document understanding?

**Expected output:**
- Przegląd podejść w branży
- Rekomendacje z praktyki

### 4. Hybrid approaches

**Pytania:**
- Czy istnieją podejścia łączące oba?
- Two-pass extraction (surowa → schema-guided)?
- Jakie trade-offy?

**Expected output:**
- Hybrid strategies
- Kiedy który approach

## Output Contract

**Struktura wyników:**

```markdown
# Research Results: Extraction Order

## TL;DR (3-5 findings)

## Per Question

### Q1: Confirmation bias
**Finding:** ...
**Evidence strength:** Strong | Medium | Weak
**Sources:** ...

[...]

## Recommendation for PE workflow

## Open Questions
```

**Zakaz:** Nie oceniaj dopasowania do Mrowiska — to osobny krok.

## Search Hints

**Phase 1 (official):**
- "schema-guided information extraction"
- "confirmation bias LLM extraction"
- "document understanding pipeline order"

**Phase 2 (community):**
- "prompt engineering extraction order"
- "LLM structured output best practices"
