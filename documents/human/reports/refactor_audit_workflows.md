# Refactor Audit: Workflows → CONVENTION_WORKFLOW compliance

**Data:** 2026-03-24
**Autor:** PE
**Scope:** bi_view_creation_workflow.md, developer_workflow.md

---

## Podsumowanie zmian

| Workflow | Stara nazwa | Nowa nazwa | Zmiany strukturalne |
|---|---|---|---|
| BI View | bi_view_creation_workflow.md | workflow_bi_view_creation.md | +YAML header, +Outline |
| Developer | developer_workflow.md | workflow_developer.md | +YAML header, +Outline |

**Treść:** Bez zmian. Refaktor dotyczy tylko struktury (YAML, Outline, nazwa).

---

## 1. bi_view_creation_workflow.md

### Elementy do zachowania (mapowanie)

| Element | Typ | Lokalizacja w nowym pliku | Status |
|---|---|---|---|
| Opis wstępny (linie 1-9) | Intro | Po Outline, przed fazami | ✓ zachowane |
| Inicjalizacja | Faza | ## Faza 0: Inicjalizacja | ✓ zachowane |
| Faza 0 — Discovery | Faza | ## Faza 1: Discovery | ✓ zachowane |
| Faza 1 — Plan mapowania | Faza | ## Faza 2: Plan mapowania | ✓ zachowane |
| Faza 1a — Tworzenie planu | Sub-faza | ### Faza 2a: Tworzenie planu | ✓ zachowane |
| Faza 1b — Recenzja planu | Sub-faza | ### Faza 2b: Recenzja planu | ✓ zachowane |
| Faza 2 — SQL na brudnopisie | Faza | ## Faza 3: SQL na brudnopisie | ✓ zachowane |
| Faza 3 — Weryfikacja eksportu | Faza | ## Faza 4: Weryfikacja eksportu | ✓ zachowane |
| Faza 4 — Zapis i wdrożenie | Faza | ## Faza 5: Zapis i wdrożenie | ✓ zachowane |
| Zarządzanie kontekstem | Sekcja | ## Zarządzanie kontekstem | ✓ zachowane |
| Kiedy eskalować | Sekcja | ## Kiedy eskalować | ✓ zachowane |

### Elementy do dodania

| Element | Źródło | Treść |
|---|---|---|
| YAML header | CONVENTION_WORKFLOW 01R | workflow_id, version, owner_role, trigger, participants, related_docs, outputs |
| Outline | CONVENTION_WORKFLOW 02R | Lista faz z lotu ptaka |

### YAML header (propozycja)

```yaml
---
workflow_id: bi_view_creation
version: "2.0"
owner_role: erp_specialist
trigger: "Użytkownik prosi o utworzenie widoku BI"
participants:
  - erp_specialist (implementacja)
  - analyst (recenzja planu, weryfikacja eksportu)
  - human (DBA deployment)
related_docs:
  - documents/erp_specialist/ERP_SQL_SYNTAX.md
  - documents/erp_specialist/ERP_SCHEMA_PATTERNS.md
prerequisites:
  - session_init_done
  - schema_loaded
outputs:
  - type: file
    path: "solutions/bi/views/{NazwaWidoku}.sql"
  - type: file
    path: "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_export.xlsx"
  - type: commit
---
```

### Outline (propozycja)

```markdown
## Outline

0. **Inicjalizacja** — utworzenie plików roboczych
1. **Discovery** — analiza struktury, enumeracje, typy danych
2. **Plan mapowania** — plan kolumn + recenzja Analityka
3. **SQL na brudnopisie** — iteracyjne budowanie SELECT
4. **Weryfikacja eksportu** — bi_verify + approval Analityka
5. **Zapis i wdrożenie** — CREATE VIEW, DBA, katalog, commit
```

---

## 2. developer_workflow.md

### Elementy do zachowania (mapowanie)

| Element | Typ | Lokalizacja w nowym pliku | Status |
|---|---|---|---|
| Opis wstępny (linie 1-5) | Intro | Po Outline | ✓ zachowane |
| Routing table | Sekcja | ## Routing | ✓ zachowane |
| Narzędzie (Tool) | Sekcja | ## Narzędzie | ✓ zachowane |
| Bug fix | Sekcja | ## Bug fix | ✓ zachowane |
| Patch | Sekcja | ## Patch | ✓ zachowane |
| Suggestions | Sekcja | ## Suggestions | ✓ zachowane |
| Zamknięcie sesji | Sekcja | ## Zamknięcie sesji | ✓ zachowane |
| Mockup outputu | Sekcja | ## Mockup outputu | ✓ zachowane |

### Elementy do dodania

| Element | Źródło | Treść |
|---|---|---|
| YAML header | CONVENTION_WORKFLOW 01R | workflow_id, version, owner_role, trigger |
| Outline | CONVENTION_WORKFLOW 02R | Lista sekcji routing |

### YAML header (propozycja)

```yaml
---
workflow_id: developer_operations
version: "2.0"
owner_role: developer
trigger: "Developer otrzymuje zadanie operacyjne lub taktyczne"
related_docs:
  - documents/dev/DEVELOPER.md
  - documents/dev/PROJECT_START.md
prerequisites:
  - session_init_done
outputs:
  - type: commit
  - type: message
    field: "notyfikacje do ról (jeśli narzędzie wspólne)"
---
```

### Outline (propozycja)

```markdown
## Outline

Workflow multi-scenario — wybierz sekcję według typu zadania:

1. **Narzędzie** — nowe narzędzie lub rozbudowa istniejącego
2. **Bug fix** — diagnoza i naprawa błędu
3. **Patch** — drobna zmiana (≤5 linii, jeden plik)
4. **Suggestions** — przetwarzanie sugestii od Wykonawców
5. **Zamknięcie** — końcówka sesji (commit, log)
```

---

## Weryfikacja po refaktorze

**Checklist:**
- [x] Wszystkie fazy/sekcje zmapowane? ✓
- [x] Żaden content nie usunięty? ✓
- [x] YAML header zgodny z 01R? ✓
- [x] Outline zgodny z 02R? ✓

**Porównanie linii:**
- bi_view: 551 → 582 (+31 = YAML + Outline)
- developer: 183 → 209 (+26 = YAML + Outline)

**Sekcje zachowane:**
- bi_view: 9/9 (+ Outline)
- developer: 7/7 (+ Outline)

---

## Kolejność wykonania

1. Archiwizuj oryginały do `archive/pre_workflow_refactor/`
2. Utwórz nowy plik z YAML header + Outline
3. Skopiuj całą treść (bez zmian)
4. Usuń stary plik
5. Commit
6. Weryfikacja mapowania (przejdź przez tabelę)
