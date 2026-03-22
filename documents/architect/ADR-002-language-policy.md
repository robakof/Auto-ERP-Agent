# ADR-002: Polityka językowa PL/EN

**Status:** Accepted
**Data:** 2026-03-22
**Decydent:** Architect
**Kontekst:** Analiza PE (#180), research `research_results_language_impact.md`

---

## Kontekst

System Mrowisko używa mieszanki języka polskiego i angielskiego. Brak formalnej konwencji prowadził do pytań:
- Czy migrować na pełne EN (optymalizacja tokenów)?
- Czy obecna hybryda jest wystarczająco konsekwentna?
- Jak sformalizować podział?

## Decyzja

**Zachowujemy hybrydę PL/EN z formalną konwencją podziału.**

### Konwencja warstw

| Warstwa | Język | Przykłady |
|---------|-------|-----------|
| **Techniczna** | 100% EN | Kod Python, schemat DB, CLI params, JSON keys, komunikaty błędów |
| **Sterowania** | Struktura EN, treść PL | Prompty agentów: tagi XML (`<mission>`) EN, instrukcje PL |
| **Komunikacji** | Struktura EN, treść PL | Messages/suggestions: pola EN (`title`, `status`), wartości PL |
| **Strategiczna** | 100% PL | Workflow, ADR, SPIRIT.md, dokumentacja dla użytkownika |

### Szczegóły

**Warstwa techniczna (100% EN):**
- Nazwy zmiennych, funkcji, klas, docstringi
- Tabele i kolumny w DB (`suggestions`, `backlog`, `created_at`)
- Wartości enum statusów (`open`, `done`, `in_progress`)
- Parametry CLI (`--role`, `--status`)
- Klucze JSON

**Warstwa sterowania (struktura EN, treść PL):**
- Tagi XML w promptach: `<mission>`, `<scope>`, `<critical_rules>`
- Metadane YAML: klucze EN (`agent_id`, `allowed_tools`)
- Treść instrukcji: PL ("Eskaluj gdy nie masz pewności...")

**Warstwa komunikacji (struktura EN, treść PL):**
- Pola wiadomości: EN (`sender`, `recipient`, `content`)
- Tytuły i treść: PL ("Refaktor render.py zakończony")
- Typy: EN (`observation`, `rule`, `discovery`)

**Warstwa strategiczna (100% PL):**
- Workflow dokumenty
- ADR (ten dokument)
- SPIRIT.md, METHODOLOGY.md
- Plany, raporty, analizy

## Uzasadnienie

1. **Transparentność > optymalizacja** — użytkownik nie zna EN wystarczająco do debugowania promptów samodzielnie
2. **SPIRIT.md** — wiedza musi być dostępna, system budowany jako "dom" dla właściciela
3. **Budżet tokenowy ~10%** — brak presji kosztowej
4. **Różnica jakości PL vs EN** — niewielka dla high-resource language (~2-4% wg research)
5. **Zero kosztów migracji** — obecna hybryda już działa

## Konsekwencje

**Pozytywne:**
- Użytkownik może czytać i edytować prompty bez pomocy
- Brak ryzyka regresji z tłumaczenia
- Spójna konwencja do egzekwowania

**Negatywne:**
- Wyższe zużycie tokenów niż pełne EN (szacunkowo +10-20%)
- Przy współpracy z anglojęzycznym zespołem — bariera

## Kiedy ponownie rozważyć

- Budżet tokenowy regularnie >70%
- Współpraca z anglojęzycznym zespołem
- Long-context staje się wąskim gardłem (intensywny multi-agent)

## Powiązane

- Research: `documents/prompt_engineer/research_results_language_impact.md`
- Wiadomość PE: inbox #180
- Odpowiedź: `tmp/msg_pe_language_decision.md`

---

*Dokument: ADR-002*
*Lokalizacja: documents/architect/ADR-002-language-policy.md*
