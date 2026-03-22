# Eksperyment E3: Wymagania dla promptu autonomicznego

Data: 2026-03-22
Eksperymentator: Developer
Backlog: #114 — Plan eksperymentów: Runner wieloagentowy

---

## Cel

Zidentyfikować dlaczego agent może czekać na human input mimo promptu autonomicznego i ustalić wymagania dla Prompt Engineer.

---

## Stan obecny

### Prompt autonomiczny (runner_autonomous.md)

```
{role}
[TRYB AUTONOMICZNY — brak interakcji z użytkownikiem]
[TASK od: {sender}]
[ADRES ZWROTNY: {instance_id}]

Uruchom session_init --role {role}.

Gdy session_start mówi "Czekaj na instrukcję od użytkownika" — Twoja instrukcja to task poniżej.
Nie czekaj na kolejną wiadomość. Realizuj task zgodnie ze swoim workflow.

Task do realizacji:
{content}

Gdy skończysz — zaloguj przez agent_bus i zakończ sesję.
```

### Reguła w promptach ról (DEVELOPER.md, ERP_SPECIALIST.md, etc.)

Wszystkie role mają w `<session_start>`:

```
3. Jeśli widzisz [TRYB AUTONOMICZNY] gdziekolwiek w kontekście — task w kontekście jest Twoją instrukcją, przejdź do realizacji.
   W przeciwnym razie: czekaj na instrukcję od użytkownika — nie realizuj inbox automatycznie.
```

---

## Potencjalne problemy

### P1: Kolejność wstrzykiwania system prompt

**Obecna komenda (mrowisko_runner.py:166):**
```python
--append-system-prompt system_injection
```

**Wynikowy system prompt:**
```
[CLAUDE.md]
[DEVELOPER.md — z session_start: "czekaj na instrukcję"]
[--append-system-prompt: "[TRYB AUTONOMICZNY] Task: ..."]
```

**Problem:**
Agent czyta promptu sekwencyjnie. Gdy dochodzi do linii:
> "czekaj na instrukcję od użytkownika"

może zatrzymać wykonanie **zanim** dotrze do `[TRYB AUTONOMICZNY]` na końcu.

**Rozwiązanie:**
- Opcja A: `--system-prompt` zamiast `--append-system-prompt` (zastąpienie całości)
- Opcja B: Reguła `[TRYB AUTONOMICZNY]` **na początku** session_start (przed "czekaj na instrukcję")
- Opcja C: Dedykowany tryb `--permission-mode autonomous` (jeśli istnieje w Claude Code)

---

### P2: Workflow gate wymaga wyboru

**Obecna reguła (CLAUDE.md):**
> Przed rozpoczęciem każdego zadania:
> 1. Dopasuj zadanie do dostępnego workflow swojej roli.
> 2. Powiedz użytkownikowi: "Wchodzę w workflow: [nazwa]."

**Problem:**
Agent może czekać na potwierdzenie wyboru workflow przed działaniem.

**Rozwiązanie:**
W trybie autonomicznym: workflow wybierany automatycznie bez komunikatu do użytkownika.

Wariant promptu autonomicznego:
```
[TRYB AUTONOMICZNY]
Workflow gate: wybierz workflow automatycznie, nie pytaj o potwierdzenie.
```

---

### P3: Brak jasnej instrukcji zakończenia

**Obecny prompt (runner_autonomous.md linia 14):**
```
Gdy skończysz — zaloguj przez agent_bus i zakończ sesję.
```

**Problem:**
"Zakończ sesję" może nie być wystarczająco jasne. Agent może:
- Czekać na kolejną komendę
- Nie wiedzieć jak zakończyć (brak `/exit` w Claude Code)

**Rozwiązanie:**
Jaśniejsza instrukcja:
```
Gdy skończysz task:
1. Zapisz log sesji przez agent_bus_cli.py log
2. Napisz: "Task zakończony. Sesja kończy się."
3. STOP — nie czekaj na kolejną wiadomość od użytkownika.
```

---

### P4: Max turns może być za niski

**Obecne ustawienie (mrowisko_runner.py:42):**
```python
MAX_TURNS = "8"
```

**Problem:**
Złożone taski mogą wymagać >8 tur (session_init → inbox → workflow → realizacja → log).

**Rozwiązanie:**
Zwiększyć do 15-20 dla autonomicznych sesji lub parametryzować per rola/task.

---

## Analiza komendy mrowisko_runner.py

### Obecna komenda (build_cmd, linia 163-176):

```python
[
    CLAUDE_CMD, "-p", prompt,
    "--output-format", "stream-json",           # ← Blokuje interaktywność
    "--verbose",
    "--include-partial-messages",
    "--no-session-persistence",                 # ← Nie można resumować
    "--append-system-prompt", system_injection, # ← Może być za późno
    "--max-turns", MAX_TURNS,
    "--max-budget-usd", MAX_BUDGET_USD,
    "--permission-mode", PERMISSION_MODE.get(role, "default"),
    "--tools", TOOL_SCOPE.get(role, "Read,Grep,Glob"),
]
```

### Problemy:

1. **`--output-format stream-json`** — blokuje interaktywność (człowiek nie może dołączyć)
2. **`--no-session-persistence`** — nie można resumować sesji (`--continue`)
3. **`--append-system-prompt`** — może wstrzykiwać za późno (po promptach ról)

### Propozycja zmian (dla v2):

```python
[
    CLAUDE_CMD, "-p", prompt,
    # BEZ --output-format (normalny terminal)
    "--verbose",
    # BEZ --no-session-persistence (pozwól resumowanie)
    "--system-prompt", full_system_prompt,  # Całość kontrolowana przez runner
    "--max-turns", "15",                     # Więcej dla złożonych tasków
    "--max-budget-usd", MAX_BUDGET_USD,
    "--permission-mode", "acceptEdits",      # Autonomiczny = auto-approve
    "--tools", TOOL_SCOPE.get(role, "Read,Grep,Glob"),
]
```

**Zmiana kluczowa:**
- `--system-prompt` zamiast `-p prompt + --append-system-prompt`
- Kontrola pełnego system promptu przez runner (złożenie: CLAUDE.md + rola + tryb autonomiczny)

---

## Wymagania dla Prompt Engineer

### Zadanie: Refaktor promptu autonomicznego

**Cel:** Zapewnić że agent **zawsze** wykonuje task bez czekania na human input.

**Zakres:**

1. **Rewizja runner_autonomous.md:**
   - Jasna instrukcja: "[TRYB AUTONOMICZNY]" ma pierwszeństwo przed "czekaj na instrukcję"
   - Workflow gate: wybór automatyczny, bez komunikatu do użytkownika
   - Zakończenie sesji: konkretna instrukcja (STOP po zakończeniu taska)

2. **Rewizja session_start we wszystkich rolach:**
   - Przenieść regułę `[TRYB AUTONOMICZNY]` **przed** "czekaj na instrukcję"
   - Przykład:

   **Przed:**
   ```
   3. Sprawdź flagi do człowieka...
   4. Czekaj na instrukcję od użytkownika.
   5. Jeśli widzisz [TRYB AUTONOMICZNY] — realizuj task.
   ```

   **Po:**
   ```
   3. Sprawdź flagi do człowieka...
   4. Jeśli widzisz [TRYB AUTONOMICZNY] gdziekolwiek w kontekście — task w kontekście jest Twoją instrukcją, przejdź do realizacji.
      W przeciwnym razie: czekaj na instrukcję od użytkownika.
   ```

3. **Dedykowany wariant promptu dla trybu autonomicznego:**
   - Opcja A: Osobny plik per rola (`DEVELOPER_AUTONOMOUS.md`)
   - Opcja B: Sekcja `<autonomous_mode>` w obecnym promptcie roli
   - Opcja C: Prompty w DB (Faza 3) z wariantem `mode: autonomous`

4. **Testowanie:**
   - Minimalne zadanie: "Wypisz zawartość katalogu narzędziem Glob (pattern: tools/*.py). Zakończ."
   - Złożone zadanie: "Sprawdź backlog Dev, jeśli są taski — pokaż mi listę. Zakończ."
   - Weryfikacja: agent wykonuje bez pytań + kończy sesję sam

---

## Output contract dla PE

**Plik wynikowy:** `documents/prompt_engineer/autonomous_prompt_refactor.md`

**Struktura:**

```markdown
# Refaktor promptu autonomicznego

## Problem (zdiagnozowany)
[Co blokuje autonomię?]

## Rozwiązanie
[Konkretne zmiany w promptach]

## Pliki zmienione
- runner_autonomous.md
- DEVELOPER.md (session_start)
- ERP_SPECIALIST.md (session_start)
- ...

## Test plan
[Jak przetestować że działa]

## Trade-offs
[Co tracemy zyskując autonomię]
```

---

## Następne kroki

1. **Developer → PE:** Handoff zadania refaktoru promptu autonomicznego
2. **PE:** Analiza + refaktor (zgodnie z wymaganiami powyżej)
3. **Developer:** Test E2 (terminal interaktywny) po wdrożeniu zmian PE
4. **Developer:** mrowisko_runner.py v2 (integracja wyników E1+E2+E3)

---

## Trade-offs: autonomia vs human-in-the-loop

| Aspekt | Autonomiczny | Human-in-the-loop |
|--------|--------------|-------------------|
| **Szybkość** | ✓ Błyskawiczny | ✗ Czeka na człowieka |
| **Kontrola** | ✗ Brak zatwierdzenia | ✓ Człowiek zatwierdza |
| **Błędy** | ✗ Eskalacja post-factum | ✓ Zapobieganie przed działaniem |
| **Skalowanie** | ✓ Setki tasków/dzień | ✗ Bottleneck na człowieku |
| **Koszt błędu** | Wysoki (auto-commit, auto-deploy) | Niski (dry-run, approval) |

**Rekomendacja:**
- Taski zaufane (powtarzalne workflow) → autonomiczny
- Taski ryzykowne (nowe obszary) → approval gate

---

**Status eksperymentu E3:** ✓ Zakończony (wymaga handoff do PE)

