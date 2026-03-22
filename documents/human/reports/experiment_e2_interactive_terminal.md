# Eksperyment E2: Terminal interaktywny z wstrzykniętym taskiem

Data: 2026-03-22
Eksperymentator: Developer
Backlog: #114 — Plan eksperymentów: Runner wieloagentowy

---

## Cel

Sprawdzić czy można uruchomić normalną sesję Claude Code z wstrzykniętym taskiem, która:
1. Jest interaktywna (można pisać w terminalu)
2. Ma wstrzyknięty task przez --append-system-prompt
3. Działa autonomicznie (nie czeka na human bez powodu)
4. Obsługuje --continue / --resume

---

## Problem obecny

`mrowisko_runner.py` używa:
```
--output-format stream-json
```

To zabija interaktywność — sesja jest jednokierunkowa (proces → stdout), brak możliwości dołączenia human.

---

## Hipoteza

Usunięcie `--output-format stream-json` z komendy da normalną sesję interaktywną, która:
- Wykonuje task autonomicznie (bo ma --append-system-prompt z instrukcją)
- Pozwala human wpisać wiadomość w terminalu (interaktywność)
- Może być wznowiona przez --continue

---

## Test 1: Komenda minimalna (bez stream-json)

**Komenda:**
```bash
claude -p "developer" --append-system-prompt "[TRYB AUTONOMICZNY] Task: Wypisz zawartość katalogu narzędziem Glob (pattern: tools/*.py). Zakończ."
```

**Pytania weryfikacyjne:**
- [ ] Czy sesja się uruchomiła?
- [ ] Czy agent wykonał task (Glob tools/*.py)?
- [ ] Czy sesja czeka na input czy się zakończyła?
- [ ] Czy można pisać w terminalu podczas działania agenta?

**Wynik:**
(do wypełnienia po eksperymencie)

---

## Test 2: Komenda z --max-turns (ograniczenie autonomii)

**Komenda:**
```bash
claude -p "developer" --append-system-prompt "[TRYB AUTONOMICZNY] Task: Wypisz zawartość katalogu narzędziem Glob (pattern: tools/*.py). Zakończ." --max-turns 3
```

**Pytania weryfikacyjne:**
- [ ] Czy agent zatrzymał się po 3 turach?
- [ ] Czy sesja zakończyła się sama czy czeka na input?

**Wynik:**
(do wypełnienia po eksperymencie)

---

## Test 3: Wznowienie sesji (--continue)

**Przebieg:**
1. Uruchomić Test 1 lub Test 2
2. Zanotować session_id
3. Uruchomić: `claude --continue <session_id>`

**Pytania weryfikacyjne:**
- [ ] Czy --continue wznawia sesję?
- [ ] Czy agent pamięta kontekst (poprzednie komendy)?
- [ ] Czy można kontynuować interaktywnie?

**Wynik:**
(do wypełnienia po eksperymentu)

---

## Test 4: Komenda z pełnym promptem autonomicznym (jak w runner)

**Przygotowanie:**
- Skopiować treść `tools/prompts/runner_autonomous.md`
- Podstawić zmienne: {role} → developer, {sender} → human, {instance_id} → test, {content} → "Wypisz zawartość katalogu narzędziem Glob (pattern: tools/*.py). Zakończ."

**Komenda:**
(wygenerowana po przygotowaniu)

**Pytania weryfikacyjne:**
- [ ] Czy agent uruchomił session_init?
- [ ] Czy wykonał task bez czekania na potwierdzenie?
- [ ] Czy zakończył sesję sam?

**Wynik:**
(do wypełnienia po eksperymencie)

---

## Wnioski (do wypełnienia)

### Czy eksperyment udany?
- [ ] Tak — znaleziono working command line
- [ ] Częściowo — sesja działa, ale są problemy
- [ ] Nie — nie działa zgodnie z założeniami

### Working command line (jeśli znaleziono):
```
(komenda)
```

### Problemy / blokery:
(lista problemów)

### Następne kroki:
(co dalej)

---

## Trade-offs: stream-json vs interaktywny terminal

| Aspekt | stream-json | terminal interaktywny |
|--------|-------------|----------------------|
| Interaktywność (human może dołączyć) | ✗ | ✓ |
| Programmatic parsing (JSON events) | ✓ | ✗ |
| Rendering output w runnerze | Wymaga parsera | Terminal robi to sam |
| Współdzielony terminal (tmux, screen) | ✗ | ✓ |
| Agent Teams integration | ? | ? |

