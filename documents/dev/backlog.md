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

### [ERP] Sesja inspekcji schematu CDN

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Niezbadane: inne funkcje CDN, widoki CDN.* vs tabele, tabele słownikowe powtarzalne w widokach BI.
Propozycja: INFORMATION_SCHEMA + sp_helptext przed kolejnym widokiem BI.

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
