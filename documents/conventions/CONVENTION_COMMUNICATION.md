---
convention_id: communication-convention
version: "2.0"
status: active
created: 2026-03-25
updated: 2026-03-25
author: architect
owner: architect
approver: dawid
audience: [developer, architect, prompt_engineer, erp_specialist, analyst, metodolog]
scope: "Zasady komunikacji agent-agent wymagające osądu — mechanizmy egzekwowane przez tooling"
---

# CONVENTION_COMMUNICATION — Komunikacja agent-agent

## TL;DR

- Jeden kanał do jednej funkcji: suggest = obserwacja, backlog = zadanie, send = koordynacja, flag = eskalacja, handoff = przekazanie
- Typ sugestii dobierz świadomie: rule / discovery / observation / tool — nie defaultuj do observation
- Tytuł max 80 znaków, konkretny, jednoznacznie identyfikujący obserwację
- Handoff: phase + status + summary (co zrobiono) + next-action (co dalej) — bez ogólników
---

## Zakres

**Pokrywa:**
- Wybór kanału komunikacji (decision tree)
- Format sugestii: typ, tytuł, treść
- Format handoff
- Stale review (TTL sugestii)
- Antywzorce komunikacyjne

**NIE pokrywa:**
- Implementacja techniczna agent_bus (to Developer)
- Mechanizmy egzekwowane przez tooling (mark-read, reply-to, session_id, inline content — wbudowane w CLI)
- Treść merytoryczna sugestii (to ich autorzy)
- Workflow trigger/execution (to CONVENTION_WORKFLOW)

---

## Kontekst

### Problem

Bez konwencji komunikacji agenci:
- Używają złego kanału (suggest zamiast backlog, flag zamiast send)
- Piszą sugestie bez struktury — typ observation na wszystko
- Tworzą delegation loops (4 wiadomości, 0 akcji)
- Nie zamykają wątków — sugestie rosną w nieskończoność

### Rozwiązanie

Dwuwarstwowe:
1. **Mechanizmy w toolingu** (Agent Bus v2, #187) — mark-read, reply-to, session_id, inline content. Agent nie musi pamiętać — system egzekwuje.
2. **Konwencja** (ten dokument) — decyzje wymagające osądu: który kanał, jaki typ, jaka jakość tytułu.

---

## Reguły

### 01R: Decision tree — wybór kanału

Przed wysłaniem komunikatu wybierz kanał:

| Mam...                               | Kanał         | Kto widzi               |
| ------------------------------------ | ------------- | ----------------------- |
| Obserwację, regułę, odkrycie z pracy | `suggest`     | Triage przez Architekta |
| Konkretne zadanie do realizacji      | `backlog-add` | Rola owner obszaru      |
| Pytanie, odpowiedź, prośba o review  | `send`        | Adresat                 |
| Blokadę wymagającą decyzji człowieka | `flag`        | Dawid                   |
| Zakończenie fazy, przekazanie pracy  | `handoff`     | Adresat                 |

**Jedna wiadomość = jeden cel.** Nie mieszaj obserwacji z pytaniem w jednej wiadomości.

**Flag = blokada, nie pytanie.** Jeśli możesz kontynuować bez odpowiedzi — to nie jest flag.

---

### 02R: Typ sugestii — dobierz świadomie

| Typ | Kiedy | Przykład |
|-----|-------|---------|
| `rule` | Masz konkretną regułę do wdrożenia | "Idempotency guard jako standard w agent_bus" |
| `discovery` | Odkryłeś jak coś działa technicznie | "PYTHONIOENCODING stabilniejsze niż encoding=" |
| `observation` | Zauważyłeś wzorzec, nie masz recepty | "Inbox overflow — systemowy problem skali" |
| `tool` | Brakuje narzędzia lub rozszerzenia | "Brakuje komendy bulk mark-read" |

**Nie defaultuj do observation.** Jeśli masz receptę → `rule`. Jeśli odkryłeś fakt techniczny → `discovery`. Jeśli chcesz narzędzie → `tool`.

---

### 03R: Jakość tytułu

- **Max 80 znaków**
- **Konkretny** — jednoznacznie identyfikuje obserwację
- **Imperatyw lub opis** — nie pytanie

Dobrze:
```
Mark-read wymaga explicit kroku w workflow
Dual data path = bug factory — jedna ścieżka do danych
Mechanizm przed konwencją — reguła kompensująca brak narzędzia to workaround
```

Źle:
```
Obserwacja z sesji                   ← zbyt ogólny
Może warto dodać X?                  ← pytanie
Problem z wiadomościami bo agenci    ← "bo" to treść, nie tytuł
```

---

### 04R: Format handoff

Handoff MUSI zawierać konkretne wartości:

- `--phase` — nazwa etapu który się zakończył (nie ogólnik)
- `--status` — PASS / FAIL / PARTIAL
- `--summary` — co zrobiono (czas przeszły, fakty)
- `--next-action` — co musi zrobić adresat (imperatyw)

Dobrze:
```
phase: "Code review — known_gaps feature"
status: PASS
summary: "0 critical, 2 warnings. Raport: documents/human/reports/review_known_gaps.md"
next-action: "Napraw W1 (FK pragma) i W2 (testy) przed merge."
```

Źle:
```
phase: "review"           ← zbyt ogólne
summary: "Zrobiłem."      ← co konkretnie?
next-action: "Zajmij się." ← czym?
```

---

### 05R: Duplikaty — merge zamiast kasowania

Duplikat może nieść dodatkowy kontekst.

- Identyczna obserwacja → nie wysyłaj nowej. Dodaj komentarz do istniejącej.
- Upgrade (observation → rule) → wyślij nową, oznacz starą jako `merged` z referencją.
- Nie kasuj duplikatów bez sprawdzenia czy niosą dodatkową informację.

---

## Przykłady

### Przykład 1: Dobra sugestia — rule

```
suggest --from developer --type rule \
  --title "Idempotency guard jako standard w agent_bus" \
  --content "Sprawdź stan przed UPDATE, zwróć info zamiast nadpisywać. Dotyczy wszystkich operacji zmiany statusu."
```

✓ Typ właściwy (rule), tytuł <80 zn, treść zwięzła

---

### Przykład 2: Dobry handoff

```
handoff --from developer --to architect \
  --phase "Implementacja Agent Bus v2" \
  --status PASS \
  --summary "M1-M4 wdrożone, 172 PASS, M5 deferred." \
  --next-action "Code review. Raport do: documents/human/reports/"
```

✓ Faza konkretna, summary z faktami, next-action z imperatywem

---

### Przykład 3: Właściwy kanał

```
# Agent ma pytanie architektoniczne — send, nie flag
send --from developer --to architect \
  --content "Dylemat: claim/unclaim w InstanceService czy MessageService? Trade-off: [opis]. Proponuję Instance. APPROVE?"

# Agent jest zablokowany bez decyzji człowieka — flag
flag --from erp_specialist \
  --reason "Brak dostępu do tabeli CDN.TraNag — potrzebuję uprawnienia DBA."
```

---

## Antywzorce

### 01AP: Typ observation na wszystko

**Źle:**
```
suggest --type observation --title "Idempotency guard jako standard"
# To jest rule, nie observation
```

**Dlaczego:** Wszystko jako observation blokuje triage. Triażer nie wie czy to wymaga backlog (tool), zmiany reguły (rule), czy tylko zanotowania.

**Dobrze:** Użyj właściwego typu. Patrz 02R.

---

### 02AP: Delegation loops

**Źle:**
```
Architect → Developer: "Zrób X"
Developer → Architect: "Nie jestem pewien, co myślisz?"
Architect → Developer: "Sprawdź Y"
Developer → Architect: "Y mówi Z, ale..."
# 4 wiadomości, 0 akcji
```

**Dlaczego:** Każdy back-and-forth bez decyzji to zmarnowany kontekst obu stron.

**Dobrze:** Podaj propozycję z trade-offami zamiast pytać "co myślisz?":
```
send --from developer --to architect \
  --content "JOIN vs subquery. JOIN szybszy 30%, subquery czytelniejszy. Proponuję JOIN. APPROVE/REJECT?"
```

---

### 03AP: Flag zamiast send dla spraw niekrytycznych

**Źle:**
```
flag --from erp_specialist --reason "Nie wiem czy JOIN czy subquery."
```

**Dlaczego:** Flag = blokada. Człowiek może nie odpowiedzieć przez godziny. Pytanie o SQL nie jest blokadą.

**Dobrze:**
```
send --from erp_specialist --to architect --content "Dylemat JOIN vs subquery — jakie trade-offy?"
```

---

## References

- Research: `documents/researcher/research/research_results_convention_communication.md`
- Agent Bus v2 (backlog #187): mechanizmy M1-M4 wdrożone
- FIPA ACL, PagerDuty, Alertmanager: wzorce dedup/grouping/suppress
- Zasada: "mechanizm przed konwencją" (suggest #345)

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 2.0 | 2026-03-25 | Rewrite po Agent Bus v2. Reduced scope: 6 reguł o osądzie (z 13). Usunięto reguły egzekwowane przez mechanizmy (mark-read, reply-to, session_id, inline content, dedup check). |
| 1.1 | 2026-03-25 | Enrichment z researchu: korelacja, stale/TTL, delegation loops, merge semantics. |
| 1.0 | 2026-03-25 | Wersja początkowa — decision tree, formaty, anty-duplikacja, lifecycle inbox. Status: BLOCKED by #187. |
