---
workflow_id: convention_creation
version: "1.0"
owner_role: architect
trigger: "Potrzeba nowej konwencji dla aspektu projektu bez istniejącego standardu"
participants:
  - architect (owner, draft, review)
  - prompt_engineer (research prompt, revision support)
  - dawid (approval — jedyny approver)
related_docs:
  - documents/conventions/CONVENTION_META.md
  - documents/conventions/CONVENTION_WORKFLOW.md
  - documents/methodology/SPIRIT.md
prerequisites:
  - session_init_done
  - identified_gap (brak konwencji dla aspektu)
outputs:
  - type: file
    path: "documents/conventions/CONVENTION_{ZAKRES}.md"
  - type: file
    path: "documents/human/conventions/CONVENTION_{ZAKRES}.md"
  - type: message
    field: "powiadomienie ról których dotyczy konwencja"
  - type: commit
    field: "git commit z nową konwencją"
---

# Workflow: Tworzenie konwencji

Proces tworzenia nowej konwencji dla projektu Mrowisko. Właściciel procesu: Architect.
Używaj gdy brakuje standardu dla aspektu projektu (np. format commitów, struktura workflow, nazewnictwo).

## Outline

1. **Identyfikacja** — rozpoznanie braku konwencji
2. **Research** — badanie best practices przed draftem
3. **Draft** — minimalna wersja konwencji
4. **Review** — weryfikacja architektoniczna i jakościowa
5. **Revision** — poprawki na podstawie feedbacku
6. **Approval** — zatwierdzenie przez Dawida
7. **Publication** — commit, powiadomienia, dokumentacja

---

## Zasady przewodnie

**Z historii projektu (sesje 2026-03-24):**

> "Wolałbym żeby była napisana w miarę minimalnie dając więcej elastyczności i czasem ją nabudowywać."

> "Każdy aspekt projektu powinniśmy zaczynać od konwencji żeby mieć czystą architekturę."

**Pattern:** Convention First Architecture — zanim implementujesz, zdefiniuj standard.

**Minimalizm:** Konwencja minimalna, elastyczna. Rozbudowuj iteracyjnie na podstawie praktyki, nie teoretycznie.

---

## Faza 1: Identyfikacja

**Owner:** architect (lub rola która zauważyła brak)

**Założenie:** Projekt docelowo ma 100% pokrycia konwencjami. Tworzenie nowej konwencji jest rzadkie i pracochłonne. Częściej aktualizujemy istniejące.

### Steps

1. Szukaj istniejącej konwencji (nie zakładaj że nie istnieje).
   1.1. Sprawdź `documents/conventions/` — główna lokalizacja.
   1.2. Jeśli nie ma → przeszukaj repo szerzej:
        - `Glob documents/**/*CONVENTION*.md`
        - `Grep "convention_id:" --path documents/`
   1.3. Jeśli znaleziona gdzie indziej → przenieś do `documents/conventions/` lub użyj.
   1.4. Jeśli nadal nie ma → **zapytaj użytkownika** przed tworzeniem nowej:
        "Nie znalazłem konwencji dla [aspekt]. Czy na pewno nie istnieje? Czy tworzymy nową?"

2. Jeśli konwencja istnieje → rozważ update zamiast tworzenia nowej.
   2.1. Czy istniejąca konwencja pokrywa potrzebę?
   2.2. Jeśli częściowo → zaproponuj rozszerzenie (update, nie nowa).
   2.3. Jeśli zupełnie nie pasuje → kontynuuj tworzenie nowej.

3. Nazwij gap (tylko jeśli potwierdzono brak konwencji).
   3.1. Co dokładnie wymaga standaryzacji?
   3.2. Kogo dotyczy (audience)?
   3.3. Dlaczego teraz? (trigger)

4. Sprawdź czy to konwencja czy workflow.
   - **Konwencja** = zestaw reguł JAK coś POWINNO wyglądać (standard)
   - **Workflow** = procedura JAK coś zrobić (proces)
   - Jeśli to workflow → użyj `workflow_workflow_creation.md`

### Forbidden

- Nie zakładaj że konwencja nie istnieje bez szerszego przeszukania repo
- Nie twórz nowej konwencji bez walidacji z użytkownikiem

### Exit gate

PASS jeśli:
- Przeszukano repo (nie tylko `documents/conventions/`)
- Użytkownik potwierdził że konwencja nie istnieje
- Gap zidentyfikowany (nazwa, scope, audience)
- Potwierdzone że to konwencja (nie workflow)

BLOCKED jeśli:
- Konwencja istnieje → użyj istniejącej lub zaproponuj update
- Użytkownik nie potwierdził potrzeby nowej konwencji

---

## Faza 2: Research

**Owner:** architect (zleca) + prompt_engineer (tworzy prompt)

### Steps

1. Określ pytania badawcze.
   1.1. Jakie best practices istnieją dla tego aspektu?
   1.2. Jakie formaty stosują inne projekty?
   1.3. Jakie są znane anti-patterns?

2. Sprawdź istniejący ecosystem.
   2.1. Czy Claude Code / Mrowisko ma już working pattern? (np. SKILL.md)
   2.2. Jeśli tak → użyj jako baseline, research uzupełnia.

3. Utwórz research prompt (lub poproś PE).
   3.1. Zapisz do `documents/researcher/prompts/research_{temat}.md`
   3.2. Użyj base prompt (rigorystyczny lub eksploracyjny)
   3.3. Dodaj constraints Mrowisko-specific (agility, DB-readiness, agent-centric)

4. Wykonaj research.
   4.1. Uruchom research przez WebSearch lub zewnętrznego agenta
   4.2. Zapisz wyniki do `documents/researcher/research/{temat}.md`

5. Przeczytaj wyniki researchu.
   5.1. Zidentyfikuj kluczowe wzorce
   5.2. Zidentyfikuj anti-patterns do unikania

### Forbidden

- Nie pisz draftu konwencji BEZ researchu — research first!
- Nie kopiuj ślepo istniejących wzorców bez oceny dopasowania do Mrowiska

### Exit gate

PASS jeśli:
- Research wykonany i zapisany
- Kluczowe wzorce zidentyfikowane
- Anti-patterns znane

ESCALATE jeśli research nie daje jasnych wyników → konsultacja z Metodolog.

---

## Faza 3: Draft

**Owner:** architect

### Steps

1. Przeczytaj CONVENTION_META (struktura konwencji).
   ```
   Read documents/conventions/CONVENTION_META.md
   ```

2. Utwórz draft konwencji.
   2.1. Zacznij od YAML header (wymagane pola z CONVENTION_META):
        ```yaml
        ---
        convention_id: string
        version: "1.0"
        status: draft
        created: YYYY-MM-DD
        updated: YYYY-MM-DD
        author: architect
        owner: architect
        approver: dawid
        audience: [lista ról]
        scope: "1 zdanie"
        ---
        ```
   2.2. Dodaj wymagane sekcje:
        - TL;DR (3-5 punktów, esencja)
        - Zakres (co pokrywa, co NIE)
        - Reguły (numerowane: 01R, 02R...)
        - Przykłady
        - Antywzorce (Bad → Why → Good)
        - Changelog

3. Stosuj minimalizm.
   - Mniej reguł > więcej reguł
   - Elastyczność > szczegółowość
   - Opcjonalne sekcje dodawaj tylko gdy potrzebne

4. Zapisz draft.
   4.1. Zapisz do `documents/conventions/CONVENTION_{ZAKRES}.md`
   4.2. Status = draft

### Forbidden

- Nie rozbudowuj konwencji "na zapas" — minimalizm!
- Nie wzoruj się na starych dokumentach bez sprawdzenia czy są zgodne z CONVENTION_META
- Nie pisz po angielsku (warstwa sterowania = polski)

### Exit gate

PASS jeśli:
- YAML header kompletny
- Wszystkie wymagane sekcje obecne
- Status = draft
- Plik zapisany w `documents/conventions/`

---

## Faza 4: Review

**Owner:** architect (self-review) + opcjonalnie inni

### Steps

1. Self-review: sprawdź zgodność z CONVENTION_META.
   - [ ] YAML header kompletny?
   - [ ] Wszystkie wymagane sekcje?
   - [ ] Reguły numerowane (01R, 02R)?
   - [ ] Antywzorce w formacie Bad → Why → Good?
   - [ ] Język polski?

2. Architektoniczny review.
   - [ ] Konwencja jest DB-ready? (YAML parseable)
   - [ ] Zgodna z SPIRIT.md? (filozofia projektu)
   - [ ] Nie blokuje emergencji? (agility > stability)
   - [ ] Audience poprawne?

3. Jeśli konwencja dotyczy workflow/promptów → poproś PE o review.

4. Zapisz uwagi.

### Exit gate

PASS jeśli:
- Self-review checklist kompletny
- Brak critical issues

BLOCKED jeśli critical issues → wróć do Faza 3.

---

## Faza 5: Revision

**Owner:** architect

### Steps

1. Zbierz feedback.
   1.1. Od reviewerów (PE, Metodolog jeśli zaangażowani)
   1.2. Od użytkownika (Dawid) — wstępne uwagi

2. Wprowadź poprawki.
   2.1. Adresuj każdą uwagę
   2.2. Zachowaj minimalizm (nie dodawaj rzeczy "bo może się przydadzą")

3. Zaktualizuj draft.
   3.1. Bump `updated` date
   3.2. Zapisz zmiany

4. Zmień status na `review`.
   ```yaml
   status: review
   ```

### Iteracja

Jeśli feedback wymaga dużych zmian → wróć do Faza 3.
Jeśli drobne poprawki → kontynuuj do Faza 6.

### Exit gate

PASS jeśli:
- Wszystkie uwagi zaadresowane
- Status = review
- Draft gotowy do zatwierdzenia

---

## Faza 6: Approval

**Owner:** dawid (jedyny approver)

### Steps

1. Przedstaw konwencję do zatwierdzenia.
   1.1. Skopiuj do `documents/human/conventions/CONVENTION_{ZAKRES}.md` (kopia robocza dla Dawida)
   1.2. Powiadom Dawida że konwencja czeka na approval

2. Dawid przegląda i zatwierdza.
   2.1. Jeśli uwagi → wróć do Faza 5
   2.2. Jeśli OK → kontynuuj

3. Zmień status na `active`.
   ```yaml
   status: active
   ```

### Exit gate

PASS jeśli:
- Dawid zatwierdził
- Status = active

BLOCKED jeśli Dawid ma uwagi → wróć do Faza 5.

---

## Faza 7: Publication

**Owner:** architect

### Steps

1. Git commit.
   ```
   py tools/git_commit.py --message "feat(conventions): CONVENTION_{ZAKRES} v1.0 approved — [krótki opis]" --all
   ```

2. Powiadom role których dotyczy.
   2.1. Wyślij wiadomość przez agent_bus do każdej roli z audience
   2.2. Treść: nowa konwencja, lokalizacja, co zmienia

3. Zaktualizuj powiązane dokumenty (jeśli potrzebne).
   3.1. Czy role documents wymagają update? (session_start, checklist)
   3.2. Jeśli tak → utwórz backlog item dla PE

4. Zaloguj sesję.
   ```
   py tools/agent_bus_cli.py log --role architect --content-file tmp/log_convention.md
   ```

### Exit gate

PASS jeśli:
- Commit wykonany
- Role powiadomione
- Powiązane dokumenty zaktualizowane (lub backlog items utworzone)

---

## Decision Points

### Decision Point 1: Konwencja vs Workflow

**decision_id:** check_convention_or_workflow
**condition:** Dokument definiuje standard (jak coś POWINNO wyglądać) vs procedurę (jak coś zrobić)
**path_true:** Kontynuuj ten workflow (to konwencja)
**path_false:** Użyj `workflow_workflow_creation.md` (to workflow)
**default:** Zapytaj Metodologa

### Decision Point 2: Research potrzebny?

**decision_id:** check_research_needed
**condition:** Aspekt jest nowy LUB nie ma internal baseline (istniejący pattern w ecosystem)
**path_true:** Faza 2 (research)
**path_false:** Faza 3 (draft) — użyj internal baseline
**default:** Faza 2 (research bezpieczniejszy)

---

## Forbidden (pułapki z praktyki)

1. **Nie wzoruj się na starych dokumentach bez weryfikacji.**
   - PE wzorował się na `bi_view_creation_workflow.md` (nie DB-ready) → konwencja też nie DB-ready
   - Zawsze sprawdź czy wzorzec jest zgodny z aktualnymi standardami

2. **Nie rozbudowuj konwencji "na zapas".**
   - "Optional fields" które nigdy nie będą używane = szum
   - Minimalna konwencja + iteracyjne rozbudowywanie

3. **Nie pisz konwencji bez researchu.**
   - Research first, draft second
   - Research ujawnia anti-patterns i proven patterns

4. **Nie approver = author.**
   - Dawid jest jedynym approverem dla wszystkich konwencji
   - Autor nie zatwierdza własnej pracy

5. **Nie cicha edycja aktywnej konwencji.**
   - Każda zmiana = bump version + changelog entry
   - Agenci z cached knowledge muszą wiedzieć że coś się zmieniło

---

## Self-check przed zakończeniem

- [ ] Konwencja ma YAML header z wszystkimi wymaganymi polami?
- [ ] Wszystkie wymagane sekcje obecne (TL;DR, Zakres, Reguły, Przykłady, Antywzorce, Changelog)?
- [ ] Status = active (zatwierdzone przez Dawida)?
- [ ] Git commit wykonany?
- [ ] Role z audience powiadomione?
- [ ] Jeśli nie → workflow nie jest zakończony!

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-24 | Początkowa wersja — na podstawie historii tworzenia CONVENTION_META i CONVENTION_WORKFLOW |
