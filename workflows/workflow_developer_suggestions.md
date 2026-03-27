---
workflow_id: developer_suggestions
version: "1.0"
owner_role: developer
trigger: "Developer przetwarza open suggestions od Wykonawców"
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

Workflow dla przetwarzania open suggestions od Wykonawców przez Developera.

## Outline

1. **Przegląd** — odczytaj i oceń open suggestions
2. **Weryfikacja** — sprawdź aktualność, zatwierdzenie usera
3. **Realizacja** — backlog-add, aktualizacja statusów

---

## Faza 1: Przegląd

**Owner:** developer

### Steps

1. Przeczytaj open suggestions:
   ```
   python tools/render.py suggestions --format md --status open
   ```
   Domyślnie → `documents/human/suggestions/`
2. Dla każdego wpisu oceń: warto wdrożyć / nie warto / wymaga dyskusji.
3. Przedstaw ocenę użytkownikowi — poczekaj na zatwierdzenie.

### Exit gate

PASS: każda suggestion oceniona, ocena przedstawiona użytkownikowi.

---

## Faza 2: Weryfikacja i realizacja

**Owner:** developer + human

### Steps

1. **Przed dodaniem do backlogu:** sprawdź czy funkcjonalność już nie istnieje.
   Sugestie mogą być przestarzałe — zweryfikuj stan kodu (grep, glob, git log).
2. Zatwierdzone i zweryfikowane → dodaj do backlogu:
   ```
   python tools/agent_bus_cli.py backlog-add --title "..." --area <obszar> --content-file tmp/tmp.md
   ```
3. Oznacz suggestion jako implemented:
   ```
   python tools/agent_bus_cli.py suggest-status --id <id> --status implemented
   ```

### Exit gate

PASS jeśli:
- [ ] Każda open suggestion oceniona
- [ ] Użytkownik zatwierdzył decyzje
- [ ] Zatwierdzone przeniesione do backlogu
- [ ] Statusy suggestions zaktualizowane

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-27 | Wydzielenie z workflow_developer.md (sekcja Suggestions) |
