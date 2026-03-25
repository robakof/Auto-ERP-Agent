---
convention_id: meta-convention
version: "1.1"
status: active
created: 2026-03-24
updated: 2026-03-25
author: architect
owner: architect
approver: dawid
audience: [architect, prompt_engineer, developer, metodolog]
scope: "Definiuje strukturę wszystkich konwencji w projekcie Mrowisko"
---

# CONVENTION_META — Konwencja dla konwencji

## TL;DR

- Konwencja = YAML frontmatter + markdown body
- Wymagane sekcje: TL;DR, Zakres, Reguły, Przykłady, Antywzorce, Changelog
- Cykl życia statusu: `draft` → `review` → `active` → `deprecated`
- Tylko Dawid może zatwierdzić przejście do `active`
- Język: polski (warstwa sterowania)

---

## Zakres

**Pokrywa:**
- Struktura każdej konwencji (wymagane sekcje)
- YAML frontmatter (pola metadata)
- Cykl życia statusu
- Model własności (author/owner/approver)

**NIE pokrywa:**
- Treść poszczególnych konwencji (decydują ich ownerzy)
- Tooling do walidacji (przyszłość: osobna konwencja)

---

## Kontekst

### Problem

Bez CONVENTION_META:
- Każda konwencja ma inną strukturę
- Brak machine-readable metadata (nie można parsować do DB)
- Brak zarządzania cyklem życia (kto zatwierdza? kiedy deprecated?)

### Rozwiązanie

CONVENTION_META definiuje:
1. **Unified structure** — wszystkie konwencje tej samej anatomii
2. **Machine-readable metadata** — YAML frontmatter parseable do DB
3. **Lifecycle states** — jawne przejścia statusów

---

## Reguły

### 01R: YAML Frontmatter wymagany

Każda konwencja MUSI mieć YAML frontmatter z polami:

```yaml
---
convention_id: string     # unikalny identyfikator (kebab-case)
version: string           # "1.0", "1.1", etc.
status: enum              # draft | review | active | deprecated
created: date             # YYYY-MM-DD
updated: date             # YYYY-MM-DD (ostatnia modyfikacja)
author: string            # kto napisał
owner: string             # kto utrzymuje
approver: string          # kto zatwierdza przejścia statusów
reviewer: list[string]    # [opcjonalne] kto robi review przed zatwierdzeniem
audience: list[string]    # kogo dotyczy (relacje DB)
scope: string             # co konwencja pokrywa (1 zdanie)
---
```

### 02R: Wymagane sekcje markdown

Każda konwencja MUSI mieć sekcje:

| Sekcja | Cel |
|---|---|
| **TL;DR** | 3-5 punktów, esencja |
| **Zakres** | Co pokrywa, co NIE, odbiorcy |
| **Reguły** | Numerowane reguły (01R, 02R...) |
| **Przykłady** | Przykłady zgodne z konwencją |
| **Antywzorce** | Bad → Why → Good (struktura 3-częściowa) |
| **Changelog** | Historia wersji |

**Opcjonalne sekcje:**
- Kontekst (dla złożonych konwencji)

### 03R: Cykl życia statusu

```
draft ──→ review ──→ active ──→ deprecated
```

| Status | Znaczenie | Kto może ustawić |
|---|---|---|
| **draft** | W trakcie pracy | Author |
| **review** | Gotowa do zatwierdzenia | Author |
| **active** | Zatwierdzona, obowiązuje | Tylko Dawid |
| **deprecated** | Wygaszana | Tylko Dawid |

### 04R: Wersjonowanie zamiast cichych edycji

Gdy konwencja fundamentalnie się zmienia:
1. Utwórz nową wersję (bump numeru wersji)
2. Udokumentuj zmianę w Changelog

NIE przepisuj cicho aktywnej konwencji bez śladu.

### 05R: Lokalizacja konwencji

Wszystkie konwencje żyją w: `documents/conventions/`

Nazewnictwo: `CONVENTION_{ZAKRES}.md` (UPPER_CASE)

### 06R: Limity jednoznaczne — twarda granica, nie widełki

Gdy reguła definiuje limit, granicę lub próg — musi być jednoznaczna.

**Dobrze:** "max 10 reguł", "max 200 linii", "max 500 znaków"
**Źle:** "8-10 reguł", "50-200 linii", "około 500 znaków"

Widełki nie są granicą — są sugestią. Agent zinterpretuje je dowolnie.
Jeśli dolna granica jest ważna — sformułuj jako osobną regułę.

---

## Przykłady

### Przykład 1: Minimalna konwencja

```yaml
---
convention_id: commit-convention
version: "1.0"
status: active
created: 2026-03-24
updated: 2026-03-24
author: developer
owner: developer
approver: dawid
audience: [developer, architect, prompt_engineer, erp_specialist]
scope: "Format wiadomości commitów"
---

# CONVENTION_COMMIT

## TL;DR

- Format: `type(scope): description`
- Typy: feat, fix, refactor, docs, test, chore
- Używaj narzędzia git_commit.py

## Zakres

Pokrywa: format wiadomości commitów dla wszystkich ról.
NIE pokrywa: nazewnictwo branchy, format PR.

## Reguły

### 01R: Format wiadomości
...

## Przykłady
...

## Antywzorce
...

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-24 | Wersja początkowa |
```

### Przykład 2: Poziomy ładowania (guideline)

Agenci ładują konwencje na odpowiedniej głębokości:

- **Start sesji:** YAML frontmatter + TL;DR (~100 tokenów)
- **Wejście w workflow:** + Zakres + Reguły + Przykłady (~500 tokenów)
- **Review/update:** Pełny dokument (~1000+ tokenów)

To jest guideline, nie wymuszane przez tooling.

---

## Antywzorce

### 01AP: Brak YAML Frontmatter

**Źle:**
```markdown
# Moja Konwencja

Jakieś reguły tutaj...
```

**Dlaczego:** Nie machine-readable, brak metadata, nie można śledzić statusu/własności.

**Dobrze:**
```yaml
---
convention_id: moja-konwencja
version: "1.0"
status: draft
...
---

# Moja Konwencja
```

### 02AP: Ciche breaking changes

**Źle:**
```markdown
# Całkowicie zmieniona sekcja Reguły
# Brak bump wersji, brak wpisu w changelog
```

**Dlaczego:** Agenci z cached knowledge będą nieświadomie łamać "nowe" reguły.

**Dobrze:**
```yaml
version: "2.0"  # bumped
---

## Changelog
| 2.0 | 2026-03-25 | Breaking: nowa struktura Reguł |
```

### 03AP: Approver = Author

**Źle:**
```yaml
author: architect
owner: architect
approver: architect  # Ta sama osoba zatwierdza własną pracę
```

**Dlaczego:** Brak bramki review, jakość niezweryfikowana.

**Dobrze:**
```yaml
author: architect
owner: architect
approver: dawid  # Zewnętrzne zatwierdzenie
```

---

## References

- Research: `documents/researcher/research/research_results_meta_convention.md`
- SKILL.md pattern: Claude Code ecosystem
- Python PEP 1: https://peps.python.org/pep-0001/
- MADR: https://adr.github.io/madr/

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.1 | 2026-03-25 | 06R: Limity jednoznaczne (twarda granica, nie widełki). Lekcja z review CONV_PROMPT/CODE. |
| 1.0 | 2026-03-24 | Początkowa CONVENTION_META — wersja minimalna, status: active |
