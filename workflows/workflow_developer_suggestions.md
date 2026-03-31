---
workflow_id: developer_suggestions
version: "2.0"
owner_role: developer
trigger: "Developer przetwarza open suggestions od Wykonawcow"
participants:
  - developer (owner)
  - human (zatwierdzenie decyzji)
related_docs:
  - documents/dev/DEVELOPER.md
  - workflows/workflow_suggestions_processing.md
prerequisites:
  - session_init_done
outputs:
  - type: backlog_item
    field: "zatwierdzone suggestions → backlog"
  - type: state
    field: "suggestions status updated"
---

# Workflow: Developer — Suggestions

Workflow dla przetwarzania open suggestions od Wykonawcow przez Developera.

## Outline

1. **Przeglad** — odczytaj i ocen open suggestions
2. **Weryfikacja** — sprawdz aktualnosc, zatwierdzenie usera
3. **Realizacja** — backlog-add, aktualizacja statusow

---

## Faza 1: Przeglad

**Owner:** developer

### Inputs required
- [ ] `session_init_done`: session_init wykonany
- [ ] `open_suggestions_exist`: Istnieja open suggestions do przetworzenia

### Steps

## Step 1: Eksportuj open suggestions

**step_id:** export_suggestions
**action:** Eksportuj open suggestions do pliku czytelnego dla czlowieka
**tool:** Bash
**command:** `py tools/render.py suggestions --format md --status open`
**verification:** Plik z suggestions wygenerowany w documents/human/suggestions/
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Blad renderowania. Sprawdz render.py."
**next_step:** evaluate_suggestions (if PASS)

---

## Step 2: Ocen kazda suggestion

**step_id:** evaluate_suggestions
**action:** Dla kazdego wpisu ocen: warto wdrozyc / nie warto / wymaga dyskusji
**tool:** manual
**command:** Analiza tresci kazdej suggestion
**verification:** Kazda suggestion ma ocene (wdrozyc / odrzucic / dyskusja)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Niekompletna ocena. Wroc do nieocenionych."
**next_step:** present_to_user (if PASS)

---

## Step 3: Przedstaw ocene uzytkownikowi

**step_id:** present_to_user
**action:** Przedstaw ocene uzytkownikowi — poczekaj na zatwierdzenie
**tool:** manual
**command:** Prezentacja: lista suggestions z ocenami i rekomendacjami
**verification:** Uzytkownik zatwierdzil decyzje
**on_failure:**
  - retry: no
  - skip: no
  - escalate: no
  - reason: "Uzytkownik nie zatwierdzil. Czekaj na feedback."
**next_step:** verify_staleness (if PASS)

→ HANDOFF: human. STOP.
  Mechanizm: czekaj na user input
  Czekaj na: zatwierdzenie decyzji per suggestion
  Nie przechodz do realizacji bez zatwierdzenia.

### Exit Gate

**Checklist:**
- [ ] `all_evaluated`: Kazda suggestion oceniona
- [ ] `user_approved`: Uzytkownik zatwierdzil decyzje

**Status:**
- PASS if: wszystkie == true
- BLOCKED if: user_approved == false → czekaj

---

## Faza 2: Weryfikacja i realizacja

**Owner:** developer + human

### Inputs required
- [ ] `decisions_approved`: Decyzje zatwierdzone przez uzytkownika

### Steps

## Step 4: Sprawdz aktualnosc

**step_id:** verify_staleness
**action:** Przed dodaniem do backlogu sprawdz czy funkcjonalnosc juz nie istnieje. Sugestie moga byc przestarzale.
**tool:** Grep
**command:** `Grep <pattern_sugestii>` + `Glob <sciezki>` + `git log --oneline --grep=<temat>`
**verification:** Kazda zatwierdzona suggestion zweryfikowana — aktualna lub przestarzala
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Nie mozna zweryfikowac aktualnosci. Sprawdz recznie."
**next_step:** add_to_backlog (if PASS)

---

## Step 5: Dodaj zatwierdzone do backlogu

**step_id:** add_to_backlog
**action:** Zatwierdzone i zweryfikowane suggestions dodaj do backlogu
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py backlog-add --title "..." --area <obszar> --content-file tmp/tmp.md`
**verification:** Backlog items utworzone dla zatwierdzonych suggestions
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad dodawania do backlogu. Sprawdz agent_bus_cli."
**next_step:** update_statuses (if PASS)

---

## Step 6: Zaktualizuj statusy suggestions

**step_id:** update_statuses
**action:** Oznacz suggestions jako implemented/noted
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py suggest-status --id <id> --status implemented`
**verification:** Kazda przetworzona suggestion ma zaktualizowany status
**on_failure:**
  - retry: yes
  - skip: yes
  - escalate: no
  - reason: "Blad aktualizacji statusu. Best-effort."
**next_step:** END

### Exit Gate

**Checklist:**
- [ ] `all_evaluated`: Kazda open suggestion oceniona
- [ ] `user_approved`: Uzytkownik zatwierdzil decyzje
- [ ] `staleness_checked`: Aktualnosc zweryfikowana
- [ ] `backlog_created`: Zatwierdzone przeniesione do backlogu
- [ ] `statuses_updated`: Statusy suggestions zaktualizowane

**Status:**
- PASS if: backlog_created == true AND statuses_updated == true

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 2.0 | 2026-03-31 | Konwersja do strict format 04R (DB-ready): 6 steps, 1 HANDOFF, exit gates z item_id. |
| 1.0 | 2026-03-27 | Wydzielenie z workflow_developer.md (sekcja Suggestions) |
