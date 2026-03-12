# Backlog developerski

Przetworzone i priorytetyzowane zadania developerskie.
Zarządza: Developer.

---

## Przegląd

| # | Tytuł | Obszar | Wartość | Praca |
|---|---|---|---|---|
| 1 | LOOM — publikacja na GitHub | Dev | średnia | mała |
| 2 | NO_SQL zbyt agresywne | Bot | wysoka | mała |
| 3 | Kontekst firmowy + prompt caching | Bot | wysoka | mała–średnia |
| 4 | Reload konfiguracji bez restartu | Bot | średnia | mała |
| 5 | Routing model Haiku/Sonnet | Bot | średnia | średnia |
| 6 | Fallback przy błędzie SQL | Bot | średnia | średnia |
| 7 | Sygnatury narzędzi powielone | Arch | średnia | mała/duża |
| 8 | arch_check.py — walidator ścieżek | Arch | średnia | mała |
| 9 | Brak backlogu per-rola | Arch/Metodolog | średnia | mała–średnia |
| 10 | Sesja inspekcji schematu CDN | ERP | średnia | mała |
| 11 | Research prompts -- plik odpowiedzi + rola Researcher | Arch/Metodolog | średnia | mała-średnia |
| 12 | Eval harness -- golden tasks dla widoków BI i bota | Arch | wysoka | średnia |
| 13 | Audit trail / trace -- logowanie decyzji agentów | Arch | wysoka | średnia |
| 14 | Model abstraction layer -- multi-model + fallback | Arch | średnia | średnia |

---

## Format wpisu

```
### [Obszar] Tytuł

**Źródło:** ...
**Sesja:** data
**Wartość:** wysoka | średnia | niska
**Pracochłonność:** mała | średnia | duża

Opis problemu i propozycja rozwiązania.
```

---

## Aktywne

### [Dev] LOOM — publikacja na GitHub

**Źródło:** methodology_progress
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Folder `_loom/` zawiera komplet plików gotowych do wypchnięcia jako osobne repo.

Kroki:
1. Utwórz repo GitHub (np. `CyperCyper/loom`)
2. Wypchnij zawartość `_loom/` jako root repo
3. Zaktualizuj placeholder URL w `_loom/seed.md`

---

### [Bot] NO_SQL zbyt agresywne — częściowe odpowiedzi

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** mała

Bot zwraca NO_SQL gdy pytanie zawiera dane częściowo niedostępne. Powinien odpowiedzieć
na część pytania i poinformować o braku pozostałych danych.

Fix w `SYSTEM_PROMPT_TEMPLATE` (`nlp_pipeline.py`):
- Obecne: "Jeśli pytanie jest poza zakresem → odpowiedz NO_SQL"
- Poprawione: "Jeśli pytanie jest częściowo poza zakresem → wygeneruj SQL dla dostępnej części. NO_SQL tylko gdy całkowicie poza zakresem."

---

### [Bot] Kontekst firmowy + prompt caching

**Źródło:** obserwacja sesji testowej Haiku
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** mała–średnia

Bot nie zna wartości słownikowych (magazyny, handlowcy) → błędne WHERE, zerowy row_count.

Rozwiązanie:
1. `bot/config/business_context.txt` — fakty firmowe
2. Prompt caching (`cache_control: ephemeral`) — koszt ~10x niższy dla statycznej części

---

### [Bot] Reload konfiguracji bez restartu

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** średnia
**Pracochłonność:** mała

Komenda `/reload` przez Telegram (tylko admin) lub watchdog na `.env`.

---

### [Bot] Routing model — Haiku dla prostych pytań, Sonnet dla złożonych

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** średnia
**Pracochłonność:** średnia

Classifier w Call 1 — Haiku ocenia złożoność i wybiera model do generowania SQL.

---

### [Bot] Fallback przy błędzie SQL

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** średnia
**Pracochłonność:** średnia

Gdy `execution_result.ok = False` — ponów Call 1 z instrukcją "wygeneruj prostszą wersję".
Max 1 retry.

---

### [Arch] Sygnatury narzędzi powielone w wielu miejscach

**Źródło:** developer_suggestions
**Sesja:** 2026-03-08
**Wartość:** średnia
**Pracochłonność:** mała (opcja 3) / duża (opcja 1)

Opcje:
1. `gen_docs.py` generuje sekcję Narzędzia z docstringów
2. Jeden plik referencyjny TOOLS.md + dyscyplina
3. Test CI sprawdzający czy narzędzia w AGENT.md istnieją jako pliki w tools/

---

### [Arch] arch_check.py — walidator ścieżek w dokumentach

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Skanuje pliki `.md` w poszukiwaniu wzorców `` `documents/...` `` i sprawdza czy ścieżki istnieją.
Do wdrożenia przy kolejnym dużym refaktorze.

---

### [Arch] Brak backlogu per-rola — eskalacja do Metodologa

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała–średnia

Zadania domenowe (ERP, Bot) mieszają się z architektonicznymi w jednym pliku.
Opcje: osobne pliki per-rola vs tagi domenowe.
Decyzja należy do Metodologa.

---

### [Arch/Metodolog] Research prompts -- plik odpowiedzi + rola Researcher

**Źródło:** sesja metodologiczna 2026-03-12
**Sesja:** 2026-03-12
**Wartość:** średnia
**Pracochłonność:** mała-średnia

Obecnie research prompty (documents/methodology/research_prompt_*.md) są wykonywane
przez zewnętrzne narzędzie przeglądarkowe, a wyniki wklejane ręcznie.

Krótkoterminowo (zrobione): każdy prompt zawiera sekcję "Plik odpowiedzi" z instrukcją
zapisu wyników do `research_results_*.md`.

Długoterminowo: rola agenturalna Researcher z dostępem do WebSearch/WebFetch,
która czyta prompt badawczy i autonomicznie zapisuje wyniki. Routing w CLAUDE.md.

---

### [ERP] Sesja inspekcji schematu CDN

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Niezbadane: inne funkcje CDN, widoki CDN.* vs tabele, tabele słownikowe powtarzalne w widokach BI.
Propozycja: INFORMATION_SCHEMA + sp_helptext przed kolejnym widokiem BI.

---

### [Arch] Eval harness -- golden tasks dla widoków BI i bota

**Źródło:** research AGI horizon + sesja metodologiczna 2026-03-12
**Sesja:** 2026-03-12
**Wartość:** wysoka
**Pracochłonność:** średnia

Zestaw golden tasks z oczekiwanym wynikiem, wykonywanych automatycznie po zmianach.
Testuje zachowanie systemu jako całości, nie pojedyncze narzędzia.

Zakres:
- Golden tasks BI: "zbuduj widok dla X" → oczekiwany SQL, count, brak NULL w kluczach
- Golden tasks bot: pytanie → oczekiwany SQL, poprawne kolumny, poprawny wynik
- Golden tasks konfiguracja: "znajdź prefiksy w tabeli Y" → oczekiwany komplet

Istniejący fundament: 253+ testów jednostkowych, 10 pytań testowych bota.
Brakuje: format golden task, runner end-to-end, raport pass/fail, porównanie z wzorcem.

Moat: evale na realnych zadaniach ERP z prawdziwymi danymi -- tego vendor nie skopiuje.
Rośnie organicznie z każdym zrealizowanym zadaniem.

---

### [Arch] Audit trail / trace -- logowanie decyzji agentów

**Źródło:** research AGI horizon + sesja metodologiczna 2026-03-12
**Sesja:** 2026-03-12
**Wartość:** wysoka
**Pracochłonność:** średnia

Structured log każdego kroku agenta: co przeczytał, jakie narzędzie wywołał,
jaką decyzję podjął i dlaczego, jaki był wynik.

Cele:
- Debugging: odtworzenie ścieżki gdy widok/konfiguracja ma błąd
- Uczenie się: wzorce z 50+ sesji (gdzie agent się myli, co traci kontekst)
- Regulacje: EU AI Act wymaga audytowalności dla produktu enterprise (horyzont 2)
- Skala: jedyny sposób na monitoring mrowiska przy wielu agentach (horyzont 3)

Istniejący fundament: `logs/bot/YYYY-MM-DD.jsonl`, progress_log, suggestions.
Brakuje: ujednolicony format, narzędzie do odtwarzania sesji, trace per-task.

Łączy się z: handoff DB architecture (tabela `state`/`audit`), architektura agentocentryczna.

---

### [Arch] Model abstraction layer -- multi-model + fallback

**Źródło:** research AGI horizon + sesja metodologiczna 2026-03-12
**Sesja:** 2026-03-12
**Wartość:** średnia
**Pracochłonność:** średnia

Cienka warstwa abstrakcji między logiką biznesową a dostawcą modelu.
Umożliwia multi-model routing, fallback i łatwą zmianę dostawcy.

Interfejs: `llm.complete(task, context, tier)` gdzie tier mapuje na model:
- "heavy" → Claude Opus (złożone zadania)
- "standard" → Claude Sonnet (typowe zadania)
- "cheap" → Haiku (proste klasyfikacje, routing)
- "fallback" → lokalne Llama/Ollama (gdy API niedostępne)

Istniejący fundament: `BOT_MODEL_FORMAT` env var w bocie, backlog #5 (routing Haiku/Sonnet).
Brakuje: ujednolicony interfejs, konfiguracja per-tier, fallback logic, support open-weight.

Priorytet niższy niż eval/audit -- Claude działa stabilnie, nie pali się.
Staje się krytyczny przy: zmianie pricingu, awarii API, wejściu na rynek (horyzont 2).

---

## Archiwum

**[Agent] Baza wzorców numeracji** — zrealizowane 2026-03-11 (pliki reference gotowe, prefiksy zweryfikowane we wszystkich tabelach — wynik pusty, dokumentacja kompletna)

**[Dev] Zasada "zbadaj strukturę przed budowaniem"** — zrealizowane 2026-03-11 (DEVELOPER.md zasada #6)

**[Dev] Agent edytuje pliki chronione bez jawnego zatwierdzenia** — zrealizowane 2026-03-11 (CLAUDE.md: protokół pytania przed edycją)

**[Arch] Kanał Developer → ERP Specialist** — zrealizowane 2026-03-11 (`developer_notes.md` + routing w ERP_SPECIALIST.md + ANALYST.md)

**[Analityk] Weryfikator konwencji** — zrealizowane 2026-03-11 (`analyst_start.md`: dwie role, audyt, format review)

**[Dev] Kontekst na końcu wiadomości + węzłowość reguł** — zrealizowane 2026-03-11

**[Arch] Separacja pamięci między agentami wykonawczymi** — zrealizowane 2026-03-11

**[Dev] git_commit.py** — zrealizowane 2026-03-10

**[Workflow] ERP_VIEW_WORKFLOW + ERP_SCHEMA_PATTERNS** — zrealizowane 2026-03-10

**[P1–P4 + bi_discovery + komendy]** — zrealizowane 2026-03-09

**Pozycje #1–#10 z sesji 2026-03-08** — zrealizowane, szczegóły w `agent_reflections.md`
