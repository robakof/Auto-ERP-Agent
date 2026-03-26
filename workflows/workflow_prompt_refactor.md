---
workflow_id: prompt_refactor
version: "1.1"
owner_role: prompt_engineer
trigger: "PE identyfikuje prompt/workflow wymagający refaktoru (styl stary, domena inline, niespójność z konwencją)"
participants:
  - prompt_engineer
  - human (review)
related_docs:
  - documents/conventions/CONVENTION_WORKFLOW.md
  - documents/conventions/CONVENTION_PROMPT.md
  - documents/conventions/CONVENTION_META.md
prerequisites:
  - session_init_done
  - target_file_identified
outputs:
  - type: file
    path: "workflows/archive_pre_refactor/{original_name}"
  - type: file
    path: "{refactored_file}"
  - type: file
    path: "documents/human/reports/refactor_audit_{nazwa}.md"
  - type: commit
---

# Workflow: Refaktor promptów i workflow

Workflow dla refaktoru istniejących dokumentów (prompty ról, workflow, konwencje).
Używaj gdy dokument wymaga modernizacji do aktualnej konwencji lub separation of concerns.

## Outline

1. **Analiza** — zidentyfikuj styl, domenę inline, niezgodności z konwencją
2. **Archiwizacja** — zachowaj oryginał przed zmianami
3. **Ekstrakcja reguł** — wyciągnij wszystkie reguły z oryginału
4. **Separation** — wyciągnij domenę do related_docs
5. **Przepisanie** — przepisz do aktualnej konwencji
6. **Weryfikacja** — sprawdź mapowanie, brak zgubień
7. **Review** — user przegląda
8. **Publication** — commit z audytem

---

## Routing

| Typ dokumentu | Konwencja referencyjna | Cel |
|---|---|---|
| Workflow | CONVENTION_WORKFLOW.md | YAML header, outline, strict steps |
| Prompt roli | CONVENTION_PROMPT.md | Struktura sekcji, mission/scope/rules |
| Konwencja | CONVENTION_META.md | TL;DR, reguły, antywzorce |

---

## Faza 0: Analiza

**Owner:** prompt_engineer

### Steps

1. Przeczytaj dokument docelowy (`Read`).
2. Zidentyfikuj styl:
   - **Stary (domain-heavy):** ~500+ linii, snippety inline, długie Forbidden/Self-check
   - **Nowy (proces-focused):** ~200-300 linii, linki do related_docs, krótkie listy
3. Sprawdź niezgodności z konwencją:
   - Brak YAML header?
   - Brak outline?
   - Domena inline zamiast w related_docs?
   - Numeracja niespójna?
4. Zapisz diagnozę w `tmp/refactor_diagnosis_{nazwa}.md`:
   - Styl: stary/nowy
   - Linie: X
   - Główne problemy: [lista]
   - Domena do wyciągnięcia: [lista sekcji]

### Exit gate

PASS jeśli diagnoza zapisana i problemy zidentyfikowane.

---

## Faza 1: Archiwizacja

**Owner:** prompt_engineer

### Steps

1. Skopiuj oryginał do `workflows/archive_pre_refactor/` (lub `documents/.../archive_pre_refactor/`).
2. Zachowaj oryginalną nazwę pliku.
3. Zweryfikuj że kopia istnieje (`Glob`).

### Exit gate

PASS jeśli oryginał zarchiwizowany.

---

## Faza 2: Ekstrakcja reguł

**Owner:** prompt_engineer

### Steps

1. Przeczytaj oryginał sekcja po sekcji.
2. Dla każdej sekcji wypisz wszystkie reguły/kroki/forbidden items.
3. Zapisz listę w `tmp/refactor_rules_{nazwa}.md`:
   ```
   ## Sekcja: [nazwa]
   - Reguła 1: [treść]
   - Reguła 2: [treść]
   ...
   ```
4. Policz reguły: X total.

### Exit gate

PASS jeśli lista reguł kompletna (wszystkie sekcje pokryte).

---

## Faza 3: Separation of Concerns

**Owner:** prompt_engineer

### Steps

1. Zidentyfikuj wiedzę domenową (snippety SQL, wzorce ERP, przykłady techniczne).
2. Sprawdź czy related_docs istnieją:
   - Tak → zweryfikuj że pokrywają wyciąganą domenę
   - Nie → utwórz nowy plik domenowy
3. Przenieś domenę do related_docs (lub potwierdź że już tam jest).
4. W przepisywanym dokumencie zostaw tylko linki do related_docs.

### Forbidden

- Nie usuwaj domeny bez upewnienia się że jest w related_docs.
- Nie duplikuj domeny (jedno miejsce).

### Exit gate

PASS jeśli domena w related_docs, workflow/prompt zawiera tylko linki.

---

## Faza 4: Przepisanie do konwencji

**Owner:** prompt_engineer

### Steps

1. Otwórz konwencję referencyjną (routing table wyżej).
2. Przepisz dokument zgodnie z konwencją:
   - YAML header (workflow_id, version, owner_role, trigger, related_docs)
   - Outline na górze
   - Numeracja kroków: 1, 1.1, 1.1.1
   - Exit gate per faza
3. Zachowaj WSZYSTKIE reguły z Fazy 2.
4. Zapisz przepisany dokument.

### Exit gate

PASS jeśli dokument zgodny z konwencją.

---

## Faza 5: Weryfikacja mapowania

**Owner:** prompt_engineer

### Steps

1. Otwórz listę reguł z Fazy 2 (`tmp/refactor_rules_{nazwa}.md`).
2. Dla każdej reguły znajdź gdzie trafiła w nowym dokumencie:
   - Zachowana → zapisz lokalizację (plik:sekcja)
   - Usunięta → zapisz uzasadnienie
   - Przeniesiona do related_docs → zapisz ścieżkę
3. Zapisz mapowanie w `documents/human/reports/refactor_audit_{nazwa}.md`:
   ```
   ## Mapowanie reguł

   | # | Reguła (oryginał) | Status | Lokalizacja (nowy) |
   |---|---|---|---|
   | 1 | [treść] | zachowana | workflow.md:Faza 2 |
   | 2 | [treść] | przeniesiona | ERP_SCHEMA_PATTERNS.md |
   | 3 | [treść] | usunięta | Powód: duplikat reguły #1 |
   ```
4. Policz: X zachowanych, Y przeniesionych, Z usuniętych (z uzasadnieniem).
5. **Verification:** Suma = liczba reguł z Fazy 2. Jeśli nie → szukaj zgubień.

### Forbidden

- Nie zamykaj fazy bez 100% pokrycia mapowania.
- "Usunięta" wymaga uzasadnienia (nie może być "zgubiona").

### Exit gate

PASS jeśli 100% reguł zmapowanych (zachowane + przeniesione + usunięte z uzasadnieniem).
BLOCKED jeśli suma nie zgadza się z liczbą z Fazy 2.

---

## Faza 6: Review

**Owner:** prompt_engineer + human

### Steps

1. Pokaż użytkownikowi:
   - Przepisany dokument (diff jeśli możliwy)
   - Audyt mapowania (`documents/human/reports/refactor_audit_{nazwa}.md`)

   → HANDOFF: human. STOP.
     Mechanizm: czekaj na user input
     Czekaj na: feedback lub zatwierdzenie
     Nie przechodź do Fazy 7 bez zatwierdzenia.

2. Jeśli poprawki → wróć do Fazy 4 lub 5.

### Exit gate

PASS jeśli użytkownik zatwierdził.

---

## Faza 7: Publication

**Owner:** prompt_engineer

### Steps

1. Commit z opisem:
   ```
   refactor(PE): {nazwa} v{old} -> v{new} - {główna zmiana}

   - Separation: domena do {related_docs}
   - Zgodność z CONVENTION_{typ}
   - Audyt: documents/human/reports/refactor_audit_{nazwa}.md
   ```
2. Wyślij notyfikację do ról które używają dokumentu (jeśli dotyczy).
3. Zaktualizuj status backlogu (jeśli task z backlogu).

### Exit gate

PASS jeśli commit wykonany i notyfikacje wysłane.

---

## Scenariusze

### Scenariusz A: Refaktor workflow

**Konwencja:** CONVENTION_WORKFLOW.md

**Typowe zmiany:**
- Dodanie YAML header
- Dodanie outline
- Wyciągnięcie domeny do ERP_SCHEMA_PATTERNS.md / ERP_SQL_SYNTAX.md
- Zmiana numeracji na 1, 1.1, 1.1.1
- Dodanie exit gate per faza

**Przykład:** bi_view_creation v2.0 → v3.0 (580 → 290 linii)

### Scenariusz B: Refaktor promptu roli

**Konwencja:** CONVENTION_PROMPT.md

**Typowe zmiany:**
- Dodanie/aktualizacja YAML header (agent_id, role_type, escalates_to)
- Reorganizacja sekcji (mission, scope, critical_rules, workflow, tools)
- Wyciągnięcie domain knowledge do osobnych plików
- Skrócenie critical_rules (max 8-10)

### Scenariusz C: Refaktor konwencji

**Konwencja:** CONVENTION_META.md

**Typowe zmiany:**
- Dodanie TL;DR na górze
- Dodanie sekcji Antywzorce
- Dodanie Changelog
- Ujednolicenie formatu reguł (numeracja: 01R, 02R...)

---

## Styl: Stary vs Nowy

| Aspekt | Styl stary | Styl nowy |
|---|---|---|
| Rozmiar | ~500+ linii | ~200-300 linii |
| Domena | Inline (snippety, przykłady) | W related_docs (linki) |
| Forbidden | Długa lista | Krótka (tylko znane pułapki) |
| Self-check | Rozbudowany | Opcjonalny lub krótki |
| Numeracja | 1a, 1b, 2a | 1, 1.1, 1.1.1 |
| YAML header | Brak lub niepełny | Pełny (workflow_id, version, etc.) |
| Outline | Brak | Na górze dokumentu |

---

## Metryki sukcesu

- **Redukcja linii:** ≥30% (domena wyciągnięta)
- **Pokrycie reguł:** 100% (żadna zgubiona)
- **Zgodność z konwencją:** Wszystkie wymagane sekcje obecne
- **Audyt:** Plik istnieje w documents/human/reports/
