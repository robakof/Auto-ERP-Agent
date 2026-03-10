# Handoff → Metodolog | 2026-03-10

## Stan projektu

Projekt ma cztery role agentów:

| Rola | Dokument | Status |
|---|---|---|
| Agent ERP | `documents/agent/AGENT.md` | aktywny, produkcyjny |
| Analityk Danych | `documents/analyst/ANALYST.md` | nowy, właśnie zbudowany |
| Developer | `documents/dev/DEVELOPER.md` | aktywny |
| Metodolog | `documents/methodology/METHODOLOGY.md` | aktywny |

Narzędzia Analityka: 5 nowych CLI (`data_quality_*`), 308 testów, 100% zielone.

---

## Obserwacja która wywołała sygnał

Budując Analityka Danych okazało się, że metodologia zakłada jeden poziom wykonawczy
("Agent") — ale projekt ma już dwie odrębne role wykonawcze (ERP + Analityk) i może
mieć więcej w przyszłości.

To ujawniło trzy niespójności:

**1. Nazwa poziomu**
METHODOLOGY.md i CLAUDE.md mówią o jednym poziomie "Agent".
Faktycznie jest to poziom z wieloma rolami. Nazwa jest myląca.

**2. Wspólna pamięć refleksji**
Obie role wykonawcze dzielą `agent_suggestions.md`.
Obserwacje Analityka (jakość danych, wzorce anomalii) i Agenta ERP (schematy SQL,
JOINy, workflow BI) to różne kategorie wiedzy — mieszanie je zaszumi plik i utrudni
Developerowi przetwarzanie.

**3. Progress log Analityka — brak wzorca**
Agent ERP prowadzi progress log per projekt (widok, filtr, kolumna) — jednostka pracy
jest jasna. Analityk nie ma zdefiniowanej jednostki pracy.
Per zakres (jeden widok/tabela)? Per sesja? Per raport?
Obecna architektura zakłada plik `_workdb.db` per zakres jako stan sesji, ale
nie ma odpowiednika progress loga dla ciągłości między sesjami analitycznymi.

---

## Pytania do rozważenia

1. Jak nazwać poziom wykonawczy gdy jest na nim wiele ról?
   (propozycja: "Executor" lub "Agenci" — ale to decyzja metodologiczna, nie techniczna)

2. Czy każda rola wykonawcza powinna mieć własny plik suggestions?
   Jeśli tak — jak Developer ma je przetwarzać? Jeden backlog czy osobne?

3. Jaka jest jednostka pracy Analityka dla progress loga?
   Czy w ogóle potrzebuje progress loga w sensie projektowym, czy `_workdb.db`
   wystarczy jako stan sesji?

4. Czy zasada "1 poziom — 1 plik refleksji" powinna być zastąpiona
   "1 rola — 1 plik refleksji"?

---

## Co już zdecydowane (nie wymaga metodologa)

- Architektura narzędzi Analityka — gotowa, przetestowana
- ANALYST.md — gotowy, wymaga tylko korekty jeśli metodolog zmieni strukturę pamięci
- Routing w CLAUDE.md — gotowy, może wymagać korekty nazwy poziomu
