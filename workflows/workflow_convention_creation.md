---
workflow_id: convention_creation
version: "2.0"
owner_role: architect
trigger: "Potrzeba nowej konwencji dla aspektu projektu"
participants:
  - architect (owner, draft)
  - prompt_engineer (research prompt)
  - dawid (approval)
related_docs:
  - documents/conventions/CONVENTION_META.md
  - documents/conventions/CONVENTION_WORKFLOW.md
  - documents/methodology/SPIRIT.md
prerequisites:
  - session_init_done
outputs:
  - type: file
    path: "documents/conventions/CONVENTION_{ZAKRES}.md"
  - type: file
    path: "documents/human/conventions/CONVENTION_{ZAKRES}.md"
  - type: message
    field: "powiadomienie rol z audience"
  - type: commit
---

# Workflow: Tworzenie konwencji

Proces tworzenia nowej konwencji. Owner: Architect.

## Outline

1. **Identyfikacja** — walidacja ze konwencja nie istnieje
2. **Research** — badanie best practices (petla az wyczerpane)
3. **Draft** — minimalna wersja
4. **Review** — weryfikacja
5. **Revision** — poprawki
6. **Approval** — zatwierdzenie przez Dawida
7. **Publication** — commit, powiadomienia

---

## Zasady przewodnie

> "Wolalbym zeby byla napisana minimalnie dajac wiecej elastycznosci."

> "Kazdy aspekt projektu powinnismy zaczynac od konwencji."

**Convention First Architecture** — zanim implementujesz, zdefiniuj standard.

---

## Faza 1: Identyfikacja

**Owner:** architect

**Zalozenie:** Projekt ma 100% pokrycia konwencjami. Tworzenie nowej jest rzadkie.

### Inputs required
- [ ] `session_init_done`: session_init wykonany z rola architect
- [ ] `convention_need`: Zidentyfikowany gap w konwencjach

### Steps

## Step 1: Sprawdz czy konwencja istnieje

**step_id:** check_existing_convention
**action:** Przeszukaj documents/conventions/ i repo szerzej (Glob, Grep) pod katem istniejacej konwencji
**tool:** Glob
**command:** `Glob documents/conventions/CONVENTION_*.md` + `Grep "<temat>" documents/`
**verification:** Wynik przeszukania znany — konwencja istnieje lub nie
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Blad wyszukiwania. Ponow probe."
**next_step:** validate_with_user (if PASS — nie znaleziono), END (if FAIL — konwencja istnieje, uzyj istniejacej)

---

## Step 2: Waliduj z uzytkownikiem

**step_id:** validate_with_user
**action:** Potwierdz z uzytkownikiem ze konwencja naprawde nie istnieje i jest potrzebna
**tool:** manual
**command:** Zapytaj uzytkownika: "Konwencja <temat> nie istnieje. Potwierdzasz potrzebe?"
**verification:** Uzytkownik potwierdzil
**on_failure:**
  - retry: no
  - skip: no
  - escalate: no
  - reason: "Uzytkownik nie potwierdzil potrzeby. EXIT."
**next_step:** check_domain (if PASS), END (if FAIL — uzytkownik odmowil)

---

## Decision Point 1: Domena

**decision_id:** check_domain
**condition:** Czy temat to konwencja (Architect), workflow (PE), prompt (PE), czy metodologia (Metodolog)?
**path_true:** define_gap (konwencja — to domena Architect)
**path_false:** handoff_to_role (inna domena — przekaz do wlasciwej roli)
**default:** handoff_to_role (zapytaj PE)

---

## Step 3: Przekaz do wlasciwej roli (warunkowy)

**step_id:** handoff_to_role
**action:** Przekaz zadanie do wlasciwej roli (PE dla workflow/prompt, Metodolog dla metody)
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from architect --to <rola> --content-file tmp/convention_handoff.md`
**verification:** Wiadomosc wyslana
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad wysylki. Sprawdz agent_bus_cli."
**next_step:** END (handoff — Architect konczy)

---

## Step 4: Nazwij gap

**step_id:** define_gap
**action:** Nazwij gap: co, dla kogo, dlaczego teraz
**tool:** manual
**command:** Opis: temat konwencji, audience, uzasadnienie
**verification:** Gap opisany jednoznacznie
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Niejasny gap. Doprecyzuj z uzytkownikiem."
**next_step:** define_research_questions (if PASS)

### Exit Gate

**Checklist:**
- [ ] `no_existing`: Konwencja nie istnieje (zwalidowane)
- [ ] `user_confirmed`: Uzytkownik potwierdzil potrzebe
- [ ] `domain_architect`: To domena Architect (nie PE/Metodolog)
- [ ] `gap_defined`: Gap opisany (co, dla kogo, dlaczego)

**Status:**
- PASS if: wszystkie == true
- EXIT if: no_existing == false → uzyj istniejacej konwencji
- BLOCKED if: domain_architect == false → handoff do wlasciwej roli

---

## Faza 2: Research

**Owner:** architect (zleca) + PE (prompt) + human (wykonanie)

Research to petla: research → nowe watki → kolejny research → az wyczerpane.

### Inputs required
- [ ] `gap_defined`: Gap opisany z Fazy 1

### Steps

## Step 5: Okresl pytania badawcze

**step_id:** define_research_questions
**action:** Okresl pytania badawcze (best practices, formaty, anti-patterns). Sprawdz ecosystem Mrowisko jako baseline.
**tool:** manual
**command:** Analiza gapow wiedzy, sformulowanie pytan
**verification:** Lista pytan badawczych sformulowana
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Niejasne pytania. Doprecyzuj zakres."
**next_step:** send_to_pe (if PASS)

---

## Step 6: Wyslij pytania do PE

**step_id:** send_to_pe
**action:** Wyslij pytania badawcze do PE przez agent_bus
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from architect --to prompt_engineer --content-file tmp/research_questions.md`
**verification:** Wiadomosc wyslana (brak bledu CLI)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad wysylki. Sprawdz agent_bus_cli."
**next_step:** receive_research_prompt (if PASS)

→ HANDOFF: prompt_engineer. STOP.
  Mechanizm: agent_bus send
  Czekaj na: research prompt od PE w inbox (documents/researcher/prompts/research_{temat}.md)
  Nie przechodz do receive_research_prompt bez otrzymania promptu od PE.

---

## Step 7: Odbierz research prompt i przekaz do czlowieka

**step_id:** receive_research_prompt
**action:** Odbierz research prompt od PE. Przekaz go uzytkownikowi do wykonania zewnetrznym agentem.
**tool:** manual
**command:** Odbierz prompt z inbox, pokaz uzytkownikowi
**verification:** Uzytkownik otrzymal prompt do wykonania
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "PE nie dostarczyl promptu. Eskaluj do PE."
**next_step:** receive_research_results (if PASS)

→ HANDOFF: human. STOP.
  Mechanizm: czekaj na user input
  Czekaj na: wyniki researchu w documents/researcher/research/{temat}.md
  Research wykonuje user lub zewnetrzny agent — nie Architect.
  Nie przechodz bez wynikow.

---

## Step 8: Odbierz i ocen wyniki

**step_id:** receive_research_results
**action:** Odbierz wyniki od uzytkownika i ocen. Nowe watki → kolejna iteracja. Wyczerpane → kontynuuj.
**tool:** Read
**command:** `Read documents/researcher/research/{temat}.md`
**verification:** Wyniki przeczytane i ocenione. Decyzja: kolejna iteracja lub kontynuacja.
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Brak wynikow. Czekaj na uzytkownika."
**next_step:** define_research_questions (if FAIL — nowe watki do eksploracji), read_convention_meta (if PASS — research wyczerpany)

### Exit Gate

**Checklist:**
- [ ] `research_done`: Research wyczerpany (brak nowych watkow)
- [ ] `patterns_known`: Wzorce i anti-patterns znane
- [ ] `results_file`: Wyniki w pliku

**Status:**
- PASS if: research_done == true
- RETRY if: research_done == false → kolejna iteracja (define_research_questions)
- ESCALATE if: PE nie dostarcza promptu → eskaluj

---

## Faza 3: Draft

**Owner:** architect

### Inputs required
- [ ] `research_done`: Research z Fazy 2 zakonczony
- [ ] `results_file`: Wyniki researchu w pliku

### Steps

## Step 9: Przeczytaj CONVENTION_META

**step_id:** read_convention_meta
**action:** Przeczytaj CONVENTION_META i sprawdz overlap z istniejacymi konwencjami
**tool:** Read
**command:** `Read documents/conventions/CONVENTION_META.md`
**verification:** CONVENTION_META przeczytana, overlap sprawdzony
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Plik nie istnieje lub niedostepny. Sprawdz sciezke."
**next_step:** evaluate_rules (if PASS)

---

## Step 10: Ocen reguly — osad vs mechanizm

**step_id:** evaluate_rules
**action:** Dla kazdej planowanej reguly: osad agenta czy mechanizm w narzedziu? Regula kompensujaca brak mechanizmu = workaround, nie konwencja.
**tool:** manual
**command:** Klasyfikacja per regula: wymaga decyzji/osadu → konwencja. Wymaga "pamietaj zrobic X" → mechanizm (backlog Developer).
**verification:** Kazda regula oceniona. Zero regul kompensujacych brak mechanizmu.
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Reguly kompensujace brak mechanizmu → backlog do Developera, nie konwencja."
**next_step:** write_draft (if PASS)

---

## Step 11: Napisz draft

**step_id:** write_draft
**action:** Utworz draft konwencji (YAML header + wymagane sekcje wg CONVENTION_META). Status = draft.
**tool:** Write
**command:** `Write documents/conventions/CONVENTION_{ZAKRES}.md`
**verification:** Plik istnieje, YAML header kompletny, wymagane sekcje obecne, brak overlapu
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Draft niekompletny. Uzupelnij brakujace sekcje."
**next_step:** self_review (if PASS)

### Exit Gate

**Checklist:**
- [ ] `yaml_complete`: YAML header kompletny
- [ ] `sections_present`: Wymagane sekcje obecne
- [ ] `no_overlap`: Brak overlapu z innymi konwencjami
- [ ] `no_workarounds`: Zero regul kompensujacych brak mechanizmu
- [ ] `file_saved`: Plik zapisany

**Status:**
- PASS if: wszystkie == true
- BLOCKED if: no_workarounds == false → backlog do Developera

---

## Faza 4: Review

**Owner:** architect + reviewer

### Inputs required
- [ ] `draft_written`: Draft z Fazy 3 zapisany

### Steps

## Step 12: Self-review

**step_id:** self_review
**action:** Self-review zgodnosc z CONVENTION_META. Walidacja scope: kazda regula nalezy do TEGO dokumentu. Limity jednoznaczne (twarda granica, nie widelki).
**tool:** Read
**command:** `Read documents/conventions/CONVENTION_{ZAKRES}.md`
**verification:** Zgodnosc z META, scope poprawny, limity jednoznaczne
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Niezgodnosc z META lub scope leak. Popraw draft."
**next_step:** architecture_review (if PASS), write_draft (if FAIL — wroc do draftu)

---

## Step 13: Review architektoniczny

**step_id:** architecture_review
**action:** Review: DB-ready, zgodnosc z SPIRIT.md. Zapisz uwagi.
**tool:** manual
**command:** Analiza draftu pod katem architektury i SPIRIT.md
**verification:** Review kompletny, uwagi zapisane
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Review niekompletny. Dokoncz."
**next_step:** apply_feedback (if PASS — brak critical issues), apply_feedback (if FAIL — critical issues do poprawy)

### Exit Gate

**Checklist:**
- [ ] `meta_compliant`: Zgodnosc z CONVENTION_META
- [ ] `scope_valid`: Kazda regula nalezy do tego dokumentu
- [ ] `limits_clear`: Limity jednoznaczne
- [ ] `no_critical`: Brak critical issues

**Status:**
- PASS if: wszystkie == true
- BLOCKED if: no_critical == false → Faza 5 (revision)

---

## Faza 5: Revision

**Owner:** architect

### Inputs required
- [ ] `review_done`: Review z Fazy 4 zakonczony
- [ ] `feedback_collected`: Uwagi zebrane

### Steps

## Step 14: Wprowadz poprawki

**step_id:** apply_feedback
**action:** Zbierz feedback, wprowadz poprawki, bump updated date, zmien status na review
**tool:** Edit
**command:** `Edit documents/conventions/CONVENTION_{ZAKRES}.md`
**verification:** Uwagi zaadresowane, status = review, updated date zaktualizowany
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Poprawki niekompletne. Sprawdz kazda uwage."
**next_step:** copy_for_approval (if PASS)

### Exit Gate

**Checklist:**
- [ ] `feedback_addressed`: Uwagi zaadresowane
- [ ] `status_review`: Status = review
- [ ] `date_updated`: Updated date zaktualizowany

**Status:**
- PASS if: wszystkie == true

---

## Faza 6: Approval

**Owner:** dawid

### Inputs required
- [ ] `revision_done`: Revision z Fazy 5 zakonczona, status = review

### Steps

## Step 15: Skopiuj do katalogu czlowieka

**step_id:** copy_for_approval
**action:** Skopiuj draft do documents/human/conventions/ dla Dawida
**tool:** Bash
**command:** `cp documents/conventions/CONVENTION_{ZAKRES}.md documents/human/conventions/`
**verification:** Plik istnieje w documents/human/conventions/
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Blad kopiowania. Sprawdz sciezke."
**next_step:** human_approve_convention (if PASS)

---

## Step 16: Dawid zatwierdza

**step_id:** human_approve_convention
**action:** Dawid przegladal i zatwierdza konwencje. Uwagi → Faza 5. OK → status = active.
**tool:** manual
**command:** Prezentacja konwencji Dawidowi, czekaj na decyzje
**verification:** Dawid odpowiedzial: OK lub uwagi
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "Brak odpowiedzi Dawida. Czekaj."
**next_step:** commit_convention (if PASS — OK), apply_feedback (if FAIL — uwagi → Faza 5)

→ HANDOFF: human. STOP.
  Mechanizm: czekaj na user input
  Czekaj na: zatwierdzenie ("OK") lub uwagi od Dawida
  Nie przechodz do publication bez zatwierdzenia.

### Exit Gate

**Checklist:**
- [ ] `dawid_approved`: Dawid zatwierdzil
- [ ] `status_active`: Status = active

**Status:**
- PASS if: dawid_approved == true
- BLOCKED if: dawid_approved == false → wroc do apply_feedback

---

## Faza 7: Publication

**Owner:** architect

### Inputs required
- [ ] `dawid_approved`: Dawid zatwierdzil, status = active

### Steps

## Step 17: Git commit

**step_id:** commit_convention
**action:** Commituj konwencje
**tool:** Bash
**command:** `py tools/git_commit.py --message "feat(arch): CONVENTION_{ZAKRES} v1.0" --all`
**verification:** Commit wykonany (brak bledu)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad commitu. Sprawdz git status."
**next_step:** notify_roles (if PASS)

---

## Step 18: Powiadom role z audience

**step_id:** notify_roles
**action:** Wyslij powiadomienie do rol z audience konwencji
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from architect --to <rola> --content-file tmp/convention_notification.md`
**verification:** Wiadomosci wyslane do kazdej roli z audience
**on_failure:**
  - retry: yes
  - skip: yes
  - escalate: no
  - reason: "Blad wysylki. Powiadomienie jest best-effort."
**next_step:** log_convention_session (if PASS)

---

## Step 19: Zaloguj sesje

**step_id:** log_convention_session
**action:** Zaloguj sesje w agent_bus
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py log --role architect --content-file tmp/convention_log.md`
**verification:** Log zapisany
**on_failure:**
  - retry: yes
  - skip: yes
  - escalate: no
  - reason: "Blad logowania. Log jest best-effort."
**next_step:** END

### Exit Gate

**Checklist:**
- [ ] `committed`: Commit wykonany
- [ ] `roles_notified`: Role z audience powiadomione
- [ ] `session_logged`: Log sesji zapisany

**Status:**
- PASS if: committed == true (notify i log sa best-effort)

---

## Forbidden

1. **Brak przywiazania do legacy.**
   Jest nowsze, lepsze (potwierdzone researchem) → zastepujemy stare bez sentymentow.

2. **Nie approver = author.**
   Dawid jedyny approver.

3. **Nie cicha edycja aktywnej konwencji.**
   Zmiana = bump version + changelog.

---

## Self-check

- [ ] Konwencja nie istniala (zwalidowane)?
- [ ] Research wyczerpany?
- [ ] YAML header kompletny?
- [ ] Brak overlapu z innymi konwencjami?
- [ ] Kazda regula nalezy do tego dokumentu (nie innej konwencji)?
- [ ] Kazda regula wymaga osadu (nie kompensuje braku mechanizmu)?
- [ ] Limity jednoznaczne (twarde granice, nie widelki)?
- [ ] Status = active?
- [ ] Commit + powiadomienia?

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 2.0 | 2026-03-31 | Konwersja do strict format 04R (DB-ready): wszystkie kroki z step_id, action, tool, command, verification, on_failure, next_step. Decision points z decision_id. Exit gates z item_id. HANDOFF_POINT zachowane. |
| 1.4 | 2026-03-25 | Lekcja z CONV_COMMUNICATION: Faza 3 +krok "osad vs mechanizm". Exit gate + self-check rozszerzony. |
| 1.3 | 2026-03-25 | Lekcje z review CONV_PROMPT: Faza 3 +overlap check, Faza 4 +scope validation. |
| 1.2 | 2026-03-25 | Faza 2: HANDOFF_POINT po kroku 3 i nowy krok 3.5. |
| 1.1 | 2026-03-24 | Review: minimalizm, research jako petla, domain check |
| 1.0 | 2026-03-24 | Poczatkowa wersja |
