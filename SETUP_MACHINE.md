# Setup nowej maszyny

Po sklonowaniu repo na nową maszynę — użyj automatycznego narzędzia albo wykonaj setup ręcznie.

---

## Szybki start — pełna procedura

```bash
# 1. Sklonuj repo
git clone <url-do-repo> ~/OneDrive/Pulpit/Mrowisko
cd ~/OneDrive/Pulpit/Mrowisko

# 2. Instaluj dependencies
py -m pip install -r requirements.txt

# 3. (Opcjonalnie) Skopiuj bazę danych jeśli migrujesz z innej maszyny
# Wklej plik mrowisko.db do katalogu głównego projektu

# 4. Konfiguracja Claude Code (automatyczna)
py tools/setup_machine.py

# 5. (Opcjonalnie) Git config jeśli będziesz tworzyć commity
git config user.name "Twoje Imię"
git config user.email "twoj@email.com"

# 6. Weryfikacja
py tools/agent_bus_cli.py backlog --area Dev --status planned
```

Szczegóły każdego kroku poniżej.

---

## Metoda 1: Automatyczna (REKOMENDOWANE)

Narzędzie `tools/setup_machine.py` automatycznie wykrywa ścieżki i interpreter Python:

```bash
# Przejdź do katalogu projektu
cd <ścieżka-do-Mrowisko>

# Uruchom narzędzie
py tools/setup_machine.py

# Lub z custom parametrami:
py tools/setup_machine.py --project-path /path/to/project --python-cmd python3

# Opcjonalnie: podgląd bez zapisywania plików
py tools/setup_machine.py --dry-run
```

**Co robi:**
- Wykrywa interpreter Python (`py`, `python3`, `python`)
- Generuje ścieżki dla Windows i Unix
- Tworzy pliki `.claude/settings*.json` i `bot/.claude/settings.local.json` z templates
- Podstawia właściwe wartości placeholderów

Po uruchomieniu możesz od razu zacząć pracę w Claude Code.

**Co zostaje skonfigurowane:**
- Ścieżki projektu i interpreter Python
- Permissions dla narzędzi (Read, Write, Edit, Grep, Glob)
- **Hooki bezpieczeństwa** (automatyczna walidacja komend Bash)
- Dozwolone komendy CLI (agent_bus, git_commit, session_init, render)

Skrypty hooków (`tools/hooks/*.py`) są w repo — działają automatycznie po setup.

---

## Metoda 2: Ręczna

Jeśli wolisz manual setup:

### 1. Instalacja dependencies

```bash
py -m pip install -r requirements.txt
```

### 2. Konfiguracja Claude Code

Skopiuj templates i zaktualizuj ścieżki:

```bash
# Root projekt
cp .claude/settings.template.json .claude/settings.json
cp .claude/settings.local.template.json .claude/settings.local.json

# Bot subdirectory
cp bot/.claude/settings.local.template.json bot/.claude/settings.local.json
```

Edytuj pliki i zamień placeholdery:
- `{{PROJECT_PATH}}` → ścieżka do projektu w formacie Unix (np. `~/OneDrive/Pulpit/Mrowisko` lub `~/Desktop/Mrowisko`)
- `{{PYTHON_CMD}}` → komenda Python na Twojej maszynie (`python`, `python3`, lub `py`)
- `{{PROJECT_PATH_WINDOWS}}` → ścieżka Windows bez `C:\` (np. `Users/cypro/OneDrive/Pulpit/Mrowisko`)
- `{{PROJECT_PATH_WINDOWS_ESCAPED}}` → jak wyżej ale z `\\` zamiast `\` (np. `C:\\\\Users\\\\cypro\\\\OneDrive\\\\Pulpit\\\\Mrowisko`)

**Przykład dla Windows + py launcher:**
```
{{PROJECT_PATH}} → ~/OneDrive/Pulpit/Mrowisko
{{PYTHON_CMD}} → py
{{PROJECT_PATH_WINDOWS}} → Users/cypro/OneDrive/Pulpit/Mrowisko
{{PROJECT_PATH_WINDOWS_ESCAPED}} → C:\\\\Users\\\\cypro\\\\OneDrive\\\\Pulpit\\\\Mrowisko
```

### 3. Baza danych

`mrowisko.db` jest lokalna dla każdej maszyny (nie synchronizowana przez git).

Po sklonowaniu repo:
- Jeśli pracujesz na nowej maszynie — baza zostanie utworzona automatycznie przy pierwszym użyciu `agent_bus_cli.py`
- Jeśli migrujesz z innej maszyny — skopiuj plik `mrowisko.db` ręcznie

**Uwaga:** Synchronizacja bazy między maszynami będzie wdrożona w przyszłości (backlog #90).

---

## Weryfikacja setupu (dla obu metod)

### 1. Test dependencies

```bash
py -c "import anthropic, openpyxl, sqlite3; print('Dependencies OK')"
```

### 2. Test konfiguracji i hooków

```bash
py tools/agent_bus_cli.py backlog --area Dev --status planned
```

**Oczekiwany wynik:**
- Polecenie działa bez pytania o zatwierdzenie → permissions OK
- Zwraca listę zadań lub pustą listę → baza danych działa
- Brak błędów hooków → hooki skonfigurowane poprawnie

### 3. Test hooków bezpieczeństwa

Uruchom Claude Code i spróbuj wykonać zablokowaną komendę:

```bash
# W sesji Claude Code napisz: "wykonaj ls -la przez Bash"
# Hook powinien zwrócić błąd: "Użyj narzędzia Glob zamiast ls."
```

Jeśli hook blokuje komendę — setup bezpieczeństwa działa.

---

## Uwagi

### Git config

Jeśli planujesz tworzyć commity, skonfiguruj użytkownika Git:

```bash
git config user.name "Twoje Imię"
git config user.email "twoj@email.com"
```

Bez tego `git_commit.py` zwróci błąd przy próbie commitu.

### Baza danych
`mrowisko.db` jest lokalna dla każdej maszyny (nie synchronizowana przez git).
- Nowa maszyna: baza utworzona automatycznie przy pierwszym użyciu `agent_bus_cli.py`
- Migracja z innej maszyny: skopiuj plik `mrowisko.db` ręcznie
- **Uwaga:** Synchronizacja bazy między maszynami w backlog (zadanie #90)

### Bot
Jeśli używasz bota, zaktualizuj ścieżkę w `bot/CLAUDE.md`:
- Sekcja "Uruchomienie" — zamień ścieżkę na aktualną
- Zamień interpreter Python jeśli potrzeba
