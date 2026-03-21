# Architektura synchronizacji między maszynami

**Problem:** Pliki specyficzne dla maszyny i baza danych powodują konflikty git przy pracy na wielu maszynach.

**Zakres:** Konfiguracja Claude Code + synchronizacja bazy danych mrowisko.db (agent_bus komunikacja).

---

## Problem 1: Pliki konfiguracyjne `.claude/settings*`

**Aktualna sytuacja:**
- `.claude/settings.json`, `.claude/settings.local.json`, `bot/.claude/settings.local.json` — śledzone w git
- Zawierają ścieżki absolutne specyficzne dla maszyny (`~/Desktop/...` vs `~/OneDrive/Pulpit/...`)
- Interpreter Python różny między maszynami (`python` vs `py`)
- Przy pull → konflikty lub nadpisywanie konfiguracji

**Rozwiązanie (proste):**

1. Stworzyć templates w repo:
   - `.claude/settings.template.json`
   - `.claude/settings.local.template.json`
   - `bot/.claude/settings.local.template.json`

2. Dodać do `.gitignore`:
   ```
   .claude/settings.json
   .claude/settings.local.json
   bot/.claude/settings.local.json
   ```

3. Instrukcja w README: "Po sklonowaniu repo skopiuj templates → usuń .template, zaktualizuj ścieżki."

4. Opcjonalnie: skrypt `tools/setup_machine.py` — automatycznie generuje lokalne settings z templates podstawiając aktualne ścieżki.

**Trade-offy:**
- ✓ Zero konfliktów git
- ✓ Łatwe onboarding nowej maszyny
- ✗ Wymaga ręcznego setupu po clone (ale tylko raz)

**Decyzja:** GOTOWE DO WDROŻENIA — nie wymaga dalszej analizy.

---

## Problem 2: Baza danych `mrowisko.db` — komunikacja między agentami

**Aktualna sytuacja:**
- `mrowisko.db` w repo (śledzona)
- Zawiera:
  - Logi sesji (conversation_log)
  - Komunikacja agent-agent (agent_bus: messages, suggestions)
  - Backlog zadań
  - Flagi do człowieka
- Przy pracy na dwóch maszynach równolegle → konflikty merge niemożliwe do automatycznego rozwiązania

**Cel:** Agenci na różnych maszynach mogą wymieniać się wiadomościami i zadaniami.

**Opcje:**

### Opcja A: Git LFS + manual merge

**Jak działa:**
- `mrowisko.db` w Git LFS (duże pliki binarne)
- Przy konflikcie — ręczny merge przez export/import:
  1. `git checkout --ours mrowisko.db` lub `--theirs`
  2. Export rekordów z drugiej wersji (SQL dump tabeli z timestampem)
  3. Import do wybranej wersji

**Trade-offy:**
- ✓ Minimalne zmiany w architekturze
- ✗ Ręczny merge przy każdym konflikcie
- ✗ Git LFS wymaga konfiguracji (dodatkowy setup)
- ✗ Nie skaluje — przy 3+ maszynach staje się niemożliwe

**Ocena:** Prowizorka. Nie spełnia "Buduj dom" z SPIRIT.md.

---

### Opcja B: Baza zewnętrzna (PostgreSQL / SQLite w chmurze)

**Jak działa:**
- Baza danych na serwerze (np. Railway, Supabase, własny VPS)
- Wszystkie agenci łączą się przez sieć
- W repo: tylko schemat (`schema.sql` + migracje)

**Trade-offy:**
- ✓ Zero konfliktów
- ✓ Realtime sync między maszynami
- ✓ Skaluje — dowolna liczba maszyn
- ✗ Wymaga infrastruktury (koszt, setup, utrzymanie)
- ✗ Wymaga połączenia internetowego
- ✗ Latencja (nieznaczna dla agent_bus, ale istnieje)

**Ocena:** Profesjonalne rozwiązanie. Zgodne z SPIRIT ("Buduj dom"). Koszt: czas setupu + ewentualnie $$ za hosting.

---

### Opcja C: Podział na bazę lokalną i współdzieloną

**Jak działa:**
- **Lokalna baza (`mrowisko.local.db`):** w .gitignore
  - Logi sesji lokalnych
  - Draft suggestions przed publikacją
  - Cache
- **Współdzielona baza (`mrowisko.shared.db`):** w repo
  - Backlog zadań (READ-ONLY dla agentów, WRITE przez dedykowane API)
  - Zatwierdzone suggestions
  - Flagi do człowieka
- Agent zapisuje lokalnie → commit do shared przez dedykowane narzędzie (atomic append)

**Trade-offy:**
- ✓ Nie wymaga zewnętrznej infrastruktury
- ✓ Offline-first — działa bez internetu
- ✓ Mniej konfliktów (shared ma append-only workflow)
- ✗ Złożoność — dwie bazy, synchronizacja między nimi
- ✗ Backlog trudny do edycji równolegle (ale możliwe przez pull → local edit → push)
- ✗ Nie realtime — wymaga pull/push

**Ocena:** Kompromis między A i B. Może działać jeśli nie ma potrzeby realtime sync.

---

### Opcja D: Event sourcing (append-only log)

**Jak działa:**
- Baza danych to append-only log zdarzeń (każdy wpis ma UUID, timestamp, machine_id)
- W repo: `events.jsonl` lub `events.db` (tylko INSERT, nigdy UPDATE/DELETE)
- Przy pull → auto-merge (konkatenacja logów) + deduplikacja po UUID
- Rebuild stanu przez replay eventów

**Trade-offy:**
- ✓ Zero konfliktów merge (append-only)
- ✓ Pełna historia zmian
- ✓ Nie wymaga zewnętrznej infrastruktury
- ✓ Skaluje — dowolna liczba maszyn
- ✗ Wymaga przeprojektowania agent_bus (z tabeli relacyjnej → event log)
- ✗ Rebuild stanu może być wolny przy dużej liczbie eventów
- ✗ Bardziej złożone zapytania (replay zamiast SELECT)

**Ocena:** Eleganckie rozwiązanie architektoniczne. Zgodne z SPIRIT ("Buduj dom"). Koszt: refactor agent_bus.

---

## Rekomendacja

**Krótki termin (następna sesja):**
Wdrożyć rozwiązanie dla **Problem 1** (templates + gitignore) — 30 minut pracy, zero trade-offów.

**Średni termin (tydzień):**
Wybrać architekturę dla bazy danych na podstawie priorytetów:

| Jeśli priorytet to... | Wybierz opcję |
|---|---|
| Szybkość wdrożenia + zero kosztów | **C** (podział lokalnej i shared) |
| Realtime sync + profesjonalność | **B** (baza zewnętrzna) |
| Elegancja + brak vendor lock-in | **D** (event sourcing) |
| Minimalne zmiany | **A** (Git LFS) — NIE REKOMENDOWANE |

**Moje osobiste głosy:**
1. **Opcja D** (event sourcing) — najbardziej zgodna z SPIRIT, skaluje bez infrastruktury, pełna historia
2. **Opcja B** (zewnętrzna baza) — jeśli user ma dostęp do serwera lub akceptuje koszt hostingu

---

## Następne kroki

1. User decyduje: która opcja dla bazy danych?
2. Dla wybranej opcji tworzę szczegółowy plan implementacji
3. Implementacja etapami (config templates → DB migration)

---

**Pytania do user:**

1. Czy praca na dwóch maszynach będzie równoległa (jednocześnie) czy sekwencyjna (jedna maszyna naraz)?
2. Czy akceptujesz koszt zewnętrznego hostingu bazy ($5-10/mies) w zamian za realtime sync?
3. Czy zależy Ci na pełnej historii zmian (audit log) czy tylko aktualny stan?
4. Jak często planujesz synchronizację? (realtime / kilka razy dziennie / raz dziennie)
