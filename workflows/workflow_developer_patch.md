---
workflow_id: developer_patch
version: "2.0"
owner_role: developer
trigger: "Developer otrzymuje drobna zmiane: <=5 linii, jeden plik, bez zmiany interfejsu"
participants:
  - developer (owner)
related_docs:
  - documents/dev/DEVELOPER.md
prerequisites:
  - session_init_done
outputs:
  - type: commit
  - type: message
    field: "notyfikacja do PE jesli zmiana docs instrukcyjnych"
---

# Workflow: Developer — Patch

Workflow dla drobnych zmian istniejacych narzedzi — nie bug fix, nie nowe narzedzie.

## Outline

1. **Zmiana** — read, edit, smoke test
2. **Zamkniecie** — commit, notyfikacja PE jesli docs

---

## Zakres

- Zmiana <=5 linii kodu
- Jeden plik
- Nie zmienia interfejsu (API, argumenty CLI, format outputu)
- Przyklady: dodanie wartosci do enuma, zmiana domyslnego parametru, poprawka walidacji

---

## Faza 1: Zmiana

**Owner:** developer

### Inputs required
- [ ] `session_init_done`: session_init wykonany
- [ ] `target_file`: Plik do zmiany zidentyfikowany

### Steps

## Step 1: Przeczytaj plik docelowy

**step_id:** read_target_file
**action:** Przeczytaj plik ktorego dotyczy zmiana
**tool:** Read
**command:** `Read <sciezka_pliku>`
**verification:** Plik przeczytany, kontekst zmiany zrozumiany
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Plik niedostepny. Sprawdz sciezke."
**next_step:** edit_file (if PASS)

---

## Step 2: Wprowadz zmiane

**step_id:** edit_file
**action:** Edytuj plik — wprowadz zmiane (<=5 linii)
**tool:** Edit
**command:** `Edit <sciezka_pliku>`
**verification:** Zmiana wprowadzona, <=5 linii, jeden plik
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Edycja nieudana. Sprawdz old_string."
**next_step:** check_scope (if PASS)

---

## Decision Point 1: Zakres zmiany

**decision_id:** check_scope
**condition:** Zmiana <=5 linii AND jeden plik AND nie zmienia interfejsu
**path_true:** smoke_test (kontynuuj)
**path_false:** escalate_scope (zmiana za duza — przejdz na workflow developer_tool)
**default:** escalate_scope

---

## Step 3: Smoke test

**step_id:** smoke_test
**action:** Uruchom smoke test — upewnij sie ze narzedzie dziala po zmianie
**tool:** Bash
**command:** `py <sciezka_narzedzia> --help` lub odpowiedni test
**verification:** Narzedzie dziala, brak bledow
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Smoke test failed. Sprawdz zmiane."
**next_step:** commit_patch (if PASS), edit_file (if FAIL — cofnij i popraw)

### Forbidden

- Zmiany interfejsu (wymagaja workflow `developer_tool` + konsultacja z rolami ktore uzywaja).
- Zmiany >5 linii (ocen czy to nie nowe narzedzie).

### Exit Gate

**Checklist:**
- [ ] `file_read`: Plik przeczytany
- [ ] `change_applied`: Zmiana wprowadzona
- [ ] `scope_valid`: <=5 linii, jeden plik, brak zmiany interfejsu
- [ ] `smoke_passed`: Smoke test OK

**Status:**
- PASS if: wszystkie == true
- BLOCKED if: scope_valid == false → przejdz na workflow developer_tool

---

## Faza 2: Zamkniecie

**Owner:** developer

### Steps

## Step 4: Commit

**step_id:** commit_patch
**action:** Commituj zmiane z opisem
**tool:** Bash
**command:** `py tools/git_commit.py --message "fix(dev): <opis zmiany>" --files <plik>`
**verification:** Commit wykonany (brak bledu)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad commitu. Sprawdz git status."
**next_step:** check_docs_change (if PASS)

---

## Decision Point 2: Zmiana dotyczy docs instrukcyjnych?

**decision_id:** check_docs_change
**condition:** Zmieniony plik to CLAUDE.md, workflow/*.md, lub documents/*/[ROLA].md
**path_true:** notify_pe (tak — powiadom PE)
**path_false:** END (nie — koniec)
**default:** END

---

## Step 5: Powiadom PE

**step_id:** notify_pe
**action:** Wyslij notyfikacje do Prompt Engineer o zmianie w docs instrukcyjnych
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from developer --to prompt_engineer --content-file tmp/patch_notification.md`
**verification:** Wiadomosc wyslana
**on_failure:**
  - retry: yes
  - skip: yes
  - escalate: no
  - reason: "Blad wysylki. Notyfikacja jest best-effort."
**next_step:** END

### Exit Gate

**Checklist:**
- [ ] `committed`: Commit wykonany
- [ ] `pe_notified`: PE powiadomiony (jesli zmiana dotyczy docs instrukcyjnych)

**Status:**
- PASS if: committed == true

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 2.0 | 2026-03-31 | Konwersja do strict format 04R (DB-ready): step_id, verification, on_failure, next_step. Decision points: check_scope, check_docs_change. |
| 1.0 | 2026-03-27 | Wydzielenie z workflow_developer.md (sekcja Patch) |
