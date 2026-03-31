---
workflow_id: developer_bugfix
version: "1.0"
owner_role: developer
trigger: "Developer otrzymuje zadanie: diagnoza i naprawa błędu"
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

Workflow dla diagnozy i naprawy błędów.

## Outline

1. **Diagnoza** — zidentyfikuj przyczynę, zasięg, propozycję naprawy
2. **Naprawa** — fix z test checkpoints i blast radius
3. **Zamknięcie** — commit z opisem przyczyny

---

## Faza 1: Diagnoza

**Owner:** developer

### Steps

1. Zdiagnozuj problem — zrozum przyczynę, nie tylko objaw.
2. Blind spot query: czy ten sam błąd nie występuje szerzej?
   Jeden przypadek może być symptomem wzorca.
3. Oceń skalę: ile miejsc dotkniętych? Naprawa ręczna vs narzędzie?
4. Przedstaw diagnozę użytkownikowi — zakres, przyczyna, propozycja naprawy.

### Exit gate

PASS: przyczyna zidentyfikowana, zasięg zdiagnozowany, użytkownik zaakceptował podejście.

---

## Faza 2: Naprawa

**Owner:** developer

### Steps

1. Napraw. Test checkpoint po każdej zmianie.
2. Uruchom testy dotykające zmienionego kodu — raportuj explicit: `test_X.py::TestY — N/N PASS`.
3. **Blast radius check:** grep po pattern który naprawiłeś. Ten sam bug może istnieć w innych miejscach.
4. Commit z opisem przyczyny (nie tylko objawu).

### Forbidden

- Naprawianie jednej instancji gdy jest ich 10 — najpierw diagnoza zasięgu.
- Obejście jednorazowe zamiast naprawy narzędzia.

### Exit gate

PASS jeśli:
- [ ] Przyczyna zidentyfikowana (nie tylko objaw)
- [ ] Zasięg zdiagnozowany (blind spot query)
- [ ] Fix zweryfikowany — explicit: `test_X.py::TestY — N/N PASS`
- [ ] Istniejące testy zmienionego kodu też passują
- [ ] Blast radius check — ten sam bug nie istnieje w innych miejscach
- [ ] Commit

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-27 | Wydzielenie z workflow_developer.md (sekcja Bug fix) |
