# Prompt badawczy: wzorce komunikacji i pamięci w systemach wieloagentowych

**Dla:** Researcher / Web Search Agent
**Zlecający:** Metodolog (sesja 2026-03-12)
**Cel:** Zebrać wzorce architektoniczne klasy "shared cognitive space" — alternatywy dla
message-passing między agentami LLM. Nie szukamy tutoriali ani przewodników — szukamy
nazw, wzorców i trade-offów.

---

## Kontekst

Projektujemy architekturę komunikacji dla systemu wieloagentowego (agenci LLM).
Zidentyfikowaliśmy trzy warstwy:
1. Dyrektywy — stabilne wytyczne per rola
2. Wiadomości — kierowana komunikacja punkt-punkt
3. Myśli — wspólna pamięć tematyczna (tagowana, bez adresata)

Warstwa 3 to "telepathy pattern": agent zapisuje myśl do wspólnej przestrzeni z tagami,
inny agent odpytuje przestrzeń po temacie. Żadnego explicite "wyślij do X".

Chcemy wiedzieć: jakie inne wzorce tej klasy istnieją, jak zostały nazwane, jakie są
ich trade-offy i gdzie są stosowane w praktyce.

---

## Pytania badawcze

### 1. Wzorce architektoniczne — identyfikacja i nazwy

Zbadaj następujące kierunki i dla każdego ustal: co to jest, skąd pochodzi, gdzie stosowane,
jakie trade-offy:

- **Blackboard architecture** (klasyczny AI, lata 80.) — czy jest stosowana w systemach LLM?
  Jakie są nowoczesne implementacje?
- **Tuple space / Linda paradigm** (Gelernter, 1985) — czy jest stosowana w multi-agent LLM?
- **Stigmergy** (z badań nad mrówkami i rojem) — pośrednia komunikacja przez środowisko,
  nie przez wiadomości. Czy ma zastosowanie w systemach AI?
- **Global Workspace Theory** (Baars) — teoria świadomości jako "broadcast medium";
  czy ktoś implementuje to w multi-agent systems?
- **Publish-subscribe vs shared memory** — jakie są praktyczne różnice w systemach agentowych?

### 2. Implementacje w nowoczesnych frameworkach LLM

Jak rozwiązują problem wspólnej pamięci i komunikacji:

- **LangGraph** — jak zarządza stanem współdzielonym między agentami?
- **AutoGen (Microsoft)** — model komunikacji; czy jest coś poza message passing?
- **CrewAI** — jak agenci dzielą się wiedzą?
- **Swarm (OpenAI)** — skąd nazwa, co oznacza architektonicznie?
- **mem0, Letta (MemGPT)** — systemy pamięci dla agentów; jakie typy pamięci wyróżniają?

### 3. Pamięć agentów — taksonomia

Jaka jest standardowa taksonomia typów pamięci agenta LLM?
Szukamy czegoś w stylu: episodic / semantic / procedural / working — ale dla LLM agentów.
Czy istnieje konsensus? Gdzie jest opisana?

### 4. Semantic search jako wspólna pamięć

Wzorzec: agenci zapisują "myśli" jako embeddingi do vector store, inni agenci odpytują
semantycznie. Czy ktoś to opisuje jako wzorzec architektoniczny? Jakie frameworki to implementują?
Jakie są ograniczenia (halucynacje retrieval, stale embeddings, koszt)?

### 5. Stigmergy w AI — czy ktoś to próbuje?

Stigmergy = mrówka zostawia feromon, inna mrówka go czyta i modyfikuje zachowanie.
Środowisko jest nośnikiem komunikacji, nie wiadomości.
Czy istnieją implementacje tego wzorca dla LLM agentów? Jakie wyniki?

---

## Format odpowiedzi

Dla każdego wzorca / frameworka:

```
### Nazwa wzorca

**Źródło:** (paper, framework, autor)
**Krótki opis:** (2-3 zdania — co to jest)
**Gdzie stosowane:** (konkretne systemy, frameworki)
**Trade-offy:**
  ✓ zalety
  ✗ wady / ograniczenia
**Związek z naszą architekturą:** (jak się ma do warstwy myśli / shared memory)
**Linki / źródła:** (konkretne URL lub paper)
```

---

## Plik odpowiedzi

Zapisz wyniki badania do pliku: `documents/methodology/research_results_swarm_communication.md`
Stwórz plik od razu na starcie i dopisuj do niego w miarę postępu badania.

---

## Czego NIE szukamy

- Tutoriali "jak zbudować agenta LLM"
- Porównań modeli (GPT vs Claude vs Gemini)
- Ogólnych opisów czym jest AI
- Marketingowych opisów frameworków bez konkretów technicznych

---

## Priorytet

1. Blackboard + Tuple space — klasyczne wzorce, czy mają nowoczesne implementacje LLM
2. Taksonomia pamięci agenta — szukamy standardu lub konsensusu
3. LangGraph / AutoGen / CrewAI — konkretnie jak rozwiązują shared memory
4. Stigmergy — ciekawostka badawcza, niski priorytet jeśli brak implementacji LLM
