---
workflow_id: developer_bugfix
version: "2.0"
owner_role: developer
trigger: "Developer otrzymuje zadanie: diagnoza i naprawa bledu"
participants:
  - developer (owner)
  - human (diagnoza, zatwierdzenie)
related_docs:
  - documents/dev/DEVELOPER.md
prerequisites:
  - session_init_done
outputs:
  - type: commit
---

# Workflow: Developer — Bug fix

Workflow dla diagnozy i naprawy bledow.

## Outline

1. **Diagnoza** — zidentyfikuj przyczyne, zasieg, propozycje naprawy
2. **Naprawa** — fix z test checkpoints i blast radius
3. **Zamkniecie** — commit z opisem przyczyny

---

## Faza 1: Diagnoza

**Owner:** developer

### Inputs required
- [ ] `session_init_done`: session_init wykonany
- [ ] `bug_report`: Opis bledu (od usera, z backlogu, lub z obserwacji)

### Steps

## Step 1: Zdiagnozuj przyczyne

**step_id:** diagnose_root_cause
**action:** Zdiagnozuj problem — zrozum przyczyne, nie tylko objaw
**tool:** Read
**command:** `Read <pliki_zwiazane_z_bledem>` + `Grep <pattern_bledu>`
**verification:** Przyczyna zidentyfikowana (nie tylko objaw)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Nie mozna zidentyfikowac przyczyny. Eskaluj do usera z opisem objawow."
**next_step:** blind_spot_query (if PASS)

---

## Step 2: Blind spot query

**step_id:** blind_spot_query
**action:** Sprawdz czy ten sam blad nie wystepuje szerzej — jeden przypadek moze byc symptomem wzorca
**tool:** Grep
**command:** `Grep <pattern_bledu>` w calym repo
**verification:** Zasieg zdiagnozowany — lista wszystkich wystapien
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Pattern nie znaleziony. Sprawdz alternatywne warianty."
**next_step:** assess_scale (if PASS)

---

## Step 3: Ocen skale

**step_id:** assess_scale
**action:** Ocen skale: ile miejsc dotkietych? Naprawa reczna vs narzedzie?
**tool:** manual
**command:** Analiza wynikow blind spot query
**verification:** Skala oceniona, podejscie do naprawy wybrane
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Niejasna skala. Doprecyzuj z userem."
**next_step:** present_diagnosis (if PASS)

---

## Step 4: Przedstaw diagnoze uzytkownikowi

**step_id:** present_diagnosis
**action:** Przedstaw diagnoze uzytkownikowi: zakres, przyczyna, propozycja naprawy
**tool:** manual
**command:** Prezentacja: przyczyna, zasieg, propozycja fix
**verification:** Uzytkownik zaakceptowal podejscie
**on_failure:**
  - retry: no
  - skip: no
  - escalate: no
  - reason: "Uzytkownik odrzucil podejscie. Zmien strategie naprawy."
**next_step:** apply_fix (if PASS), diagnose_root_cause (if FAIL — nowa diagnoza)

### Exit Gate

**Checklist:**
- [ ] `root_cause_found`: Przyczyna zidentyfikowana (nie tylko objaw)
- [ ] `scope_assessed`: Zasieg zdiagnozowany (blind spot query)
- [ ] `user_approved`: Uzytkownik zaakceptowal podejscie

**Status:**
- PASS if: wszystkie == true
- BLOCKED if: user_approved == false → zmien strategie

---

## Faza 2: Naprawa

**Owner:** developer

### Inputs required
- [ ] `diagnosis_done`: Diagnoza z Fazy 1 zakonczona
- [ ] `approach_approved`: Uzytkownik zaakceptowal podejscie

### Steps

## Step 5: Zastosuj fix

**step_id:** apply_fix
**action:** Napraw blad. Test checkpoint po kazdej zmianie.
**tool:** Edit
**command:** `Edit <pliki_z_bledem>`
**verification:** Zmiana wprowadzona
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Edycja nieudana. Sprawdz old_string."
**next_step:** run_tests (if PASS)

---

## Step 6: Uruchom testy

**step_id:** run_tests
**action:** Uruchom testy dotykajace zmienionego kodu — raportuj explicit: test_X.py::TestY — N/N PASS
**tool:** Bash
**command:** `py -m pytest <testy> -v`
**verification:** Wszystkie testy PASS (nowe i istniejace)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Testy FAIL. Napraw kod, nie test."
**next_step:** blast_radius_check (if PASS), apply_fix (if FAIL — popraw fix)

---

## Step 7: Blast radius check

**step_id:** blast_radius_check
**action:** Grep po pattern ktory naprawiles — ten sam bug moze istniec w innych miejscach
**tool:** Grep
**command:** `Grep <naprawiony_pattern>` w calym repo
**verification:** Ten sam bug nie istnieje w innych miejscach LUB wszystkie wystapienia naprawione
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Znaleziono dodatkowe wystapienia. Napraw wszystkie."
**next_step:** commit_fix (if PASS), apply_fix (if FAIL — napraw pozostale)

---

## Step 8: Commit

**step_id:** commit_fix
**action:** Commit z opisem przyczyny (nie tylko objawu)
**tool:** Bash
**command:** `py tools/git_commit.py --message "fix(dev): <przyczyna bledu>" --files <zmienione_pliki>`
**verification:** Commit wykonany
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad commitu. Sprawdz git status."
**next_step:** END

### Forbidden

- Naprawianie jednej instancji gdy jest ich 10 — najpierw diagnoza zasiegu.
- Obejscie jednorazowe zamiast naprawy narzedzia.

### Exit Gate

**Checklist:**
- [ ] `root_cause_fixed`: Przyczyna naprawiona (nie tylko objaw)
- [ ] `scope_covered`: Zasieg pokryty (blind spot query + blast radius)
- [ ] `tests_pass`: Testy PASS — explicit lista
- [ ] `existing_tests_pass`: Istniejace testy zmienionego kodu tez PASS
- [ ] `committed`: Commit wykonany

**Status:**
- PASS if: wszystkie == true
- BLOCKED if: tests_pass == false → napraw kod

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 2.0 | 2026-03-31 | Konwersja do strict format 04R (DB-ready): 8 steps z step_id, verification, on_failure, next_step. Exit gates z item_id. |
| 1.0 | 2026-03-27 | Wydzielenie z workflow_developer.md (sekcja Bug fix) |
