---
convention_id: prompt-convention
version: "1.0"
status: active
created: 2026-03-24
updated: 2026-03-25
author: prompt_engineer
owner: prompt_engineer
approver: dawid
audience: [prompt_engineer]
scope: "Definiuje strukturę, formatowanie i składnię promptów ról agentów"
---

# CONVENTION_PROMPT — Struktura i składnia promptów ról

## TL;DR

- Prompt roli = YAML metadata + XML tags (granice sekcji) + Markdown (treść wewnątrz)
- Warstwy: shared_base > role > workflow > domain_pack > runtime
- Hierarchia ważności: identity + critical rules na górze, checklista na dole
- Reguła żyje na najwyższym węźle gdzie obowiązuje
- Zmiana promptu wymaga failure mode + diff + uzasadnienie + plan testów
- Workflow mają osobną konwencję: `CONVENTION_WORKFLOW.md`

---

## Zakres

**Pokrywa:**
- Struktura promptów ról agentów (układ sekcji, szablon)
- Formatowanie (XML/Markdown hybrid, numeracja, styl pisania)
- Przynależność reguły do warstwy (co gdzie trafia)
- Zasady zmian i ocena jakości promptów
- Format promptów badawczych (research prompts)

**NIE pokrywa:**
- Struktura workflow → `documents/conventions/CONVENTION_WORKFLOW.md`
- Konwencje kodu → `documents/dev/CODE_STANDARDS.md`
- Treść domenowa (SQL, ERP, BI) → domain packs per rola

---

## Reguły

### 01R: Warstwy systemu promptowego

```
CLAUDE.md (shared_base)        ← zawsze ładowany, wspólne reguły
  └─ Role prompt (.md)         ← ładowany per rola (ERP_SPECIALIST.md, ANALYST.md...)
       └─ Workflow (.md)       ← ładowany per typ zadania (workflow_developer.md...)
            └─ Domain pack     ← ładowany per kontekst (ERP_SCHEMA_PATTERNS.md...)
                 └─ Runtime    ← inbox, backlog, stan zadania
```

Zasady warstw:
- Reguła żyje na najwyższym węźle gdzie obowiązuje wszystkich odbiorców.
- Nie powielaj reguły w niższej warstwie — odwołuj się do wyższej.
- Domain pack i workflow ładowane na żądanie, nie wbudowane w rolę.

---

### 02R: Hybrid XML/Markdown format

Prompt roli stosuje **hybrid XML/Markdown**:
- **XML tags** dla granic logicznych sekcji (`<mission>`, `<scope>`, `<critical_rules>`...)
- **Markdown** wewnątrz sekcji (listy, tabele, numeracja, nagłówki `###`)
- **YAML frontmatter** (`---` blok) dla metadanych routingu

Dlaczego XML na granicach:
- Anthropic rekomenduje XML tags do oddzielania sekcji w złożonych promptach.
- Pomagają Claude rozpoznawać strukturę i odróżniać typy informacji.
- „Lost in the Middle" — jasne granice sekcji zmniejszają ryzyko utraty salience.
- Lepsze niż `##` headers gdy model musi odróżnić wiele podobnych sekcji.

Dlaczego Markdown wewnątrz:
- Czytelny dla człowieka (edycja, review).
- Numerowane listy, tabele, checkboxy — naturalne w Markdown.
- XML wewnątrz sekcji nie dodaje wartości, tylko szum.

**Workflow nie używają XML tags** — są dokumentami procesowymi, nie promptami ról.

---

### 03R: Hierarchia ważności w dokumencie

Pozycja w pliku = ważność. Od góry:
1. Kim jesteś + co dostarczasz (opening statement)
2. Reguły krytyczne (wysoko = wysoka salience)
3. Workflow (środek)
4. Narzędzia i referencje (nisko = rzadko potrzebne in extenso)
5. Checklista końcowa (na dole = ostatnia rzecz przed odpowiedzią)

Uzasadnienie: badania „Lost in the Middle" — model najlepiej wykorzystuje informację na początku i na końcu kontekstu. Krytyczne reguły wysoko, checklista na dole — dwie krawędzie.

---

### 04R: Numeracja

- **Kroki workflow z fazami:** hierarchia dziesiętna: `1.1, 1.2, 1.1.1`
- **Listy niezależne od faz:** numeracja prosta: `1, 2, 3...`
- **Reguły w konwencjach:** format `01R, 02R...`
- **Antywzorce:** format `01AP, 02AP...`

---

### 05R: Styl pisania

- **Afirmatywne reguły**: „Przed zmianą sprawdź gate" zamiast „Nie zmieniaj bez gate'a".
- **Jedna reguła = jeden punkt.** Dwa zdania w punkcie → rozbij na dwa punkty.
- **Bez uzasadnień inline** w regułach krytycznych. Jeśli potrzebne — komentarz
  HTML `<!-- dlaczego -->` lub sekcja „Kontekst decyzji" na dole dokumentu.
- **Bez emoji** (dozwolone: ✓, ✗).
- **Bez narracji przyspieszającej:** żadnego "natychmiast", "od razu", "szybko", "bez czekania".
- Przykłady: maks 1-3, tylko edge case'y.

---

### 06R: Szablon promptu roli

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

### 07R: Sekcje opcjonalne

Dodawaj tylko gdy rola ich wymaga:

- `<persona>` — profil psychologiczny roli (charakter, styl myślenia).
  Umieść po `<mission>`, przed `<scope>`. Dla ról gdzie charakter wpływa na zachowanie.
  **UWAGA:** Few-shot examples (08R) często skuteczniejsze od długiego opisu persony.
- `<behavior_examples>` — 2-5 scenariuszy konkretnych zachowań. Format:
  ```
  *Scenariusz: [kontekst]*
  ✗ [złe zachowanie]
  ✓ [dobre zachowanie]
  ```
  Anthropic research: few-shot examples skuteczniejsze od długiego opisu persony.
  Preferuj examples przed dodawaniem kolejnych linii do `<persona>`.
- `<gates>` — warunki wejścia/wyjścia (reviewer, workflow-heavy roles)
- `<output_contract>` — sztywny format wyniku (reviewer, meta roles)
- `<examples>` — 1-3 kanoniczne edge case'y (gdy zero-shot nie wystarcza)
- `<decision_policy>` — reguły rozstrzygania konfliktów (orkiestrator)
- `<context_management>` — zasady zarządzania kontekstem (role z dużymi outputami)
- `<code_maturity_levels>` — skala oceny kodu (reviewer roles)

---

### 08R: Przynależność reguły do warstwy

| Treść | Warstwa | Plik |
|---|---|---|
| Eskalacja, logowanie, agent_bus, git, bash rules | shared_base | `CLAUDE.md` |
| Cel roli, zakres, reguły krytyczne, narzędzia roli | role prompt | `{ROLA}.md` |
| Fazy, gates, forbidden, exit conditions | workflow | `workflows/*.md` |
| Wzorce SQL, konwersje, enumy, schematy | domain pack | `documents/erp_specialist/ERP_*.md` |
| Inbox, backlog items, stan zadania | runtime | Ładowane dynamicznie na starcie sesji |

**Test przynależności** — przed dodaniem reguły do pliku:
1. Dotyczy wszystkich ról? → `CLAUDE.md`
2. Dotyczy jednej roli, zawsze? → prompt roli
3. Dotyczy jednego typu zadania? → workflow
4. Dotyczy wiedzy dziedzinowej? → domain pack
5. Zmienia się między sesjami? → runtime (nie wpisuj do promptu)

---

### 09R: Zasady zmian promptów

1. Zmiana wymaga identyfikacji failure mode lub celu jakościowego.
2. Dobierz skalę: patch (1 blok) vs refaktor (cała struktura).
3. Każda zmiana = commit + diff + uzasadnienie + plan testów.
4. Patch nie może pogarszać dwóch wymiarów żeby poprawić jeden.
5. Gdy problem nie leży w prompcie → ESCALATE_ARCHITECTURE.
6. **Minimal viable prompt przy nowej roli:**
   - Minimum: mission, scope, critical rules (5-8), output contract, minimal workflow routing
   - Workflow nabudowuj iteracyjnie na podstawie rzeczywistych sesji i failure modes

---

### 10R: Wymiary oceny promptu

1. **Clarity** — jedna sekcja = jedna odpowiedzialność?
2. **Salience** — reguły krytyczne wysoko i osobno?
3. **Scope** — nie miesza odpowiedzialności ról?
4. **Gate reliability** — warunki wejścia/wyjścia testowalne?
5. **Output determinism** — format wyniku jednoznaczny?
6. **Modularity** — domain knowledge odłączalne?

---

### 11R: Prompty badawcze (research prompts)

Każdy prompt do zewnętrznego researchera musi zawierać sekcję **Output contract**:

```markdown
## Output contract

Zapisz wyniki do pliku: `documents/researcher/research/research_results_{temat}.md`

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

Lokalizacja promptów: `documents/researcher/prompts/research_{temat}.md`
Lokalizacja wyników: `documents/researcher/research/research_results_{temat}.md`

---

### 12R: Config as source of truth

Gdy mechanizm ma zewnętrzny config (plik, DB, env), prompt referencuje config — nie definiuje jego struktury.

- Dobrze: "Dostępne role zdefiniowane w `session_init` context."
- Źle: "Dostępne role: erp_specialist, analyst, developer, architect, metodolog, prompt_engineer."

Powód: duplikacja config → desynchronizacja. Prompt się nie aktualizuje gdy config się zmienia.

---

## Przykłady

### Przykład 1: Minimalny prompt roli (nowa rola)

```md
# Rola X — instrukcje operacyjne

Robisz Y. Twój output to Z.

---
agent_id: rola_x
role_type: executor
escalates_to: developer
allowed_tools: [Read, Edit, Write, Grep, Glob]
disallowed_tools: []
---

<mission>
1. Kryterium sukcesu A.
2. Kryterium sukcesu B.
</mission>

<scope>
W zakresie:
1. Zadanie A
2. Zadanie B

Poza zakresem:
1. Nie robię C — eskaluj do D.
</scope>

<critical_rules>
1. Reguła 1.
2. Reguła 2.
</critical_rules>

<session_start>
1. Przeczytaj inbox.
2. Sprawdź backlog.
</session_start>

<workflow>
Workflow gate — patrz CLAUDE.md.
</workflow>

<escalation>
1. Problem X → eskaluj do Y.
</escalation>

<end_of_turn_checklist>
1. Czy output jest kompletny?
2. Czy obserwacje zapisane?
</end_of_turn_checklist>
```

### Przykład 2: Test przynależności (08R)

Reguła: "Przed commitem uruchom testy."
- Dotyczy wszystkich ról? → Tak → `CLAUDE.md` (sekcja "Zero failing tests")
- ✗ Nie wstawiaj do ERP_SPECIALIST.md, DEVELOPER.md itp.

Reguła: "Przed SQL sprawdź schema patterns."
- Dotyczy jednej roli (ERP)? → Tak → domain pack (`ERP_SCHEMA_PATTERNS.md`)
- ✗ Nie wstawiaj do CLAUDE.md

---

## Antywzorce

### 01AP: Duplikacja reguł między warstwami

**Źle:** Reguła o eskalacji powtórzona w CLAUDE.md i w DEVELOPER.md.

**Dlaczego:** Agent widzi dwie wersje, jedna zdezaktualizowana — konflikt. Aktualizacja wymaga zmian w N plikach.

**Dobrze:** Reguła w CLAUDE.md (shared_base), prompt roli odwołuje się: "Eskalacja — patrz CLAUDE.md."

---

### 02AP: Prose zamiast numerowanych kroków

**Źle:**
```
Najpierw sprawdź status, potem jeśli wszystko OK to możesz przejść do generowania SQL,
ale pamiętaj żeby wcześniej zweryfikować schemę...
```

**Dlaczego:** Agent gubi kolejność, pomija kroki, nie ma checkpointów.

**Dobrze:**
```
1. Sprawdź git status.
2. Zweryfikuj schema patterns.
3. Wygeneruj SQL.
```

---

### 03AP: Uzasadnienia historyczne w regułach krytycznych

**Źle:**
```
5. Nie używaj metody X, bo w sesji z 15 marca agent Y popełnił błąd Z i musieliśmy cofać...
```

**Dlaczego:** Agent nie ma pamięci kontekstu historycznego — potrzebuje działania, nie opowieści.

**Dobrze:**
```
5. Używaj metody W zamiast X. <!-- X powoduje błąd Z w kontekście Y -->
```

---

### 04AP: Sekcje "na zapas"

**Źle:** Prompt opisuje narzędzie `data_quality_check.py` które jeszcze nie istnieje.

**Dlaczego:** Agent próbuje użyć nieistniejącego narzędzia → error → eskalacja → strata czasu.

**Dobrze:** Dodawaj narzędzia do promptu po ich wdrożeniu i przetestowaniu.

---

### 05AP: Mieszanie instrukcji z esejami

**Źle:** Dokument roli zawiera 3 akapity filozofii projektu + instrukcje operacyjne w jednym pliku.

**Dlaczego:** Agent nie odróżnia kontekstu od polecenia. Filozofia rozmywa salience reguł.

**Dobrze:** Filozofia → SPIRIT.md (czytane raz na starcie). Prompt roli → tylko instrukcje.

---

### 06AP: Markdown headers zamiast XML tags w promptach ról

**Źle:**
```markdown
## Mission
## Scope
## Critical Rules
```

**Dlaczego:** Model traktuje `##` jako formatting, nie granice logiczne. Przy wielu podobnych sekcjach traci kontekst.

**Dobrze:**
```xml
<mission>...</mission>
<scope>...</scope>
<critical_rules>...</critical_rules>
```

---

## References

- CONVENTION_META: `documents/conventions/CONVENTION_META.md`
- CONVENTION_WORKFLOW: `documents/conventions/CONVENTION_WORKFLOW.md`
- Anthropic prompt engineering: XML tags best practices
- Research "Lost in the Middle": positional salience w dużych kontekstach

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-25 | Reformat do CONVENTION_META: YAML frontmatter, TL;DR, Zakres, reguły 01R-11R, Antywzorce 01AP-06AP, Changelog. Treść zachowana z oryginalnego dokumentu, sekcja 5 (szablon workflow) przeniesiona do CONVENTION_WORKFLOW.md. |
