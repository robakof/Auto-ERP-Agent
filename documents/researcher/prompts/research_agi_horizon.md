# Prompt badawczy: horyzont AGI i gotowość infrastrukturalna

**Dla:** Researcher / Web Search Agent
**Zlecający:** Metodolog (sesja 2026-03-12)
**Cel:** Zbudować realistyczny obraz horyzontu AGI (~2 lata) z uwzględnieniem czynników
geopolitycznych (eskalacja konfliktu globalnego) i odpowiedzieć na pytanie: co oznacza
"być gotowym" dla małej firmy budującej infrastrukturę agentową.

---

## Kontekst

CEO firmy produkcyjnej buduje system wieloagentowy do autonomicznego prowadzenia
działalności biznesowej (ERP, konfiguracja, analiza danych, raportowanie). Teza robocza:
AGI pojawi się w ciągu ~2 lat. Wartość nie będzie w modelu (każdy go będzie miał) --
będzie w infrastrukturze organizacyjnej: kto potrafi skoordynować rój agentów AI,
ten wygrywa w swojej branży.

Dodatkowy czynnik: rosnące ryzyko konfliktu globalnego (scenariusz WW3). To nie jest
temat poboczny -- wpływa bezpośrednio na dostępność infrastruktury chmurowej,
łańcuchy dostaw chipów, regulacje AI i tempo rozwoju.

---

## Pytania badawcze

### 1. Trajektoria do AGI -- stan obecny (marzec 2026)

- Jaki jest aktualny konsensus (lub brak konsensusu) wśród badaczy AI co do horyzontu AGI?
- Kluczowe kamienie milowe osiągnięte w 2025-2026 które przybliżają AGI.
- Jakie są główne definicje AGI używane w branży? (DeepMind levels, Anthropic RSP levels, inne)
- Czy istnieją publiczne prognozy z datami od: Anthropic, OpenAI, DeepMind, Meta AI?
- Forecasting: Metaculus, Manifold Markets -- aktualne szacunki prawdopodobieństwa AGI do 2028.

### 2. Czynniki przyspieszające

- **Scaling laws** -- czy nadal działają? Jakie są sygnały wyczerpywania vs kontynuacji?
- **Inference-time compute** -- o1/o3/Claude thinking jako nowy wymiar skalowania.
  Co to oznacza dla trajektorii AGI?
- **Agent frameworks** -- czy pojawienie się dojrzałych frameworków agentowych
  (LangGraph, AutoGen, Claude Code, Devin) jest sygnałem że infrastruktura
  dogania możliwości modeli?
- **Otwarcie modeli** -- Llama, Mistral, DeepSeek. Jak open-source wpływa na tempo?
- **Synthetic data i self-play** -- czy modele trenujące się na własnych outputach
  przyspieszają czy spowalniają postęp?

### 3. Czynniki spowalniające i ryzyka

- **Geopolityka i chipy** -- TSMC, sankcje na Chiny, zależność od Tajwanu.
  Co się dzieje z AI gdy Tajwan jest zagrożony?
- **Scenariusz WW3** -- jakie są realistyczne scenariusze eskalacji globalnej
  w horyzoncie 2026-2028? Jak każdy z nich wpływa na:
  - Dostępność GPU/TPU i chmury obliczeniowej
  - Regulacje AI (militaryzacja vs ograniczenia)
  - Łańcuchy dostaw hardware
  - Priorytetyzację zasobów obliczeniowych (wojsko vs cywile)
  - Dostępność talentów AI (mobilizacja, emigracja, relokacja labów)
- **Regulacje** -- EU AI Act, US executive orders, chińskie regulacje.
  Jakie regulacje mogą realnie spowolnić deployment AGI?
- **Alignment i safety** -- czy obawy o bezpieczeństwo mogą spowodować
  dobrowolne lub wymuszone moratorium? Jakie są scenariusze?
- **Energia** -- czy zapotrzebowanie energetyczne data centers jest realnym
  ograniczeniem w horyzoncie 2 lat?

### 4. Co oznacza "być gotowym" -- infrastruktura

Dla małej firmy (1-10 osób) budującej infrastrukturę agentową:

- **Jakie elementy infrastruktury są trwałe** -- przeżyją zmianę modelu bazowego?
  (np. protokoły komunikacji, architektura ról, warstwa narzędzi)
- **Jakie elementy są tymczasowe** -- będą wymagać przepisania przy AGI?
  (np. prompt engineering, ręczne guardrails, ograniczenia kontekstu)
- **Model "AGI-ready" infrastruktury** -- czy ktoś to opisuje?
  Jakie firmy się do tego przygotowują i jak?
- **Wzorce z poprzednich rewolucji technologicznych** -- kto wygrywał gdy
  pojawiał się nowy paradygmat (internet, mobile, cloud)?
  Czy to byli twórcy technologii czy twórcy infrastruktury nad nią?

### 5. Scenariusze dla branży ERP/wdrożeniowej

- Jak AI zmienia branżę wdrożeń ERP w 2025-2026?
  Jakie firmy wdrożeniowe automatyzują i jak daleko są?
- Czy istnieją produkty "AI-powered ERP configuration"?
  Comarch, SAP, Oracle -- co oferują?
- Jakie jest ryzyko że duży vendor (Comarch, SAP) sam zbuduje to
  co my budujemy -- i jaki jest czas ich reakcji?
- **Moat** -- co jest fosą obronną dla małej firmy w tej przestrzeni?
  Dane? Metodologia? Szybkość iteracji? Relacje z klientami?

### 6. Scenariusz pesymistyczny: disruption

Co jeśli:
- AGI pojawi się szybciej niż 2 lata i nasze narzędzia staną się zbędne?
- AGI pojawi się ale będzie kontrolowane przez 3 firmy i niedostępne?
- Konflikt globalny odetnie dostęp do API/chmury na miesiące?
- Regulacje zabraniają autonomicznego AI w biznesie?

Dla każdego scenariusza: co z naszej infrastruktury przetrwa i dlaczego?

---

## Źródła do przeszukania

- **Forecasting:** Metaculus, Manifold Markets, Epoch AI, AI Impacts
- **Laby AI:** Anthropic blog/research, OpenAI blog, DeepMind blog, Meta AI
- **Think tanki:** RAND Corporation, CSIS (scenariusze geopolityczne + AI),
  Center for AI Safety, Future of Life Institute
- **Branża ERP:** Gartner raporty ERP + AI, Comarch roadmap/blog,
  SAP AI announcements 2025-2026
- **Geopolityka + tech:** Semiconductor Industry Association,
  Chris Miller "Chip War" follow-ups, analizy TSMC/Taiwan
- **Papers:** "Levels of AGI" (DeepMind), Anthropic RSP, governance papers 2025
- **Biznes + infrastruktura:** a16z "AI Infrastructure" posts,
  Sequoia "AI 50" analyses, YC AI company patterns

---

## Format odpowiedzi

### Sekcja podsumowująca

Tabela scenariuszy: 3 scenariusze (optymistyczny / bazowy / pesymistyczny)
z osią czasu AGI, czynnikiem geopolitycznym i implikacją dla naszego projektu.

### Dla każdego znalezionego źródła/wzorca

```
### Nazwa / temat

**Źródło:** (paper, raport, blog, forecast)
**Data:** (kiedy opublikowane -- ważne przy szybko zmieniającym się temacie)
**Kluczowy wniosek:** (2-3 zdania)
**Implikacja dla nas:** (co to zmienia w naszym planie)
**Link:**
```

### Na końcu

Lista pytań na które NIE znalazłeś odpowiedzi -- żebyśmy wiedzieli
gdzie są białe plamy.

---

## Plik odpowiedzi

Zapisz wyniki badania do pliku: `documents/methodology/research_results_agi_horizon.md`
Stwórz plik od razu na starcie i dopisuj do niego w miarę postępu badania.

---

## Czego NIE szukamy

- Ogólnych opisów "czym jest AGI"
- Optymistycznego marketingu firm AI
- Spekulacji bez danych lub źródeł
- Teorii spiskowych -- szukamy realistycznych analiz z konkretnymi mechanizmami
