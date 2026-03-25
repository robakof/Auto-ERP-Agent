# Research: Prompt engineering dla spójnej identyfikacji wizualnej — mapowanie obszarów wiedzy

## Kontekst

Budujemy nową rolę agenta (roboczo: **Art Director**) w systemie wieloagentowym.
Agent będzie autonomicznie generować i utrzymywać spójną identyfikację wizualną firmy produkcyjnej:
zdjęcia produktowe, grafiki marketingowe, materiały brandowe, wizualizacje danych.

To jest prompt eksploracyjny — pierwszy krok. Celem nie jest gotowe rozwiązanie,
lecz **mapa obszarów wiedzy** które Art Director musi opanować.

## Cel researchu

Zmapuj wszystkie istotne obszary wiedzy, standardy, metody i narzędzia związane z:
1. Pisaniem promptów do generowania spójnych wizualnie obrazów
2. Utrzymywaniem brand consistency w generatywnych pipeline'ach
3. Narzędziami i systemami do vibe-designu na skalę przemysłową

## Obszary badawcze

### A. Fundamenty prompt engineeringu wizualnego

1. Jak zbudowany jest skuteczny prompt do generowania obrazów?
   - Anatomia promptu (subject, style, composition, lighting, camera, mood...)
   - Kolejność elementów vs wpływ na wynik
   - Negative prompts — kiedy i jak
   - Różnice w składni między modelami (DALL-E, Midjourney, Stable Diffusion, Flux, Ideogram)
2. Jakie są znane techniki utrzymywania spójności stylu między sesjami?
   - Style references / style anchors
   - Seed control, consistent characters, IP-adapter
   - Token weighting, prompt matrices
3. Jakie są ograniczenia i pułapki?
   - Prompt drift (degradacja stylu przy wielu generacjach)
   - Model-specific biases i artefakty
   - Halucynacje wizualne (tekst w obrazach, anatomia, fizyka)

### B. Brand identity w kontekście generatywnym

1. Jak definiować i utrzymywać visual brand guidelines dla AI?
   - Tradycyjne brand books vs AI-native brand systems
   - Color palette enforcement w promptach
   - Typography consistency (jeśli w ogóle możliwa)
   - Moodboard → prompt translation
2. Jakie firmy/projekty robią to na skalę i co publikują?
   - Case studies (e-commerce, moda, FMCG, produkcja)
   - Open-source style guides dla AI-generated content
3. Jak wygląda quality assurance generowanych materiałów?
   - Human-in-the-loop vs automated scoring
   - CLIP similarity, FID, aesthetic scores
   - A/B testing wizualizacji

### C. Zdjęcia produktowe — specifics

1. Jakie są standardy zdjęć produktowych (e-commerce, katalogi, B2B)?
   - Tło, oświetlenie, kąty, proporcje
   - Normy platform (Amazon, Allegro, własny e-commerce)
   - Packshot vs lifestyle vs in-context
2. Jak generować spójne zdjęcia produktowe seryjnie?
   - Template prompts z zmiennymi (produkt, wariant, scena)
   - Inpainting / outpainting dla wariantów
   - ControlNet, reference images, img2img pipelines
3. Jakie są granice realności (uncanny valley w produktach)?

### D. Narzędzia i systemy — landscape 2025/2026

1. **Modele generatywne** — aktualny state-of-the-art:
   - Zamknięte: DALL-E 3/4, Midjourney v6/v7, Ideogram, Adobe Firefly, Google Imagen
   - Open: Stable Diffusion 3/XL, Flux, Playground
   - Wyspecjalizowane: produktowe (Photoroom, Booth.ai, Pebblely), modowe, architektoniczne
2. **Systemy do pracy na skalę (vibe-design przemysłowy):**
   - Batch generation pipelines (ComfyUI workflows, A1111 scripts)
   - API-first platforms (Replicate, fal.ai, RunPod, Modal)
   - Brand management + AI (Frontify, Bynder, Brandfolder z AI features)
   - DAM (Digital Asset Management) z generatywnym AI
3. **Narzędzia wspomagające:**
   - Prompt builders / prompt management (PromptHero, Civitai, własne systemy)
   - Style transfer i fine-tuning (LoRA, DreamBooth, textual inversion)
   - Upscaling, post-processing pipelines
   - Version control dla wizualnych assetów
4. **Koszty i skalowalność:**
   - Porównanie kosztów per image (API vs self-hosted vs managed)
   - Throughput (ile obrazów/h na różnych setupach)
   - Które podejście skaluje się do 1000+ obrazów/mies bez degradacji jakości

### E. Metodyki i frameworki

1. Czy istnieją uznane metodyki/frameworki do systematycznego promptingu wizualnego?
   - Akademickie (papers, benchmarki)
   - Praktyczne (community guides, korporacyjne playbooks)
   - Emerging standards (ISO, W3C accessibility dla AI-generated images)
2. Jak wygląda workflow profesjonalnego AI art directora?
   - Brief → moodboard → test prompts → refinement → batch → QA → delivery
   - Ile jest manualnego vs automatycznego
3. Jak dokumentować i wersjonować visual prompt library?
   - Prompt templates vs prompt databases
   - Tagging, search, reuse patterns
   - Regression testing (czy stary prompt daje ten sam wynik na nowej wersji modelu)

### F. Integracja z istniejącym systemem agentów

1. Jakie interfejsy potrzebuje Art Director?
   - Input: brief od innej roli (ERP Specialist, marketing)
   - Output: gotowe assety + metadata (prompt użyty, model, seed, parametry)
   - Feedback loop: human review → korekta promptu
2. Jakie decyzje Art Director podejmuje autonomicznie vs eskaluje?
   - Wybór modelu per task
   - Ocena "czy to jest on-brand"
   - Budżet (ile generacji na task)

---

## Output contract

Zapisz wyniki do pliku: `documents/researcher/research/research_results_visual_identity_prompting.md`

### Struktura pliku wynikowego:

```markdown
# Research: Prompt engineering dla spójnej identyfikacji wizualnej

Data: YYYY-MM-DD

## TL;DR — 5-7 najważniejszych odkryć / kierunków

## Wyniki per obszar badawczy

### A. Fundamenty prompt engineeringu wizualnego
(odpowiedzi na pytania z sekcji A; dla każdego: opis + siła dowodów [empiryczne / praktyczne / spekulacja])

### B. Brand identity w kontekście generatywnym
(...)

### C. Zdjęcia produktowe
(...)

### D. Narzędzia i systemy — landscape
(tabele porównawcze gdzie to możliwe)

### E. Metodyki i frameworki
(...)

### F. Integracja z systemem agentów
(...)

## Mapa obszarów wiedzy
(diagram lub lista: które obszary są dobrze zbadane, które emerging, które białe plamy)

## Co nierozwiązane / otwarte pytania

## Źródła / odniesienia
```

### Czego NIE rób:

- Nie oceniaj dopasowania do naszego systemu — to osobny krok po researchu
- Nie dawaj jednej odpowiedzi — dawaj pole możliwości z trade-offami
- Nie skracaj gdy brakuje danych — zaznacz lukę i siłę dowodów
- Nie ograniczaj się do jednego modelu/narzędzia — mapuj landscape szeroko
- Nie proponuj architektury agenta — to zadanie dla Architekta po przeczytaniu wyników
