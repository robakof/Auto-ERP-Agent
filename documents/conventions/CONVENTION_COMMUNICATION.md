---
convention_id: communication-convention
version: "1.1"
status: draft  # BLOCKED: czeka na Agent Bus v2 (backlog #187)
created: 2026-03-25
updated: 2026-03-25
author: architect
owner: architect
approver: dawid
audience: [developer, architect, prompt_engineer, erp_specialist, analyst, metodolog]
scope: "Format i zasady komunikacji agent-agent w systemie Mrowisko"
---

# CONVENTION_COMMUNICATION — Komunikacja agent-agent

## TL;DR

- Jeden kanał do jednej funkcji: suggest = obserwacja, backlog = zadanie, send = koordynacja, flag = eskalacja do człowieka, handoff = przekazanie roli
- Przed suggest sprawdź duplikaty: `suggestions --status open --from <rola>` + szukaj po keywords
- Sugestia = zwięzła obserwacja (max 300 znaków treści), nie esej — jeśli wymaga kontekstu, linkuj plik
- Wiadomość send z długą treścią = wskaźnik do pliku, nie inline
- Inbox MUSI być zamknięty (mark-read) po przetworzeniu — to krok workflow, nie opcja
- Korelacja: każda odpowiedź referuje `Re: msg #<id>` — bez tego wątki sierocą
- Sugestie open >14 dni → cykliczny triage (stale review), nie ignorowanie

---

## Zakres

**Pokrywa:**
- Kiedy używać każdego kanału komunikacji (decision tree)
- Format sugestii: typ, tytuł, treść
- Format backlog items: tytuł, treść
- Format wiadomości send i handoff
- Anty-duplikacja: jak sprawdzać przed wysłaniem
- Zamykanie inbox po przetworzeniu

**NIE pokrywa:**
- Implementacja techniczna agent_bus (to Developer)
- Treść merytoryczna sugestii (to ich autorzy)
- Workflow trigger/execution (to CONVENTION_WORKFLOW)

---

## Kontekst

### Problem

Projekt ma 176+ open suggestions. Root cause: brak konwencji sprawia, że każdy agent:
- Pisze sugestie bez struktury — eseje zamiast zwięzłych obserwacji
- Używa `type: observation` na wszystko zamiast właściwego typu
- Duplikuje tę samą obserwację (mark-read pojawił się 3 razy od różnych ról)
- Wysyła pełne raporty inline w wiadomościach zamiast linku do pliku
- Nie zamyka inbox — wiadomości rosną w nieskończoność

### Rozwiązanie

CONVENTION_COMMUNICATION definiuje:
1. **Decision tree** — jasny wybór kanału dla każdej sytuacji
2. **Format per kanał** — co musi zawierać każdy typ komunikatu
3. **Anty-duplikacja** — obowiązkowy check przed każdym suggest
4. **Limity rozmiaru** — max długości dla każdego pola
5. **Lifecycle** — jak zamykać inbox po przetworzeniu

---

## Reguły

### 01R: Decision tree — wybór kanału

Przed wysłaniem komunikatu wybierz kanał:

```
Mam obserwację / regułę / odkrycie z pracy?
  → suggest

Mam zadanie do zrealizowania w przyszłości?
  → backlog-add

Chcę skoordynować działanie z inną rolą (prośba, pytanie, odpowiedź)?
  → send

Napotkałem blokadę wymagającą decyzji człowieka?
  → flag

Kończę fazę i przekazuję pracę innej roli?
  → handoff
```

| Kanał | Kiedy użyć | Kto widzi |
|---|---|---|
| `suggest` | Obserwacja, reguła, odkrycie techniczne, propozycja narzędzia | Wszyscy (triage przez Architekta/Metodologa) |
| `backlog-add` | Konkretne zadanie z zakresem i wartością | Rola owner obszaru |
| `send` | Pytanie, odpowiedź, prośba o review, krótka koordynacja | Adresat |
| `flag` | Blokada wymagająca człowieka: brak decyzji, nieodwracalna zmiana, anomalia | Użytkownik (Dawid) |
| `handoff` | Przekazanie wyniku fazy do innej roli | Adresat |

**Zakaz mieszania:** jedna wiadomość = jeden cel. Nie wysyłaj suggest + pytanie w jednej wiadomości send.

---

### 02R: Format sugestii — typ

Każda sugestia MUSI mieć właściwy typ. Typy i ich znaczenie:

| Typ | Znaczenie | Przykład |
|---|---|---|
| `rule` | Zasada do wdrożenia — zmiana zachowania agenta | "Nie commituj z failing testami" |
| `discovery` | Odkrycie techniczne — nowa wiedza o systemie/narzędziach | "PYTHONIOENCODING stabilniejsze niż encoding=" |
| `observation` | Spostrzeżenie procesowe — co zaobserwowałem, bez recepty | "Inbox overflow — systemowy problem skali" |
| `tool` | Propozycja nowego narzędzia lub rozszerzenia | "Brakuje komendy CLI do X" |

**Reguła wyboru:**
- Masz konkretną regułę do wdrożenia → `rule`
- Odkryłeś jak coś działa technicznie → `discovery`
- Zauważyłeś wzorzec lub problem, nie wiesz jeszcze co z nim zrobić → `observation`
- Chcesz nowe narzędzie lub rozszerzenie istniejącego → `tool`

**Zakaz:** `type: observation` jako default gdy nie wiesz co wybrać. Jeśli niepewny — `observation` jest poprawny tylko gdy naprawdę nie masz recepty.

---

### 03R: Format sugestii — tytuł

Tytuł sugestii MUSI spełniać:

- **Max 80 znaków** (bez przycięcia przez CLI)
- **Format:** `[Co] — [Gdzie/Kiedy]` lub samo `[Co]` jeśli kontekst oczywisty
- **Imperatyw lub opis** — nie pytanie, nie zdanie z "bo"
- **Unikalny** — tytuł powinien jednoznacznie identyfikować obserwację

Dobre przykłady:
```
Mark-read wymaga explicit kroku w workflow, nie pamięci agenta
PYTHONIOENCODING stabilniejsze niż encoding= na Windows
Konwencja formatu != implementacja — pilnuj granicy scope
```

Złe przykłady:
```
Obserwacja z sesji                  ← zbyt ogólny
Może warto dodać X?                 ← pytanie zamiast tytułu
Problem z wiadomościami bo agenci   ← za długi, "bo" to treść, nie tytuł
```

---

### 04R: Format sugestii — treść

Treść sugestii MUSI być zwięzła:

- **Max 300 znaków** dla prostych obserwacji
- **Max 500 znaków** dla złożonych z kontekstem (rule/discovery)
- **Powyżej 500 znaków** → zapisz szczegóły do pliku, w treści umieść link do pliku

Struktura treści dla `rule`:
```
[Obserwacja — co się dzieje]
[Reguła — co z tym zrobić]
[Źródło opcjonalne — gdzie to widziałem]
```

Struktura treści dla `discovery`:
```
[Co odkryłem]
[Dowód / kontekst techniczny — max 1-2 zdania]
```

Struktura treści dla `observation`:
```
[Co zaobserwowałem]
[Impakt — dlaczego to ważne, opcjonalnie]
```

Struktura treści dla `tool`:
```
[Brakuje: opis luki]
[Propozycja: co zbudować]
```

**Zakaz:** Sugestia nie jest dokumentem analitycznym. Nie wklejaj pełnych logów, schematów SQL, długich list punktowanych. Jeśli potrzebujesz więcej — plik + link.

---

### 05R: Anty-duplikacja — obowiązkowy check

Przed każdym `suggest` MUSISZ sprawdzić istniejące sugestie:

```bash
# Krok 1: Sprawdź swoje ostatnie sugestie
py tools/agent_bus_cli.py suggestions --status open --from <rola>

# Krok 2: Jeśli wątpisz że inna rola już to napisała — sprawdź wszystkie open
py tools/agent_bus_cli.py suggestions --status open
```

**Decision:**
- Identyczna obserwacja istnieje → **nie wysyłaj**, zamiast tego użyj `suggest-status` żeby oznaczyć istniejącą jako "wymaga akcji" lub dodaj komentarz przez `send` do właściciela
- Podobna obserwacja z innej perspektywy → możesz wysłać, ale w treści wskaż: "Patrz też #[id]"
- Brak podobnych → wysyłaj

**Merge semantics:** Duplikat to nie śmieć — może nieść dodatkowy kontekst.
- Identyczna → nie wysyłaj nowej. Jeśli masz nowy kontekst → dodaj komentarz do istniejącej przez `send` do ownera.
- Upgrade (observation → rule) → wyślij nową, oznacz starą jako `merged` z referencją: "Merged into #<new_id>".
- Nie kasuj duplikatów bez sprawdzenia czy niosą dodatkową informację.

**Wyjątek:** `rule` nadpisujące wcześniejszą `observation` to nie duplikat — to upgrade. Oznacz starą jako `rejected` lub `merged`.

---

### 06R: Format wiadomości send

Wiadomość send MUSI być krótka i skoncentrowana:

- **Max 500 znaków treści** dla pytań i krótkich koordynacji
- **Powyżej 500 znaków** → zapisz do pliku, wyślij wskaźnik:
  ```
  Raport code review w: documents/human/reports/review_X_YYYY_MM_DD.md
  Pytanie do ciebie: [konkretne pytanie — max 2 zdania]
  ```
- **Jeden cel per wiadomość** — nie łącz raportu z pytaniem i prośbą o review
- **Temat zawsze czytelny** z samej treści — adresat musi wiedzieć co chcesz bez otwierania pliku

Struktura wiadomości send:
```
[Co: jedna linia — cel wiadomości]
[Kontekst: opcjonalne 1-2 zdania]
[Pytanie / prośba: opcjonalne — co oczekujesz w odpowiedzi]
[Link do pliku: jeśli długa treść]
```

---

### 07R: Format backlog items — tytuł

Tytuł backlog item MUSI używać prefiksu obszaru w nawiasie kwadratowym:

```
[TAG] Krótki opis zadania — kontekst
```

Tagi obszarów:
- `[ERP]` — zadania ERP Specialist
- `[BOT]` — Bot / automatyzacja
- `[ARCH]` — architektura (Architect)
- `[DEV]` — narzędzia i implementacja (Developer)
- `[CONV]` — konwencje
- `[PE]` — Prompt Engineer (workflow, prompty)
- `[DATA]` — Analityk Danych

Przykłady:
```
[CONV] P0: CONVENTION_COMMUNICATION — nowa
[DEV] Rozszerzenie agent_bus o mark-read bulk
[ARCH] Audit config-driven architecture
```

---

### 08R: Format backlog items — treść

Treść backlog item MUSI mieć strukturę:

```markdown
## Problem
[Co jest nie tak / czego brakuje — 1-3 zdania]

## Propozycja
[Co zrobić — konkretny scope, nie "poprawić"]

## Źródło
[Skąd to wiadomo — numer sugestii, sesja, obserwacja]
```

**Opcjonalnie:**
- `## Success criteria` — jak sprawdzić że gotowe
- `## Zależności` — co musi być przed

---

### 09R: Format handoff

Handoff MUSI zawierać wszystkie wymagane pola przez CLI:

```bash
py tools/agent_bus_cli.py handoff \
  --from <rola_źródłowa> \
  --to <rola_docelowa> \
  --phase "Nazwa fazy / etapu" \
  --status PASS|FAIL|PARTIAL \
  --summary "Co zrobiono — 1-2 zdania" \
  --next-action "Co musi zrobić adresat — konkretne"
```

**Reguły:**
- `--phase` — nazwa etapu który się zakończył, nie ogólnik
- `--status` — PASS = wszystko gotowe, FAIL = zablokowany, PARTIAL = częściowe
- `--summary` — co zostało zrobione (czas przeszły), nie co planujemy
- `--next-action` — konkretna akcja dla adresata (imperatyw), nie "kontynuuj"

Dobry handoff:
```
phase: "Code review — known_gaps feature"
status: PASS
summary: "Przegląd kodu: 0 critical, 2 warnings (FK pragma, brak testów). Raport w documents/human/reports/review_known_gaps_2026_03_24.md"
next-action: "Napraw W1 (FK pragma linia 206) i W2 (dodaj testy integracyjne) przed merge."
```

Zły handoff:
```
phase: "review"                      ← zbyt ogólne
status: PASS                         ← ale summary mówi "jest kilka problemów"?
summary: "Zrobiłem review."          ← co konkretnie?
next-action: "Zajmij się tym."       ← czym?
```

---

### 10R: Zamykanie inbox po przetworzeniu

Agent MUSI zamknąć wiadomości inbox po przetworzeniu. To jest krok workflow, nie opcja.

**Po przetworzeniu pojedynczej wiadomości:**
```bash
py tools/agent_bus_cli.py mark-read --ids <id>
```

**Po przetworzeniu całego inbox (koniec sesji):**
```bash
py tools/agent_bus_cli.py mark-read --role <rola> --all
```

**Kiedy NIE zamykać:**
- Wiadomość wymaga odpowiedzi której jeszcze nie wysłałeś — zamknij dopiero po wysłaniu
- Wiadomość zawiera zadanie które realizujesz — zamknij po zakończeniu zadania

**Zakaz:** Odkładanie mark-read na "może później". Niezamknięte wiadomości to śmietnik który rośnie wykładniczo — kolejne sesje widzą 20+ unread i triażują od zera.

---

### 11R: Severity i pilność

Kanał dobieraj do pilności:

| Pilność | Kanał | Opis |
|---|---|---|
| Blokada (STOP) | `flag` | Nie możesz kontynuować bez decyzji człowieka |
| Pilne (ta sesja) | `send` | Potrzebujesz odpowiedzi żeby zakończyć zadanie |
| Ważne (następna sesja) | `backlog-add` | Zadanie do realizacji, ale może poczekać |
| Informacyjne | `suggest` | Obserwacja do triage, nie wymaga akcji od razu |

**Zakaz:** Wysyłanie `flag` dla spraw które mogą poczekać do następnej sesji. Flag = blokada, nie "mam pytanie".

---

### 12R: Korelacja wiadomości — referencje do kontekstu

Każda wiadomość `send` lub `handoff` nawiązująca do wcześniejszej komunikacji MUSI
zawierać referencję:

```
Re: msg #292 — ...
Re: backlog #148 — ...
Patrz też: #324 (suggest o tym samym)
```

**Reguły:**
- Odpowiedź na wiadomość → `Re: msg #<id>`
- Nawiązanie do backlog item → `Re: backlog #<id>`
- Powiązana sugestia → `Patrz też: #<id>`
- Handoff po implementacji planu → wskaż ID planu/review: `Plan: #296, Review: #300`

**Dlaczego:** Bez korelacji każda wiadomość jest oderwana od kontekstu. Adresat musi
sam szukać powiązań. FIPA ACL i systemy operacyjne (PagerDuty) traktują korelację
jako pole pierwszej klasy — bo bez niej odpowiedzi sierocą, wątki giną.

---

### 13R: Stale suggestions — TTL i auto-review

Sugestie open dłużej niż 14 dni bez akcji POWINNY być przejrzane:

1. **Triage cykliczny:** Architekt/Metodolog przegląda sugestie starsze niż 14 dni.
2. **Decyzja per sugestia:**
   - Nadal aktualna → oznacz (komentarz: "potwierdzone <data>")
   - Zdezaktualizowana → `suggest-status --id <id> --status rejected --reason "stale"`
   - Zrealizowana ale niezamknięta → `suggest-status --id <id> --status merged`
3. **Wyjątki od auto-review:** sugestie z tagiem `rule` lub `tool` z value `wysoka` — nie wygaszaj bez jawnej decyzji.

**Dlaczego:** GitHub, PagerDuty, Sentry — dojrzałe systemy stosują stale/TTL z wyjątkami.
Bez tego backlog rośnie w nieskończoność (176+ open suggestions to symptom braku tego mechanizmu).

---

## Przykłady

### Przykład 1: Dobra sugestia — rule

```
suggest --from developer \
  --type rule \
  --title "Idempotency guard jako standard w agent_bus" \
  --content "W1 (end_workflow_execution) nauczyło: sprawdź stan przed UPDATE, zwróć info zamiast nadpisywać. Dotyczy wszystkich operacji zmiany statusu."
```

✓ Typ właściwy (rule — zmiana zachowania)
✓ Tytuł konkretny, < 80 znaków
✓ Treść zwięzła, ma strukturę: obserwacja + reguła + zakres

---

### Przykład 2: Dobra sugestia — discovery

```
suggest --from developer \
  --type discovery \
  --title "PYTHONIOENCODING stabilniejsze niż encoding= na Windows" \
  --content "subprocess.run(encoding='utf-8') może failować gdy child process pisze w cp1252. Ustawienie env={'PYTHONIOENCODING': 'utf-8'} działa zawsze."
```

✓ Typ właściwy (discovery — wiedza techniczna)
✓ Tytuł identyfikuje odkrycie jednoznacznie
✓ Treść: co odkryłem + dowód techniczny

---

### Przykład 3: Dobra wiadomość send

```
send --from architect --to prompt_engineer \
  --content "Review CONVENTION_WORKFLOW v1.2 gotowy: NEEDS REVISION (minor). Raport: documents/human/reports/review_convention_workflow_2026_03_25.md. Pytanie: czy usunąć sekcję DB schema (Critical #1)?"
```

✓ Krótka (poniżej 500 znaków)
✓ Wskaźnik do pliku zamiast inline raportu
✓ Jedno konkretne pytanie

---

### Przykład 4: Dobry backlog item

```
Tytuł: [CONV] P0: CONVENTION_COMMUNICATION — nowa

Treść:
## Problem
Brak konwencji komunikacji powoduje chaos: 176+ sugestii bez struktury,
duplikaty, sugestie-eseje, inbox nigdy nie zamykany.

## Propozycja
Stworzyć CONVENTION_COMMUNICATION pokrywającą: decision tree kanałów,
format sugestii/backlog/handoff, anty-duplikację, lifecycle inbox.

## Źródło
Analiza 50 sugestii open + CLAUDE.md (sekcje komunikacyjne).
```

✓ Tag obszaru
✓ Struktura Problem → Propozycja → Źródło
✓ Konkretny scope

---

### Przykład 5: Dobry handoff

```
handoff --from developer --to architect \
  --phase "Implementacja known_gaps feature" \
  --status PASS \
  --summary "Tabela, API (3 metody), CLI (3 komendy), 8 testów. Wszystkie PASS. PR w gałęzi feature/known-gaps." \
  --next-action "Code review przed merge do main. Raport do: documents/human/reports/review_known_gaps_YYYY_MM_DD.md"
```

✓ Faza konkretna
✓ Summary: co zrobiono (czas przeszły)
✓ Next-action: imperatyw z miejscem na output

---

## Antywzorce

### 01AP: Sugestia-esej

**Źle:**
```
suggest --type observation \
  --title "Problem z wiadomościami" \
  --content "Zaobserwowałem że agenci nie zamykają wiadomości.
  Jest to problem ponieważ gdy inbox rośnie to przy następnej sesji
  jest dużo do triage'owania. Myślę że powinniśmy zrobić kilka rzeczy:
  po pierwsze zmienić workflow, po drugie dodać automatyczne zamykanie,
  po trzecie może zmienić session_init żeby wymuszał mark-read...
  [dalsze 400 znaków analizy]"
```

**Dlaczego:** Sugestia to obserwacja, nie dokument analityczny. Wielkie bloki tekstu nie są czytane podczas triage. Propozycja zmian = backlog, nie suggest.

**Dobrze:**
```
suggest --type rule \
  --title "Mark-read wymaga explicit kroku w workflow, nie pamięci agenta" \
  --content "Trzeci raz agenci nie zamykają inbox po sesji. Brak symetrycznego kroku w workflow zakończenia — session_init ładuje, ale nie ma 'zamknij przetworzone'. Propozycja: dodać mark-read do workflow_zamkniecia."
```

---

### 02AP: Duplikat tej samej obserwacji

**Źle:**
```
# Sesja 1 (architect): suggest "Agenci nie zamykają wiadomości" (id: 324)
# Sesja 2 (architect): suggest "Mark-read wymaga explicit kroku" (id: 334)
# Sesja 3 (prompt_engineer): suggest "Zamykanie inbox — kolejny raz" (id: ???)
```

**Dlaczego:** Ta sama obserwacja 3 razy = 3x czas triage, 0x czas naprawy. Backlog rośnie zamiast maleć.

**Dobrze:**
```
# Przed wysłaniem: sprawdź open suggestions
py tools/agent_bus_cli.py suggestions --status open --from architect
# Widzisz #324 o tym samym → nie wysyłaj nowej
# Zamiast tego: suggest-status --id 324 + komentarz "3. powtórzenie — wysoki priorytet"
```

---

### 03AP: Typ observation na wszystko

**Źle:**
```
suggest --type observation --title "Idempotency guard jako standard"
# To jest reguła do wdrożenia, nie obserwacja

suggest --type observation --title "PYTHONIOENCODING stabilniejsze niż encoding="
# To jest discovery techniczne, nie obserwacja

suggest --type observation --title "Brakuje komendy bulk do mark-read"
# To jest propozycja narzędzia, nie obserwacja
```

**Dlaczego:** Wszystko jako observation blokuje triage. Triage'ujący nie wie czy obserwacja wymaga backlog (tool), zmiany reguły (rule), czy tylko zanotowania (observation).

**Dobrze:** Użyj właściwego typu. Patrz reguła 02R (decision tree typów).

---

### 04AP: Wiadomość send z pełnym raportem inline

**Źle:**
```
send --from architect --to developer \
  --content "Zrobiłem code review. Oto wyniki:

  ## Critical Issues
  - Brak FK pragma w linii 206
  - Brak obsługi None w get_gaps()

  ## Warnings
  - Brak testów integracyjnych
  - Zbyt długa funkcja cmd_gap_add (45 linii)

  ## Suggestions
  [kolejne 300 znaków...]"
```

**Dlaczego:** Wiadomości send są przechowywane w DB, nie w plikach. Pełny raport inline = nie można linkować, nie można wersjonować, kontekst adresata zostaje zajęty całością.

**Dobrze:**
```
send --from architect --to developer \
  --content "Code review known_gaps gotowy: NEEDS REVISION (2 critical, 1 warning). Raport: documents/human/reports/review_known_gaps_2026_03_25.md"
```

---

### 05AP: Inbox nigdy nie zamykany

**Źle:**
```
# Sesja 1: session_init → inbox: 3 wiadomości → przetworzone → NIE zamknięte
# Sesja 2: session_init → inbox: 3 stare + 2 nowe = 5 wiadomości → część przetworzona → NIE zamknięte
# Sesja N: session_init → inbox: 20+ wiadomości → agent triaży od zera przy każdej sesji
```

**Dlaczego:** Niezamknięte wiadomości to kumulowany dług kontekstowy. Każda sesja traci czas na retriage. Po 10 sesjach inbox jest bezużyteczny.

**Dobrze:**
```bash
# Na końcu każdej sesji:
py tools/agent_bus_cli.py mark-read --role architect --all
```

---

### 06AP: Flag zamiast backlog dla spraw niekrytycznych

**Źle:**
```
flag --from erp_specialist \
  --reason "Nie wiem czy użyć JOIN czy subquery w tym zapytaniu.
  Może warto zapytać użytkownika?"
```

**Dlaczego:** Flag = blokada. Użytkownik może nie być dostępny przez godziny. Pytanie o SQL nie jest blokadą — eskaluj do Architekta przez `send` lub zapisz jako backlog z pytaniem.

**Dobrze:**
```bash
# Pytanie do kolegi:
send --from erp_specialist --to architect --content "Dylemat: JOIN vs subquery dla [kontekst]. Jakie trade-offy?"

# Lub jeśli może poczekać:
backlog-add --title "[ERP] Dylemat JOIN vs subquery — potrzebuję decyzji arch" --area ERP
```

---

### 07AP: Delegation loops i hotspoty komunikacyjne

**Źle (delegation loop):**
```
Architect → send do Developer: "Zrób X"
Developer → send do Architect: "Nie jestem pewien, co myślisz?"
Architect → send do Developer: "Sprawdź Y i zdecyduj"
Developer → send do Architect: "Y mówi Z, ale nie wiem czy..."
# Pętla bez konkluzji — 4 wiadomości, 0 akcji
```

**Źle (hotspot):**
```
ERP Specialist → send do Developer (pytanie)
Analyst → send do Developer (pytanie)
Architect → send do Developer (review)
PE → send do Developer (zmiana workflow)
# Developer = bottleneck, 4 role czekają na jedną
```

**Dlaczego:** Badania MAS (Detection of Undesirable Communication Patterns) pokazują że
niezbalansowana komunikacja degraduje QoS. CrewAI dokumentuje delegation loops jako realny
problem operacyjny. Każdy back-and-forth bez decyzji to zmarnowany kontekst obu stron.

**Dobrze (unikanie pętli):**
```
# Zamiast pytać "co myślisz?" — podaj propozycję z trade-offami:
send --from developer --to architect \
  --content "Dylemat: JOIN vs subquery. Trade-off: JOIN szybszy o 30%, subquery czytelniejszy. Proponuję JOIN. APPROVE/REJECT?"
```

**Dobrze (unikanie hotspotów):**
```
# Spread load — eskaluj do właściwej roli, nie domyślnie do Developera
# Pytanie architektoniczne → Architect (nie Developer)
# Pytanie o prompt → PE (nie Developer)
# Pytanie o ERP → ERP Specialist (nie Developer)
```

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.1 | 2026-03-25 | Enrichment z researchu: 12R (korelacja wiadomości), 13R (stale/TTL sugestii), 07AP (delegation loops/hotspoty), merge semantics w 05R |
| 1.0 | 2026-03-25 | Wersja początkowa — decision tree, formaty, anty-duplikacja, lifecycle inbox |
