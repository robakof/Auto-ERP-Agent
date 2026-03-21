# Plan audytu architektonicznego: Mrowisko

*Data: 2026-03-21*
*Rola: Architect*
*Cel: Identyfikacja błędów architektonicznych, tech debt, potrzebnych refaktoryzacji*

---

## Filozofia audytu

> Nie boimy się kwestionować. Każda decyzja może być błędna.
> Szukamy trupów w szafie, nie potwierdzenia że wszystko jest OK.

**Pytania przewodnie:**
- Czy to rozwiązanie skaluje się? Co jeśli będzie 10x więcej?
- Czy to jest proste czy tylko wydaje się proste?
- Czy rozumiemy dlaczego tak zrobiono, czy "tak wyszło"?
- Co by się stało gdyby nowa osoba musiała to utrzymywać?
- Gdzie są ukryte zależności i coupling?

---

## Faza 1: Inspekcja warstwy narzędzi (tools/)

**Cel:** Ocenić ~50 skryptów pod kątem spójności, duplikacji, architektury.

### 1.1 Struktura i nazewnictwo

| Pytanie | Co sprawdzić |
|---------|--------------|
| Czy nazewnictwo jest spójne? | `docs_search` vs `search_docs`, `solutions_save` vs `save_solution` |
| Czy podział na pliki ma sens? | Czy są pliki które robią za dużo? Za mało? |
| Czy `tools/lib/` jest wykorzystywane? | Ile logiki jest zduplikowane między skryptami? |

### 1.2 Kontrakty JSON

| Pytanie | Co sprawdzić |
|---------|--------------|
| Czy format odpowiedzi jest jednolity? | `{"ok": true, "data": ...}` wszędzie? |
| Czy obsługa błędów jest spójna? | `{"ok": false, "error": {...}}` czy wyjątki? |
| Czy są niezdefiniowane kontrakty? | Skrypty które zwracają co chcą? |

### 1.3 Zależności i coupling

| Pytanie | Co sprawdzić |
|---------|--------------|
| Które skrypty importują z `tools/lib/`? | Diagram zależności |
| Czy są cykliczne zależności? | A → B → A |
| Czy skrypty zależą od globalnego stanu? | .env, ścieżki hardcoded |

### 1.4 Potencjalne red flags

- [ ] Skrypty >300 linii (god scripts)
- [ ] Funkcje >50 linii
- [ ] Try/except które połykają wyjątki
- [ ] Hardcoded ścieżki / credentials
- [ ] Kopiuj-wklej między skryptami

---

## Faza 2: Inspekcja agent_bus (mrowisko.db)

**Cel:** Ocenić czy architektura komunikacji jest solidna.

### 2.1 Schema bazy danych

| Pytanie | Co sprawdzić |
|---------|--------------|
| Czy schema jest znormalizowana? | Redundancja danych? |
| Czy są indeksy na często odpytywanych kolumnach? | Performance? |
| Czy są constrainty integralności? | FK, unique, not null? |
| Czy migracje są wersjonowane? | Co jeśli schema się zmieni? |

### 2.2 API agent_bus_cli.py

| Pytanie | Co sprawdzić |
|---------|--------------|
| Czy API jest kompletne? | Brakujące operacje? |
| Czy jest walidacja inputu? | Garbage in → garbage out? |
| Czy są race conditions? | Dwa agenty piszą jednocześnie? |

### 2.3 Potencjalne red flags

- [ ] Brak transakcji przy złożonych operacjach
- [ ] Brak cleanup starych danych (logi, wiadomości)
- [ ] Synchronizacja między maszynami (backlog #90)
- [ ] Brak backupu / recovery

---

## Faza 3: Inspekcja Bot Telegram (bot/)

**Cel:** Ocenić czy bot jest produkcyjnie gotowy.

### 3.1 Architektura

| Pytanie | Co sprawdzić |
|---------|--------------|
| Czy pipeline jest testowalny? | Unit testy? Mocks? |
| Czy jest separation of concerns? | Czy nlp_pipeline robi za dużo? |
| Czy error handling jest kompletny? | Co jeśli Claude API nie odpowiada? |

### 3.2 Bezpieczeństwo

| Pytanie | Co sprawdzić |
|---------|--------------|
| Czy SQL injection jest niemożliwy? | sql_validator naprawdę blokuje? |
| Czy whitelist jest solidny? | Obejście? |
| Czy logi nie zawierają secrets? | API keys, credentials? |

### 3.3 Operacje

| Pytanie | Co sprawdzić |
|---------|--------------|
| Czy jest health check? | Monitoring? |
| Czy restart jest bezpieczny? | Stan w pamięci? |
| Czy jest rate limiting? | DoS przez użytkownika? |

### 3.4 Potencjalne red flags

- [ ] Stan konwersacji tylko w pamięci (utrata przy restarcie)
- [ ] Brak retry logic dla Claude API
- [ ] Brak timeout handling
- [ ] Brak metryk / telemetrii

---

## Faza 4: Inspekcja dokumentacji ról

**Cel:** Ocenić czy prompty są spójne, kompletne, utrzymywalne.

### 4.1 Spójność między rolami

| Pytanie | Co sprawdzić |
|---------|--------------|
| Czy format promptów jest jednolity? | Struktura, sekcje |
| Czy są sprzeczne instrukcje? | Rola A mówi X, rola B mówi nie-X |
| Czy workflow są kompletne? | Brakujące kroki? |

### 4.2 Utrzymywalność

| Pytanie | Co sprawdzić |
|---------|--------------|
| Czy prompty są za długie? | Token cost? |
| Czy jest duplikacja między promptami? | DRY? |
| Czy CLAUDE.md nie jest przeładowany? | Single responsibility? |

### 4.3 Potencjalne red flags

- [ ] Prompty >5000 tokenów
- [ ] Sprzeczne instrukcje
- [ ] Nieaktualne odwołania do plików/narzędzi
- [ ] Brak wersjonowania promptów

---

## Faza 5: Inspekcja solutions/ i erp_docs/

**Cel:** Ocenić jakość bazy wiedzy ERP.

### 5.1 Struktura solutions/

| Pytanie | Co sprawdzić |
|---------|--------------|
| Czy struktura katalogów jest spójna? | Konwencja nazewnictwa? |
| Czy erp_windows.json jest aktualny? | Drift? |
| Czy SQL jest walidowany? | Syntax errors? |

### 5.2 docs.db

| Pytanie | Co sprawdzić |
|---------|--------------|
| Czy indeks jest aktualny? | Kiedy ostatni rebuild? |
| Czy FTS5 jest optymalnie skonfigurowany? | Tokenizer? |

---

## Faza 6: Inspekcja _loom (seed replikacji)

**Cel:** Ocenić czy _loom jest gotowy do replikacji.

| Pytanie | Co sprawdzić |
|---------|--------------|
| Czy szablony są kompletne? | Brakujące pliki? |
| Czy seed.md jest aktualny? | Instrukcje działają? |
| Czy _loom jest niezależny od Mrowiska? | Hardcoded references? |

---

## Faza 7: Meta-analiza

**Cel:** Spojrzeć na całość z lotu ptaka.

### 7.1 Pytania architektoniczne

| Pytanie | Hipoteza do zweryfikowania |
|---------|---------------------------|
| Czy system wieloagentowy ma sens? | Może prostszy model byłby lepszy? |
| Czy SQLite wystarczy? | Limity przy skali? |
| Czy podział na role jest optymalny? | Za dużo? Za mało? Złe granice? |
| Czy Git jako sync ma sens? | Konflikty, latency? |

### 7.2 Tech debt inventory

Zbierz wszystkie znalezione problemy i sklasyfikuj:

| Kategoria | Przykłady |
|-----------|-----------|
| **Critical** | Bezpieczeństwo, data loss risk |
| **High** | Blokery skalowania, duża duplikacja |
| **Medium** | Niespójności, brakująca dokumentacja |
| **Low** | Code style, nice-to-have |

---

## Harmonogram realizacji

| Faza | Zakres | Estymata |
|------|--------|----------|
| 1 | tools/ (~50 plików) | 1-2 sesje |
| 2 | agent_bus | 1 sesja |
| 3 | bot/ | 1 sesja |
| 4 | dokumentacja ról | 1 sesja |
| 5 | solutions/, erp_docs/ | 0.5 sesji |
| 6 | _loom | 0.5 sesji |
| 7 | meta-analiza + raport | 1 sesja |

**Total:** ~6-8 sesji Architekta

---

## Output audytu

Po zakończeniu powstanie:

1. **ARCHITECTURE_AUDIT_REPORT.md** — pełny raport z findings
2. **TECH_DEBT_INVENTORY.md** — lista problemów z priorytetami
3. **REFACTORING_ROADMAP.md** — plan naprawczy z kolejnością

---

## Następny krok

Rozpocząć **Fazę 1** — inspekcja `tools/`.

Czy zatwierdzasz ten plan?
