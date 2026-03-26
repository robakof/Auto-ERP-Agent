# Research: Optymalizacja dokumentów workflow w systemach wieloagentowych

Data opracowania: 2026-03-15

## Executive summary

Najmocniejszy wniosek z dokumentacji Anthropic, LangChain, AutoGen i CrewAI jest spójny: gdy **kolejność kroków i kompletność wykonania są krytyczne**, workflow powinien być opisany i traktowany jak **jawna maszyna stanów / graf kroków / zestaw zadań z zależnościami**, a nie jak luźna proza. W praktyce oznacza to:

- **instrukcje proceduralne zapisywać jako checklisty + wyjścia + gate + handoff payload**, nie jako akapity;
- **trzymać workflow jako osobny, współdzielony dokument procesowy** i tylko mapować go do ról agentów;
- **przed wdrożeniem twardych narzędzi egzekucyjnych** już w promptach stosować mini-protokół fazy: wejścia, kroki, warunki wyjścia, dozwolone przejścia i format handoffu;
- **skracać przez kompresję strukturalną, nie przez usuwanie warunków**: mniej narracji, więcej tabel/checklist/schematu odpowiedzi;
- dla Waszego przypadku (ERP Specialist → Analityk → Developer, 4 fazy, BI views) najlepszy będzie **hybrydowy układ dokumentów**: jeden kanoniczny workflow w `workflows/` + cienkie dokumenty agentów z ich rolą, narzędziami i odpowiedzialnością za konkretne fazy.

---

## 1) Kluczowe wzorce (z nazwami i źródłami)

### Wzorzec 1: **Checklist over prose**
**Opis:** gdy zależy Wam na kompletności i kolejności, instrukcje powinny być zapisane jako numerowane kroki lub bullet checklisty, nie jako narracyjna proza. Anthropic wprost zaleca sekwencyjne kroki i jawne constraints, gdy kolejność lub kompletność mają znaczenie. Dodatkowo badania nad checklistami pokazują poprawę w zadaniach explicit instruction-following.

**Dlaczego działa:**
- zwiększa salience obowiązkowych kroków;
- daje modelowi „sloty” do odhaczania;
- ułatwia self-check i zewnętrzną walidację.

**Minimalna postać wzorca:**
1. Krok 1  
2. Krok 2  
3. Krok 3  
4. Na końcu sprawdź checklistę wyjściową

**Źródła:** Anthropic prompt best practices; TICK/STICK (checklist-structured feedback). [1][2]

---

### Wzorzec 2: **Explicit phase gate / exit criteria**
**Opis:** każda faza powinna mieć jawny „gate”, czyli warunki, które muszą być spełnione przed przejściem dalej: *nie kontynuuj, dopóki nie masz X, Y, Z*. To jest odpowiednik dokumentacyjny warunkowych krawędzi w grafie workflow.

**Dlaczego działa:**
- ogranicza „skakanie” do następnej fazy po częściowym wyniku;
- zmusza do sprawdzenia artefaktów, a nie tylko wrażenia „brzmi dobrze”;
- dobrze skaluje się do handoffów.

**Minimalna postać wzorca:**
- Gate PASS, jeśli:
  - eksport istnieje;
  - weryfikacja zakończona;
  - brak otwartych blokad;
  - handoff payload jest kompletny.
- Jeśli którykolwiek warunek nie jest spełniony, zwróć `BLOCKED` i listę braków.

**Źródła:** LangGraph interrupts + approve/reject; AutoGen GraphFlow conditional edges; CrewAI guardrails/HITL. [3][4][5]

---

### Wzorzec 3: **Handoff contract**
**Opis:** handoff między rolami powinien mieć własny kontrakt: kto przekazuje, do kogo, w jakim formacie, z jakimi dowodami wykonania, z jakimi pytaniami otwartymi i w jakim statusie.

**Dlaczego działa:**
- redukuje utratę informacji na styku ról;
- ogranicza „zatwierdzenie bez weryfikacji”;
- pozwala wymusić, że następny agent nie startuje z implicit assumptions.

**Minimalna postać wzorca:**
- `from_role`
- `to_role`
- `phase_completed`
- `artifacts[]`
- `verification_summary`
- `open_issues[]`
- `next_expected_action`
- `status = READY | BLOCKED`

**Źródła:** AutoGen handoffs/swarm; LangChain subagent outputs; CrewAI structured outputs. [6][7][5]

---

### Wzorzec 4: **Structured output as the unit of compliance**
**Opis:** nie prosić agenta o „zrób to i podsumuj”, tylko wymagać odpowiedzi w stałym schemacie: JSON / Pydantic / sekcje o z góry ustalonych nazwach. To nie tylko kwestia parsowania — to sposób wymuszenia, by agent jawnie podał brakujące elementy.

**Dlaczego działa:**
- łatwiej wykryć brak eksportu / brak weryfikacji / brak decyzji;
- handoff staje się maszynowo walidowalny;
- downstream agent dostaje kompletne, nie-esejowe wejście.

**Minimalna postać wzorca:**
```json
{
  "phase": "verification",
  "status": "PASS|BLOCKED",
  "required_artifacts_present": true,
  "artifacts": [],
  "checks_performed": [],
  "missing_items": [],
  "next_role": "Developer"
}
```

**Źródła:** LangChain structured output; CrewAI output_json/output_pydantic; AutoGen tool/handoff context notes. [8][5][6]

---

### Wzorzec 5: **State-machine prompting**
**Opis:** workflow opisuje się jak maszynę stanów: `STATE -> allowed actions -> gate -> next state`. To bardzo zbieżne z rekomendacjami produkcyjnymi AutoGen GraphFlow, LangGraph i badaniem StateFlow.

**Dlaczego działa:**
- oddziela „co wolno zrobić teraz” od „jak rozwiązać subproblem”;
- zmniejsza ryzyko pominięcia kroku;
- daje naturalny model dla loopów, aprobacji i retry.

**Minimalna postać wzorca:**
- `STATE: ExportPreparation`
- `Allowed actions: inspect requirements, generate export plan, create export`
- `Forbidden: approve final output`
- `Exit when: export artifact exists and was verified`
- `Next: Verification`

**Źródła:** StateFlow; AutoGen GraphFlow; LangGraph graph/state docs. [9][4][10]

---

### Wzorzec 6: **Supervisor/manager for strict sequencing**
**Opis:** gdy proces ma być rygorystyczny, lepiej mieć warstwę koordynującą (planner/manager/supervisor) albo jawny flow niż pozwalać agentom swobodnie wybierać kolejny krok.

**Dlaczego działa:**
- centralizuje decyzję „czy w ogóle wolno przejść dalej”;
- zmniejsza chaos w systemach z wieloma rolami;
- ułatwia obserwowalność i audyt.

**Trade-off:** trochę mniejsza autonomia agentów, ale większa przewidywalność procesu.

**Źródła:** LangChain supervisor/subagents; CrewAI hierarchical process; AutoGen SelectorGroupChat. [11][12][13]

---

### Wzorzec 7: **Context isolation + summarized return**
**Opis:** nie każdy agent powinien widzieć całą historię w pełnej formie. Często lepiej, żeby pracował w ograniczonym kontekście i zwracał tylko standaryzowany rezultat/handoff payload.

**Dlaczego działa:**
- ogranicza „rozlanie” kontekstu;
- redukuje gubienie ważnych reguł w długim promptcie;
- poprawia salience aktualnego gate.

**Źródła:** Anthropic subagents; LangChain subagents/context engineering. [14][7][10]

---

### Wzorzec 8: **Prompt transparency / inspect the real prompt**
**Opis:** w produkcji trzeba sprawdzać rzeczywisty prompt wysyłany do modelu, a nie tylko to, co „wydaje się”, że zdefiniowaliście. Framework może doklejać własne instrukcje.

**Dlaczego działa:**
- chroni przed niejawnie nadpisanym stylem pracy;
- ujawnia konflikty między role prompt a workflow prompt;
- pomaga wykryć, czemu agent pomija krok mimo że „miał to w dokumencie”.

**Źródła:** CrewAI customizing prompts + production transparency issue. [15]

---

## 2) Odpowiedzi na pytania badawcze

### P1. Compliance przez strukturę dokumentu
Najlepiej sprawdzają się techniki, które robią z dokumentu **procedurę z warunkami przejścia**, a nie opis zachowania. Z dostępnych źródeł i wzorców produkcyjnych wynika, że szczególnie skuteczne są:

1. **Checklisty zamiast prozy**  
2. **Jawne gates (`nie kontynuuj dopóki...`)**  
3. **Stały format odpowiedzi / handoffu**  
4. **Przykłady poprawnych i błędnych odpowiedzi**  
5. **Role + ograniczony zakres odpowiedzialności**  
6. **Samokontrola na końcu fazy („przed zakończeniem sprawdź kryteria”)**

Anthropic wprost zaleca jasne, bezpośrednie instrukcje, sekwencyjne kroki i przykłady; LangChain/CrewAI/AutoGen przesuwają to dalej do poziomu graph/flow/structured-output/interrupt. [1][3][4][5][8]

**Wniosek praktyczny:** sam dokument może już działać jak „soft guardrail”, jeśli każda faza kończy się jednym z dwóch stanów: `PASS` albo `BLOCKED`, nigdy „luźnym podsumowaniem”.

---

### P2. Separacja dokumentów: agent-centric vs process-centric
#### Opcja A: workflow w dokumencie roli (agent-centric)
**Plusy:**
- mniejszy prompt lokalny, wyższa salience;
- agent widzi tylko to, co dla niego istotne;
- łatwiej optymalizować per rola/model.

**Minusy:**
- duplikacja kroków i gate’ów między rolami;
- drift dokumentów przy zmianach procesu;
- handoffy zaczynają się różnić semantycznie;
- trudniej utrzymać jedno źródło prawdy.

#### Opcja B: osobny dokument workflow (process-centric)
**Plusy:**
- jedna definicja faz, gate’ów i handoffów;
- łatwiejszy audyt i zmiana procesu;
- lepiej pasuje do multi-agent handoffów;
- bliżej wzorców Flow/Graph/StateFlow.

**Minusy:**
- sam w sobie bywa za długi dla pojedynczego agenta;
- potrzebuje dobrego sposobu „wycinkowania” tylko aktualnej fazy;
- grozi spadkiem salience, jeśli agent dostaje cały workflow naraz.

#### Rekomendacja
Dla Waszego przypadku najlepszy jest **układ hybrydowy z kanonicznym dokumentem process-centric**:

```text
workflows/
  bi_view_creation_workflow.md      # jedyne źródło prawdy dla faz, gate’ów i handoffów
handoffs/
  bi_view_handoff_schema.md         # wspólny kontrakt przekazania
agents/
  erp_specialist.md                 # rola, narzędzia, ograniczenia, odpowiedzialność za fazy
  analyst.md
  developer.md
```

**Zasada:**  
- `workflows/` opisuje **proces i stany**;  
- `agents/` opisują **kompetencje, narzędzia, heurystyki, lokalne zakazy**;  
- agent w danym runie powinien dostać **tylko fragment workflow dla aktualnej fazy + handoff schema**, a nie cały proces.

To jest zgodne z kierunkiem:
- LangChain: workflow/supervisor oddzielony od specjalistów;  
- CrewAI: Flow jako „manager/process definition”, Crew jako wykonawcy;  
- Anthropic subagents: osobne konteksty i wyspecjalizowane prompty;  
- AutoGen: GraphFlow dla ścisłej kontroli, Swarm/Handoff dla większej autonomii. [10][11][14][16][4][6]

---

### P3. Phase gates w promptach: jak wymuszać sekwencyjność bez twardych narzędzi?
Tak — da się zbudować **mini-protokół per faza**, który samą strukturą promptu mocno zwiększa sekwencyjność.

#### Rekomendowany mini-protokół fazy
```md
## PHASE: <nazwa_fazy>

### Objective
Jedno zdanie: co ma zostać osiągnięte.

### Inputs required
- ...
- ...
- ...

### Allowed actions
1. ...
2. ...
3. ...

### Forbidden actions
- Nie zatwierdzaj.
- Nie przekazuj do następnej roli.
- Nie deklaruj ukończenia bez artefaktu X.

### Required output
Zwróć dokładnie:
- status: PASS | BLOCKED
- artifacts:
- checks_performed:
- missing_items:
- handoff_payload:

### Exit gate
Przejdź dalej tylko jeśli:
- ...
- ...
W przeciwnym razie zwróć `BLOCKED`.

### Next state
Jeśli PASS -> <kolejna faza>
Jeśli BLOCKED -> pozostajesz w tej fazie / eskalujesz
```

#### Dlaczego to działa
To jest dokumentacyjny odpowiednik:
- warunkowych krawędzi w AutoGen GraphFlow,
- `interrupt()` / approve-reject w LangGraph,
- task guardrails + structured outputs w CrewAI,
- prompt chaining i XML segregation w Anthropic. [3][4][5][1]

#### Dodatkowy trik
Na końcu każdej fazy dodaj sekcję:
- **Self-check before finish**
  - Czy wykonałeś każdy krok?
  - Czy istnieje dowód eksportu?
  - Czy handoff payload jest kompletny?
  - Jeśli nie, zwróć `BLOCKED`, nie `PASS`.

Anthropic zaleca wprost dodać self-check przeciwko kryteriom przed zakończeniem. [1]

---

### P4. Długość vs precyzja
Nie ma jednej uniwersalnej zasady „krótszy prompt = lepszy”. Z zebranych źródeł wynika bardziej subtelny obraz:

#### Co wiemy
1. **Za krótkie prompty często szkodzą**, jeśli ucinają potrzebny kontekst domenowy lub kryteria wykonania. W badaniu z 2025 krótkie instrukcje pogarszały wyniki we wszystkich badanych taskach domenowych, a dłuższe prompty z dodatkowymi szczegółami były generalnie korzystne. [17]

2. **Za długie i źle ułożone prompty też szkodzą**, bo ważne warunki giną w środku kontekstu. „Lost in the Middle” pokazało, że modele często najlepiej wykorzystują informacje z początku lub końca, a gorzej te ze środka. [18]

3. **Nie chodzi więc o długość samą w sobie, tylko o kompresję strukturalną**:
   - mniej narracji,
   - mniej duplikatów,
   - więcej jawnych sekcji,
   - ważne reguły na początku lub końcu,
   - tylko bieżąca faza w aktywnym promptcie.

#### Praktyczna zasada
- **nie skracaj przez usuwanie gate’ów ani examples;**
- **skracaj przez usunięcie prozy, powtórzeń i informacji niezwiązanych z aktualną fazą;**
- **workflow trzymaj długi na poziomie repozytorium, ale prompt do runu rób krótki i fazowy.**

#### Dobra heurystyka
- rola agenta: stała, krótka;
- workflow: pełny, repo-level;
- aktywny prompt run-time: tylko aktualna faza + kontrakt handoffu + wymagany format wyniku.

---

### P5. Wzorce z produkcji: Anthropic, LangChain, CrewAI, AutoGen
#### Anthropic
Anthropic naciska na:
- jasne i bezpośrednie instrukcje;
- numerowane kroki, gdy kolejność ma znaczenie;
- XML tags do rozdzielania instrukcji, kontekstu, przykładów i wejścia;
- few-shot examples;
- prompt chaining dla złożonych tasków;
- self-check względem kryteriów. [1][19]

**Interpretacja produkcyjna:** Anthropic wzmacnia warstwę **struktury promptu**, ale nie sugeruje, że sama rola wystarczy do egzekwowania workflow.

#### LangChain / LangGraph
LangChain bardzo wyraźnie rozróżnia:
- **workflows**: predetermined code paths, stała kolejność;
- **agents**: dynamiczne decyzje. [10]

Do rygorystycznych procesów promuje:
- graf stanów i krawędzi,
- interrupts,
- structured output,
- middleware/guardrails,
- supervisor/subagents. [3][8][10][11]

**Interpretacja produkcyjna:** jeśli kroków nie wolno pomijać, projektuj to jako workflow/graph, a nie jako „sprytnego agenta”.

#### CrewAI
CrewAI rozdziela:
- **Flows** jako backbone / process definition,
- **Crews** jako wykonawców z autonomią. [16]

Dodatkowo mocno akcentuje:
- structured outputs,
- task guardrails,
- human-in-the-loop,
- hierarchicznego managera,
- oraz fakt, że **task design jest ważniejszy niż agent persona** (80/20). [5][12][15]

**Interpretacja produkcyjna:** workflow powinien żyć na poziomie flow/task, a nie być rozsmarowany po backstory agentów.

#### AutoGen
AutoGen pokazuje dwa bardzo różne style:
- **GraphFlow**: structured execution, conditional edges, activation groups, loops, exit conditions;
- **Swarm / Handoffs**: lokalne decyzje agentów i wspólny message context. [4][6]

**Interpretacja produkcyjna:**  
- dla rygorystycznej zgodności procesu wybieraj podejście GraphFlow-like;  
- Swarm-like handoffs są dobre dla elastycznej delegacji, ale gorsze jako źródło silnej sekwencyjności.

---

## 3) Rekomendacja ws. separacji dokumentów (agent-centric vs process-centric)

## Rekomendacja końcowa
**Wybierz process-centric jako kanoniczne źródło prawdy + agent-centric jako cienkie uzupełnienie.**

### Dlaczego
Wasz problem nie dotyczy tylko „jak ma myśleć ERP Specialist” albo „jak ma pracować Developer”, ale przede wszystkim:
- kiedy wolno przekazać pracę dalej,
- co musi zawierać handoff,
- kiedy zatwierdzenie jest legalne,
- kto weryfikuje eksport i na jakiej podstawie.

To są cechy **procesu współdzielonego między rolami**, więc nie powinny być kopiowane do trzech niezależnych dokumentów roli.

### Proponowany podział
#### `workflows/bi_view_creation_workflow.md`
Zawartość:
- pełne 4 fazy;
- dla każdej fazy: objective, inputs, checklist, gate, output schema, allowed next states;
- wspólne definicje statusów (`PASS`, `BLOCKED`, `ESCALATE`);
- zasady retry/escalation;
- matryca odpowiedzialności między rolami.

#### `handoffs/bi_view_handoff_schema.md`
Zawartość:
- wspólny format payloadu;
- definicja wymaganych artefaktów;
- przykłady poprawnego i niepoprawnego handoffu.

#### `agents/*.md`
Zawartość:
- rola, narzędzia, ograniczenia, kiedy eskalować;
- które fazy agent może wykonywać;
- jak interpretować handoff received;
- lokalne heurystyki jakości.

### Zasada w runtime
Nie wstrzykuj całego workflow do każdego agenta na każdym kroku.  
Wstrzykuj:
1. dokument roli agenta,  
2. tylko aktualną fazę z workflow,  
3. handoff schema / output schema.

To daje Wam:
- jedno źródło prawdy procesu,
- mały prompt aktywny,
- mniej driftu,
- większą zgodność przy handoffach.

---

## 4) Konkretne techniki do zastosowania w Waszym workflow

## Technika A: Zastąpcie opis faz tabelą „Inputs / Steps / Gate / Output / Next”
Przykład:

| Pole | Zawartość |
|---|---|
| Phase | Verification |
| Owner | Analityk |
| Inputs required | spec widoku, eksport, lista pól |
| Steps | 1. Sprawdź zgodność eksportu, 2. Zweryfikuj pola, 3. Zapisz wynik |
| Exit gate | eksport istnieje i został sprawdzony; brak krytycznych rozbieżności |
| Required output | status + checks_performed + artifacts + missing_items |
| Next | Developer only if PASS |

**Efekt:** mniej miejsca, większa salience, łatwiejsze utrzymanie.

---

## Technika B: Wprowadźcie binarny status fazy
Każda faza kończy się wyłącznie jednym z:
- `PASS`
- `BLOCKED`
- `ESCALATE`

Nie używajcie „prawie gotowe”, „wygląda dobrze”, „przekazuję dalej mimo braku eksportu”.

---

## Technika C: Dodajcie obowiązkowy handoff payload
Każdy handoff musi zawierać co najmniej:
- `phase_completed`
- `status`
- `required_artifacts`
- `evidence_of_verification`
- `open_issues`
- `exact_next_action`

Brak któregoś pola = automatyczny `BLOCKED`.

---

## Technika D: Dodajcie sekcję „Forbidden actions”
To bardzo praktyczne w promptach produkcyjnych. Np.:
- nie zatwierdzaj bez weryfikacji;
- nie przekazuj do developera bez eksportu;
- nie zakładaj brakujących informacji;
- nie zamykaj fazy, jeśli handoff payload jest niepełny.

Anthropic wręcz sugeruje, by mówić modelowi jasno, jakie są constraints i oczekiwany format; LangChain/CrewAI pokazują, że ważniejsze jest kontrolowanie stanu i outputu niż miękka persona. [1][10][12]

---

## Technika E: Dodajcie 1–2 few-shot examples na fazę
Na każdą krytyczną fazę:
- przykład `PASS`,
- przykład `BLOCKED`.

Szczególnie ważne przy:
- eksporcie,
- weryfikacji,
- zatwierdzeniu,
- handoffie do kolejnej roli.

---

## Technika F: Uczyńcie eksport i weryfikację artefaktami, nie opisami
Zamiast prosić:
> „upewnij się, że eksport został wykonany”

wymuście:
- `export_artifact_path`
- `export_checksum / timestamp / identifier`
- `verification_summary`
- `verified_by_role`

To jest praktyczny odpowiednik structured output + gate.

---

## Technika G: Rozdzielcie „planowanie” od „wykonania”
Dla każdej fazy:
1. plan / analiza wejścia,
2. wykonanie,
3. weryfikacja,
4. handoff.

Nie łączcie wszystkiego w jeden blok instrukcji typu „zrób fazę”.

---

## Technika H: Przenieście wspólne słowniki i statusy do jednego miejsca
Np.:
- definicje statusów,
- definicje artefaktów,
- formaty nazw,
- kryteria PASS/BLOCKED,
- zasady eskalacji.

To ogranicza drift i niezgodność między agentami.

---

## Technika I: Dodajcie jawny limit dopuszczalnych przejść
Przykład:
- ERP Specialist może przejść tylko do `Analityk.Review`
- Analityk może przejść tylko do `Developer.Implementation`
- Developer nie może sam przejść do `Approved`
- Approval wymaga poprzedniego `Verification.PASS`

To jest „soft GraphFlow” zapisany w dokumencie.

---

## Technika J: Obserwowalność promptów
Jeżeli używacie frameworka, logujcie:
- finalny system prompt,
- finalny user prompt,
- handoff payload,
- powód `PASS/BLOCKED`.

CrewAI wprost ostrzega, że framework może automatycznie doklejać instrukcje. [15]

---

## 5) Co NIE działa / antywzorce

Poniższe punkty są częściowo bezpośrednio potwierdzone przez źródła, a częściowo są ostrożną inferencją z dokumentacji frameworków i badań.

### Antywzorzec 1: **Workflow opisany jako proza**
Długi opis „jak zwykle pracujemy” bez checklisty, gate’u i output schema zostawia modelowi zbyt dużo miejsca na interpretację.

**Skutek:** pomijanie kroków, mylenie obowiązków, „zatwierdzenie z rozpędu”.

---

### Antywzorzec 2: **Duplikowanie wspólnego workflow w każdym dokumencie agenta**
To prawie zawsze prowadzi do driftu: jedna rola ma nowy gate, druga jeszcze stary.

**Skutek:** niespójne handoffy i trudny auditing.

---

### Antywzorzec 3: **Poleganie na roli/backstory zamiast na task spec**
CrewAI dość jednoznacznie mówi, że większość wysiłku powinna iść w task design, nie agent persona. [12]

**Skutek:** agent „brzmi fachowo”, ale procesowo nadal pomija kroki.

---

### Antywzorzec 4: **Brak jawnego formatu odpowiedzi / handoffu**
Jeżeli kolejny agent dostaje esej zamiast kontraktu danych, będzie rekonstruował brakujące informacje z narracji.

**Skutek:** utrata informacji i błędy na styku ról.

---

### Antywzorzec 5: **Zbyt krótki prompt przez amputację wymagań**
Skracanie przez usuwanie warunków, kontekstu domenowego i examples pogarsza compliance. [17]

---

### Antywzorzec 6: **Monolityczny długi prompt z ważnymi regułami zakopanymi w środku**
Badania long-context pokazują, że ważne informacje w środku bywają wykorzystywane gorzej niż te z początku i końca. [18]

---

### Antywzorzec 7: **Dynamiczne, swobodne handoffy tam, gdzie potrzebny jest ścisły proces**
Swarm/handoffs są użyteczne, ale dla Waszego typu procesu łatwo dopuścić lokalną decyzję „już chyba można przekazać dalej”. AutoGen sam wskazuje, że GraphFlow daje precyzyjną kontrolę, a przy równoległych handoffach mogą występować nieoczekiwane zachowania. [4][6]

---

### Antywzorzec 8: **Brak kontroli nad rzeczywistym promptem frameworka**
Jeżeli framework dokleja instrukcje, a zespół ich nie widzi, to prompt compliance bywa pozorny. [15]

---

## 6) Konkretny szablon do wdrożenia w Waszym projekcie

Poniżej szablon, który warto zastosować jako wzorzec dla każdej z 4 faz:

````md
# Phase: <PHASE_NAME>

## Purpose
Jednozdaniowy cel fazy.

## Owner
<ERP Specialist | Analityk | Developer>

## Inputs required
- ...
- ...
- ...

## Steps (mandatory)
1. ...
2. ...
3. ...
4. ...

## Required artifacts
- ...
- ...

## Forbidden actions
- Nie przechodź do następnej fazy bez ...
- Nie oznaczaj jako PASS bez ...
- Nie zgaduj brakujących danych.

## Exit gate
Faza kończy się jako PASS tylko jeśli:
- ...
- ...
- ...

Jeśli którykolwiek warunek nie jest spełniony:
- status = BLOCKED
- missing_items musi zawierać wszystkie braki

## Output format
```json
{
  "phase": "<PHASE_NAME>",
  "owner": "<ROLE>",
  "status": "PASS|BLOCKED|ESCALATE",
  "artifacts": [],
  "checks_performed": [],
  "missing_items": [],
  "verification_summary": "",
  "next_role": "",
  "next_expected_action": ""
}
```

## Handoff rule
Przekazanie do kolejnej roli jest dozwolone tylko przy `status = PASS`.

## Self-check before finish
- Czy wszystkie kroki zostały wykonane?
- Czy wszystkie wymagane artefakty istnieją?
- Czy gate jest spełniony?
- Jeśli nie, zwróć BLOCKED.
````

---

## 7) Finalna rekomendacja dla Waszego przypadku

### Najlepsza decyzja architektoniczna
1. **Utwórzcie osobny folder `workflows/` i trzymajcie tam kanoniczny workflow BI.**
2. **Trzymajcie dokumenty agentów osobno**, ale odchudźcie je do:
   - roli,
   - narzędzi,
   - lokalnych ograniczeń,
   - mapowania do faz.
3. **Dodajcie wspólny dokument handoff schema.**
4. **W runtime podawajcie agentowi tylko aktualną fazę, nie cały workflow.**
5. **Każdą fazę kończcie structured output + PASS/BLOCKED gate.**

### Co to rozwiąże u Was
- brak eksportu → złapie gate na artefakcie;
- zatwierdzenie bez weryfikacji → zablokuje `Forbidden actions` + `Exit gate`;
- problemy przy handoffach → ograniczy je handoff contract;
- drift między rolami → zredukuje go jeden procesowy source of truth.

---

## Bibliografia / źródła

[1] Anthropic, *Claude Prompting Best Practices* (jasne instrukcje, sekwencyjne kroki, examples, XML, self-check).  
https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

[2] R. M. Kirk et al., *TICKing All the Boxes: Generated Checklists Improve LLM Evaluation and Generation*, arXiv:2410.03608, 2024.  
https://arxiv.org/abs/2410.03608

[3] LangChain / LangGraph, *Interrupts* (approve/reject, review/edit state, pause before critical action).  
https://docs.langchain.com/oss/python/langgraph/interrupts

[4] Microsoft AutoGen, *GraphFlow (Workflows)* (structured execution, conditional edges, activation groups, exit conditions).  
https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/graph-flow.html

[5] CrewAI, *Production Architecture* + *Tasks* (task guardrails, structured outputs, task dependencies/context).  
https://docs.crewai.com/en/concepts/production-architecture  
https://docs.crewai.com/en/concepts/tasks

[6] Microsoft AutoGen, *Handoffs* / *Swarm* / agent reference (handoff pattern, shared context, first handoff only, avoid parallel handoff confusion).  
https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/handoffs.html  
https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html  
https://microsoft.github.io/autogen/0.4.4/reference/python/autogen_agentchat.agents.html

[7] LangChain, *Subagents* (supervisor only sees final output, subagent outputs must be explicit, context isolation).  
https://docs.langchain.com/oss/python/langchain/multi-agent/subagents

[8] LangChain, *Structured output* (provider-native structured output as most reliable, schema validation).  
https://docs.langchain.com/oss/python/langchain/structured-output

[9] Y. Wu et al., *StateFlow: Enhancing LLM Task-Solving through State-Driven Workflows*, arXiv:2403.11322, 2024.  
https://arxiv.org/abs/2403.11322

[10] LangChain, *Workflows and agents* + *Context engineering in agents* + Graph API overview.  
https://docs.langchain.com/oss/python/langgraph/workflows-agents  
https://docs.langchain.com/oss/python/langchain/context-engineering  
https://docs.langchain.com/oss/javascript/langgraph/graph-api

[11] LangChain, *Subagents* / supervisor pattern.  
https://docs.langchain.com/oss/python/langchain/multi-agent/subagents  
https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant

[12] CrewAI, *Crafting Effective Agents* (80/20: task design over agent definition).  
https://docs.crewai.com/en/guides/agents/crafting-effective-agents

[13] Microsoft AutoGen, *SelectorGroupChat* (planner assigns tasks, explicit terminate, custom selector prompt).  
https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/selector-group-chat.html

[14] Anthropic, *Create custom subagents* (own context window, custom system prompt, tool restrictions, context isolation).  
https://code.claude.com/docs/en/sub-agents

[15] CrewAI, *Customizing Prompts* (production transparency issue, default prompt injection, inspect real prompt).  
https://docs.crewai.com/en/guides/advanced/customizing-prompts

[16] CrewAI, *Introduction* / *Human-in-the-Loop* / *Hierarchical Process* (Flows as process backbone, crews as workers, manager validates results, explicit delegation control).  
https://docs.crewai.com/en/introduction  
https://docs.crewai.com/en/learn/human-in-the-loop  
https://docs.crewai.com/en/learn/hierarchical-process

[17] Q. Liu, W. Wang, J. Willard, *Effects of Prompt Length on Domain-specific Tasks for Large Language Models*, arXiv:2502.14255, 2025.  
https://arxiv.org/abs/2502.14255

[18] N. F. Liu et al., *Lost in the Middle: How Language Models Use Long Contexts*, TACL / arXiv:2307.03172, 2023.  
https://arxiv.org/abs/2307.03172

[19] Anthropic, *Increase output consistency* (prompt chaining, retrieval, role consistency).  
https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency
