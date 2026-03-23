# Suggestions — 2026-03-22

*20 sugestii*

---

## Zasady (rule)

| id | autor | tytuł | status | data |
|----|-------|-------|--------|------|
| 169 | architect | Nowy kod w core/, stary w tools/ przez adaptery | open | 2026-03-22 |
| 141 | architect | Nowy kod w core/, stary w tools/ przez adaptery | open | 2026-03-22 |
| 132 | architect | Audyt Fazy 1-4: findings do wdrożenia | open | 2026-03-22 |
| 120 | architect | Workflow Architecture Discovery — kroki | open | 2026-03-21 |

## Narzędzia (tool)

| id | autor | tytuł | status | data |
|----|-------|-------|--------|------|
| 123 | architect | Narzędzie do generowania diagramu architektury | open | 2026-03-21 |

## Odkrycia (discovery)

| id | autor | tytuł | status | data |
|----|-------|-------|--------|------|
| 167 | architect | invocation_log śledzi wywołania agent→agent | open | 2026-03-22 |
| 165 | architect | Tabele trace i state są martwe/legacy | open | 2026-03-22 |
| 137 | architect | Tabele trace i state są martwe/legacy | open | 2026-03-22 |
| 133 | architect | 75k rekordów tool_calls/token_usage — gotowe do analizy | open | 2026-03-22 |
| 122 | architect | _loom jako seed replikacji | open | 2026-03-21 |

## Obserwacje (observation)

| id | autor | tytuł | status | data |
|----|-------|-------|--------|------|
| 168 | architect | Moment strategiczny na refaktor | open | 2026-03-22 |
| 166 | architect | Bot wymaga hardeningu przed skalowaniem | open | 2026-03-22 |
| 164 | architect | Dict-based architecture nie skaluje się | open | 2026-03-22 |
| 138 | architect | Bot wymaga hardeningu przed skalowaniem | open | 2026-03-22 |
| 131 | architect | Granica Architect vs Developer rozmyta | open | 2026-03-21 |
| 130 | architect | _loom wygląda na porzucony | open | 2026-03-21 |
| 129 | architect | Nazewnictwo narzędzi — brak konwencji | open | 2026-03-21 |
| 128 | architect | tmp/ jako de facto inbox człowieka | open | 2026-03-21 |
| 127 | architect | mrowisko.db — podwójna odpowiedzialność | open | 2026-03-21 |
| 121 | architect | Istniejący ARCHITECTURE.md w documents/dev/ | open | 2026-03-21 |

---

## Treści

### Zasady (rule)

#### [169] Nowy kod w core/, stary w tools/ przez adaptery
**autor:** architect  **status:** open  **data:** 2026-03-22

Strategia migracji: nowe klasy domenowe w core/, stary kod tools/ deleguje przez adaptery. Zachowujemy kompatybilność wsteczną (CLI działa bez zmian). Stopniowa migracja, nie big bang.

#### [141] Nowy kod w core/, stary w tools/ przez adaptery
**autor:** architect  **status:** open  **data:** 2026-03-22

Strategia migracji: nowe klasy domenowe w core/, stary kod tools/ deleguje przez adaptery. Zachowujemy kompatybilność wsteczną (CLI działa bez zmian). Stopniowa migracja, nie big bang.

#### [132] Audyt Fazy 1-4: findings do wdrożenia
**autor:** architect  **status:** open  **data:** 2026-03-22

Audyt architektoniczny (Fazy 1-4) — główne findings do wdrożenia:

1. **CRITICAL:** bot/pipeline/nlp_pipeline.py — brak obsługi wyjątków Anthropic API (RateLimitError, APIError)
2. **HIGH:** mrowisko.db — cleanup policy dla tool_calls (30k) i token_usage (44k)
3. **MEDIUM:** Usunąć martwą tabelę `trace`, deprecate `state`
4. **MEDIUM:** Rozbić nlp_pipeline.py (218 linii) na mniejsze komponenty
5. **LOW:** Rename search_bi.py → bi_search.py dla spójności nazewnictwa

#### [120] Workflow Architecture Discovery — kroki
**autor:** architect  **status:** open  **data:** 2026-03-21

Proponowany workflow do badania repozytoriów z lotu ptaka:

**Etap 1: Struktura (Glob)**
- Glob `**/*` lub `**/` — lista katalogów i plików
- Zidentyfikuj główne katalogi: src/, tools/, docs/, tests/

**Etap 2: Kluczowe pliki (Read równolegle)**
- README.md — cel projektu, instalacja
- CLAUDE.md lub podobne — instrukcje dla agenta
- Plik manifestu (package.json, pyproject.toml, requirements.txt)
- Główny plik architektury jeśli istnieje

**Etap 3: Głębsze nurkowanie (Read równolegle)**
- Entry points (main.py, index.js)
- Kluczowe moduły biblioteczne (lib/, core/)
- Konfiguracja (config/, .env.example)

**Etap 4: Synteza**
- Zidentyfikuj warstwy systemu
- Narysuj diagram przepływu
- Wypisz komponenty i ich relacje

**Etap 5: Dokument**
- Utwórz SYSTEM_ARCHITECTURE.md lub podobny
- Sekcje: Wizja, Diagram, Warstwy, Komponenty, Słownik

Obserwacja: równoległe Read (do 5 plików naraz) znacząco przyspiesza discovery.

### Narzędzia (tool)

#### [123] Narzędzie do generowania diagramu architektury
**autor:** architect  **status:** open  **data:** 2026-03-21

Podczas discovery ręcznie tworzę diagram ASCII.
Potencjalnie przydatne: narzędzie które skanuje strukturę katalogów
i generuje szkielet diagramu do uzupełnienia.

### Odkrycia (discovery)

#### [167] invocation_log śledzi wywołania agent→agent
**autor:** architect  **status:** open  **data:** 2026-03-22

Tabela do mrowisko_runner — loguje from_role, to_role, depth, turns, cost. 6 rekordów testowych. Będzie kluczowa przy multi-agent.

#### [165] Tabele trace i state są martwe/legacy
**autor:** architect  **status:** open  **data:** 2026-03-22

trace: 0 rekordów, zastąpiona przez tool_calls. state: 34 rekordy, legacy backlog items — dane zmigrowane do backlog/suggestions. Obie do usunięcia przy cleanup.

#### [137] Tabele trace i state są martwe/legacy
**autor:** architect  **status:** open  **data:** 2026-03-22

trace: 0 rekordów, zastąpiona przez tool_calls. state: 34 rekordy, legacy backlog items — dane zmigrowane do backlog/suggestions. Obie do usunięcia przy cleanup.

#### [133] 75k rekordów tool_calls/token_usage — gotowe do analizy
**autor:** architect  **status:** open  **data:** 2026-03-22

tool_calls (30k) i token_usage (44k) to gotowy materiał do analizy zachowania agentów.

Warto zacząć analizować:
- Zużycie tokenów per rola / per sesja
- Wzorce używania narzędzi
- Efektywność cache
- Sesje "drogie" vs "tanie"

Dane są — brakuje dashboardu/raportów.

#### [122] _loom jako seed replikacji
**autor:** architect  **status:** open  **data:** 2026-03-21

Katalog _loom/ zawiera szablony do replikacji Mrowiska w nowych projektach.
To potencjalnie osobny produkt / repo. Nie jest udokumentowany w ARCHITECTURE.md.
Warto rozważyć: wydzielenie _loom do osobnego repo lub lepsze udokumentowanie.

### Obserwacje (observation)

#### [168] Moment strategiczny na refaktor
**autor:** architect  **status:** open  **data:** 2026-03-22

Projekt po stabilizacji promptów, przed skokiem złożoności (multi-agent). Budżet tokenów wykorzystany w 10%. Lepiej przebudować teraz niż po implementacji kolejnej warstwy. ADR-001 to fundament.

#### [166] Bot wymaga hardeningu przed skalowaniem
**autor:** architect  **status:** open  **data:** 2026-03-22

Krytyczny brak: error handling dla Anthropic API. Bot crashuje przy rate limit lub API error. Dodatkowo: God Object w nlp_pipeline.py (218 linii, 7 odpowiedzialności), brak rate limiting per user.

#### [164] Dict-based architecture nie skaluje się
**autor:** architect  **status:** open  **data:** 2026-03-22

Przy rosnącej liczbie agentów i sesji równoległych, podejście proceduralne z dictami staje się nieczytelne i trudne do utrzymania. Logika rozproszona po wielu plikach, brak walidacji typów, brak enkapsulacji. ADR-001 adresuje ten problem.

#### [138] Bot wymaga hardeningu przed skalowaniem
**autor:** architect  **status:** open  **data:** 2026-03-22

Krytyczny brak: error handling dla Anthropic API. Bot crashuje przy rate limit lub API error. Dodatkowo: God Object w nlp_pipeline.py (218 linii, 7 odpowiedzialności), brak rate limiting per user.

#### [131] Granica Architect vs Developer rozmyta
**autor:** architect  **status:** open  **data:** 2026-03-21

Prompt Architekta mówi "Architekt projektuje, Developer implementuje". Ale w praktyce obie role dotykają tych samych plików (tools/, documents/). Propozycja doprecyzowania: Architect = cross-cutting concerns (architektura, NFR, wzorce systemowe), Developer = pojedyncze moduły (implementacja feature, fix, narzędzie).

#### [130] _loom wygląda na porzucony
**autor:** architect  **status:** open  **data:** 2026-03-21

Katalog _loom/ ma minimalną zawartość, ostatnia aktualizacja dawno. W obecnej formie to raczej obietnica niż produkt. Propozycja: albo rozwijamy (dodajemy brakujące szablony, testujemy bootstrap), albo usuwamy/archiwizujemy do czasu gdy będzie priorytetem.

#### [129] Nazewnictwo narzędzi — brak konwencji
**autor:** architect  **status:** open  **data:** 2026-03-21

Widzę: `docs_search` vs `search_bi`, `solutions_save` vs `save_solution`. Prefix (docs_) vs suffix (_search). Przy ~50 skryptach utrudnia nawigację i zapamiętywanie. Propozycja: ustalić konwencję (np. zawsze `<domena>_<akcja>.py`) i zrefaktorować nazwy.

#### [128] tmp/ jako de facto inbox człowieka
**autor:** architect  **status:** open  **data:** 2026-03-21

W tmp/ jest ~40 plików: handoffy, logi, sugestie, eksporty. To tam ląduje wszystko co człowiek powinien przejrzeć. Ale nazwa "tmp" sugeruje "tymczasowe, do usunięcia". Propozycja: przenieść do `inbox/` lub `human/` z lepszą strukturą (podkatalogi per typ: reviews/, exports/, handoffs/).

#### [127] mrowisko.db — podwójna odpowiedzialność
**autor:** architect  **status:** open  **data:** 2026-03-21

Baza trzyma zarówno komunikację agentów (messages, backlog, suggestions) jak i historię sesji Claude Code (conversation, tool_calls, token_usage). To dwa różne concerns w jednym pliku. Przy synchronizacji (#90) może to komplikować — historia sesji jest per-maszyna, komunikacja powinna być shared. Rozważyć podział na dwie bazy lub wyraźną separację tabel.

#### [121] Istniejący ARCHITECTURE.md w documents/dev/
**autor:** architect  **status:** open  **data:** 2026-03-21

documents/dev/ARCHITECTURE.md opisuje szczegółowo Agent ERP i Bot (Faza 1-2).
Brakuje opisu systemu wieloagentowego na wyższym poziomie.
Utworzono documents/architect/SYSTEM_ARCHITECTURE.md jako dokument nadrzędny.
Rozważyć: czy documents/dev/ARCHITECTURE.md powinien być podzbiorem lub linkowany?
