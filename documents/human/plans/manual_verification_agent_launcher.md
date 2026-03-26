# Manual verification: Agent Launcher spawn

*Data: 2026-03-26*
*Wykonawca: Dawid*
*Źródło: experiments_agent_launcher_results.md*

---

## Przygotowanie

Otwórz terminal w VS Code (ten gdzie normalnie pracujesz z Claude Code).

---

## Test 1: Spawn z --append-system-prompt

**Komenda:**
```
claude --append-system-prompt "Rola: developer. Task: sprawdz backlog Dev"
```

**Sprawdź:**
- [ ] Sesja interaktywna (możesz pisać po starcie)
- [ ] Status line widoczna
- [ ] `/help` działa
- [ ] Agent widzi wstrzyknięty kontekst (powinien zachować się jak developer)
- [ ] CLAUDE.md załadowany (agent pyta o rolę lub od razu uruchamia session_init)

Zamknij: `/exit`

---

## Test 2: Spawn z pełnym zestawem flag

**Komenda:**
```
claude --append-system-prompt "Rola: developer. Task: sprawdz backlog Dev" --session-id "test-manual-001" --name "Agent: developer"
```

**Sprawdź:**
- [ ] Sesja interaktywna
- [ ] Nazwa "Agent: developer" widoczna gdzieś (terminal title, /resume picker)
- [ ] `/resume` pokazuje sesję z nazwą "Agent: developer"

Zamknij: `/exit`

---

## Test 3: Resume w innym terminalu

**Krok 1:** Otwórz nowy terminal (drugi, obok).

**Krok 2:**
```
claude --resume "Agent: developer"
```

**Sprawdź:**
- [ ] Sesja wznowiona z pełnym kontekstem (widać poprzednią rozmowę)
- [ ] Interaktywna (możesz pisać dalej)

Zamknij: `/exit`

---

## Test 4: Permission mode

**Komenda:**
```
claude --append-system-prompt "Rola: developer" --permission-mode acceptEdits
```

**Sprawdź:**
- [ ] Agent auto-akceptuje edycje plików (nie pyta)
- [ ] Agent nadal pyta o komendy Bash (to oczekiwane zachowanie)

Zamknij: `/exit`

---

## Po testach

Zapisz wyniki (✓/✗ przy każdym checkboxie) i daj mi znać. Na tej podstawie zamykam fazę eksperymentalną i przechodzę do TECHSTACK + ARCHITECTURE.
