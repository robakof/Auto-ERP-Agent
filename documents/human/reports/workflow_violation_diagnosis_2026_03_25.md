# Diagnoza: Naruszenie workflow convention_creation

Data: 2026-03-25
Sesja: 3642827904e5
Rola: Architect

## TL;DR

Dwa naruszenia workflow w jednej sesji. Pierwsze (pominięcie fazy) to klasyczny
pośpiech. Drugie (zły executor researchu) to problem strukturalny — workflow ma
niejawne punkty przekazania kontroli, które agent zinterpretował dowolnie.
Workflow nie jest nieskuteczny — ma luki w specyfikacji handoffów.

---

## Chronologia zdarzeń

### Naruszenie 1: Pominięcie Fazy 2 (Research)

| Krok | Co powinno | Co zrobił |
|------|-----------|-----------|
| User mówi: "P0 symultanicznie" | Faza 1 → Faza 2 (Research) per konwencja | Faza 1 → Faza 3 (Draft) |
| Execution | Research questions → PE → prompt → user → external | 3x Sonnet agent → drafty bez fundamentu |
| Koszt | - | ~170k tokenów na bezwartościowe drafty |

**Przyczyna bezpośrednia:** Architect usłyszał "symultanicznie" i zinterpretował
jako "odpal maszynę natychmiast" zamiast "rób 3 konwencje równolegle, każda
przez pełny workflow".

**Architect sam przyznał:** "Pośpiech. Usłyszałem symultanicznie i zamiast
powiedzieć OK, ale każda konwencja musi przejść przez research — odpaliłem maszynę."

### Naruszenie 2: Zły executor dla researchu (po korekcie)

User kazał wrócić do Fazy 2. Architect:

| Step z workflow | Co powinien zrobić | Co zrobił |
|-----------------|-------------------|-----------|
| Step 1: Pytania badawcze | Sformułować pytania | ✓ Zrobił poprawnie |
| Step 2: Ecosystem check | Sprawdzić czy jest baseline w Mrowisku | ? Pominął |
| **Step 3: Zamów prompt u PE** | **Wyślij msg do PE przez agent_bus** | ✗ Nie wysłał |
| Step 4: Wykonaj research | **User uruchamia prompt zewnętrznie** | ✗ Szykował się do własnego researchu |

Architect po sformułowaniu pytań zapytał: "Zatwierdzasz te pytania czy chcesz
coś dodać zanim ruszę z researchem?" — sugerując że SAM będzie robił research.

User odpowiedział "jest ok. zamawiaj" — gdzie "zamawiaj" oznaczało "zamów u PE"
(zgodnie z workflow Step 3), ale Architect zinterpretował jako "zamawiaj research
sam".

---

## Analiza przyczyn źródłowych

### 1. Workflow ma niejawne punkty STOP

Faza 2, Step 3 mówi:
```
3. Zamów research prompt u PE.
   - Lokalizacja: documents/researcher/prompts/research_{temat}.md
```

Ale NIE mówi:
- **JAK** zamówić (agent_bus send? wiadomość? handoff?)
- **STOP** — nie przechodź do Step 4 dopóki PE nie dostarczy promptu
- **KTO** wykonuje research w Step 4 (agent? user? zewnętrzne narzędzie?)

Step 4 mówi:
```
4. Wykonaj research (WebSearch lub zewnętrzny agent).
```

To jest dwuznaczne: "WebSearch" sugeruje że agent sam robi research.
"Zewnętrzny agent" nie precyzuje kto go odpala.

### 2. Brak konstruktu HANDOFF_POINT w workflow

Workflow opisuje CO ma się wydarzyć, ale nie WHERE kontrola przechodzi
na inną rolę/człowieka i agent MUSI się zatrzymać. Nie ma odróżnienia między:

- Krokiem który agent wykonuje sam (np. "sformułuj pytania")
- Krokiem który wymaga innej roli (np. "PE tworzy prompt")
- Krokiem który wymaga człowieka (np. "user uruchamia research zewnętrznie")

### 3. Persona kontra dyscyplina

Architect ma personę "wywrotowy perfekcjonista" który "proponuje zanim pytają"
i "prowadzi architekturę, nie tylko odpowiada na pytania". Ta proaktywność
w połączeniu z presją czasu ("symultanicznie") przesłoniła dyscyplinę procesową.

### 4. Brak mechanizmu wymuszania (enforcement)

Workflow jest advisory. `step-log` loguje kroki ale nie wymusza kolejności.
Agent może zalogować Step 4 bez zakończenia Step 3.

---

## Czy workflow/konwencje są nieskuteczne?

**Nie.** Workflow poprawnie opisuje proces. Problem jest w dwóch warstwach:

| Warstwa | Problem | Rozwiązanie |
|---------|---------|-------------|
| **Specyfikacja** | Niejawne handoffy, dwuznaczny executor | Explicit STOP points, precyzyjny executor |
| **Enforcement** | Brak wymuszania kolejności kroków | Opcjonalnie: walidacja w step-log |

Workflow convention_creation v1.1 jest architektonicznie poprawny.
Wymaga precyzji operacyjnej — dodania jawnych punktów STOP i specyfikacji KTO wykonuje.

---

## Rekomendacje

### R1: Dodać HANDOFF_POINT do workflows (Architect + PE)

Nowy konstrukt w CONVENTION_WORKFLOW:
```markdown
→ HANDOFF: [rola/human]. STOP. Nie przechodź dalej bez odpowiedzi.
  Mechanizm: [agent_bus send / flag / czekaj na user input]
```

Zastosowanie w convention_creation, Phase 2:
```markdown
3. Wyślij pytania badawcze do PE (agent_bus send --to prompt_engineer).
   → HANDOFF: PE. STOP. PE tworzy research prompt.

3.5. Czekaj na prompt od PE (documents/researcher/prompts/research_{temat}.md).
   → HANDOFF: Human. STOP. User wykonuje research zewnętrznie.

4. Odbierz wyniki researchu od usera i oceń.
```

### R2: Dodać regułę "pace" do ARCHITECT.md (PE)

```
Architekt NIGDY się nie spieszy. Przed wykonaniem kroku:
1. Zweryfikuj: na jakim kroku workflow jestem?
2. Czy poprzedni krok jest ZAKOŃCZONY?
3. Czy ten krok wymaga innej roli? Jeśli tak — STOP, wyślij, czekaj.
```

### R3: Usunąć dwuznaczność z Phase 2, Step 4

Obecne: "Wykonaj research (WebSearch lub zewnętrzny agent)."
Proponowane: "User wykonuje research prompt zewnętrznie. Architect odbiera wyniki."

### R4: (Opcjonalnie, Developer) Walidacja kolejności w step-log

`step-log` mógłby odmówić logowania Step N jeśli Step N-1 nie ma statusu PASS.
To enforcement na poziomie kodu, nie tylko tekstu.

---

## Podsumowanie

Workflow nie zawiódł — zawiodła jego precyzja w punktach przekazania kontroli.
Agent zinterpretował niejawne handoffy jako "zrób sam". Rozwiązanie to nie
więcej reguł, a jaśniejsze reguły: explicit STOP points w każdym workflow
gdzie kontrola przechodzi na inną rolę lub człowieka.
