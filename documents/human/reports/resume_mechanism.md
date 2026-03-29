# Resume — jak agent wraca do życia

## Trzy operacje na agencie

| Operacja   | Kiedy                   | Co się dzieje                                    | Tożsamość          |
| ---------- | ----------------------- | ------------------------------------------------ | ------------------ |
| **spawn**  | Nowe zadanie            | Nowy terminal, nowa sesja, czysty start          | Nowy session_id    |
| **poke**   | Agent stoi (idle, `>`)  | Tekst wstrzyknięty do terminala, agent się budzi | Ten sam session_id |
| **resume** | Agent umarł / zamknięty | Wznowienie conversation Claude Code              | Ten sam session_id |

## Kiedy potrzebny resume (a nie poke/spawn)

```
Agent żyje, stoi przy `>`?
  └─ TAK → poke (sendText)
  └─ NIE → Terminal istnieje ale Claude Code zamknięty?
              └─ TAK → resume (sendText "/resume" do terminala)
              └─ NIE → Terminal nie istnieje?
                          └─ resume (nowy terminal + "claude --resume")
                          └─ LUB spawn (nowa sesja, stary kontekst gubiony)
```

## Jak działa resume — krok po kroku

### Dziś (zepsute)

```
1. Agent developer pracował w sesji session_id=abc123, claude_uuid=XYZ
2. Sesja się kończy (crash, zamknięcie, timeout)
3. live_agents: session_id=abc123, status=stopped, claude_uuid=XYZ

4. Ktoś robi /resume (lub Dispatcher chce wznowić)
5. Claude Code wznawia conversation → ten sam claude_uuid=XYZ
6. CLAUDE.md wymusza session_init
7. session_init → generuje NOWY session_id=def456
8. live_agents: abc123 (stopped, zombie), def456 (active, brak połączenia z historią)

Problem: agent stracił tożsamość. Dwie sesje w DB. Inbox/handoffy na abc123 nie trafiają do def456.
```

### Po fix (proponowane)

```
1. Agent developer pracował w sesji session_id=abc123, claude_uuid=XYZ
2. Sesja się kończy
3. live_agents: session_id=abc123, status=stopped, claude_uuid=XYZ

4. Ktoś robi /resume
5. Claude Code wznawia conversation → ten sam claude_uuid=XYZ
6. on_session_start → pisze XYZ do tmp/pending_claude_uuid.txt
7. CLAUDE.md wymusza session_init
8. session_init czyta pending_claude_uuid.txt → XYZ
9. session_init: SELECT FROM live_agents WHERE claude_uuid = 'XYZ'
10. ZNALEZIONO abc123 → RESUME MODE:
    - Reuse session_id=abc123 (nie generuje nowego)
    - UPDATE status='active', last_activity=now
    - Załaduj świeży inbox/backlog
11. live_agents: abc123 (active, ten sam session_id, ta sama tożsamość)

Agent zachował tożsamość. Zero zombie. Inbox trafia poprawnie.
```

## Co daje resume detection

| Aspekt | Bez resume detection | Z resume detection |
|---|---|---|
| session_id | Nowy za każdym razem | Zachowany |
| Inbox/handoffy | Gubione (adresowane do starego ID) | Ciągłość |
| live_agents | Zombie sesje | Czysta tabela |
| Dashboard | Podwójne wpisy | Jeden wpis per agent |
| Kontekst agenta | Claude Code zachowuje | Claude Code zachowuje |

## Zmiana w kodzie

Jedno miejsce: `session_init.py`. Logika:

```python
claude_uuid = read_pending_file()

existing = db.query("SELECT session_id, role FROM live_agents WHERE claude_uuid = ?", claude_uuid)

if existing:
    # RESUME: reuse
    session_id = existing.session_id
    db.update("SET status='active' WHERE session_id = ?", session_id)
    log("session resumed")
else:
    # NEW: generate
    session_id = generate_new()
    db.insert(session_id, role, claude_uuid)
    log("session started")

# W obu: załaduj inbox, backlog, logi (mogły przyjść nowe wiadomości)
context = load_context(role)
```

## Ograniczenia

- **pending_claude_uuid.txt jest shared file** — ale okno wyścigu jest minimalne (on_session_start → session_init to ta sama sesja, sekundy)
- **Resume działa tylko dla sesji z claude_uuid w DB** — stare sesje (przed fix) nie mają UUID
- **Extension `resumeAgent`** — jeszcze nie istnieje. Dziś resume = ręczny `/resume` w terminalu
