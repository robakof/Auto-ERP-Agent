# Diagnoza startu Dispatchera — 2026-03-29

## TL;DR

Dispatcher startował za długo (orientacja + dashboard), a potem autonomicznie spawnował
agentów zamiast czekać na komendę. Podwójny spawn przez błąd w narzędziach.
Poniżej: co się stało, co poszło źle, co trzeba zmienić.

---

## Co się stało — timeline

| Krok | Co                                                   | Czas*     | Problem?                                                                                                                                                                                                      |
| ---- | ---------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `session_init --role dispatcher`                     | ok        | to                                                                                                                                                                                                            |
| 2    | `inbox-summary` + `live-agents` + `handoffs-pending` | ok        | i to powinno być jednym session itnit -> kompresja plików .md. Wywoływanie każdego osbnego "zapoznania" spowalnia                                                                                             |
| 3    | `render_dashboard.py`                                | ok        | Trzeba uruchomić i tyle, nie czekać, nie czytać. Albo się podniosło albo nie.                                                                                                                                 |
| 4    | Read `Kolejka.md` + `Mrowisko.md`                    | zbędne    | Dashboard dla człowieka, nie dla agenta                                                                                                                                                                       |
| 5    | Read `LIFECYCLE_TOOLS.md`                            | zbędne    | Znałem już komendy z DISPATCHER.md -> i powinno ci to wystarczyć. Plik tools to dokumentacja techniczna bardziej dla developera lub PE. Czy to pomysł aby zacząć oznaczać dokumentację pod kątem jakościowym? |
| 6    | Read handoff #519                                    | ok        | Orientacja przed spawnem -> ostatni handogg nie odczyany może iść w seesion init. Render dashboard zresztą też .                                                                                              |
| 7    | Read backlog #199, #200                              | zbędne    | Wystarczył tytuł z backlogu -> Tytuły lecą przy pomocy session init.                                                                                                                                          |
| 8    | `spawn` developer + PE via agent_bus_cli             | ok**      | Ale bez zatwierdzenia - nie bez wyraźnej prosy z mojej strony                                                                                                                                                 |
| 9    | `vscode_uri.py` ponownie dla obu                     | BUG       | Duplikaty — spawn już otworzył URI<br>do naprawy                                                                                                                                                              |
| 10   | Próba zatrzymania duplikatów                         | naprawcze | User musiał killować ręcznie                                                                                                                                                                                  |

*Czasy relatywne — sesja od 20:58 do ~21:02 (4 minuty na orientację + spawn)

---

## Problemy zidentyfikowane

### P1: Zbyt rozbudowana orientacja
- Dashboard render + Read dashboard plików + Read LIFECYCLE_TOOLS + Read handoff + Read backlog items
- Agent czytał pliki które nie były potrzebne do raportu "Gotowy"
- **Koszt:** ~2 minuty + tokeny na zbędne Read

### P2: Autonomiczny spawn bez zatwierdzenia
- DISPATCHER.md mówi: "NIE spawaj autonomicznie (v1). Wyjątek: tryb autonomiczny."
- User napisał "[TRYB AUTONOMICZNY]" — agent potraktował to jako autoryzację
- **Problem:** "Podnieś się" ≠ "spawaj agentów". Podnieś się = bądź gotowy.

### P3: Spawn zamiast resume
- Nie sprawdziłem czy istnieją stopped sesje do wznowienia
- Spawn = nowa sesja = pełny koszt session_init + ładowanie promptu
- Resume = kontynuacja istniejącej sesji = tańsze
- **Reguła:** ZAWSZE resume > spawn

### P4: Podwójny spawn (bug proceduralny)
- `agent_bus_cli.py spawn` automatycznie otwiera URI w VS Code (tworzy terminal)
- Potem wywołałem `vscode_uri.py --command spawnAgent` — drugi terminal, drugi agent
- Wynik: 2x developer + 2x PE = 4 agenty zamiast 2
- **Fix:** po `spawn` NIE wywoływać `vscode_uri.py`

### P5: Brak modelu kosztów w promptach
- Dispatcher nie ma w instrukcjach informacji o koszcie spawn vs resume
- Brak heurystyki: "spawn nowej sesji ≈ 30-60s + ~5% kontekstu na init"
- Brak reguły: "preferuj istniejące sesje"

---

## Akcje do wdrożenia (zatwierdzone przez człowieka)

### A1: session_init kompresja — Dev task
`session_init --role dispatcher` powinien zwracać w jednym wywołaniu:
- Prompt roli (jak teraz)
- inbox-summary (zamiast osobnego CLI call)
- live-agents (zamiast osobnego CLI call)
- handoffs-pending (zamiast osobnego CLI call)
- Ostatni nieodczytany handoff dla roli (pełna treść)
- render_dashboard (fire-and-forget, bez czytania outputu)

**Cel:** Dispatcher startuje jednym wywołaniem, nie serią 5+ komend.
**Owner:** Developer (zmiana w `session_init.py`)

### A2: "Podnieś się" = session_init + "Gotowy" — PE task
Zdefiniować w DISPATCHER.md sekcji `<session_start>`:
- "Podnieś się" = `session_init` → powiedz "Gotowy" → STOP, czekaj na instrukcję
- NIE czytaj dodatkowych plików (dashboard, LIFECYCLE_TOOLS, backlog items)
- NIE spawnuj agentów bez wyraźnej prośby człowieka
- Dashboard renderujesz ale nie czytasz — to output dla człowieka

### A3: Spawn policy — resume > spawn — PE task
Dodać do DISPATCHER.md regułę:
- Spawn jest DROGI (czas + kontekst). Zawsze preferuj istniejące sesje.
- Przed spawnem: `live-agents` → czy jest stopped sesja danej roli?
  - Tak → `resume` (tańsze)
  - Nie → `spawn` (droższe, tylko gdy konieczne)
- Spawn WYŁĄCZNIE na wyraźną prośbę człowieka (v1)

### A4: Podwójny spawn guard — PE task (+ Dev bug)
- `agent_bus_cli.py spawn` otwiera URI automatycznie — NIE wywoływać `vscode_uri.py` po spawn
- Dodać notę w DISPATCHER.md sekcji `<tools>`
- **Dev bug:** rozważyć guard w `spawn` CLI żeby wykrywać duplikaty (ta sama rola w ciągu N sekund)

### A5: Tryb autonomiczny — doprecyzować semantykę — PE task
Obecna definicja "[TRYB AUTONOMICZNY]" jest niejednoznaczna.
- Dispatcher traktował to jako autoryzację do spawnu — źle
- Doprecyzować: tryb autonomiczny = realizuj task sam, ale spawn agentów = osobna autoryzacja
- Rozdzielić: autonomia własnej pracy ≠ autonomia spawnu

### A6: Tagowanie dokumentacji per audience (pomysł do zbudżetowania)
User zasugerował: oznaczać dokumenty pod kątem "dla kogo" (Dev, PE, Dispatcher...).
Cel: agent nie ładuje dokumentów które nie są dla niego.
**Status:** pomysł — wymaga analizy effort/value

---

## Docelowy model (wizja usera)

Dispatcher na nasłuchu — docelowo nie spawnuje proaktywnie:
- Czeka na wywołanie od człowieka
- Gdy wywołany — uruchamia agenta (resume > spawn)
- Pracuje na otwartych, nie wykończonych sesjach
- Przyzywanie agenta jest DROGIE — czas i kontekst
