# Research: Powtarzanie słów vs jakość dokumentu — wpływ na LLM

```yaml
research_id: repetition_vs_quality
requested_by: prompt_engineer
date: 2026-03-24
base_prompt: 01 EXPLORATORY_BASE_PROMPT.md
output_path: documents/researcher/research/repetition_vs_quality.md
type: exploratory
```

## Kontekst

Obserwacja z praktyki: dokument napisany zgodnie z konwencją (minimalistycznie) zawiera słowo "minimalizm" raz — a agent "czuje ducha minimalizmu". Czy to działa tak samo jak wielokrotne powtarzanie?

Pytanie fundamentalne: **Jak przekazać agentowi "ducha" dokumentu?**
- Przez jakość i strukturę dokumentu?
- Przez explicit powtarzanie słów kluczowych?
- Kombinacja?

## Obszary do zmapowania

### 1. Powtarzanie słów w promptach — co wiemy?

- Jak powtarzanie słów kluczowych wpływa na attention/focus modelu?
- Czy "IMPORTANT: X" powtórzone 3x działa lepiej niż 1x?
- Czy jest punkt nasycenia (diminishing returns)?
- Czy powtarzanie może być szkodliwe (noise, confusion)?

### 2. Jakość dokumentu vs explicit instructions

- Czy dobrze napisany dokument (spójny, minimalistyczny) "przenosi ducha" bez explicit powtórzeń?
- Czy model wyłapuje implicit wzorce (styl, ton, strukturę)?
- Przykład: dokument w stylu minimalistycznym vs dokument mówiący "bądź minimalistyczny" 10 razy

### 3. Show vs Tell w kontekście LLM

- "Show don't tell" — czy działa dla promptów?
- Czy przykład dobrego outputu działa lepiej niż instrukcja?
- Jak to się ma do few-shot prompting?

### 4. Attention mechanisms i salience

- Jak modele przydzielają attention?
- Czy powtórzenie zwiększa salience (wyrazistość)?
- Czy struktura (nagłówki, bold) wpływa na attention?
- Pozycja w dokumencie (początek vs koniec vs środek)

### 5. Prompt engineering best practices

- Co mówią źródła (Anthropic, OpenAI) o powtarzaniu?
- Czy są badania porównujące powtarzanie vs jakość?
- Praktyczne heurystyki z community

### 6. Emerging patterns

- Jakie nowe podejścia pojawiają się w prompt engineering?
- "Vibe-based prompting" — czy to realne?
- Czy model może "wyczuć intencję" z kontekstu?

## Search hints

- "LLM prompt repetition effect"
- "prompt engineering word repetition"
- "attention mechanism keyword salience"
- "show vs tell prompting"
- "implicit vs explicit instructions LLM"
- "prompt quality vs verbosity"
- "Anthropic prompt best practices repetition"
- "few-shot vs instruction following"

## Output contract

**Lokalizacja:** `documents/researcher/research/repetition_vs_quality.md`

**Struktura (eksploracyjna):**
1. **Mapa terenu** — co wiemy, co nie wiemy, gdzie są luki
2. **Hipotezy** — możliwe odpowiedzi (z siłą dowodów)
3. **Wzorce z praktyki** — co robią inni (examples)
4. **Otwarte pytania** — co wymaga eksperymentów
5. **Rekomendacje wstępne** — co można próbować

**Uwaga:** To jest teren słabo udokumentowany. Oczekuję więcej hipotez niż twardych faktów. Mapuj niepewność.
