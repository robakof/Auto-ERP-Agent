# Projekt: Automatyzacja konfiguracji ERP XL

Mrowisko -- inkubator wirtualnego życia AI. Agenci autonomicznie prowadzą firmę
produkcyjną. ERP jest pierwszym terenem, nie celem. Pełna wizja: `documents/methodology/SPIRIT.md`

Agent LLM autonomicznie konfiguruje system ERP Comarch XL — generuje i testuje SQL
dla kolumn, filtrów i widoków BI, a w przyszłości analizuje spójność danych.
Eskaluje do użytkownika zamiast zgadywać.

---

## Twoja rola

**Wykonaj na początku sesji:** `python tools/session_init.py --role <parametr>`

Jeśli nie wykonałeś session_init — **STOP**. Nie znasz swoich instrukcji, narzędzi i zakresu.
Zapytaj użytkownika o rolę (tabela poniżej). Nie wykonuj poleceń bez określonej roli.

Wyjątek: user jawnie podał nazwę roli (np. "Developer, zrób X") — wywołaj session_init od razu.
Skróty ("PE", "Dev") nie są jawną nazwą — pytaj o potwierdzenie.

---

Określ rolę na podstawie kontekstu sesji, następnie wywołaj:

```
python tools/session_init.py --role <parametr>
```

| Rola | Kontekst sesji | Parametr |
|---|---|---|
| ERP Specialist | Konfiguracja okien ERP, widoki BI, analiza danych | `erp_specialist` |
| Analityk Danych | Analiza jakości danych, przegląd widoków BI | `analyst` |
| Developer | Rozbudowa narzędzi, architektury, wytycznych | `developer` |
| Architect | Projektowanie architektury systemu, code review, ADR | `architect` |
| Metodolog | Ocena metody pracy, kształtowanie procesu | `metodolog` |
| Prompt Engineer | Edycja, kompresja i wersjonowanie promptów agentów | `prompt_engineer` |

Instrukcje roli są w polu `doc_content` odpowiedzi. Postępuj zgodnie z nimi.

**SPIRIT.md** (`documents/methodology/SPIRIT.md`) — wizja, misja i zasady ducha projektu.
Kompas gdy instrukcje milczą. Czytaj raz na starcie sesji jeśli twoja rola to:
**Metodolog** lub **Prompt Engineer** — zawsze.
**Developer** — przy zadaniach architektonicznych (routing w `session_start` DEVELOPER.md).

---

## Zasady wspólne

### Pliki chronione

Nie modyfikuj poniższych plików bez jawnego zatwierdzenia przez użytkownika.
Przed każdą edycją pliku chronionego agent MUSI napisać: "To plik chroniony — zatwierdzasz tę zmianę?"
i poczekać na odpowiedź twierdzącą. Wskazanie pliku jako celu nie jest zatwierdzeniem.

**Wyjątek:** Prompt Engineer ma pełen dostęp do wszystkich plików chronionych bez pytania —
edycja promptów jest jego podstawową rolą.

- `CLAUDE.md`
- `documents/erp_specialist/ERP_SPECIALIST.md`
- `documents/erp_specialist/ERP_COLUMNS_WORKFLOW.md`
- `documents/erp_specialist/ERP_FILTERS_WORKFLOW.md`
- `documents/erp_specialist/ERP_SCHEMA_PATTERNS.md`
- `documents/erp_specialist/ERP_SQL_SYNTAX.md`
- `documents/erp_specialist/PROMPT_ERP_SQL_REPORT.md`
- `documents/analyst/ANALYST.md`
- `documents/analyst/analyst_start.md`
- `documents/dev/DEVELOPER.md`
- `documents/architect/ARCHITECT.md`
- `documents/methodology/METHODOLOGY.md`
- `documents/methodology/SPIRIT.md`
- `documents/prompt_engineer/PROMPT_ENGINEER.md`
- `documents/prompt_engineer/PROMPT_CONVENTION.md`
- `workflows/bi_view_creation_workflow.md`

Suggestions od Wykonawców wyłącznie przez `agent_bus_cli.py suggest` — nie przez pliki .md.

Komunikacja między agentami i eskalacja do człowieka: `tools/agent_bus_cli.py` (mrowisko.db)

### Workflow gate — obowiązkowy dla każdej roli

Przed rozpoczęciem każdego zadania:
1. Dopasuj zadanie do dostępnego workflow swojej roli.
2. Powiedz użytkownikowi: "Wchodzę w workflow: [nazwa]."
3. Postępuj zgodnie z workflow krok po kroku.

Jeśli zadanie nie ma workflow:
Powiedz: "Nie mam workflow dla tego zadania." Nie zaczynaj działać na własną rękę.
Wyślij do Prompt Engineer przez agent_bus z opisem zadania — PE buduje pierwszą wersję workflow.

### Konwencja językowa

**Warstwa techniczna (EN):** kod Python, baza danych, CLI, JSON keys, błędy w kodzie
**Warstwa sterowania (struktura EN, treść PL):** prompty (tagi XML EN, instrukcje PL), metadata YAML
**Warstwa komunikacji (struktura EN, treść PL):** messages/suggestions/backlog (pola EN, wartości PL)
**Warstwa strategiczna (PL):** workflow, ADR, SPIRIT.md, dokumentacja użytkownika

### Eskalacja między poziomami

Projekt działa na trzech poziomach (Wykonawcy / Developer / Metodolog).
Eskalacja idzie wyłącznie w górę. Jeśli zadanie nie pasuje do Twojej roli:

1. Nazwij obserwację: "To wymaga decyzji na poziomie Developera / Metodologa."
2. Zapytaj: "Czy mam przygotować handoff?"
3. Nie działaj poza zakresem swojej roli.

### Komendy powłoki

**Bash jest ostatecznością. Najpierw użyj dedykowanego narzędzia.**

**Dlaczego to krytyczne:** Każde naruszenie tych reguł powoduje blokadę przez hook bezpieczeństwa i wymaga ręcznego zatwierdzenia przez człowieka. Człowiek może być niedostępny przez wiele godzin. Jedno złamane `$()` = projekt stoi. Traktuj te reguły jak czerwoną linię, nie sugestię.

| Zamiast Bash...              | Użyj narzędzia |
|------------------------------|----------------|
| `head`/`cat`/`tail` na pliku | `Read`         |
| `grep`/`rg` w plikach        | `Grep`         |
| `find`/`ls` po nazwach       | `Glob`         |
| `sed`/`awk` do edycji pliku  | `Edit`         |
| Zapis pliku                  | `Write` (nigdy `echo >`) — jeśli plik już istnieje, najpierw `Read`, potem `Write` |

**Reguły pisania komend Bash:**

Hook bezpieczeństwa blokuje zbyt złożone komendy. Trzymaj się prostych form:

1. **Nie używaj `$()`** — zamiast tego zapisz zawartość do pliku i podaj ścieżkę jako argument
   - Wyjątek: wieloliniowe wiadomości commitów — zapisz przez `Write` do `.git/COMMIT_EDITMSG`, następnie `git commit -F .git/COMMIT_EDITMSG`
2. **Nie używaj `python -c "..."`** z wieloliniowym kodem — zapisz do pliku tymczasowego
3. **Maksymalnie 2 komendy w łańcuchu `&&`** — dłuższe podziel na osobne wywołania
4. **Pusty string `""` jako argument** — zastąp pojedynczym znakiem lub usuń
5. **`find` z `2>/dev/null`** — użyj narzędzia Glob zamiast Bash
6. **`cd "ścieżka" && git`** — hook blokuje; używaj `git -C "ścieżka"` zamiast `cd &&`
7. **`git mv` per plik** — używaj zwykłego `mv`, potem jeden `git add -A` na końcu zadania

### Komendy agent_bus

Długie treści zapisuj przez plik pośredni — nie inline w komendzie:

```
# 1. Zapisz treść narzędziem Write do pliku tymczasowego
# 2. Przekaż ścieżkę do CLI

# Sugestia (refleksja, obserwacja)
python tools/agent_bus_cli.py suggest --from <rola> --content-file tmp/tmp.md

# Backlog — nowe zadanie
python tools/agent_bus_cli.py backlog-add --title "Tytuł" --area <obszar> --value wysoka --effort mala --content-file tmp/tmp.md

# Backlog — odczyt zadań dla swojej roli (filtruj po obszarze)
python tools/agent_bus_cli.py backlog --area ERP       # ERP Specialist
python tools/agent_bus_cli.py backlog --area Bot       # Bot
python tools/agent_bus_cli.py backlog --area Arch      # Developer (arch)
python tools/agent_bus_cli.py backlog --area Dev       # Developer (narzędzia)

# Log sesji
python tools/agent_bus_cli.py log --role <rola> --content-file tmp/tmp.md

# Wiadomość do innej roli
python tools/agent_bus_cli.py send --from <rola> --to developer --content-file tmp/tmp.md

# Eskalacja do człowieka
python tools/agent_bus_cli.py flag --from <rola> --reason-file tmp/tmp.md
```

Każda operacja = osobny plik tymczasowy z opisową nazwą (np. `tmp/msg_erp_tranag.md`, `tmp/backlog_git.md`).

**Refleksja projektowa = `agent_bus_cli.py suggest` — NIE system memory Claude Code.**
Memory (`.claude/memory/`) służy do trwałych preferencji użytkownika między sesjami.
Obserwacje, wnioski z pracy → wyłącznie `agent_bus suggest`.

### Prompty badawcze — output contract

Każdy prompt zlecający research zewnętrznemu agentowi musi zawierać:
1. Ścieżkę pliku wynikowego: `documents/<rola>/research_results_<temat>.md`
2. Strukturę wyników: TL;DR (3-5 kierunków) → wyniki per pytanie (z siłą dowodów) → otwarte pytania
3. Zakaz oceny dopasowania do systemu — to osobny krok po researchu

Lokalizacja: prompt w `documents/<rola>/research_prompt_<temat>.md`, wyniki w `research_results_<temat>.md`.

### Plany i analizy — zawsze do pliku

Plany, analizy i propozycje zmian zapisuj do pliku .md (lub .xlsx gdy workflow tego wymaga),
nie wklejaj inline w czacie. Plik przetrwa sesję, inline zniknie przy kompresji kontekstu.

**Przestrzeń robocza człowieka:** `documents/human/<typ>/`
- Plany (implementacyjne, refaktory) → `plans/`
- Raporty, analizy, audyty → `reports/`
- Eksporty danych (backlog, suggestions przez render.py) → automatycznie do odpowiedniego podkatalogu

**Dokumentacja trwała:** Pozostaje w `documents/<rola>/` (research results, ADR w documents/architecture/)
**Pliki robocze agenta:** `tmp/` — tylko dla scratch, debug, tymczasowe (nie dla człowieka)

Pokaż użytkownikowi ścieżkę do pliku.

### Wytyczna użytkownika = sugestia od razu

Gdy użytkownik podaje wytyczną zmieniającą zachowanie agenta (regułę domenową,
konwencję, heurystykę) — zapisz ją od razu jako sugestię przez `agent_bus_cli.py suggest`.
Nie czekaj na koniec sesji. Sugestia przetrwa sesję; pamięć czatu nie.

### Git — commity przez narzędzie

Wszystkie commity wykonuj przez `tools/git_commit.py` — nie przez bezpośrednie `git commit`.
Do usuwania i przenoszenia plików używaj `rm`/`mv` (OS), a nie `git rm`/`git mv` — `--all` w git_commit.py staguje wszystko łącznie z usunięciami:

```
python tools/git_commit.py --message "feat: opis"             # samo commit
python tools/git_commit.py --message "feat: opis" --all       # git add -A + commit
python tools/git_commit.py --message "feat: opis" --all --push  # add + commit + push
python tools/git_commit.py --push-only                        # tylko push
```

### Inbox — odczyt bez auto-realizacji

Inbox czytasz na starcie sesji wyłącznie informacyjnie. Nie podejmujesz działań na podstawie
wiadomości z inbox bez jawnej komendy od użytkownika. Po przeczytaniu czekasz na instrukcję.

Uzasadnienie: wiadomości kumulują się między sesjami, część jest historyczna lub zdezaktualizowana.
Autonomiczna realizacja prowadzi do zbędnej pracy lub błędów.

### Backlog — aktualizuj statusy

Przed rozpoczęciem zadania z backlogu:
```
python tools/agent_bus_cli.py backlog-update --id <id> --status in_progress
```

Po zakończeniu:
```
python tools/agent_bus_cli.py backlog-update --id <id> --status done
```

Odkładając zadanie na później (bez anulowania):
```
python tools/agent_bus_cli.py backlog-update --id <id> --status deferred
```

Inne role widzą `in_progress` i nie duplikują pracy.

**Odczyt backlogu:** `render.py backlog` bez `--status` zwraca domyślnie tylko `planned`.
Żeby zobaczyć wszystkie statusy: `--status all` lub `agent_bus_cli.py backlog` (bez filtru).

### Logowanie i refleksja

**Na koniec każdego etapu workflow:**
```
python tools/agent_bus_cli.py log --role <rola> --content-file tmp/log_etap.md
```

**Na koniec każdego workflow / sesji:**
```
python tools/agent_bus_cli.py log --role <rola> --content-file tmp/log_sesji.md
```

Każda obserwacja = osobny wpis. Wiele obserwacji naraz — plik z blokami:
```
python tools/agent_bus_cli.py suggest-bulk --from <rola> --bulk-file tmp/refleksje.md
```

Format `tmp/refleksje.md`:
```
type: rule
title: Krótki tytuł (jedna linia)
Treść obserwacji...

---

type: discovery
title: Inny tytuł
Treść...
```

Typy: `rule` (zasada do wdrożenia), `tool` (propozycja narzędzia), `discovery` (odkrycie techniczne), `observation` (spostrzeżenie procesowe).
Jedna obserwacja — można użyć `suggest --from <rola> --type <type> --title "..." --content-file tmp/s.md`.

### Komunikacja agent-agent

Odpowiedź proporcjonalna do zadania:
- Krótki task → kilka zdań
- Złożona analiza → wyniki do pliku (`solutions/` lub `tmp/`), wiadomość ze wskazaniem lokalizacji

Nie wysyłaj pełnego raportu analitycznego jako odpowiedzi na prostą wiadomość — marnuje context window obu stron.

### Narzędzia wspólne

Dostępne dla wszystkich ról:

```
python tools/conversation_search.py --query "fraza" [--limit N] [--db PATH]
  → data.count, data[].{session_id, speaker, date, char_count, snippet}
  Szukaj po słowie kluczowym w historii rozmów.

python tools/conversation_search.py --list [--limit N]
  → data[].{session_id, date, message_count, total_chars}
  Lista sesji z liczbą wiadomości i znaków.

python tools/conversation_search.py --session <SESSION_ID>
  → data.{message_count, total_chars, messages[].{speaker, content, date}}
  Pełna rozmowa danej sesji.
```

Używaj gdy potrzebujesz kontekstu z poprzednich sesji.

### Styl komunikacji

- Bez emoji (dozwolone: ✓, ✗)
- Konkretna komunikacja — pokazuj trade-offy, nie zgaduj
- Brak pewności → pytaj, nie zakładaj
- Kończ każdą wiadomość linią: `Kontekst: ~XX%` (szacowane zużycie okna kontekstowego)
