---
convention_id: prompt-convention
version: "1.0"
status: draft
created: 2026-03-25
updated: 2026-03-25
author: architect
owner: prompt_engineer
approver: dawid
audience: [prompt_engineer, architect, metodolog]
scope: "Definiuje strukturę, składnię i zasady pisania promptów agentów w projekcie Mrowisko"
---

# CONVENTION_PROMPT — Konwencja pisania promptów agentów

## TL;DR

- System promptowy ma 5 warstw: CLAUDE.md → prompt roli → workflow → domain pack → runtime
- Formatowanie: XML tags na granicach sekcji, Markdown wewnątrz, YAML frontmatter dla metadata
- Hierarchia ważności: krytyczne reguły wysoko, checklista na dole (krawędzie kontekstu)
- Szablon roli: mission → scope → critical_rules → session_start → workflow → tools → escalation → end_of_turn_checklist
- Workflow: osobny format bez XML tags, z hierarchiczną numeracją dziesiętną
- Zmiana promptu wymaga identyfikacji failure mode lub celu jakościowego

---

## Zakres

**Pokrywa:**
- Architektura warstw systemu promptowego
- Format i składnia promptów ról (sekcje, XML tags, YAML)
- Hierarchia ważności elementów w dokumencie
- Szablon promptu roli (wymagane i opcjonalne sekcje)
- Zasady rozmieszczania treści między warstwami
- Szablon dokumentu workflow
- Zasady zmian i wymiary oceny jakości promptu
- Prompty badawcze (research prompts) — output contract
- Czego unikać (antywzorce)

**NIE pokrywa:**
- Treści konkretnych promptów ról (to ownerzy poszczególnych ról)
- Treści konkretnych workflow (to ich ownerzy)
- Tooling do walidacji promptów (przyszłość)
- Formatu konwencji jako dokumentu (to CONVENTION_META)

---

## Kontekst

### Problem

Bez CONVENTION_PROMPT:
- Każdy prompt roli ma inną strukturę — agent nie wie gdzie szukać krytycznych reguł
- Reguły rozsiane między warstwami — duplikacje, sprzeczności
- Brak jasnych zasad co gdzie trafia — prompt roli vs workflow vs CLAUDE.md
- Arbitralny format workflow — nie parseable, trudny do review

### Rozwiązanie

CONVENTION_PROMPT definiuje:
1. **5-warstwowy model** — jasna hierarchia gdzie żyje każda reguła
2. **Hybrid XML/Markdown** — XML dla granic sekcji, Markdown dla czytelności
3. **Pozycja = ważność** — model najlepiej przetwarza informację na krawędziach kontekstu
4. **Jednolity szablon roli** — każdy prompt ma te same sekcje w tej samej kolejności
5. **Oddzielny format workflow** — procesowy, bez XML tags

---

## Reguły

### 01R: Architektura warstw — reguła żyje na najwyższym węźle

System promptowy ma 5 warstw (od ogółu do szczegółu):

```
CLAUDE.md (shared_base)        ← zawsze ładowany, wspólne reguły
  └─ Role prompt (.md)         ← ładowany per rola (ERP_SPECIALIST.md, ANALYST.md...)
       └─ Workflow (.md)       ← ładowany per typ zadania (bi_view_creation_workflow.md...)
            └─ Domain pack     ← ładowany per kontekst (ERP_SCHEMA_PATTERNS.md...)
                 └─ Runtime    ← inbox, backlog, stan zadania
```

**Zasady warstw:**
- Reguła żyje na najwyższym węźle gdzie obowiązuje wszystkich odbiorców.
- Nie powielaj reguły w niższej warstwie — odwołuj się do wyższej.
- Domain pack i workflow ładowane na żądanie, nie wbudowane w rolę.

**Mapowanie treści na warstwy:**

| Treść | Warstwa | Plik |
|---|---|---|
| Eskalacja, logowanie, agent_bus, git, bash rules | shared_base | `CLAUDE.md` |
| Cel roli, zakres, reguły krytyczne, narzędzia roli | role prompt | `{ROLA}.md` |
| Fazy, gates, forbidden, exit conditions | workflow | `workflows/*.md` |
| Wzorce SQL, konwersje, enumy, schematy | domain pack | `documents/erp_specialist/ERP_*.md` |
| Inbox, backlog items, stan zadania | runtime | Ładowane dynamicznie na starcie sesji |

---

### 02R: Test przynależności — przed dodaniem reguły sprawdź warstwę

Przed dodaniem reguły do pliku:
1. Dotyczy wszystkich ról? → `CLAUDE.md`
2. Dotyczy jednej roli, zawsze? → prompt roli
3. Dotyczy jednego typu zadania? → workflow
4. Dotyczy wiedzy dziedzinowej? → domain pack
5. Zmienia się między sesjami? → runtime (nie wpisuj do promptu)

---

### 03R: Formatowanie — hybrid XML/Markdown

Stosuj **hybrid XML/Markdown**:
- **XML tags** dla granic logicznych sekcji (`<role>`, `<scope>`, `<critical_rules>`...)
- **Markdown** wewnątrz sekcji (listy, tabele, numeracja, nagłówki `###`)
- **YAML frontmatter** (`---` blok) dla metadanych routingu

**Dlaczego XML na granicach:**
- Anthropic wprost rekomenduje XML tags do oddzielania sekcji w złożonych promptach.
- Pomagają modelowi rozpoznawać strukturę i odróżniać typy informacji.
- "Lost in the Middle" — jasne granice sekcji zmniejszają ryzyko utraty salience.
- Lepsze niż `##` headers gdy model musi odróżnić wiele podobnych sekcji.

**Dlaczego Markdown wewnątrz:**
- Czytelny dla człowieka (edycja, review).
- Numerowane listy, tabele, checkboxy — naturalne w Markdown.
- XML wewnątrz sekcji nie dodaje wartości, tylko szum.

**Ważne:** Markdown `##` headers jako granic sekcji w promptach ról — nie używaj. Używaj XML tags.

---

### 04R: Hierarchia ważności — pozycja = salience

Pozycja w pliku = ważność. Od góry:
1. Kim jesteś + co dostarczasz (opening statement)
2. Reguły krytyczne (wysoko = wysoka salience)
3. Workflow (środek)
4. Narzędzia i referencje (nisko = rzadko potrzebne in extenso)
5. Checklista końcowa (na dole = ostatnia rzecz przed odpowiedzią)

**Uzasadnienie:** Badania "Lost in the Middle" pokazują, że model najlepiej
wykorzystuje informację na początku i na końcu kontekstu. Krytyczne reguły
wysoko, checklista na dole — dwie krawędzie.

---

### 05R: Szablon promptu roli — wymagane sekcje w kolejności

Każdy prompt roli ma następujący układ sekcji (w tej kolejności):

```md
# {Nazwa roli} — instrukcje operacyjne

{1-2 zdania: kim jesteś, co dostarczasz. Nie filozofia — konkret.}

---
agent_id: {stable_id}
role_type: {executor|reviewer|meta}
escalates_to: {developer|methodologist|human}
allowed_tools: [...]
disallowed_tools: [...]
---

<mission>
{2-4 mierzalne kryteria sukcesu roli.}
</mission>

<scope>
W zakresie:
1. ...

Poza zakresem:
1. ...
</scope>

<critical_rules>
1. {Warunek → działanie. Afirmatywnie.}
2. ...
(maks 8-10 reguł)
</critical_rules>

<session_start>
1. {Co zrobić na starcie sesji — inbox, backlog, walidacja.}
2. ...
</session_start>

<workflow>
{Numerowane kroki głównego procesu.
 Jeśli rola ma wiele typów zadań — tabela routingu do osobnych plików workflow.}
</workflow>

<tools>
{Tylko narzędzia specyficzne dla roli.
 Format: komenda → wejście/wyjście (1 linia per narzędzie).
 Narzędzia wspólne (agent_bus, git_commit) — nie powtarzaj, są w CLAUDE.md.}
</tools>

<escalation>
{Kiedy przerywasz i pytasz. Numerowana lista warunków.}
</escalation>

<end_of_turn_checklist>
1. {Punkt kontrolny przed wysłaniem odpowiedzi.}
2. ...
(maks 3-5 punktów)
</end_of_turn_checklist>
```

---

### 06R: Sekcje opcjonalne promptu roli — dodawaj tylko gdy potrzebne

Dodawaj tylko gdy rola ich wymaga:

- **`<persona>`** — profil psychologiczny roli (charakter, styl myślenia, podejście do pracy).
  Umieść po `<mission>`, przed `<scope>`. Dla ról gdzie charakter wpływa na zachowanie
  (np. Architekt: wywrotowy perfekcjonista). Persona opisuje JAK rola działa, nie CO robi.
  UWAGA: Few-shot examples często skuteczniejsze od długiego opisu persony.

- **`<behavior_examples>`** — 2-5 scenariuszy konkretnych zachowań. Format:
  ```
  *Scenariusz: [kontekst]*
  ✗ [złe zachowanie]
  ✓ [dobre zachowanie]
  ```
  Anthropic research: few-shot examples skuteczniejsze od długiego opisu persony.
  Preferuj examples przed dodawaniem kolejnych linii do `<persona>`.

- **`<gates>`** — warunki wejścia/wyjścia (reviewer, workflow-heavy roles)

- **`<output_contract>`** — sztywny format wyniku (reviewer, meta roles)

- **`<examples>`** — 1-3 kanoniczne edge case'y (gdy zero-shot nie wystarcza)

- **`<decision_policy>`** — reguły rozstrzygania konfliktów (orkiestrator)

- **`<context_management>`** — zasady zarządzania kontekstem (role z dużymi outputami)

---

### 07R: Styl pisania reguł

- **Afirmatywne reguły**: "Przed zmianą sprawdź gate" zamiast "Nie zmieniaj bez gate'a".
- **Jedna reguła = jeden punkt**. Dwa zdania w punkcie → rozbij na dwa punkty.
- **Bez uzasadnień inline** w regułach krytycznych. Jeśli potrzebne — komentarz
  HTML `<!-- dlaczego -->` lub sekcja "Kontekst decyzji" na dole dokumentu.
- **Bez emoji** (dozwolone: ✓, ✗).
- Przykłady: maks 1-3, tylko edge case'y.

---

### 08R: Numeracja kroków workflow

- **Kroki workflow z fazami:** numer fazy + litera kroku: `1a, 1b, 2a, 2b...`
- **Listy niezależne od faz:** numeracja prosta: `1, 2, 3...`
- Wzorzec: `bi_view_creation_workflow.md` (Faza 0, Faza 1a, Faza 1b...)

---

### 09R: Szablon workflow — format i układ

Workflow (ładowane per typ zadania) mają własny układ — **nie używają XML tags**:

```md
# Workflow: {Nazwa}

{1 zdanie: czemu służy ten workflow.}
Statusy faz: `PASS` | `BLOCKED` | `ESCALATE`

---

## Faza N — {Nazwa}

**Owner:** {rola}

### Steps
1. ...

### Forbidden
- ...

### Exit gate
PASS jeśli:
- [ ] ...
BLOCKED jeśli:
- [ ] ...
```

**Dlaczego workflow nie używa XML tags:**
Workflow jest dokumentem procesowym, nie promptem roli.
XML tags rezerwujemy dla promptów ról gdzie model musi odróżniać typy instrukcji.

---

### 10R: Zasady zmian promptu — tylko przy zidentyfikowanym failure mode

1. Zmiana wymaga identyfikacji failure mode lub celu jakościowego.
2. Dobierz skalę: patch (1 blok) vs refaktor (cała struktura).
3. Każda zmiana = commit + diff + uzasadnienie + plan testów.
4. Patch nie może pogarszać dwóch wymiarów żeby poprawić jeden.
5. Gdy problem nie leży w prompcie → ESCALATE_ARCHITECTURE.

---

### 11R: Minimal viable prompt przy nowej roli

Przy tworzeniu nowej roli:
- Minimum: mission, scope, critical rules (5-8), output contract, minimal workflow routing
- NIE pisz szczegółowych kroków workflow zanim nie zobaczysz jak rola działa w praktyce
- Workflow nabudowuj iteracyjnie na podstawie rzeczywistych sesji i failure modes
- Elastyczność > sztywność. Agent uczy się w praktyce, nie z góry zaprojektowanych scenariuszy.

---

### 12R: Wymiary oceny jakości promptu

Przy review lub zmianie promptu oceń sześć wymiarów:

1. **Clarity** — jedna sekcja = jedna odpowiedzialność?
2. **Salience** — reguły krytyczne wysoko i osobno?
3. **Scope** — nie miesza odpowiedzialności ról?
4. **Gate reliability** — warunki wejścia/wyjścia testowalne?
5. **Output determinism** — format wyniku jednoznaczny?
6. **Modularity** — domain knowledge odłączalne?

---

### 13R: Research prompts — obowiązkowy output contract

Każdy prompt do zewnętrznego researchera musi zawierać sekcję **Output contract**:

```markdown
## Output contract

Zapisz wyniki do pliku: `documents/<rola>/research_results_<temat>.md`

Struktura pliku wynikowego:
# Research: [tytuł]
Data: YYYY-MM-DD

## TL;DR — 3-5 najbardziej obiecujących kierunków
## Wyniki per obszar badawczy
(sekcje odpowiadające pytaniom; dla każdego: opis + siła dowodów [empiryczne / praktyczne / spekulacja])
## Co nierozwiązane / otwarte pytania
## Źródła / odniesienia

Czego NIE rób:
- Nie oceniaj dopasowania do naszego systemu — to osobny krok
- Nie dawaj jednej odpowiedzi — dawaj pole możliwości
- Nie skracaj gdy brakuje danych — zaznacz lukę
```

**Lokalizacja:**
- Prompt: `documents/<rola>/research_prompt_<temat>.md`
- Wyniki: `documents/<rola>/research_results_<temat>.md`

---

## Przykłady

### Przykład 1: Minimalny prompt roli (nowa rola)

```md
# Analityk Danych — instrukcje operacyjne

Analizujesz jakość danych w systemie ERP i dostarczasz raporty z wnioskami.

---
agent_id: analyst
role_type: reviewer
escalates_to: developer
allowed_tools: [Read, Grep, Glob, Bash, agent_bus_cli]
disallowed_tools: []
---

<mission>
1. Zidentyfikuj anomalie w danych ERP.
2. Dostarcz raport z wnioskami i rekomendacjami.
3. Eskaluj do Developera gdy problem wymaga zmiany schematu.
</mission>

<scope>
W zakresie:
1. Analiza jakości danych w widokach BI.
2. Weryfikacja spójności między tabelami.

Poza zakresem:
1. Zmiany w SQL lub schemacie ERP.
2. Konfiguracja okien ERP.
</scope>

<critical_rules>
1. Przed analizą załaduj schemat z ERP_SCHEMA_PATTERNS.md.
2. Każdy wniosek poprzyj konkretnym przykładem (ID rekordu, wartość).
3. Anomalię bez pewnej diagnozy opisz jako obserwację, nie wniosek.
</critical_rules>

<session_start>
1. Sprawdź inbox: python tools/agent_bus_cli.py inbox --role analyst
2. Sprawdź backlog: python tools/agent_bus_cli.py backlog --area ERP
</session_start>

<workflow>
Routing:
- Analiza jakości danych → Sekcja A
- Przegląd widoku BI → Sekcja B
</workflow>

<tools>
python tools/agent_bus_cli.py suggest --from analyst --content-file tmp/s.md
  → Zapisz obserwację jako sugestię do przeglądu przez Prompt Engineera.
</tools>

<escalation>
1. Anomalia wymaga zmiany schematu → ESCALATE do Developer.
2. Brak dostępu do danych → ESCALATE do ERP Specialist.
</escalation>

<end_of_turn_checklist>
1. Czy każdy wniosek ma konkretny przykład?
2. Czy obserwacje bez pewnej diagnozy są oznaczone jako "obserwacja"?
3. Czy raport zapisany do pliku (nie inline w czacie)?
</end_of_turn_checklist>
```

---

### Przykład 2: Sekcja `<behavior_examples>` — few-shot zamiast persona

Gdy rola ma specyficzne zachowanie trudne do opisania wprost, użyj `<behavior_examples>`:

```md
<behavior_examples>

*Scenariusz: Użytkownik prosi o kolumnę ERP bez podania okna docelowego.*
✗ "Tworzę kolumnę dla domyślnego okna Transakcje."
✓ "Proszę o podanie okna docelowego — bez tego nie mogę wybrować właściwego widoku BI."

*Scenariusz: SQL generuje wynik, ale wydajność jest nieznana.*
✗ "SQL gotowy, zapisano do pliku."
✓ "SQL gotowy. Nie testowałem wydajności na produkcji — zweryfikuj EXPLAIN ANALYZE przed wdrożeniem."

</behavior_examples>
```

---

### Przykład 3: Poziomy ładowania promptu

Agenci ładują prompty na odpowiedniej głębokości:

- **Start sesji:** YAML frontmatter + `<mission>` + `<critical_rules>` (~200 tokenów)
- **Wejście w workflow:** + `<scope>` + `<workflow>` + `<tools>` (~500 tokenów)
- **Nowa rola / onboarding:** Pełny dokument (~1000+ tokenów)

To jest guideline, nie wymuszane przez tooling.

---

### Przykład 4: Test przynależności w praktyce

Reguła: "Nie commituj z failing testami."

- Dotyczy wszystkich ról? ✓ → trafia do `CLAUDE.md`
- NIE do promptu roli ERP Specialist, NIE do workflow

Reguła: "Przed wygenerowaniem SQL załaduj ERP_SCHEMA_PATTERNS.md."

- Dotyczy wszystkich ról? ✗
- Dotyczy jednej roli, zawsze? ✓ (ERP Specialist) → trafia do `ERP_SPECIALIST.md`

Reguła: "W Fazie Discovery sprawdź czy widok nie istnieje już w bazie."

- Dotyczy jednego typu zadania? ✓ (workflow tworzenia widoku BI) → trafia do workflow

---

## Antywzorce

### 01AP: Markdown headers zamiast XML tags w prompcie roli

**Źle:**
```markdown
## Krytyczne reguły

1. Nie commituj bez testów.
2. Eskaluj do Developera gdy...

## Workflow

1. Zainicjalizuj sesję.
```

**Dlaczego:** Markdown `##` headers nie oddzielają logicznie sekcji dla modelu — model
traktuje je jak ciągły tekst. Ryzyko "Lost in the Middle" — krytyczne reguły mogą zgubić salience
gdy prompt jest długi.

**Dobrze:**
```markdown
<critical_rules>
1. Nie commituj bez testów.
2. Eskaluj do Developera gdy...
</critical_rules>

<workflow>
1. Zainicjalizuj sesję.
</workflow>
```

---

### 02AP: Reguła nie na swojej warstwie — duplikacja

**Źle:**
```markdown
# ERP_SPECIALIST.md

<critical_rules>
...
7. Nie używaj git commit bezpośrednio — używaj git_commit.py.  ← duplikat z CLAUDE.md
8. Eskaluj do użytkownika zamiast zgadywać.                   ← duplikat z CLAUDE.md
</critical_rules>
```

**Dlaczego:** Duplikacja tworzy ryzyko rozjazdu. Gdy CLAUDE.md się zmieni, lokalna kopia pozostanie
stara. Agent może dostać sprzeczne instrukcje.

**Dobrze:**
```markdown
<critical_rules>
7. [reguła specyficzna dla ERP Specialist]
8. [reguła specyficzna dla ERP Specialist]
</critical_rules>
<!-- reguły wspólne (git, eskalacja) są w CLAUDE.md — nie powtarzaj -->
```

---

### 03AP: Uzasadnienia inline w regułach krytycznych

**Źle:**
```markdown
<critical_rules>
1. Przed zmianą schematu sprawdź gate, bo w przeszłości zdarzały się rollbacki
   które kosztowały godziny pracy i dlatego wprowadziliśmy tę zasadę po incydencie
   z widokiem TransakcjeBI w marcu 2025.
</critical_rules>
```

**Dlaczego:** Agent nie ma pamięci między sesjami — historia incydentu nie pomaga.
Długi punkt gubi właściwe działanie w narracji. Salience reguły spada.

**Dobrze:**
```markdown
<critical_rules>
1. Przed zmianą schematu sprawdź exit gate poprzedniej fazy.
</critical_rules>

<!-- Historia: rollback TransakcjeBI 2025-03 — dokumentacja w ADR-007 -->
```

---

### 04AP: XML tags w workflow

**Źle:**
```markdown
# Workflow: Tworzenie kolumny BI

<phase>
## Faza 1 — Discovery

<steps>
1. Załaduj schemat.
2. Sprawdź czy kolumna istnieje.
</steps>

<exit_gate>
PASS jeśli schemat załadowany.
</exit_gate>
</phase>
```

**Dlaczego:** Workflow to dokument procesowy — XML tags nie dodają wartości,
tylko utrudniają edycję i review. XML tags rezerwujemy dla promptów ról.

**Dobrze:**
```markdown
# Workflow: Tworzenie kolumny BI

## Faza 1 — Discovery

**Owner:** erp_specialist

### Steps
1. Załaduj schemat.
2. Sprawdź czy kolumna istnieje.

### Exit gate
PASS jeśli schemat załadowany.
```

---

### 05AP: Sekcja "na zapas" opisująca narzędzia które nie istnieją

**Źle:**
```markdown
<tools>
python tools/schema_validator.py --validate  → waliduje schemat (TODO: do zbudowania)
python tools/sql_formatter.py --format       → formatuje SQL (planowane)
python tools/erp_connector.py --connect      → łączy z ERP (future)
</tools>
```

**Dlaczego:** Agent próbuje używać narzędzi które nie istnieją. Sekcja tools to kontrakt,
nie roadmapa.

**Dobrze:**
```markdown
<tools>
<!-- Tylko narzędzia które ISTNIEJĄ i działają -->
python tools/agent_bus_cli.py suggest --from erp_specialist --content-file tmp/s.md
  → Zapisz sugestię do przeglądu przez Prompt Engineera.
</tools>
```

---

### 06AP: Prose zamiast numerowanych kroków

**Źle:**
```markdown
<workflow>
Na początku sesji należy sprawdzić inbox i backlog. Następnie, w zależności od
tego co znajdziesz, podejmij odpowiednie działania. Jeśli jest zadanie ERP to
zacznij od załadowania schematu, a jeśli jest zadanie analityczne to zacznij
od przeglądu widoków. Pamiętaj też żeby logować postęp.
</workflow>
```

**Dlaczego:** Model nie może wykonać prozy krok po kroku. Brak jasnych warunków,
brak kolejności, brak punktów decyzyjnych.

**Dobrze:**
```markdown
<workflow>
1. Sprawdź inbox: python tools/agent_bus_cli.py inbox --role erp_specialist
2. Sprawdź backlog: python tools/agent_bus_cli.py backlog --area ERP
3. Routing:
   - Zadanie ERP → załaduj ERP_SCHEMA_PATTERNS.md → Faza Discovery
   - Zadanie analityczne → załaduj widoki BI → Faza Analiza
4. Loguj kroki: workflow-start, step-log, workflow-end
</workflow>
```

---

### 07AP: Mieszanie instrukcji dla agenta z esejem dla człowieka

**Źle:**
```markdown
# ERP_SPECIALIST.md

## Kontekst projektu

Mrowisko to ambitny projekt automatyzacji ERP. Zaczęliśmy od prostej konfiguracji
kolumn i stopniowo rozszerzamy zakres. Filozofia projektu zakłada że agent powinien
rozumieć biznesowy kontekst każdej decyzji technicznej. W przyszłości planujemy
rozszerzyć to na analizę spójności danych i automatyczne raportowanie. Historia
projektu sięga 2024 roku kiedy...

<critical_rules>
...
</critical_rules>
```

**Dlaczego:** Esej dla człowieka zużywa cenne miejsce na początku kontekstu (wysokie salience)
i przykrywa reguły krytyczne. Agent nie potrzebuje historii — potrzebuje instrukcji.

**Dobrze:**
```markdown
# ERP_SPECIALIST.md

Konfigurujesz system ERP Comarch XL — generujesz i testujesz SQL dla kolumn,
filtrów i widoków BI. Eskalujesz do użytkownika zamiast zgadywać.

<critical_rules>
...
</critical_rules>
<!-- Kontekst projektu → SPIRIT.md, nie prompt roli -->
```

---

## References

- Plik źródłowy: `documents/prompt_engineer/PROMPT_CONVENTION.md`
- CONVENTION_META: `documents/conventions/CONVENTION_META.md`
- CONVENTION_WORKFLOW: `documents/conventions/CONVENTION_WORKFLOW.md`
- Przykładowy workflow: `workflows/bi_view_creation_workflow.md`
- Anthropic: rekomendacje XML tags w złożonych promptach
- Research "Lost in the Middle": pozycja informacji w kontekście a jej wykorzystanie przez model

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-25 | Migracja PROMPT_CONVENTION.md do formatu CONVENTION_META. Status: draft. |
