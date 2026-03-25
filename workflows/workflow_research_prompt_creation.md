---
workflow_id: research_prompt_creation
version: "1.0"
owner_role: prompt_engineer
trigger: "PE otrzymuje zlecenie research promptu (od Architekta, Developera lub z backlogu)"
participants:
  - prompt_engineer (owner)
  - architect / developer (zlecający — dostarcza pytania badawcze)
  - human (uruchamia prompt w zewnętrznym narzędziu)
related_docs:
  - documents/prompt_engineer/PROMPT_CONVENTION.md
  - documents/researcher/prompts/research_convention_prompt.md
prerequisites:
  - session_init_done
  - zlecenie_exists
outputs:
  - type: file
    path: "documents/researcher/prompts/research_{temat}.md"
  - type: message
    field: "powiadomienie zlecającego o gotowym prompcie"
---

# Workflow: Tworzenie research promptu

PE tworzy self-contained research prompt do uruchomienia w zewnętrznym narzędziu (Claude, ChatGPT itp.).
Prompt musi zawierać pełną rolę researchera (base prompt) + zadanie badawcze + output contract.

## Outline

1. **Odczyt zlecenia** — zrozum co badamy i skąd pytania
2. **Draft promptu** — base prompt + zadanie badawcze
3. **Weryfikacja** — checklist kompletności
4. **Publikacja** — zapis + powiadomienie

---

## Faza 1: Odczyt zlecenia

**Owner:** PE

### Steps

1. Odczytaj zlecenie (message w inbox, backlog item, lub instrukcja od usera).
2. Zidentyfikuj:
   - Kto zleca (Architect, Developer, user)
   - Co badamy (temat, kontekst, cel)
   - Jakie pytania badawcze (dostarczone przez zlecającego lub do sformułowania przez PE)
   - Typ promptu: eksploracyjny (mapowanie terenu) vs weryfikacyjny (potwierdzenie hipotez)
   - Recency — jak ważna aktualność źródeł

### Exit gate

PASS: temat jasny, pytania zidentyfikowane, typ promptu wybrany.

---

## Faza 2: Draft promptu

**Owner:** PE

### Steps

1. Skopiuj base prompt researchera z referencji:
   `documents/researcher/prompts/research_convention_prompt.md` (linie 1-136)

   Base prompt zawiera:
   - Kim jesteś (persona researchera)
   - Workflow 5-fazowy (Scope → Breadth → Gaps → Verify → Write)
   - Jakość źródeł (polityka preferencji, triangulacja, konflikty)
   - Output contract (obowiązkowa struktura wyników)
   - Zasady krytyczne (5 reguł)
   - Forbidden (6 anti-patterns)
   - Przykład dobrego wyniku

2. Napisz sekcję "Zadanie badawcze" po base prompcie:
   ```markdown
   ## Zadanie badawcze

   # Research: [tytuł]

   ## Kontekst
   [Dlaczego badamy, jaki problem, jaki agent/system]
   [Recency: jakie źródła akceptowalne (np. "2025-2026")]
   [Czego NIE rób: zakaz oceny dopasowania do systemu]

   ## Obszary badawcze
   ### A. [Obszar 1]
   1. [Pytanie 1]
   2. [Pytanie 2]
   ### B. [Obszar 2]
   ...

   ## Output contract
   Zapisz wyniki do: `documents/researcher/research/research_results_{temat}.md`
   Struktura (obowiązkowa):
   - TL;DR — N najważniejszych odkryć z siłą dowodów
   - Wyniki per obszar — każdy osobno
   - Otwarte pytania / luki
   - Źródła — tytuł, URL, opis
   ```

3. Prompt MUSI być self-contained — external researcher nie ma kontekstu Mrowiska.
   Daj wystarczający kontekst w sekcji "Kontekst", ale nie zdradzaj implementacji systemu.

### Forbidden

- Prompt bez base prompt researchera — researcher nie wie jak pracować.
- Prompt bez output contract — wyniki w losowym formacie.
- Prompt z konkretnym narzędziem/modelem z pamięci PE — landscape się zmienia, researcher ma szukać aktualnych źródeł.
- Prompt z oceną dopasowania do systemu — to osobny krok po researchu.

### Exit gate

PASS: prompt zawiera base prompt + kontekst + pytania + output contract + recency.

---

## Faza 3: Weryfikacja

**Owner:** PE

### Steps

1. Checklist kompletności:
   - [ ] Base prompt researchera wklejony (persona, workflow, jakość źródeł, output contract, zasady, forbidden)?
   - [ ] Kontekst wystarczający dla external researchera (self-contained)?
   - [ ] Pytania badawcze konkretne (nie "zbadaj temat X")?
   - [ ] Recency zdefiniowane (np. "źródła 2025-2026")?
   - [ ] Zakaz oceny dopasowania do systemu?
   - [ ] Output contract ze ścieżką pliku wynikowego?
   - [ ] Brak konkretnych nazw narzędzi z pamięci (researcher ma szukać aktualnych)?
2. Jeśli checklist niepełny → wróć do Fazy 2.

### Exit gate

PASS: wszystkie punkty checklist spełnione.

---

## Faza 4: Publikacja

**Owner:** PE

### Steps

1. Zapisz prompt:
   ```
   documents/researcher/prompts/research_{temat}.md
   ```
2. Commit:
   ```
   py tools/git_commit.py --message "feat(PE): research prompt — {temat}" --all
   ```
3. Powiadom zlecającego (jeśli nie user):
   ```
   py tools/agent_bus_cli.py send --from prompt_engineer --to <zlecający> --content-file tmp/research_prompt_ready.md
   ```
   Treść: ścieżka do promptu, krótki opis zakresu, ścieżka oczekiwanych wyników.

4. Poinformuj usera: "Prompt gotowy do uruchomienia: [ścieżka]."

   → HANDOFF: human. STOP.
     Mechanizm: czekaj na user input
     Czekaj na: user uruchamia prompt w zewnętrznym narzędziu i wraca z wynikami.

### Exit gate

PASS: prompt zapisany, commit, zlecający powiadomiony.
