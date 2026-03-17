# Research results — Runner Faza 1b (instance routing)

Data: 2026-03-17

## 1. SQLite atomic claim przy WAL mode

Odpowiedź:

**Czy dwa równoległe procesy mogą oba zapisać `claimed_by` dla tego samego wiersza?**

Dla wzorca:

```sql
UPDATE messages
SET status = 'claimed', claimed_by = ?
WHERE id = ? AND status = 'unread';
```

— **nie**, o ile warunek claimu (`status = 'unread'`) jest w **tym samym `UPDATE`** i każda instancja ma własne połączenie do DB. W SQLite zapis jest atomowy na poziomie statement/transaction, a w WAL nadal obowiązuje zasada **„tylko jeden writer naraz”**. WAL zwiększa współbieżność **reader + writer**, ale **nie** pozwala na dwóch jednoczesnych writerów do tego samego DB. [S1][S2][S3]

Praktycznie oznacza to:
- runner A wykona `UPDATE` i zmieni `status` na `claimed`,
- runner B może poczekać na lock albo dostać `SQLITE_BUSY`,
- gdy runner B dojdzie do wykonania `UPDATE`, warunek `status = 'unread'` będzie już fałszywy, więc `rowcount == 0`.

To jest poprawny wzorzec **atomic claim**. Ryzyko race condition wraca dopiero wtedy, gdy logika jest rozbita na osobny `SELECT` i późniejszy `UPDATE` bez warunku broniącego w `UPDATE`. [S1][S3]

**Czy potrzebujemy `BEGIN IMMEDIATE` albo `BEGIN EXCLUSIVE`?**

Dla pojedynczego claimu realizowanego jednym `UPDATE` — **nie jest to wymagane**. `BEGIN IMMEDIATE` służy do wcześniejszej rezerwacji write transaction; może być przydatne, jeśli claim ma być częścią większego, wielostatementowego read-modify-write, ale dla jednego `UPDATE ... WHERE status='unread'` nie daje niezbędnej gwarancji ponad to, co już zapewnia sam statement. W WAL `EXCLUSIVE` i `IMMEDIATE` są równoważne dla writer locków, więc `BEGIN EXCLUSIVE` nie wnosi tu dodatkowej wartości. [S4]

**Czy `check_same_thread=False` wystarcza przy wielu procesach?**

To ustawienie dotyczy **wątków**, nie procesów. Przy wielu procesach każdy proces i tak powinien mieć **własne połączenie**. `check_same_thread=False` tylko wyłącza ochronę Pythona przed użyciem tego samego connection w innym wątku; dokumentacja wprost zaznacza, że przy współdzieleniu connection między wątkami operacje zapisu trzeba serializować po stronie aplikacji. [S5][S6]

Dodatkowa uwaga: 2026-03-13 SQLite opublikował fix rzadkiego błędu WAL („WAL-reset bug”), naprawionego w 3.51.3 oraz backportach 3.44.6 i 3.50.7. To **nie podważa** wzorca `UPDATE ... WHERE status='unread'` jako atomic claim, ale jeśli runner ma działać produkcyjnie na WAL, warto sprawdzić runtime SQLite i unikać podatnych buildów. [S2]

Rekomendacja dla implementacji:

1. Zostaw claim jako **jeden statement** `UPDATE ... WHERE id=? AND status='unread'`.
2. **Nie** rób osobnego `SELECT` bez warunku ochronnego w `UPDATE`.
3. Nie używaj `BEGIN IMMEDIATE` dla samego claimu; rozważ je tylko wtedy, gdy claim będzie częścią większej sekwencji kilku zapisów, które muszą być w jednej transakcji.
4. Każdy runner-process powinien mieć **własne połączenie** SQLite.
5. Dla odporności operacyjnej ustaw `timeout=` albo `PRAGMA busy_timeout`, żeby sporadyczny lock nie kończył się od razu błędem. [S7][S8]
6. Dodatkowo sprawdź lokalną wersję SQLite; przy WAL warto celować w build z fixem 3.51.3+/3.50.7+/3.44.6+.

---

## 2. Claude Code CLI — weryfikacja flag

Odpowiedź:

**`--permission-mode acceptEdits`**

Ta flaga **istnieje**. Dostępne tryby permission mode to:
- `default`
- `acceptEdits`
- `plan`
- `dontAsk`
- `bypassPermissions` [S9][S10]

Ważny detal: `acceptEdits` **nie oznacza pełnego non-interactive auto-approve**. Dokumentacja mówi, że w tym trybie Claude **auto-akceptuje edycje plików, ale nadal pyta o komendy/shell commands**. To ma duże znaczenie dla runnera uruchamianego przez subprocess, bo jeśli agent będzie chciał użyć `Bash`, samo `--permission-mode acceptEdits` może nie wystarczyć do w pełni bezobsługowego przebiegu. [S11][S12]

**`--tools "Read,Grep,Glob,Bash"`**

Ta flaga **istnieje** i dokumentacja opisuje ją jako ograniczenie, które **restricts which built-in tools Claude can use**. Format pokazany w oficjalnych przykładach CLI to **jeden string z nazwami rozdzielonymi przecinkami**, np. `"Bash,Edit,Read"`. [S9]

Czy to jest pełny **capability boundary**? **Częściowo.** Ogranicza zestaw narzędzi dostępnych Claude, ale dokumentacja bezpieczeństwa rozróżnia:
- **permissions** — kontrolują, z jakich narzędzi Claude może korzystać,
- **sandboxing** — robi OS-level enforcement dla `Bash` i jego child processes. [S13][S14]

Wniosek: `--tools` jest **allowlistą narzędzi**, ale nie zastępuje sandboxa ani reguł permission. Jeśli zostawiasz `Bash`, to rzeczywista granica bezpieczeństwa zależy jeszcze od permission rules i sandboxa. [S13][S14]

**Dokładny format z przecinkiem i spacjami?**

Dokumentacja CLI pokazuje format **bez spacji**: `"Bash,Edit,Read"`. Nie znalazłem jednoznacznej informacji, czy parser toleruje spacje po przecinku w CLI. **Nie znaleziono — wymaga testu lokalnego.** [S9]

**`--max-budget-usd`**

Ta flaga **istnieje** i jest opisana jako **print mode only**: maksymalny limit kosztu API, po którego przekroczeniu proces się zatrzymuje. To nie jest tylko wewnętrzny mechanizm — to oficjalna flaga CLI. [S9][S15]

**`--include-partial-messages`**

Ta flaga **istnieje**. Jest **opcjonalna**, ale dokumentacja mówi, że **wymaga** `--print` oraz `--output-format=stream-json`. Innymi słowy:
- przy `stream-json` możesz jej użyć, jeśli chcesz partial streaming events,
- nie jest wymagana do samego `stream-json`,
- jest wymagana tylko wtedy, gdy chcesz **partial messages** w output. [S16]

Rekomendacja dla implementacji:

1. Jeśli runner ma działać całkiem bezobsługowo, **nie zakładaj**, że `--permission-mode acceptEdits` wystarczy przy włączonym `Bash`.
2. Dla przewidywalności używaj dokładnie formatu z docs: `--tools "Read,Grep,Glob,Bash"` (bez spacji).
3. Traktuj `--tools` jako allowlistę narzędzi, ale dla realnej izolacji używaj też **permissions + sandbox**.
4. `--max-budget-usd` możesz włączyć — to oficjalna flaga.
5. `--include-partial-messages` dodawaj tylko wtedy, gdy parser faktycznie potrzebuje partial events; inaczej nie jest konieczne.
6. Jeśli runner ma tylko czytać kod i odpowiadać tekstem, rozważ **usunąć `Bash`** z `--tools`; to znacząco zmniejsza powierzchnię nieprzewidywalności.

---

## 3. Heartbeat w Pythonie — threading przy subprocess

Odpowiedź:

**`threading.Timer` czy `threading.Thread` + `Event.wait(10)`?**

Lepszym wyborem jest **dedykowany `threading.Thread` z pętlą i `stop_event.wait(10)`**. `threading.Timer` jest w docs opisany jako obiekt do uruchomienia **jednej akcji po upływie czasu**; da się go rekursywnie odpalać, ale do periodycznego heartbeat to gorszy pattern: generuje kolejne obiekty/threads i trudniej go pewnie zatrzymać. `Event` jest natomiast wprost przeznaczony do prostej komunikacji między wątkami i ma wygodne `wait(timeout)`. [S17][S18]

**Czy można współdzielić jedno SQLite connection między heartbeat thread a main thread przy `check_same_thread=False`?**

Formalnie: **można**, ale dokumentacja Python `sqlite3` mówi, że przy `check_same_thread=False` dostęp z wielu wątków jest dozwolony, jednak operacje zapisu mogą wymagać serializacji po stronie użytkownika, żeby uniknąć problemów. [S5]

W praktyce dla runnera bezpieczniej jest zrobić:
- **osobne connection w głównym wątku**,
- **osobne connection w heartbeat thread**.

To upraszcza model, zmniejsza ryzyko blokowania przez współdzielony cursor/transaction state i lepiej pasuje do zasady „connection per thread / per process”, którą opisuje Python i SQLite. [S5][S6]

**Czy jest prostszy pattern, np. `concurrent.futures`?**

Dla jednego powtarzalnego heartbeat podczas `proc.wait(timeout=600)` — **nie widzę prostszego patternu niż jeden daemon thread + `Event`**. `concurrent.futures` wnosi tu raczej dodatkową warstwę abstrakcji, a nie realne uproszczenie. `subprocess.wait()` może spokojnie blokować główny wątek, a heartbeat może działać obok w osobnym lekkim threadzie. [S17][S18]

Rekomendacja dla implementacji:

1. Uruchom heartbeat w osobnym `threading.Thread(daemon=True)`.
2. W środku użyj pętli:

```python
while not stop_event.wait(10):
    update_heartbeat()
```

3. Zrób **osobne SQLite connection na heartbeat thread**.
4. Ustaw `timeout=` / `busy_timeout` na obu connection, żeby chwilowy writer lock nie zabijał heartbeat. [S7][S8]
5. Po zakończeniu subprocess ustaw `stop_event.set()` i `join()` thread z krótkim timeoutem.

---

## 4. Cleanup przy nagłym zamknięciu terminala

Odpowiedź:

**Czy `signal.signal(signal.SIGTERM, handler)` + `atexit.register()` pokrywa zamknięcie terminala na Windows?**

**Nie w pełni.** `atexit` działa przy **normalnym** zakończeniu interpretera, ale dokumentacja mówi wprost, że nie uruchamia się, gdy proces zostaje zabity sygnałem nieobsłużonym przez Pythona, przy błędzie fatalnym ani przy `os._exit()`. [S19]

Na Windows `signal.signal()` obsługuje tylko wybrane sygnały (`SIGABRT`, `SIGFPE`, `SIGILL`, `SIGINT`, `SIGSEGV`, `SIGTERM`, `SIGBREAK`). [S20]

Problem polega na tym, że **zamknięcie okna konsoli** w Windows nie jest opisane przez Python `signal` jako `SIGTERM`. W dokumentacji Windows konsola przy zamknięciu wysyła **`CTRL_CLOSE_EVENT`** do procesów przyłączonych do konsoli. To jest osobny mechanizm WinAPI (`SetConsoleCtrlHandler`), nie zwykły `SIGTERM` z modułu `signal`. [S21][S22]

**Czy na Windows `SIGTERM` jest wysyłany przy zamknięciu okna CMD/PowerShell?**

Z dokumentacji, którą znalazłem, wynika że **nie należy na to liczyć**. Oficjalny mechanizm konsolowy dla zamknięcia okna to `CTRL_CLOSE_EVENT`, a nie `SIGTERM`. Pythonowy `signal` potrafi rejestrować handler dla `SIGTERM`, ale to nie oznacza, że zamknięcie konsoli mapuje się na ten sygnał. To jest **wniosek z dokumentacji**, nie znalazłem jednego zdania w docs Pythona mówiącego literalnie „console close != SIGTERM”. [S20][S21][S22]

**Jaki jest rekomendowany pattern cleanup dla długiego skryptu Python na Windows?**

Najbezpieczniejszy pattern to warstwa wielopoziomowa:

1. `atexit.register(...)` — na normalny exit,
2. `signal.signal(SIGINT/SIGBREAK/SIGTERM, ...)` — na Ctrl+C / Ctrl+Break / termination,
3. **Windows-specific console handler** przez `SetConsoleCtrlHandler` (np. przez `ctypes`) — na `CTRL_CLOSE_EVENT`, `CTRL_LOGOFF_EVENT`, `CTRL_SHUTDOWN_EVENT`,
4. i tak traktować cleanup jako **best effort**, bo twarde ubicia procesu (np. brutalny kill / crash) nie da się w 100% obsłużyć.

Dlatego w modelu DB runner powinien istnieć jeszcze mechanizm **stale instance detection** po heartbeat (`last_seen_at` + TTL), żeby osierocone instancje same wygasały nawet bez czystego `status='terminated'`. [S19][S21][S22]

Rekomendacja dla implementacji:

1. Zostaw `atexit.register()` jako warstwę „normal exit”.
2. Dodaj `signal.signal()` dla `SIGINT`, `SIGBREAK`, `SIGTERM`.
3. Na Windows dodaj `SetConsoleCtrlHandler` przez `ctypes` i w handlerze ustaw flagę shutdown + spróbuj wykonać szybki cleanup.
4. Nie polegaj wyłącznie na cleanupie „on exit”; dodaj logikę wygaszania po heartbeat TTL, np. `last_seen_at < now() - 30s => instance stale`.
5. Traktuj `status='terminated'` jako optymalizację, a **heartbeat TTL jako źródło prawdy** przy recovery.

---

## Krótki werdykt implementacyjny

- **Atomic claim przez pojedynczy `UPDATE ... WHERE status='unread'` jest poprawny** w SQLite + WAL.
- **`BEGIN IMMEDIATE` nie jest potrzebny** dla samego claimu.
- **`check_same_thread=False` nie rozwiązuje nic dla multi-process**; to flaga wątkowa.
- Dla heartbeat użyj **osobnego thread + `Event.wait(10)` + osobnego SQLite connection**.
- Na Windows **`SIGTERM + atexit` nie pokrywa zamknięcia konsoli**; potrzebny jest **`SetConsoleCtrlHandler`** albo równoważny wrapper.
- W runnerze z `claude -p` uważaj na **`acceptEdits`**: ten mode nadal pyta o komendy, więc przy włączonym `Bash` nie daje automatycznie w pełni bezobsługowego przebiegu.

---

## Źródła

[S1]: SQLite FAQ — concurrency and locking: https://sqlite.org/faq.html

[S2]: SQLite WAL docs — concurrency and 2026 WAL-reset bug note: https://sqlite.org/wal.html

[S3]: SQLite isolation docs: https://sqlite.org/isolation.html

[S4]: SQLite transaction docs (`BEGIN IMMEDIATE` / `EXCLUSIVE`): https://sqlite.org/lang_transaction.html

[S5]: Python `sqlite3` docs — `check_same_thread`: https://docs.python.org/3/library/sqlite3.html

[S6]: Python `sqlite3` docs — `threadsafety`: https://docs.python.org/3/library/sqlite3.html

[S7]: Python `sqlite3.connect(..., timeout=...)`: https://docs.python.org/3/library/sqlite3.html

[S8]: SQLite `busy_timeout`: https://sqlite.org/c3ref/busy_timeout.html

[S9]: Claude Code CLI reference: https://code.claude.com/docs/en/cli-reference

[S10]: Claude Code permissions docs — permission modes: https://code.claude.com/docs/en/permissions

[S11]: Claude Code “How Claude Code works” — acceptEdits still asks for commands: https://code.claude.com/docs/en/how-claude-code-works

[S12]: Claude Code Desktop docs — `dontAsk` only in CLI / permission mode behavior: https://code.claude.com/docs/en/desktop

[S13]: Claude Code permissions docs — permissions vs sandboxing: https://code.claude.com/docs/en/permissions

[S14]: Claude Code sandboxing docs — OS-level enforcement for Bash: https://code.claude.com/docs/en/sandboxing

[S15]: Claude Code costs docs (budget/cost control context): https://code.claude.com/docs/en/costs

[S16]: Claude Code CLI reference — `--include-partial-messages`: https://code.claude.com/docs/en/cli-reference

[S17]: Python `threading` docs — `Timer`: https://docs.python.org/3/library/threading.html

[S18]: Python `threading` docs — `Event`: https://docs.python.org/3/library/threading.html

[S19]: Python `atexit` docs: https://docs.python.org/3/library/atexit.html

[S20]: Python `signal` docs on Windows: https://docs.python.org/3/library/signal.html

[S21]: Microsoft Learn — `SetConsoleCtrlHandler`: https://learn.microsoft.com/en-us/windows/console/setconsolectrlhandler

[S22]: Microsoft Learn — `CTRL_CLOSE_EVENT` / close console semantics: https://learn.microsoft.com/en-us/windows/console/ctrl-close-signal
