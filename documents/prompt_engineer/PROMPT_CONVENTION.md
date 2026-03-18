# Konwencja pisania promptów agentów

Dokument referencyjny dla Prompt Engineera. Każdy prompt roli w systemie
musi być zgodny z tą konwencją.

---

## 1. Warstwy systemu promptowego

```
CLAUDE.md (shared_base)        ← zawsze ładowany, wspólne reguły
  └─ Role prompt (.md)         ← ładowany per rola (ERP_SPECIALIST.md, ANALYST.md...)
       └─ Workflow (.md)       ← ładowany per typ zadania (bi_view_creation_workflow.md...)
            └─ Domain pack     ← ładowany per kontekst (ERP_SCHEMA_PATTERNS.md...)
                 └─ Runtime    ← inbox, backlog, stan zadania
```

Zasady warstw:
- Reguła żyje na najwyższym węźle gdzie obowiązuje wszystkich odbiorców.
- Nie powielaj reguły w niższej warstwie — odwołuj się do wyższej.
- Domain pack i workflow ładowane na żądanie, nie wbudowane w rolę.

---

## 2. Formatowanie — decyzje i uzasadnienia

### Znaczniki sekcji: XML tags + Markdown wewnątrz

Stosujemy **hybrid XML/Markdown**:
- **XML tags** dla granic logicznych sekcji (`<role>`, `<scope>`, `<critical_rules>`...)
- **Markdown** wewnątrz sekcji (listy, tabele, numeracja, nagłówki `###`)
- **YAML frontmatter** (`---` blok) dla metadanych routingu

Dlaczego XML na granicach:
- Anthropic wprost rekomenduje XML tags do oddzielania sekcji w złożonych promptach.
- Pomagają Claude rozpoznawać strukturę i odróżniać typy informacji.
- „Lost in the Middle" — jasne granice sekcji zmniejszają ryzyko utraty salience.
- Lepsze niż `##` headers gdy model musi odróżnić wiele podobnych sekcji.

Dlaczego Markdown wewnątrz:
- Czytelny dla człowieka (edycja, review).
- Numerowane listy, tabele, checkboxy — naturalne w Markdown.
- XML wewnątrz sekcji nie dodaje wartości, tylko szum.

### Hierarchia ważności w dokumencie

Pozycja w pliku = ważność. Od góry:
1. Kim jesteś + co dostarczasz (opening statement)
2. Reguły krytyczne (wysoko = wysoka salience)
3. Workflow (środek)
4. Narzędzia i referencje (nisko = rzadko potrzebne in extenso)
5. Checklista końcowa (na dole = ostatnia rzecz przed odpowiedzią)

Uzasadnienie: badania „Lost in the Middle" pokazują że model najlepiej
wykorzystuje informację na początku i na końcu kontekstu. Krytyczne reguły
wysoko, checklista na dole — dwie krawędzie.

### Numeracja

- **Kroki workflow z fazami:** numer fazy + litera kroku: `1a, 1b, 2a, 2b...`
- **Listy niezależne od faz:** numeracja prosta: `1, 2, 3...`
- Wzorzec: `bi_view_creation_workflow.md` (Faza 0, Faza 1a, Faza 1b...)

### Styl pisania

- **Afirmatywne reguły**: „Przed zmianą sprawdź gate" zamiast „Nie zmieniaj bez gate'a".
- **Jedna reguła = jeden punkt**. Dwa zdania w punkcie → rozbij na dwa punkty.
- **Bez uzasadnień inline** w regułach krytycznych. Jeśli potrzebne — komentarz
  HTML `<!-- dlaczego -->` lub sekcja „Kontekst decyzji" na dole dokumentu.
- **Bez emoji** (dozwolone: ✓, ✗).
- Przykłady: maks 1-3, tylko edge case'y.

---

## 3. Szablon promptu roli

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

### Sekcje opcjonalne

Dodawaj tylko gdy rola ich wymaga:

- `<gates>` — warunki wejścia/wyjścia (reviewer, workflow-heavy roles)
- `<output_contract>` — sztywny format wyniku (reviewer, meta roles)
- `<examples>` — 1-3 kanoniczne edge case'y (gdy zero-shot nie wystarcza)
- `<decision_policy>` — reguły rozstrzygania konfliktów (orkiestrator)
- `<context_management>` — zasady zarządzania kontekstem (role z dużymi outputami)

---

## 4. Co gdzie trafia

| Treść | Warstwa | Plik |
|---|---|---|
| Eskalacja, logowanie, agent_bus, git, bash rules | shared_base | `CLAUDE.md` |
| Cel roli, zakres, reguły krytyczne, narzędzia roli | role prompt | `{ROLA}.md` |
| Fazy, gates, forbidden, exit conditions | workflow | `workflows/*.md` |
| Wzorce SQL, konwersje, enumy, schematy | domain pack | `documents/erp_specialist/ERP_*.md` |
| Inbox, backlog items, stan zadania | runtime | Ładowane dynamicznie na starcie sesji |

### Test przynależności

Przed dodaniem reguły do pliku:
1. Dotyczy wszystkich ról? → `CLAUDE.md`
2. Dotyczy jednej roli, zawsze? → prompt roli
3. Dotyczy jednego typu zadania? → workflow
4. Dotyczy wiedzy dziedzinowej? → domain pack
5. Zmienia się między sesjami? → runtime (nie wpisuj do promptu)

---

## 5. Szablon workflow

Workflow (ładowane per typ zadania) mają własny układ:

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

Workflow nie używa XML tags — jest dokumentem procesowym, nie promptem roli.
XML tags rezerwujemy dla promptów ról gdzie model musi odróżniać typy instrukcji.

---

## 6. Zasady zmian (dla Prompt Engineera)

1. Zmiana wymaga identyfikacji failure mode lub celu jakościowego.
2. Dobierz skalę: patch (1 blok) vs refaktor (cała struktura).
3. Każda zmiana = commit + diff + uzasadnienie + plan testów.
4. Patch nie może pogarszać dwóch wymiarów żeby poprawić jeden.
5. Gdy problem nie leży w prompcie → ESCALATE_ARCHITECTURE.

### Wymiary oceny promptu

1. Clarity — jedna sekcja = jedna odpowiedzialność?
2. Salience — reguły krytyczne wysoko i osobno?
3. Scope — nie miesza odpowiedzialności ról?
4. Gate reliability — warunki wejścia/wyjścia testowalne?
5. Output determinism — format wyniku jednoznaczny?
6. Modularity — domain knowledge odłączalne?

---

## 7. Prompty badawcze (research prompts)

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

Lokalizacja promptów: `documents/<rola>/research_prompt_<temat>.md`
Lokalizacja wyników: `documents/<rola>/research_results_<temat>.md`

---

## 8. Czego unikać

- Duplikacji reguł między warstwami.
- Prose zamiast numerowanych kroków.
- Uzasadnień historycznych w regułach krytycznych (agent nie ma pamięci — daj działanie).
- Sekcji „na zapas" opisujących narzędzia które nie istnieją.
- Mieszania instrukcji dla agenta z esejem dla człowieka w jednym dokumencie.
- Markdown `##` headers jako granic sekcji w promptach ról — używaj XML tags.
