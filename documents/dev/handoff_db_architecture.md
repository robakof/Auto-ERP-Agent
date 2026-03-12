# Handoff: Architektura agentocentryczna — DB jako single source of dynamic truth

**Od:** Metodolog (sesja 2026-03-12)
**Do:** Developer
**Priorytet:** Wysoki — zmiana fundamentalna, wpływa na całą strukturę projektu

---

## Kontekst i uzasadnienie

Sesja metodologiczna 2026-03-12 rozstrzygnęła kierunek architektury komunikacji.
Pełna obserwacja: `documents/methodology/methodology_suggestions.md` wpis [2026-03-12].

Kluczowy fakt empiryczny: użytkownik już nie czyta dokładnie tego co agent zapisuje
w plikach .md o swoim stanie. Architektura człowiekocentryczna nie opisuje rzeczywistości.

---

## Zasada zatwierdzona przez Metodologa

```
Instrukcje / wytyczne  →  .md    (statyczne, bootstrap + kontekst sesji)
Stan / komunikacja     →  DB     (dynamiczne, dostępne przez narzędzia)
```

---

## Pytania do rozstrzygnięcia przez Developera

### 1. Format i technologia DB

- SQLite (lokalny plik, zero infrastruktury) vs lekki serwis (SQLite + HTTP wrapper)?
- JSON-lines jako alternatywa dla małej skali zanim pojawi się pełna DB?
- Jak agent pisze do DB? Bezpośrednio przez Python tool czy przez dedykowane CLI?

### 2. Schemat tabel

Minimalny zestaw do zdefiniowania:

```
messages   (id, sender, recipient, type, content, status, created_at, session_id)
state      (id, role, session_id, type, content, created_at)
           -- type: progress | reflection | backlog_item
directives (id, key, content, version, updated_at)
role_directives (role, directive_id, order)
```

Pytania:
- Czy dyrektywy od razu do DB czy to faza 2?
- Jak wersjonować dyrektywy przy zmianie (audit trail)?
- Czy backlog i progress log to jedna tabela `state` z tagiem czy osobne?

### 3. Narzędzia dla agenta (minimalny zestaw)

```python
get_context(role)              # dyrektywy + aktywne wątki + inbox
get_inbox(role, status)        # nieprzetworzone wiadomości
send_message(to, content, type)
write_progress(session_id, content)
write_reflection(role, session_id, content)
flag_for_human(reason, urgency)
```

Pytania:
- Czy to oddzielny moduł `tools/agent_bus.py` czy rozszerzenie istniejących tools?
- Jak agent dostaje `session_id`? Generuje na starcie czy dostaje z DB?

### 4. Bootstrap — co zostaje w CLAUDE.md

CLAUDE.md musi pozostać jako plik ładowany automatycznie przez Claude Code.
Pytanie: co jest absolutnym minimum które musi tam być?

Propozycja:
```
# Projekt: X
Agent: wywołaj get_context(role=<rola>) żeby dostać instrukcje sesji.
Rola: określ na podstawie kontekstu sesji (tabela w tym pliku lub parametr wejściowy).
```

Czy routing ról zostaje w CLAUDE.md czy też trafia do DB?

### 5. Generowanie widoków dla człowieka

Narzędzia agenturalne generujące .md na żądanie:
- `generate_view("backlog")` → `backlog.md`
- `generate_view("progress")` → `progress_report.md`
- `generate_view("inbox")` → czytelny widok wiadomości

Pytanie: czy to osobne skrypty CLI czy narzędzia dostępne dla agenta?

### 6. Migracja istniejących plików

Co z obecnymi plikami stanu:
- `documents/dev/backlog.md`
- `documents/erp_specialist/erp_specialist_suggestions.md`
- `documents/analyst/analyst_suggestions.md`
- `documents/dev/developer_suggestions.md`
- `documents/dev/progress_log.md`
- `documents/methodology/methodology_progress.md` (ten plik może zostać jako .md — rzadko aktualizowany)

Opcje:
- A: Migracja jednorazowa (import historii do DB, archiwizacja .md)
- B: Nowe wpisy od teraz do DB, stare .md jako archiwum read-only
- C: Stopniowe — zacznij od messages i state, dyrektywy w fazie 2

### 7. Zakres fazy 1 (rekomendacja Metodologa)

Nie przepisuj wszystkiego naraz. Propozycja faz:

**Faza 1 — komunikacja i stan:**
- Tabele: messages, state
- Narzędzia: send_message, get_inbox, write_progress, write_reflection
- Migracja: nowe wpisy do DB, stare pliki jako archiwum
- .md suggestions.md i backlog.md przestają być aktualizowane przez agentów

**Faza 2 — dyrektywy:**
- Tabele: directives, role_directives
- Narzędzia: get_context(role) zwraca dyrektywy z DB
- CLAUDE.md redukuje się do bootstrap
- Migracja: przepisanie wytycznych do dyrektyw atomowych

**Faza 3 — widoki i monitoring:**
- generate_view() dla człowieka
- Analityka przepływu komunikacji
- Dashboard lub CLI do przeglądu stanu systemu

---

## Warstwa myśli — wzorzec i pytania implementacyjne

Sesja metodologiczna wypracowała wzorzec dla warstwy 3 (myśli / shared memory).
Research potwierdził że wzorzec jest znany, ale brak gotowej implementacji dla LLM.
Ref: `documents/methodology/research_results_swarm_communication.md`

**Wzorzec:** Hybryda Blackboard + Tuple Space z attention-based scoring

```
thoughts table:
  id, author_role, session_id, content, tags[], score REAL,
  created_at, last_read_at, status (active|archived)

operacje:
  write_thought(content, tags)         → tworzy wpis, score=0
  read_thoughts(tags, semantic_query)  → zwraca wyniki ważone score, inkrementuje score
  decay_job()                          → background, score -= δ per interwał
```

Uwaga jako sygnał wartości: myśl często przywoływana rośnie w score naturalnie.
Myśl ignorowana gaśnie. Rój sam organizuje relevancję — bez ręcznej priorytetyzacji.

**Pytania do Developera — warstwa myśli:**

- Czy SQLite obsłuży concurrent writes od wielu agentów bez lock contention?
- Jaki δ dla decay? Czy to konfigurowalne per tag/rola?
- Próg archiwizacji: score < X po Y dniach → status=archived?
- Semantic search: lokalne embeddingi (sentence-transformers) czy API? Koszt vs latency?
- Czy metadata filter (tagi) + semantic search jest wykonalne w SQLite+FTS5 czy wymaga osobnego vector store?

## Ostrzeżenie: ryzyko pułapki wdrożeniowej

Metodolog explicite flaguje: koncepcja jest spójna i wartościowa, ale **wizjonerska**.
Przed jakimkolwiek commitmentem implementacyjnym Developer powinien odpowiedzieć:

1. **Proof of concept first** — czy attention-based scoring w SQLite działa przy symulowanym
   obciążeniu (100 agentów, 10k myśli)? Zanim zaprojektujemy pełny schemat.

2. **Czy semantic search jest konieczny w fazie 1?** Może tagi wystarczą do pierwszej
   weryfikacji wzorca — semantic search dokłada w fazie 2.

3. **Koszt decay job** — background process wymaga schedulera. Czy to nowy komponent
   czy można to zrobić lazy (decay przy każdym read)?

4. **Alternatywa uproszczona:** zwykły timestamp sort (najnowsze wyżej) zamiast score —
   weryfikuje wzorzec komunikacji bez mechanizmu attention. Jeśli wzorzec działa,
   attention scoring dodajemy w następnej iteracji.

Metodolog rekomenduje: **zweryfikuj najprostszą wersję wzorca zanim zbudujesz pełny system.**

---

## Decyzja nie należy do Metodologa

Metodolog zatwierdził kierunek i zasadę separacji. Decyzje techniczne (SQLite vs serwis,
schemat, fazy migracji, narzędzia) należą do Developera i wymagają zatwierdzenia przez człowieka
przed implementacją.
