
# Wymuszanie reguł behawioralnych na agentach LLM
**Temat:** jak skutecznie egzekwować ograniczenia behawioralne na agencie LLM działającym w pętli tool-use  
**Data:** 2026-03-16

## TL;DR

Samo `CLAUDE.md` prawie na pewno nie wystarczy. W agencie tool-use reguła w prompcie jest tylko **miękką preferencją**, która konkuruje z:
1. dominującymi wzorcami z pretrainingu (`cat`, `grep`, `find`, `head`, `tail` są znacznie bardziej „naturalne” niż lokalne narzędzia typu `Read`, `Grep`, `Glob`),
2. spadającą saliencją reguł w długim i zmieniającym się kontekście,
3. niejednoznacznością zestawu narzędzi (jeśli kilka narzędzi „umie prawie to samo”, model będzie wybierał niekonsekwentnie),
4. szczególną słabością modeli do **instrukcji negatywnych** („nie rób X”). [3][4][8][10]

Najskuteczniejsze podejścia to **przeniesienie reguły z promptu do warstwy wykonawczej**:
- **najmocniejsze:** usunięcie zakazanych możliwości z `allowed_tools` / rozdzielenie ról na subagenty z różnymi toolsetami,
- **bardzo mocne:** synchroniczny `PreToolUse` blokujący `Bash` z zakazanymi komendami i zwracający naprawczą informację typu „użyj Read/Grep/Glob”,
- **pomocnicze, ale niewystarczające same:** pozytywne reguły w promptach, przykłady few-shot, powtórzenie reguły w kilku miejscach. [1][2][7][8][9][10]

**Rekomendacja dla tego projektu:**  
1. **Nie polegać na dokumentacji jako głównym mechanizmie enforcementu.**  
2. **Jeśli to możliwe: odciąć `Bash` od agentów eksploracyjnych** i dać im tylko `Read`, `Grep`, `Glob`.  
3. **Jeśli `Bash` musi zostać:** wdrożyć **synchroniczny lokalny `PreToolUse` command hook** dla `Bash`, który wykrywa `cat|head|tail|grep|rg|find|ls` i zwraca `permissionDecision: "deny"` z precyzyjną instrukcją naprawczą.  
4. W `CLAUDE.md` przepisać reguły z formy zakazu na formę **routingową**: „jeśli chcesz X, użyj Y”, plus 3–5 krótkich przykładów. [1][2][4][7][8]

---

## 1. Dlaczego dokumentacja nie wystarcza

### 1.1. Prompt nie jest enforcementem, tylko miękkim sygnałem sterującym

Anthropic wprost rozróżnia prompt engineering od mocniejszych form kontroli i zaznacza, że **nie każda porażka evali powinna być rozwiązywana promptem**. Równocześnie ich dokumentacja hooków opisuje hooki jako warstwę dającą **deterministyczną kontrolę** nad zachowaniem Claude Code, „zamiast polegać na tym, że LLM sam wybierze właściwe działanie”. [1][7]

To jest sedno problemu:  
- prompt mówi modelowi, **co powinien zrobić**,  
- hook / ograniczenie toolsetu decyduje, **co agent w ogóle może wykonać**.

Gdy stawką jest przestrzeganie reguły operacyjnej („nie używaj `cat`, użyj `Read`”), sam prompt przegrywa z mechanizmem wykonawczym niemal zawsze, gdy tylko model „wpadnie” na inny lokalnie sensowny plan.

### 1.2. W długim kontekście reguła traci saliencję

W pracy **Lost in the Middle** pokazano, że modele gorzej wykorzystują informacje umieszczone w środku długiego kontekstu; wydajność jest zwykle najwyższa dla informacji z początku lub końca, a istotnie spada, gdy potrzebna informacja leży „w środku”. [3]

To bardzo dobrze pasuje do obserwacji z agentów:
- reguła trafia do `CLAUDE.md`,
- potem agent gromadzi historię rozmowy, wyniki narzędzi, streszczenia, plany i błędy,
- w chwili wyboru kolejnego tool calla reguła może być już **słabo aktywna**.

Anthropic opisuje to szerzej jako problem **context engineering**: w długich pętlach agenta „context rot” i skończony „attention budget” obniżają zdolność do niezawodnego przywołania właściwej instrukcji. [2]

### 1.3. Instrukcje negatywne są szczególnie kruche

To nie jest tylko intuicja. Praca **Can Large Language Models Truly Understand Prompts? A Case Study with Negated Prompts** pokazała, że dla negowanych promptów pojawia się wręcz **inverse scaling law**: większe modele nie poprawiają się, lecz wypadają gorzej, a różnica między promptem pozytywnym i negowanym jest duża. Autorzy raportują, że różne typy modeli „perform worse on negated prompts as they scale”. [4]

Dlatego reguła typu:

> „Nie używaj `cat`, `grep`, `find`, `ls`...”

jest z definicji słabsza niż:

> „Jeśli chcesz przeczytać plik, użyj `Read`.”  
> „Jeśli chcesz wyszukać wzorzec, użyj `Grep`.”  
> „Jeśli chcesz znaleźć ścieżki, użyj `Glob`.”

Negacja bywa rozumiana, ale jest mniej niezawodna niż pozytywny routing akcji. [4][8]

### 1.4. Pretraining i „naturalność” formatu pchają model w stronę standardowych komend

Anthropic zaleca, by format narzędzi był „bliski temu, co model widział naturalnie w tekście w internecie”. [9] To ma praktyczną konsekwencję: `cat`, `grep`, `find`, `ls`, `head`, `tail` są wzorcami niezwykle częstymi w danych treningowych, podczas gdy projektowe narzędzia `Read`, `Grep`, `Glob` są relatywnie sztuczne i lokalne.

To nie znaczy, że model „ignoruje instrukcję złośliwie”. Bardziej prawdopodobny mechanizm jest taki:
- model rozpoznaje lokalny zamiar: „chcę podejrzeć plik”,
- aktywuje silnie utrwalony wzorzec: `cat path`,
- dopiero później instrukcja projektowa próbuje ten odruch nadpisać.

Jeżeli reguła nie jest bardzo salientna albo nie jest wsparta przez warstwę wykonawczą, wygra wzorzec częstszy i bardziej „ergonomiczny” z punktu widzenia modelu. To jest **architektoniczno-statystyczne**, a nie „psychologiczne” w ludzkim sensie. [2][4][9]

### 1.5. Problemem jest też overlap narzędzi, nie tylko posłuszeństwo

Anthropic pisze wprost, że częstą porażką są **nadmuchane zestawy narzędzi** i **niejednoznaczne punkty decyzyjne**: jeśli człowiek nie umie jednoznacznie powiedzieć, którego narzędzia użyć w danej sytuacji, agent też nie będzie umiał. Zalecają „minimal viable set of tools” i minimalny overlap funkcjonalny. [2]

To jest bardzo ważne dla Twojego case’u. Jeżeli agent ma jednocześnie:
- `Bash`, które „też potrafi czytać pliki i wyszukiwać tekst”,
- oraz `Read` / `Grep` / `Glob`, które robią to bardziej pożądanie,

to z punktu widzenia modelu masz **konkurencyjne affordance’y** dla tego samego zadania. Wtedy prompt mówi „preferuj A”, ale środowisko mówi „A i B oba działają”. Takie środowisko samo generuje naruszenia.

### 1.6. Samo „wie, ale nie robi” jest normalnym trybem awarii agentów

W nowszej literaturze o narzędziach problem nie jest opisywany jako zwykła „nieposłuszność”, tylko jako wynik słabego interfejsu i złego zestawu narzędzi. Praca **Learning to Rewrite Tool Descriptions for Reliable LLM-Agent Tool Use** pokazuje, że jakość opisów i schematów narzędzi jest realnym bottleneckiem, szczególnie gdy liczba kandydatów rośnie; narzędzia „human-oriented” często zawodzą jako interfejs dla agenta. [10]

W praktyce oznacza to:
- dokumentacja dla ludzi ≠ dobre sterowanie agentem,
- „narzędzie zakazane, ale dostępne” to nadal narzędzie bardzo prawdopodobne do użycia,
- lepsze opisy pomagają, ale same nie zastępują hard guardrail.

---

## 2. Czy `PreToolUse` jest skuteczniejszy niż prompt?

### 2.1. Tak — bo to warstwa wykonawcza, nie sugestia

Claude Code dokumentuje hooki jako mechanizm „deterministic control”. `PreToolUse` uruchamia się **przed** wykonaniem narzędzia i może:
- dopuścić wywołanie,
- odmówić (`permissionDecision: "deny"`),
- poprosić użytkownika (`"ask"`),
- a także zmodyfikować input (`updatedInput`). [1]

Oficjalna dokumentacja mówi wprost, że przy `deny` Claude Code **anuluje tool call** i przekazuje `permissionDecisionReason` z powrotem do Claude jako feedback. [1]

To jest zasadniczo silniejsze niż prompt, bo nawet jeśli model wybierze złą akcję, środowisko ją zatrzymuje.

### 2.2. Czy `deny + reason` „uczy” model w sesji?

**Tak, ale tylko lokalnie i nietrwale.**

Co wiemy twardo:
- Claude Code przekazuje reason z hooka z powrotem do modelu jako feedback. [1]
- W pracy **Reflexion** pokazano, że językowy feedback i refleksja nad błędem poprawiają kolejne próby agenta w następnych iteracjach. [6]

Najrozsądniejszy wniosek praktyczny jest więc taki:
- `deny + "użyj Read zamiast cat"` często **zwiększy szansę**, że agent poprawi się w tej samej sesji,
- ale to **nie jest trwałe uczenie wag**, tylko adaptacja in-context,
- po nowej sesji, compaction albo zmianie kontekstu efekt może zniknąć.

Czyli: **tak, pomaga jako mechanizm naprawczy, ale nie należy go mylić z trwałym wytrenowaniem zachowania**. [1][6]

### 2.3. Ograniczenia hook-based enforcement

Hooki są bardzo mocne, ale nie magiczne.

**(a) Są reaktywne, nie prewencyjne poznawczo**  
Agent najpierw wybiera zły plan, a dopiero potem zostaje zatrzymany. To zwiększa liczbę kroków i może prowadzić do krótkich pętli naprawczych.

**(b) Działają tylko na tym, co umiesz wykryć**  
Jeśli blokujesz tylko literalne `cat `, model może przejść na `sed -n '1,200p'`, `awk`, `perl`, `while read`, itp. Reguła musi więc wykrywać **intencję klasy komend**, nie tylko jeden token.

**(c) HTTP hooki nie są fail-closed**  
Anthropic dokumentuje, że dla HTTP hooków `non-2xx`, timeouty i connection failures są **non-blocking** i wykonanie idzie dalej. Dla krytycznego enforcementu to oznacza, że zdalny serwis walidacyjny jest słabszy niż lokalny command hook. [1]

**(d) Async hooki nie nadają się do enforcementu**  
Async hooki uruchamiają się po fakcie; dokumentacja mówi wprost, że nie mogą blokować ani kontrolować zachowania. [1]

**(e) `PostToolUse` nie cofnie szkody**  
Anthropic podkreśla, że `PostToolUse` nie może cofnąć akcji, bo narzędzie już się wykonało. Do enforcementu musi być `PreToolUse`. [1]

**(f) Command hook nie przełączy Ci narzędzia**  
Command hook może zablokować albo zwrócić structured decision, ale sam nie „wywoła za model” `Read` czy `Grep`; może najwyżej wytłumaczyć, co model ma zrobić dalej. [1]

Wniosek: hook jest bardzo skuteczny jako **hard stop + repair signal**, ale najlepsze wyniki daje dopiero razem z redukcją overlapu narzędzi.

---

## 3. Alternatywne podejścia: co działa, a co zawodzi

### 3.1. Usunięcie zakazanych możliwości z toolsetu
**Skuteczność: najwyższa**

To jedyna metoda, która naprawdę eliminuje klasę naruszeń, bo agent nie może wybrać zakazanej ścieżki, jeśli ona nie istnieje. Anthropic explicite pokazuje, że subagenty można ograniczać do konkretnych narzędzi i że redukuje to ryzyko niepożądanych działań; podają wręcz przykład subagenta z dostępem tylko do `Read` i `Grep`. [5]

Jeśli eksploracja kodu ma używać `Read/Grep/Glob`, to najczystszy design to:
- **subagent eksploracyjny:** `Read`, `Grep`, `Glob`,
- **subagent wykonawczy:** `Bash` (gdy naprawdę potrzebny),
- główny agent deleguje zadania zależnie od typu pracy.

To nie tylko egzekwuje regułę; to także zmniejsza niejednoznaczność wyboru narzędzia. [2][5]

### 3.2. `PreToolUse` deny dla `Bash` z zakazanymi komendami
**Skuteczność: bardzo wysoka**

To najlepszy wariant, jeśli `Bash` musi pozostać dostępny. Oficjalnie wspierany, deterministyczny, działa przed wykonaniem, może zwrócić precyzyjną przyczynę i feedback do modelu. [1]

Najlepsza praktyka:
- hook **lokalny** (`type: "command"`), nie HTTP, dla fail-closed na poziomie procesu,
- **synchronczny**, nie async,
- reason w formacie **naprawczym**, np.  
  - „Do odczytu plików użyj `Read`, nie `cat/head/tail`.”  
  - „Do wyszukiwania tekstu użyj `Grep`, nie `grep/rg`.”  
  - „Do wyszukiwania ścieżek użyj `Glob`, nie `find/ls`.”

### 3.3. Przeprojektowanie opisów narzędzi i minimalizacja overlapu
**Skuteczność: wysoka, ale wspierająca**

Literatura i dokumentacja Anthropic są tu zgodne:
- narzędzia muszą mieć **jasne granice**, mały overlap i być „obvious” dla modelu,
- dobre opisy i parametry realnie poprawiają wybór narzędzi,
- duże, nakładające się zestawy narzędzi pogarszają zachowanie. [2][9][10]

To podejście jest ważne, ale nie daje twardej gwarancji. Traktowałbym je jako **warstwę redukującą częstość naruszeń**, nie jako enforcement sam w sobie.

### 3.4. Pozytywne reguły i few-shot zamiast samych zakazów
**Skuteczność: średnia**

Anthropic zaleca jasne, bezpośrednie instrukcje oraz przykłady; „examples are one of the most reliable ways to steer” oraz „For an LLM, examples are the pictures worth a thousand words.” [2][8]

Dlatego lepszy prompt to nie lista zakazów, tylko coś w stylu:

- Jeśli chcesz przeczytać zawartość pliku → użyj `Read`.
- Jeśli chcesz znaleźć wzorzec w plikach → użyj `Grep`.
- Jeśli chcesz znaleźć pliki lub ścieżki → użyj `Glob`.
- `Bash` używaj tylko do operacji, których nie da się wykonać przez `Read/Grep/Glob`.

Plus 3–5 mini-przykładów.

To działa zauważalnie lepiej niż „nie rób X”, ale nadal pozostaje miękkim sterowaniem. [4][8]

### 3.5. Constitutional AI / auto-krytyka / prompt-based hooks
**Skuteczność: średnia do niskiej jako enforcement, dobra jako recovery**

Constitutional AI i Reflexion pokazują, że self-critique oraz językowy feedback mogą poprawiać zachowanie i zwiększać zgodność z regułami. [6][11] Nowsze wyniki wokół **instruction hierarchy** pokazują też, że prawdziwa odporność na konflikt instrukcji najlepiej powstaje na etapie **treningu modelu**, nie przez sam prompt. [12][13]

W praktyce jednak:
- prompt-based / agent-based hook to nadal **kolejny modelowy osąd**,
- więc nie daje takiej gwarancji jak prosty deterministyczny parser komend,
- jest dobry, gdy trzeba rozstrzygać subtelne przypadki,
- jest słaby, gdy reguła jest prosta i syntaktyczna.

Dla Twojego use-case’u (`cat/head/tail`, `grep/rg`, `find/ls`) to jest overkill. Najlepszy będzie hook deterministyczny, nie LLM-owy.

### 3.6. Powtarzanie reguły w wielu miejscach dokumentacji
**Skuteczność: niska do średniej**

To może trochę zwiększyć saliencję, ale nie rozwiązuje podstawowego problemu. Anthropic wyraźnie ostrzega przed wrzucaniem „laundry list of edge cases” do promptu; zaleca raczej minimalne, jasne instrukcje i kanoniczne przykłady niż rozrastającą się listę zakazów. [2]

Powtarzanie reguły ma sens tylko jako **warstwa wspierająca**:
- `CLAUDE.md`,
- dokument roli,
- sekcja `## Tool guidance`,
- przykład few-shot.

Nigdy jako jedyny mechanizm enforcementu.

---

## 4. Ranking podejść enforcement

### Ranking ogólny (od najmocniejszego do najsłabszego)

**1. Usunięcie możliwości z toolsetu / rozdzielenie na subagentów z różnymi toolami**  
Najsilniejszy mechanizm, bo eliminuje klasę błędów zamiast prosić model, żeby ich nie popełniał. [2][5]

**2. Synchroniczny lokalny `PreToolUse` hook dla `Bash` z `deny` + komunikatem naprawczym**  
Prawie tak mocny jak #1, jeśli `Bash` musi istnieć. To właściwy runtime guardrail. [1]

**3. Redukcja overlapu narzędzi + dopracowane opisy i parametry narzędzi**  
Bardzo przydatne do zmniejszenia liczby naruszeń i niejednoznacznych decyzji, ale bez twardej gwarancji. [2][9][10]

**4. Pozytywne reguły „jeśli X, użyj Y” + few-shot examples**  
Dobre jako steerowanie, szczególnie lepsze niż zakazy, ale nadal miękkie. [4][8]

**5. Prompt-/agent-based self-check / constitutional-style krytyka przed akcją**  
Może poprawić zachowanie i recovery, ale nie daje deterministycznej gwarancji przy prostych regułach syntaktycznych. [6][11][13]

**6. Sama dokumentacja (`CLAUDE.md`, role docs) z listą zakazów**  
Najsłabsze. Pomaga tylko wtedy, gdy wszystko inne już jest dobrze ustawione.

---

## 5. Konkretna rekomendacja dla tego projektu

## 5.1. Co wdrożyć teraz

### A. Wdrożyć `PreToolUse` na `Bash` jako twardy guardrail
Dla krytycznego enforcementu polecam **lokalny command hook**, nie HTTP hook.

**Dlaczego lokalny command hook?**
- jest prosty,
- działa przed wykonaniem,
- nie zależy od sieci,
- nie ma problemu „timeout = non-blocking” charakterystycznego dla HTTP hooków. [1]

### B. W `CLAUDE.md` przepisać reguły na routing akcji
Zamiast:

- nie używaj `cat`
- nie używaj `grep`
- nie używaj `find`

użyć:

- jeśli chcesz przeczytać plik, użyj `Read`
- jeśli chcesz wyszukać tekst, użyj `Grep`
- jeśli chcesz znaleźć pliki/ścieżki, użyj `Glob`
- `Bash` jest do komend, których nie da się wykonać przez `Read/Grep/Glob`

I dodać 3–5 krótkich przykładów.

### C. W średnim terminie: rozdzielić role na subagentów
Najlepszy docelowy układ:
- **research / code-reading agent:** `Read`, `Grep`, `Glob`
- **execution agent:** `Bash`
- **editor agent:** narzędzia edycji

To usuwa overlap i zmniejsza obciążenie promptu. [2][5]

---

## 6. Proponowana implementacja

### 6.1. `settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validate_bash_tool.py"
          }
        ]
      }
    ]
  }
}
```

### 6.2. `validate_bash_tool.py`

```python
#!/usr/bin/env python3
import json
import re
import shlex
import sys

payload = json.load(sys.stdin)
command = ((payload.get("tool_input") or {}).get("command") or "").strip()

def deny(reason: str) -> int:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }))
    return 0

if not command:
    sys.exit(0)

try:
    argv = shlex.split(command)
except ValueError:
    # Nie parsuje się? Lepiej przepuścić lub zablokować wg polityki.
    sys.exit(0)

if not argv:
    sys.exit(0)

first = argv[0]

READ_CMDS = {"cat", "head", "tail"}
SEARCH_CMDS = {"grep", "rg"}
GLOB_CMDS = {"find", "ls"}

if first in READ_CMDS:
    sys.exit(deny(
        "Do odczytu plików użyj Read zamiast cat/head/tail."
    ))

if first in SEARCH_CMDS:
    sys.exit(deny(
        "Do wyszukiwania tekstu użyj Grep zamiast grep/rg."
    ))

if first in GLOB_CMDS:
    sys.exit(deny(
        "Do wyszukiwania plików i ścieżek użyj Glob zamiast find/ls."
    ))

# Opcjonalnie: wykrywaj też bardziej złożone wzorce.
if re.search(r"\b(cat|head|tail)\b", command):
    sys.exit(deny(
        "Wykryto komendę do odczytu plików w Bash. Użyj Read."
    ))

if re.search(r"\b(grep|rg)\b", command):
    sys.exit(deny(
        "Wykryto komendę do wyszukiwania tekstu w Bash. Użyj Grep."
    ))

if re.search(r"\b(find|ls)\b", command):
    sys.exit(deny(
        "Wykryto komendę do wyszukiwania ścieżek w Bash. Użyj Glob."
    ))

sys.exit(0)
```

### 6.3. Dlaczego `permissionDecision: "deny"` zamiast tylko `exit 2`?
Oba podejścia działają. `exit 2` też blokuje `PreToolUse`. Jednak structured JSON z `permissionDecision: "deny"` daje czytelniejszy, jawny kontrakt i precyzyjny komunikat naprawczy. Dokumentacja Anthropic wspiera oba tryby; JSON na `exit 0` to „finer-grained control”, a `deny` pokazuje Claude reason. [1]

### 6.4. Co dopisać do `CLAUDE.md`

Proponowany minimalny blok:

```md
## Tool routing (obowiązkowe)

- Jeśli chcesz przeczytać zawartość pliku, użyj `Read`.
- Jeśli chcesz znaleźć tekst lub regex w plikach, użyj `Grep`.
- Jeśli chcesz znaleźć pliki, katalogi lub ścieżki, użyj `Glob`.
- Nie używaj `Bash` do zadań, które da się wykonać przez `Read`, `Grep` lub `Glob`.

Przykłady:
- "Pokaż zawartość src/app.ts" → `Read`
- "Znajdź wystąpienia UserService" → `Grep`
- "Znajdź wszystkie pliki *.test.ts" → `Glob`
```

To nie zastępuje hooka, ale poprawia pierwsze trafienie i zmniejsza liczbę deny-loopów. [2][4][8]

---

## 7. Czego bym nie robił jako głównej strategii

### 7.1. Nie opierałbym enforcementu na samym `CLAUDE.md`
To jest dokumentacja, nie kontrola wykonawcza.

### 7.2. Nie używałbym HTTP hooka jako jedynego guardrailu
Jeżeli endpoint padnie albo przekroczy timeout, dokumentacja mówi, że to jest błąd **non-blocking** i wykonanie idzie dalej. [1]

### 7.3. Nie robiłbym enforcementu przez `PostToolUse`
Za późno: narzędzie już się wykonało. [1]

### 7.4. Nie używałbym async hooków do blokowania
Async nie może blokować. [1]

### 7.5. Nie rozbudowywałbym promptu w nieskończoność
Anthropic ostrzega zarówno przed promptami zbyt ogólnymi, jak i zbyt „hardcoded”; zaleca minimalny, jasny prompt oraz przykłady zamiast rosnącej listy edge-case’ów. [2]

---

## 8. Najkrótsza odpowiedź na pytanie badawcze

**Jak skutecznie wymusić ograniczenia behawioralne na agencie LLM w pętli tool-use?**

Przez **przeniesienie ograniczeń z promptu do architektury i runtime’u**:
1. usuń zakazane affordance z toolsetu, gdzie tylko się da,
2. resztę zablokuj w `PreToolUse`,
3. prompt zostaw jako warstwę pomocniczą: jasny routing + przykłady.

**Co zawodzi i dlaczego?**
- Zawodzi sama dokumentacja, bo ginie w kontekście, konkuruje z pretrainingiem i jest szczególnie krucha, gdy ma formę negacji. [2][3][4]
- Zawodzą też szerokie, nakładające się zestawy narzędzi, bo wytwarzają niejednoznaczne decyzje tool-selection. [2][10]

**Najpraktyczniejsza rekomendacja dla tego projektu**
- **teraz:** `PreToolUse` deny dla `cat/head/tail`, `grep/rg`, `find/ls`,  
- **zaraz potem:** przepisać reguły na „if X → use Y” + przykłady,  
- **docelowo:** agent/subagent bez `Bash` do eksploracji kodu. [1][2][5][8]

---

## Źródła

[1] Anthropic, *Claude Code Hooks / Hooks Guide / Subagents*, 2026.  
- https://code.claude.com/docs/en/hooks  
- https://code.claude.com/docs/en/hooks-guide  
- https://code.claude.com/docs/en/sub-agents

[2] Anthropic, *Effective context engineering for AI agents*, 2025.  
https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

[3] Liu et al., *Lost in the Middle: How Language Models Use Long Contexts*, TACL 2024.  
https://aclanthology.org/2024.tacl-1.9/

[4] Jang, Ye, Seo, *Can Large Language Models Truly Understand Prompts? A Case Study with Negated Prompts*, 2023.  
https://arxiv.org/abs/2209.12711

[5] Anthropic, *Subagents in the SDK / Tool restrictions*, 2026.  
https://platform.claude.com/docs/en/agent-sdk/subagents

[6] Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning*, 2023.  
https://arxiv.org/abs/2303.11366

[7] Anthropic, *Prompt engineering overview*, 2026.  
https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview

[8] Anthropic, *Prompting best practices*, 2026.  
https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

[9] Anthropic, *Building effective agents*, 2024.  
https://www.anthropic.com/engineering/building-effective-agents

[10] Guo et al., *Learning to Rewrite Tool Descriptions for Reliable LLM-Agent Tool Use*, 2026.  
https://arxiv.org/html/2602.20426

[11] Bai et al., *Constitutional AI: Harmlessness from AI Feedback*, 2022/2023.  
https://arxiv.org/abs/2212.08073

[12] Wallace et al., *The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions*, 2024.  
https://arxiv.org/abs/2404.13208

[13] OpenAI, *Improving instruction hierarchy in frontier LLMs / IH-Challenge*, 2026.  
https://openai.com/index/instruction-hierarchy-challenge/
