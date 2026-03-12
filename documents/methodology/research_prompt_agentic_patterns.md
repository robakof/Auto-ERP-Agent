# Prompt badawczy: wzorce architektoniczne systemów agentowych

**Dla:** Researcher / Web Search Agent
**Zlecający:** Metodolog (sesja 2026-03-12)
**Cel:** Zebrać katalog wzorców architektonicznych dla systemów wieloagentowych LLM —
nazwy, opisy, trade-offy, źródła. Nie tutoriale — wzorce i ich konsekwencje.

---

## Kontekst

Budujemy system agentów LLM do autonomicznej konfiguracji systemu ERP. Mamy działające
role (ERP Specialist, Analityk, Developer, Metodolog) z hierarchią eskalacji i refleksji.
Projektujemy warstwę komunikacji i pamięci wspólnej (osobny prompt badawczy).

Teraz chcemy szerszego obrazu: jakie wzorce architektoniczne opisują budowę systemów
agentowych jako całości — nie tylko komunikację, ale orchestrację, dekompozycję zadań,
kontrolę błędów, nadzór człowieka, ewaluację.

---

## Obszary badania

### 1. Wzorce orchestracji

Jak decyduje się które agenty działają, w jakiej kolejności, z jakim kontekstem:

- **Single orchestrator** — jeden agent koordynuje resztę. Wady, gdzie się sypie?
- **Hierarchical orchestration** — drzewo orchestratorów. Jak głębokość wpływa na błędy?
- **Emergent orchestration** — agenci sami negocjują kto co robi. Czy to działa w praktyce?
- **Event-driven** — agenci reagują na zdarzenia, nie na rozkazy. Jakie implementacje?
- Czy istnieje katalog / taksonomia wzorców orchestracji dla LLM? Gdzie?

### 2. Wzorce dekompozycji zadań

Jak duże zadanie rozbijane jest na kawałki dla agentów:

- **Plan-then-execute** — agent planuje, inne wykonują. Jakie frameworki to implementują?
- **ReAct** (Reason + Act) — agent myśli i działa przemiennie. Ograniczenia przy wieloagentowości?
- **Tree of Thoughts** — eksploatacja drzewa możliwości. Czy skaluje się na wielu agentów?
- **Speculative execution** — równoległa praca na alternatywnych planach, wygrany plan wygrywa.
  Kto to robi? Jakie koszty?
- Inne wzorce dekompozycji wartę uwagi?

### 3. Wzorce nadzoru i kontroli błędów

Jak system radzi sobie z błędami, halucynacjami, dryfem:

- **Human-in-the-loop** — gdzie i jak wbudować zatwierdzenia człowieka bez blokowania systemu?
  Jakie są praktyki (approval queues, confidence thresholds)?
- **Self-critique / reflection** — agent ocenia własny output przed oddaniem. Czy to działa?
  Koszt vs jakość?
- **Critic agent** — osobny agent oceniający output innego. Wzorzec Red Team / Blue Team w LLM?
- **Guardrails** — co to jest jako wzorzec architektoniczny (nie marketing)? Jak implementowane?
- **Rollback i checkpoints** — jak cofać stan systemu gdy agent popełni błąd?
  Czy istnieją wzorce do tego?

### 4. Wzorce granicy autonomii

Gdzie i jak agent powinien się zatrzymać i zapytać człowieka:

- Jakie są wzorce klasyfikacji decyzji (autonomiczna vs eskalowana)?
- **Confidence-based escalation** — agent eskaluje gdy niepewność przekracza próg.
  Jak mierzyć pewność w LLM? Czy to działa?
- **Blast radius assessment** — agent ocenia odwracalność akcji przed wykonaniem.
  Czy ktoś to formalnie opisuje?
- Jakie są praktyczne heurystyki gdzie kończy się autonomia, a zaczyna eskalacja?

### 5. Wzorce ewaluacji systemu agentowego

Jak mierzyć czy system agentowy działa dobrze:

- Jakie metryki stosuje się dla systemów wieloagentowych (nie pojedynczego LLM)?
- **Trajectory evaluation** — ocena ścieżki decyzji, nie tylko wyniku końcowego. Gdzie stosowane?
- Jak ewaluować agenta który działa długoterminowo (wiele sesji, zmieniający się kontekst)?
- Jakie narzędzia ewaluacyjne istnieją dla multi-agent LLM?

### 6. Wzorce bootstrapu i inicjalizacji roli

Jak agent wie kim jest i co ma robić na starcie sesji:

- Jakie są wzorce "system prompt composition" dla wielu ról?
- **Role injection vs role inheritance** — czy istnieje opisany wzorzec?
- Jak frameworki rozwiązują problem "agent musi wiedzieć jak dostać swoje instrukcje
  zanim dostanie swoje instrukcje" (bootstrap paradox)?
- Jakie są praktyki zarządzania wersjami promptów / instrukcji agenta?

### 7. Wzorce przy długoterminowej pracy agenta

Specyfika systemów które działają przez wiele sesji / dni / tygodni:

- Jak zarządzać dryfem kontekstu (agent w sesji 100 ma inne założenia niż w sesji 1)?
- **Periodic alignment** — regularne sesje kalibracyjne z człowiekiem. Czy ktoś to opisuje?
- Jak wykrywać że agent "się zgubił" i potrzebuje resetu kontekstu?
- Wzorce zarządzania długoterminową pamięcią bez przeciążenia kontekstu?

---

## Źródła do przeszukania

- Anthropic documentation (agent patterns, tool use best practices)
- Papers: "Agents" survey papers 2024-2025 (AgentBench, AgentEval, podobne)
- LangGraph documentation — wzorce orchestracji
- AutoGen (Microsoft) — wzorce multi-agent
- Crew AI — wzorce ról i delegacji
- Google "Agents" whitepaper (jeśli istnieje)
- Arxiv: multi-agent LLM architecture patterns 2024-2025
- Blog inżynierski: Anthropic, OpenAI, DeepMind — posty o wzorcach, nie produktach

---

## Format odpowiedzi

Dla każdego wzorca:

```
### Nazwa wzorca

**Kategoria:** orchestracja | dekompozycja | kontrola błędów | autonomia | ewaluacja | bootstrap | długoterminowość
**Źródło:** (paper, dokumentacja, autor, framework)
**Krótki opis:** (2-3 zdania)
**Gdzie stosowane w praktyce:** (konkretne systemy / frameworki)
**Trade-offy:**
  ✓ zalety
  ✗ wady / ograniczenia / kiedy nie stosować
**Relevancja dla naszego systemu:** (wysoka / średnia / niska + 1 zdanie dlaczego)
**Link / źródło:**
```

Na końcu: lista wzorców których NIE znalazłeś ale które były pytane — żebyśmy wiedzieli
co wymaga głębszego badania.

---

## Plik odpowiedzi

Zapisz wyniki badania do pliku: `documents/methodology/research_results_agentic_patterns.md`
Stwórz plik od razu na starcie i dopisuj do niego w miarę postępu badania.

---

## Czego NIE szukamy

- Opisów produktów AI (Copilot, Claude, ChatGPT jako produkty)
- Tutoriali budowy agenta krok po kroku
- Porównań modeli bazowych
- Marketingowych opisów bez konkretów architektonicznych
