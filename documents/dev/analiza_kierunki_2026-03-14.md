# Analiza kierunków projektu — 2026-03-14

## Podsumowanie

Pięć propozycji atakuje ten sam problem z różnych stron: projekt rośnie, agenci potrzebują
lepszego kontekstu, ciągłości i koordynacji. Żadna z propozycji nie jest zła — pytanie
o kolejność i co da najwyższy zwrot teraz.

**Rekomendacja priorytetowa:**

1. **(5) Agent-to-agent invocation** — najwyższy zwrot strategiczny, buduje rdzeń mrowiska.
   Aktualnie agent_bus jest gotową infrastrukturą — brakuje tylko runnera.
2. **(3) Zapis konwersacji do bazy** — niski koszt wdrożenia (hooki Claude Code), wysoka
   wartość natychmiast (debugging, audit trail, ciągłość kontekstu).
3. **(2) Project Manager** — sensowny po tym, jak mamy agentów wywołujących się nawzajem.
   Bez #5 PM nie ma czym zarządzać.
4. **(1) Prompt Engineer + prompts w bazie** — wartościowe, ale duże ryzyko: traci się
   git diff, audit, human-readability. Warto rozważyć hybrydę (baza dla dynamicznych
   fragmentów, pliki dla stałych).
5. **(4) Cała dokumentacja do bazy** — najwyższy koszt i ryzyko, najniższy priorytet.
   Obecny hybrydowy model (pliki + DB) jest funkcjonalny i wystarczający przez długi czas.

---

## 1. Prompt Engineer + prompty w bazie

**Idea:** Prompty z plików .md trafiają do bazy. Nowa rola "Prompt Engineer" buduje je
dynamicznie — optymalizuje kontekst, eliminuje redundancję, usuwa protected files.

**Wartość:**
- Eliminuje problem plików chronionych (edycja przez rolę, nie git)
- Dynamiczne budowanie promptu = mniej tokenów (ładujesz tylko co potrzebne)
- Wersjonowanie promptów niezależnie od kodu

**Koszty i ryzyko:**
- Traci się `git diff` na promptach — zmiany niewidoczne w historii
- Agenci muszą wiedzieć jak załadować prompt z bazy na starcie sesji (dodatkowy krok)
- Bootstrap nowego projektu staje się trudniejszy (nie ma pliku do sklonowania)
- Jeśli baza się zepsuje / zmigruje — prompty znikają
- Obecny problem to nie tyle format promptów co ich treść i egzekucja reguł

**Ocena:** Sensowne jako ewolucja, nie rewolucja. Lepszy wariant: dynamiczne fragmenty
(kontekst firmowy, lista narzędzi, backlog) w bazie; szkielet roli zostaje w plikach.
Eliminuje największą wadę (monolityczne pliki .md) bez ryzyka utraty audytowalności.

**Wysiłek:** duży (refaktor wszystkich ról + nowa rola + testy)
**Zysk teraz:** średni — obecne pliki działają, ból pojawia się przy skali 10+ agentów

---

## 2. Project Manager — orkiestracja agentów

**Idea:** Rola PM planuje wielowątkowe sesje, monitoruje postęp, zapewnia ciągłość
między sesjami — zarówno dla agentów jak i człowieka.

**Wartość:**
- Człowiek deleguje do PM, nie do każdego agenta osobno
- PM może śledzić czy zadanie zostało zrealizowane i eskalować
- Naturalny punkt wejścia dla "firma prowadzona przez AI"

**Koszty i ryzyko:**
- PM bez możliwości wywoływania agentów = tylko koordynator papierowy
- Dodaje warstwę pośrednią, która może stać się wąskim gardłem
- PM potrzebuje bogatego kontekstu o stanie wszystkich agentów — duże zużycie tokenów
- Bez #5 (agent invocation) PM to tylko kolejny czytający inbox

**Ocena:** Właściwy krok, ale w złej kolejności. PM ma sens po zbudowaniu mechanizmu
wywoływania agentów. Teraz agent_bus + człowiek jako dispatcher wystarcza.

**Wysiłek:** średni-duży
**Zysk teraz:** niski — staje się wartościowy dopiero przy 3+ równoległych wątkach

---

## 3. Zapis konwersacji do bazy

**Idea:** Treść sesji (tool calls, decyzje, wyniki) zapisywana do bazy bezpośrednio
z wiersza poleceń — dla analizy, ciągłości i pełnego audytu.

**Wartość:**
- Ciągłość kontekstu między sesjami bez polegania na MEMORY.md
- Debugging: "dlaczego agent podjął tę decyzję w sesji X"
- Podstawa dla eval harness (golden tasks)
- EU AI Act wymaga audytowalności (horyzont 2)
- Dane do uczenia na własnych sesjach

**Koszty i ryzyko:**
- Claude Code nie eksportuje historii konwersacji bezpośrednio
- Hooki `PostToolUse` / `Stop` mogą przechwycić tool calls i wyniki — to realne
- Duże wolumeny danych (jedna sesja = MB), potrzeba filtrowania sygnału
- Prywatność: konwersacje mogą zawierać dane wrażliwe

**Techniczne możliwości już teraz:**
- `~/.claude/hooks/` z `PostToolUse` → zapis do mrowisko.db
- Istniejący fundament: `logs/bot/YYYY-MM-DD.jsonl` (bot już loguje)
- `session_log` tabela w DB już istnieje — rozszerzenie naturalne

**Ocena:** Najlepszy stosunek wysiłku do wartości z całej piątki. Hook + tabela `trace`
w DB to ~1 dzień pracy. Natychmiast: debugging sesji, ciągłość kontekstu, fundament evali.

**Wysiłek:** mały-średni
**Zysk teraz:** wysoki

---

## 4. Cała dokumentacja do bazy

**Idea:** Dokumenty .md, struktura projektu, plany, raporty — wszystko w jednej bazie
zamiast systemu plików.

**Wartość:**
- Jedno źródło prawdy, queryowalne
- Relacje między dokumentami (np. widok BI → plan → konwencje)
- Dynamiczne raporty i agregacje

**Koszty i ryzyko:**
- Git traci sens jako historia dokumentacji — kluczowe narzędzie audytu
- Bootstrap projektu wymaga bazy, nie wystarczy `git clone`
- Pliki .md są czytelne dla człowieka bezpośrednio — baza już nie
- Migracja istniejącej dokumentacji: duże ryzyko utraty struktury
- Markdown FTS5 już działa (`docs.db`) — dodatkowa wartość jest marginalna

**Ocena:** Najwyższy koszt, najniższy priorytet. Obecny hybrydowy model (pliki dla
stałej wiedzy, DB dla dynamicznych danych) jest optymalny przez bardzo długi czas.
Migracja byłaby sensowna gdyby dokumentacja generowała realne wąskie gardła — na razie nie.

**Wysiłek:** bardzo duży
**Zysk teraz:** niski

---

## 5. Agent-to-agent invocation

**Idea:** Agenci mogą się nawzajem wywoływać przez wiadomości — jeden agent kończy
pracę i inicjuje kolejnego bez interwencji człowieka.

**Wartość:**
- Rdzeń mrowiska: prawdziwa autonomia wielowątkowa
- ERP Specialist kończy widok → automatycznie wyzwala Analityka do recenzji
- PM zleca zadania i odbiera wyniki bez człowieka w pętli
- Najważniejszy krok na drodze od "asystent" do "autonomiczna firma"

**Koszty i ryzyko:**
- Techniczne: Claude Code nie ma API do wywoływania innych instancji z wewnątrz sesji
- Możliwe podejścia:
  a) **Scheduler/daemon** czyta inbox i startuje sesje Claude Code CLI (`claude --message "..."`)
  b) **Webhook** — agent_bus_server.py odbiera event i wywołuje subprocess
  c) **Człowiek jako tymczasowy dispatcher** — agent pisze do inboxu, człowiek ręcznie startuje
- Opcja (c) już działa. Opcje (a)/(b) wymagają ostrożności: nieskończone pętle, koszty API
- Bezpieczeństwo: agent nie może wywołać agenta o wyższych uprawnieniach

**Stan obecny:** agent_bus gotowy jako szyna komunikacyjna.
Brakuje: runner który czyta inbox i startuje sesje autonomicznie.

**Opcja (a) — runner CLI:**
```
# mrowisko_runner.py — daemon polling inbox
while True:
    tasks = agent_bus.get_inbox(role="erp_specialist", status="unread")
    for task in tasks:
        subprocess.run(["claude", "--message", task["content"]])
    sleep(60)
```

**Ocena:** Strategicznie najważniejsze. Proof of concept jest mały (~50 linii).
Ryzyko: niekontrolowane pętle i koszty — wymaga rate limiting i approval gate.
Rekomendacja: zbudować runner z manualnym approvalem jako guard (człowiek zatwierdza
każde wywołanie zanim runner odpali agenta) — eliminuje ryzyko, zachowuje wartość.

**Wysiłek:** mały PoC / duży produkcyjnie
**Zysk teraz:** wysoki strategicznie, zależy od implementacji

---

## Mapa zależności

```
#3 Zapis konwersacji  ──►  dane do debugowania i evali (natychmiast)
#5 Agent invocation   ──►  autonomia (fundament mrowiska)
        │
        ▼
#2 Project Manager    ──►  orkiestracja (sensowny gdy #5 gotowe)
        │
        ▼
#1 Prompt Engineer    ──►  optymalizacja (gdy skala wymaga)
#4 Docs do bazy       ──►  (gdy pliki stają się wąskim gardłem — długi horyzont)
```

---

*Dokument: Developer, sesja 2026-03-14*
