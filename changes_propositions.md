# Plan zmian — separacja pamięci między agentami wykonawczymi

**Sesja:** 2026-03-11
**Zakres:** architektura refleksji, etykiety poziomów, progress log Analityka

---

## Otwarte wątki z poprzednich sesji

Brak innych otwartych wątków blokujących ten zakres.

---

## 1. Nowy plik suggestions dla Analityka

**Plik:** `documents/analyst/analyst_suggestions.md`

Nowy plik refleksji Analityka Danych — analogiczna struktura do `agent_suggestions.md`.
Nagłówek z opisem jak pisać + sekcja Wpisy + sekcja Archiwum.

---

## 2. ANALYST.md — dwie zmiany

**Plik chroniony — wymaga zatwierdzenia.**

**a) Sekcja "Refleksja po sesji" (linia 171):**

```
# przed
Po zakończeniu analizy dopisz wpis do `documents/agent/agent_suggestions.md`.

# po
Po zakończeniu analizy dopisz wpis do `documents/analyst/analyst_suggestions.md`.
```

**b) Nowa sekcja "Progress log" (przed "Refleksja po sesji"):**

```
## Progress log

Dla każdego zakresu analizy prowadź lokalny progress log:

  solutions/analyst/{Zakres}/{Zakres}_progress.md

Twórz go przy inicjalizacji obszaru roboczego (Krok 1). Zapisuj:
- co zbadano, jakie wzorce znaleziono
- decyzje podjęte podczas analizy
- "Następny krok:" zawsze obecny — punkt wejścia dla kolejnej sesji

Plik jest zewnętrzną pamięcią sesji — odbiorcą jest kolejna instancja Analityka.
```

---

## 3. CLAUDE.md — dwie zmiany

**Plik chroniony — wymaga zatwierdzenia.**

**a) Linia 41 — rozszerzenie wyjątku o oba pliki suggestions:**

```
# przed
Wyjątek: `documents/agent/agent_suggestions.md` — agent dopisuje autonomicznie po etapie pracy.

# po
Wyjątki — dopisywane autonomicznie po etapie pracy:
- `documents/agent/agent_suggestions.md` (Agent ERP)
- `documents/analyst/analyst_suggestions.md` (Analityk Danych)
```

**b) Linia 45 — zmiana etykiety poziomu "Agent" → "Wykonawcy":**

```
# przed
Projekt działa na trzech poziomach (Agent / Developer / Metodolog).

# po
Projekt działa na trzech poziomach (Wykonawcy / Developer / Metodolog).
```

---

## 4. METHODOLOGY.md — dwie zmiany

**Plik chroniony — wymaga zatwierdzenia.**

**a) Tabela ról (linia 67-70) — zaktualizować żeby pokazywała wielość ról na poziomie Wykonawcy:**

```
# przed
| **Agent** | Executor | `CLAUDE.md` → `documents/agent/AGENT.md` | Realizuje konkretne zadania |

# po — jeden zbiorczy wiersz
| **Wykonawcy** | Executor | Agent ERP: `documents/agent/AGENT.md`, Analityk Danych: `documents/analyst/ANALYST.md` | Realizują zadania w swojej domenie |
```

**b) Tabela przepływu refleksji (linia 304-310) — dodać wiersz Analityka:**

```
# przed
| Agent | `documents/agent/agent_suggestions.md` | `documents/dev/backlog.md` | Developer |

# po
| Agent ERP | `documents/agent/agent_suggestions.md` | `documents/dev/backlog.md` | Developer |
| Analityk Danych | `documents/analyst/analyst_suggestions.md` | `documents/dev/backlog.md` | Developer |
```

---

## 5. backlog.md — archiwizacja po wdrożeniu

Przenieść `[Arch] Separacja pamięci między agentami wykonawczymi` do sekcji Archiwum.

---

## Poza zakresem

- Zmiana struktury progress logu Agenta ERP (nadal w globalnym `documents/dev/progress_log.md`) — nie ruszamy.
- Migracja zawartości `agent_suggestions.md` — nie ruszamy, tylko zaprzestajemy kierowania Analityka do tego pliku.
- Zmiana nazwy folderu `documents/agent/` — nie ruszamy (folder zawiera wytyczne tylko dla Agent ERP).

---

## Kolejność implementacji

1. Utwórz `documents/analyst/analyst_suggestions.md`
2. Zaktualizuj `ANALYST.md`
3. Zaktualizuj `CLAUDE.md`
4. Zaktualizuj `METHODOLOGY.md`
5. Zarchiwizuj w `backlog.md`
6. Commit + push
