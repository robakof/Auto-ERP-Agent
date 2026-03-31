---
workflow_id: developer_patch
version: "1.0"
owner_role: developer
trigger: "Developer otrzymuje drobną zmianę: ≤5 linii, jeden plik, bez zmiany interfejsu"
participants:
  - developer (owner)
related_docs:
  - documents/dev/DEVELOPER.md
prerequisites:
  - session_init_done
outputs:
  - type: commit
  - type: message
    field: "notyfikacja do PE jeśli zmiana docs instrukcyjnych"
---

# Workflow: Developer — Patch

Workflow dla drobnych zmian istniejących narzędzi — nie bug fix, nie nowe narzędzie.

## Outline

1. **Zmiana** — read, edit, smoke test
2. **Zamknięcie** — commit, notyfikacja PE jeśli docs

---

## Zakres

- Zmiana ≤5 linii kodu
- Jeden plik
- Nie zmienia interfejsu (API, argumenty CLI, format outputu)
- Przykłady: dodanie wartości do enuma, zmiana domyślnego parametru, poprawka walidacji

---

## Faza 1: Zmiana

**Owner:** developer

### Steps

1. Read pliku którego dotyczy zmiana.
2. Edit — wprowadź zmianę.
3. Test smoke (jeśli dotyczy) — upewnij się że narzędzie działa.

### Forbidden

- Zmiany interfejsu (wymagają workflow `developer_tool` + konsultacja z rolami które używają).
- Zmiany >5 linii (oceń czy to nie nowe narzędzie).

### Exit gate

PASS: zmiana ≤5 linii, smoke test OK.

---

## Faza 2: Zamknięcie

**Owner:** developer

### Steps

1. Commit z opisem zmiany.
2. Jeśli zmiana dotyczy dokumentów instrukcyjnych (CLAUDE.md, workflow/*.md, documents/*/[ROLA].md):
   Wyślij notyfikację do Prompt Engineer — PE jest gatekeeperem spójności promptów
   i musi poinformować inne role o zmianie.

### Exit gate

PASS jeśli:
- [ ] Zmiana ≤5 linii, jeden plik
- [ ] Smoke test OK (jeśli dotyczy)
- [ ] Commit
- [ ] Jeśli zmiana dotyczy dokumentów instrukcyjnych → notyfikacja do PE

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-27 | Wydzielenie z workflow_developer.md (sekcja Patch) |
