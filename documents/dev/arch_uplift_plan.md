# Plan podnoszenia architektury — Mrowisko 2.0

Cel: przejście od systemu agentów wyzwalanych ręcznie do autonomicznego roju z pełną
obserwowalnością. Każda faza jest niezależnie wartościowa i deployowalna.

Analiza koncepcyjna: `documents/dev/analiza_kierunki_2026-03-14.md`

---

## Faza 1 — Zapis sesji (w toku)

**Cel:** każda sesja jest identyfikowalna, każda wiadomość człowieka i agenta zapisana.

| id | Zadanie | Status |
|----|---------|--------|
| 47 | Zapis konwersacji do bazy — trace + conversation tables | w toku |
| 49 | on_stop zapisuje last_assistant_message + render sesji | planned |
| 50 | session_init — jeden tool call zamiast czytania 3-4 plików .md | planned |

**Wyniki E1-E3 (2026-03-14):**
- Hook UserPromptSubmit: działa, daje session_id + transcript_path + treść wiadomości
- Hook Stop: działa, daje last_assistant_message + transcript_path
- transcript_path → pełny .jsonl transkrypt sesji już istnieje — nie budujemy własnego trace
- Claude Code własne session_id zastępuje nasze UUID

**Następny krok:** on_stop.py zapisuje do conversation; zbadać strukturę .jsonl; skrócić CLAUDE.md

---

## Faza 2 — Wywoływanie agentów (planned)

**Cel:** agent może zlecić zadanie innemu agentowi bez człowieka w pętli.

| id | Zadanie | Status |
|----|---------|--------|
| 48 | Mrowisko runner — inbox poller + subprocess Claude Code CLI | planned |
| 51 | Runner z approval gate (człowiek zatwierdza każde wywołanie) | planned |
| 52 | Runner autonomiczny (bez gate, dla zaufanych par ról) | planned |

**Zależność:** wymaga działającej Fazy 1 (session_id jako parent_session_id wywołania).

---

## Faza 3 — Prompty z bazy (planned)

**Cel:** prompty ról w DB zamiast plików .md — dynamiczne, wersjonowane, edytowalne przez rolę.

| id | Zadanie | Status |
|----|---------|--------|
| 53 | Tabela prompts + migracja dokumentów ról | planned |
| 54 | Prompt Engineer — rola do edycji promptów w DB | planned |

**Efekt:** CLAUDE.md staje się minimalny (routing + "wywołaj session_init"). Pliki chronione znikają.

---

## Faza 4 — Project Manager (planned)

**Cel:** rola orkiestrująca wielowątkowe sesje agentów.

| id | Zadanie | Status |
|----|---------|--------|
| 55 | PM — rola: planuje sesje, monitoruje backlog, raportuje stan | planned |

**Zależność:** sensowny dopiero po Fazie 2 (bez runnera PM nie ma czym zarządzać).

---

## Faza 5 — Dokumentacja w bazie + rendery (planned)

**Cel:** jedna baza danych jako źródło wiedzy; człowiek i agent widzą to samo przez rendery.

| id | Zadanie | Status |
|----|---------|--------|
| 56 | Tabela docs + migracja documents/ do DB | planned |
| 57 | render.py --session → XLSX: Conversation / ToolCalls / Summary | planned |

**Efekt:** człowiek w 30s rozumie co agent dostał i co zrobił w sesji.

---

## Mapa zależności

```
Faza 1 (zapis sesji)
    │
    ▼
Faza 2 (agent invocation)  →  Faza 3 (prompty w DB)
    │
    ▼
Faza 4 (PM)
    │
    ▼
Faza 5 (docs w DB + rendery)
```

---

*Ostatnia aktualizacja: 2026-03-14*
