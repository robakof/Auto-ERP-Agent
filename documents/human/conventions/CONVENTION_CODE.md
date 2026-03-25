---
convention_id: code-convention
version: "1.2"
status: draft
created: 2026-03-25
updated: 2026-03-25
author: architect
owner: architect
approver: dawid
audience: [developer, architect, prompt_engineer]
scope: "Standardy kodu Python w projekcie Mrowisko"
---

# CONVENTION_CODE — Standardy kodu Python

## TL;DR

- Każde narzędzie CLI w `tools/` MUSI mieć wzorzec: `argparse → main() → JSON output → sys.exit`
- Funkcja publiczna MUSI mieć type hints dla argumentów i wartości zwracanej
- JSON output = zawsze `{"ok": bool, "data": ..., "error": ..., "meta": ...}` — bez wyjątków
- Importy: stdlib → third-party → local, tylko importy absolutne
- `print()` jest zakazany w narzędziach — używaj `print_json()` z `tools/lib/output.py`
- Nazwy plików: `snake_case`, opisowe, bez temporal suffixów (`_new`, `_v2`, `_final`)
- Exit codes: 0 (OK), 1 (runtime error), 2 (usage error) — wspólny enum
- stdout wyłącznie dla JSON, stderr dla diagnostyki — nie mieszaj kanałów
- Każde narzędzie ma minimum 4 testy kontraktowe (help, success, bad args, runtime error)

---

## Zakres

**Pokrywa:**
- Kod Python w `tools/`, `tools/lib/`, `tests/`
- Pattern CLI narzędzi (argparse, output, exit codes)
- Pattern bibliotek (`tools/lib/`)
- Type hints, docstrings, importy, error handling
- Konwencje testów

**NIE pokrywa:**
- SQL (patrz: `documents/erp_specialist/ERP_SQL_SYNTAX.md`)
- Konfiguracja infrastruktury (Docker, CI/CD)
- JavaScript / inne języki

---

## Reguły

### 01R: Wzorzec CLI narzędzi (tools/*.py)

Każdy skrypt CLI w `tools/` MUSI mieć strukturę:

```python
def main() -> None:
    parser = argparse.ArgumentParser(description="Opis narzędzia.", allow_abbrev=False)
    # argumenty...
    args = parser.parse_args()

    result = funkcja_biznesowa(args.parametr)
    print_json(result)


if __name__ == "__main__":
    main()
```

**Obowiązki:**
- `argparse` — parsowanie argumentów (nie ręczne `sys.argv`), z `allow_abbrev=False` (stabilność interfejsu)
- `main()` — jedyny punkt wejścia CLI
- `print_json(result)` — jedyny sposób zapisu do stdout
- `if __name__ == "__main__": main()` — wymagany guard

**Zakaz:** `print()`, `sys.exit()` wewnątrz logiki biznesowej — tylko w `main()` gdy niezbędne.

---

### 02R: Format JSON output

Każda funkcja zwracająca wynik do CLI MUSI używać struktury:

```python
{
    "ok": True | False,
    "data": <wynik> | None,
    "error": None | {"type": "ERROR_TYPE", "message": "opis"},
    "meta": {"duration_ms": int, "truncated": bool}
}
```

**Reguły:**
- `ok: True` — operacja zakończona sukcesem
- `ok: False` — operacja nieudana; `error` zawiera szczegóły
- `meta` — wymagane gdy narzędzie mierzy czas lub może obciąć wynik
- `error.type` — UPPER_SNAKE_CASE (np. `GIT_ERROR`, `NOT_FOUND`, `VALIDATION_ERROR`)

**Zakaz:** Własne formaty JSON, zwracanie samego stringa, zwracanie `None` do stdout.

---

### 03R: Type hints dla funkcji publicznych

Każda funkcja publiczna (bez prefiksu `_`) MUSI mieć type hints dla wszystkich argumentów i wartości zwracanej.

```python
# Dobrze
def git_commit(
    message: str = "",
    files: list[str] | None = None,
    add_all: bool = False,
) -> dict:

# Dobrze — funkcja pomocnicza (prywatna), hints opcjonalne
def _parse_status_files(status_output: str) -> list[str]:
```

**Zakaz:** Funkcja publiczna bez type hints.

---

### 04R: Docstrings dla funkcji publicznych

Każda funkcja publiczna, która nie jest oczywista z sygnatury, MUSI mieć docstring w formacie Google.

```python
def get_context(role: str, config: dict, bus: AgentBus) -> dict:
    """Zbiera kontekst sesji per konfigurację.

    Args:
        role: Nazwa roli agenta (np. "developer").
        config: Słownik konfiguracji z session_init_config.json.
        bus: Instancja AgentBus z otwartym połączeniem DB.

    Returns:
        Słownik z kluczami: inbox, backlog, logs (zależnie od config).
    """
```

**Kiedy wymagane:**
- Argumenty nie są oczywiste z nazwy
- Funkcja ma efekty uboczne (zapis do DB, zapis pliku)
- Funkcja jest punktem integracyjnym (wywoływana przez inne moduły)

**Kiedy można pominąć:**
- Funkcja prywatna (`_`) z prostą logiką
- Funkcja pomocnicza z self-dokumentującą się sygnaturą

---

### 05R: Kolejność importów

Importy w kolejności: stdlib → third-party → local. Grupy oddzielone pustą linią.

```python
# stdlib
import argparse
import json
import sys
from pathlib import Path

# third-party
import pytest

# local (absolutne)
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.lib.agent_bus import AgentBus
from tools.lib.output import print_json
```

**Zakaz:** Importy względne (`from . import`, `from .. import`) — używaj absolutnych.

**Uwaga `sys.path.insert`:** Dozwolone wyłącznie w plikach CLI (`tools/*.py`) i testach — wymagane ze względu na brak instalacji pakietu. W `tools/lib/` niedozwolone.

---

### 06R: Nazewnictwo

| Kontekst | Konwencja | Przykład |
|---|---|---|
| Funkcje, zmienne | `snake_case` | `get_context`, `session_id` |
| Klasy | `PascalCase` | `AgentBus`, `ViewConfig` |
| Stałe modułowe | `UPPER_SNAKE_CASE` | `DB_PATH`, `ALLOWED_MESSAGE_TYPES` |
| Pliki Python | `snake_case` | `agent_bus_cli.py`, `git_commit.py` |
| Pliki testów | `test_<modul>.py` | `test_git_commit.py` |

**Nazwy opisowe — zakaz temporal suffix:**
- `query` zamiast `query_new`
- `process_backlog` zamiast `process_backlog_v2`
- `render_md` zamiast `render_md_final`

**Test nazwy funkcji:** Jeśli nazwa zawiera `and` lub `or` — funkcja prawdopodobnie robi za dużo.

---

### 07R: Error handling

**Kiedy `try/except`:**
- Operacje I/O (plik, sieć, DB) — gdy failure jest przewidywalny i obsługiwalny
- Konwersje typów z zewnętrznego inputu

**Kiedy `raise`:**
- Naruszenie kontraktu funkcji (nieprawidłowe argumenty)
- Przypadki niemożliwe do odtworzenia bez błędu logiki

**Format błędu w narzędziach CLI:**

```python
def error_result(msg: str) -> dict:
    return {
        "ok": False,
        "data": None,
        "error": {"type": "GIT_ERROR", "message": msg},
        "meta": {"duration_ms": round((time.monotonic() - start) * 1000), "truncated": False},
    }
```

**Zakaz:**
- Puste `except:` lub `except Exception: pass`
- Łykanie wyjątków bez logowania i zwrócenia błędu

---

### 08R: Logging vs print

**`print()` na stdout jest zakazany** w kodzie produkcyjnym (`tools/`, `tools/lib/`).
`print(..., file=sys.stderr)` jest dozwolony dla diagnostyki (patrz 14R).

Jedyne dozwolone wyjście na stdout: `print_json()` z `tools/lib/output.py`.

**Uzasadnienie:** Na Windows domyślne kodowanie stdout to cp1250; `print_json()` wymusza UTF-8 i zapewnia spójny format dla CLI callerów.

**W testach:** `print()` dozwolony wyłącznie do debugowania (nie commituj).

---

### 09R: Konfiguracja — źródła

| Typ | Gdzie trzymać |
|---|---|
| Ścieżka do DB | Stała `DB_PATH = "mrowisko.db"` w pliku CLI |
| Role, mapy konfiguracyjne | Słownik w pliku CLI (np. `ROLE_DOCUMENTS`) |
| Parametry sesji per rola | Plik JSON: `config/session_init_config.json` |
| Sekrety (API keys, hasła) | Zmienne środowiskowe — nigdy w kodzie |

**Zakaz:** Hardcoded sekrety, ścieżki absolutne do środowiska dewelopera.

---

### 10R: Rozmiar i odpowiedzialność modułu

- Plik CLI (`tools/*.py`): max 200 linii. Jeśli więcej — wyodrębnij logikę do `tools/lib/`.
- Plik biblioteczny (`tools/lib/*.py`): max 400 linii. Jedna klasa lub zestaw powiązanych funkcji.
- Jeden plik = jedna odpowiedzialność. Gdy moduł obsługuje >3 niepowiązane koncepcje — podziel.

---

### 11R: Testy — struktura i konwencje

> Uwaga: Gdy powstanie CONVENTION_TESTING (backlog #173), reguły 11R i 16R zostaną przeniesione tam. Tu pozostanie referencja.

**Lokalizacja:** `tests/test_<modul>.py` — jeden plik testów per moduł.

**Import modułu testowanego:**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.git_commit import git_commit
```

**Klasy testowe** — grupuj powiązane testy:
```python
class TestCliSendAndInbox:
    def test_send_and_inbox_roundtrip(self, db): ...
    def test_empty_inbox(self, db): ...
```

**Fixture'y współdzielone** — w `tests/conftest.py`. Nie duplikuj helper functions między plikami testów.

**Mockowanie:**
- Mockuj I/O i zewnętrzne zależności (`subprocess.run`, SQLite, `Path.read_text`)
- Nie mockuj logiki biznesowej którą testujesz
- `unittest.mock.patch` — preferowany nad własnym instrumentowaniem

**Testy integracyjne CLI** — używaj `subprocess.run` z `--db tmp_path`:
```python
def run_cli(args: list[str], db_path: str) -> dict:
    result = subprocess.run(
        [PYTHON, CLI, "--db", db_path] + args,
        capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    return json.loads(result.stdout)
```

**Minimum:** Każda funkcja publiczna ma ≥1 test happy path i ≥1 test failure path.

---

### 12R: Pattern `tools/lib/` — biblioteki

Moduły w `tools/lib/` są bibliotekami — nie mają `if __name__ == "__main__"`.

```python
# tools/lib/output.py
"""output.py — Opis modułu.

Uzasadnienie istnienia modułu (1-2 zdania kontekstu, np. dlaczego nie standardowy print).
"""

import json
import sys


def print_json(result: dict) -> None:
    """Drukuje słownik jako JSON na stdout z wymuszonym UTF-8."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, default=str))
```

**Obowiązki `tools/lib/`:**
- Klasy enkapsulujące logikę domenową (np. `AgentBus`)
- Funkcje użytkowe współdzielone przez wiele CLI
- Brak `argparse`, brak `sys.exit()`, brak `print()`

---

## Przykłady

### Przykład 1: Kompletna struktura narzędzia CLI

```python
"""
nazwa_narzedzia.py — Krótki opis.

CLI:
    python tools/nazwa_narzedzia.py --parametr wartosc
    python tools/nazwa_narzedzia.py --flaga

Output: JSON na stdout.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.lib.agent_bus import AgentBus
from tools.lib.output import print_json

DB_PATH = "mrowisko.db"


def operacja_biznesowa(parametr: str) -> dict:
    """Wykonuje operację i zwraca wynik w standardowym formacie.

    Args:
        parametr: Opis argumentu.

    Returns:
        Dict z kluczami ok, data, error, meta.
    """
    start = time.monotonic()
    try:
        # logika...
        wynik = {"pole": "wartość"}
        return {
            "ok": True,
            "data": wynik,
            "error": None,
            "meta": {"duration_ms": round((time.monotonic() - start) * 1000), "truncated": False},
        }
    except ValueError as e:
        return {
            "ok": False,
            "data": None,
            "error": {"type": "VALIDATION_ERROR", "message": str(e)},
            "meta": {"duration_ms": round((time.monotonic() - start) * 1000), "truncated": False},
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Krótki opis narzędzia.")
    parser.add_argument("--parametr", required=True, help="Opis parametru")
    args = parser.parse_args()

    result = operacja_biznesowa(args.parametr)
    print_json(result)


if __name__ == "__main__":
    main()
```

---

### Przykład 2: Test jednostkowy z mockiem

```python
"""Testy dla tools/nazwa_narzedzia.py."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.nazwa_narzedzia import operacja_biznesowa


class TestOperacjaBiznesowa:
    def test_happy_path(self):
        result = operacja_biznesowa("poprawna_wartość")
        assert result["ok"] is True
        assert result["data"] is not None
        assert result["error"] is None

    def test_failure_path_validation_error(self):
        result = operacja_biznesowa("")
        assert result["ok"] is False
        assert result["error"]["type"] == "VALIDATION_ERROR"
```

---

### Przykład 3: Klasa biblioteczna z docstringiem

```python
class AgentBus:
    """Komunikacja między agentami i zarządzanie stanem przez SQLite.

    Zapewnia wysyłanie wiadomości, odczyt inbox, zarządzanie backlogiem
    i logowanie sesji. Wszystkie operacje są transakcyjne.
    """

    def __init__(self, db_path: str = "mrowisko.db") -> None:
        self.db_path = db_path
        self._init_schema()

    def send_message(
        self,
        sender: str,
        recipient: str,
        content: str,
        type: str = "info",
        session_id: str | None = None,
    ) -> int:
        """Wysyła wiadomość do odbiorcy.

        Returns:
            ID nowo utworzonej wiadomości.
        """
```

---

## Antywzorce

### 01AP: `print()` zamiast `print_json()`

**Źle:**
```python
def main() -> None:
    result = get_backlog()
    print(result)          # łamie UTF-8 na Windows, nie jest JSON
    print("Done")          # nie parseable przez CLI callera
```

**Dlaczego:** Na Windows `print()` używa cp1250 — polskie znaki giną. Caller oczekuje JSON.

**Dobrze:**
```python
from tools.lib.output import print_json

def main() -> None:
    result = get_backlog()
    print_json(result)
```

---

### 02AP: Własny format JSON output

**Źle:**
```python
return {"status": "ok", "items": [...], "count": 3}
return {"success": True, "result": {...}}
```

**Dlaczego:** Caller nie może generycznie sprawdzić `result["ok"]`. Różne kształty = osobny kod parsowania dla każdego narzędzia.

**Dobrze:**
```python
return {"ok": True, "data": {"items": [...], "count": 3}, "error": None, "meta": {...}}
```

---

### 03AP: Funkcja publiczna bez type hints

**Źle:**
```python
def get_messages(recipient, status, limit):
    ...
```

**Dlaczego:** IDE nie podpowiada typów, agent nie wie jak wywołać funkcję, błędy typów wykrywane dopiero w runtime.

**Dobrze:**
```python
def get_messages(
    recipient: str,
    status: str = "unread",
    limit: int = 10,
) -> list[dict]:
```

---

### 04AP: Temporal naming

**Źle:**
```python
# tools/render_new.py
# tools/agent_bus_v2.py
def process_backlog_final(items):
```

**Dlaczego:** Za rok "new" staje się "old". Historia zmian jest w git, nie w nazwie.

**Dobrze:**
```python
# tools/render.py
# tools/agent_bus.py
def process_backlog(items: list[dict]) -> dict:
```

---

### 05AP: Puste `except` lub łykanie wyjątków

**Źle:**
```python
try:
    result = subprocess.run(cmd)
except:
    pass  # cichy failure — caller nie wie co poszło nie tak

try:
    data = json.loads(content)
except Exception:
    data = {}  # maskuje błąd parsowania
```

**Dlaczego:** Silent failure = niewidoczny bug. Caller otrzymuje "sukces" przy faktycznym błędzie.

**Dobrze:**
```python
try:
    data = json.loads(content)
except json.JSONDecodeError as e:
    return {
        "ok": False,
        "data": None,
        "error": {"type": "PARSE_ERROR", "message": str(e)},
        "meta": {"duration_ms": 0, "truncated": False},
    }
```

---

### 06AP: Importy względne

**Źle:**
```python
from . import output
from ..lib.agent_bus import AgentBus
```

**Dlaczego:** Projekt nie jest zainstalowany jako pakiet. Importy względne nie działają przy uruchomieniu `python tools/skrypt.py`.

**Dobrze:**
```python
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.lib.output import print_json
from tools.lib.agent_bus import AgentBus
```

---

### 07AP: Logika biznesowa bezpośrednio w `main()`

**Źle:**
```python
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--role")
    args = parser.parse_args()

    # 50 linii logiki bezpośrednio tutaj...
    bus = AgentBus()
    messages = bus.get_messages(args.role)
    for msg in messages:
        # przetwarzanie...
    print_json({"ok": True, "data": messages})
```

**Dlaczego:** `main()` staje się nietestatowalna. Logiki nie można wywołać bez parsowania argumentów.

**Dobrze:**
```python
def cmd_inbox(args: argparse.Namespace, bus: AgentBus) -> dict:
    messages = bus.get_messages(recipient=args.role)
    return {"ok": True, "data": messages, "error": None, "meta": {...}}

def main() -> None:
    parser = argparse.ArgumentParser()
    # ...
    result = cmd_inbox(args, AgentBus(DB_PATH))
    print_json(result)
```

---

### 13R: Exit codes — wspólny enum

Każde narzędzie CLI MUSI używać wspólnego zestawu kodów wyjścia:

| Kod | Stała | Znaczenie |
|-----|-------|-----------|
| 0 | `EXIT_OK` | Sukces |
| 1 | `EXIT_ERROR` | Błąd runtime (DB, I/O, logika) |
| 2 | `EXIT_USAGE` | Błąd argumentów (domyślne `argparse`) |

**Reguły:**
- Dodatkowe kody domenowe wymagają jawnej dokumentacji w docstringu `main()`.
- Narzędzie NIE zwraca kodu wyjścia innego niż 0/1/2 bez uzasadnienia.
- `argparse` sam zwraca `2` przy błędnych argumentach — nie nadpisuj.

**Zakaz:** `sys.exit(42)` bez udokumentowania co 42 znaczy.

---

### 14R: Kanały IO — stdout dla danych, stderr dla diagnostyki

```python
# stdout: WYŁĄCZNIE JSON wynikowy (print_json)
print_json({"ok": True, "data": result})

# stderr: błędy, ostrzeżenia, debug info
import sys
print("WARNING: brak pliku config", file=sys.stderr)
```

**Reguły:**
- Na `stdout` trafia wyłącznie output machine-readable (JSON).
- Na `stderr` trafiają: ostrzeżenia, komunikaty debug, progress info.
- Agent parsujący wynik narzędzia czyta tylko `stdout`.
- `print()` bez `file=sys.stderr` jest zakazany (patrz 08R).

**Uzasadnienie:** Dojrzałe CLI (gcloud, AWS CLI, gh) konsekwentnie separują kanały.
Mieszanie danych z diagnostyką łamie potokowanie i parsowanie JSON.

---

### 15R: Centralna konfiguracja lint i type-check

Projekt MUSI mieć jedną konfigurację lint/type-check w `pyproject.toml`:

```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I"]  # minimum: errors, warnings, imports

[tool.mypy]
python_version = "3.12"
disallow_untyped_defs = true    # wymusza type hints na publicznych funkcjach
```

**Reguły:**
- Jedna konfiguracja dla całego repo — nie per-narzędzie.
- Kod MUSI przechodzić `ruff check` bez błędów przed commitem.
- `mypy --disallow-untyped-defs` na `tools/` i `tools/lib/` — wymusza 03R.
- Konfiguracja w `pyproject.toml`, nie w osobnych plikach `.ruff.toml` / `mypy.ini`.

---

### 16R: Testy kontraktowe — minimum per narzędzie CLI

Każde narzędzie CLI w `tools/` MUSI mieć minimum 4 testy kontraktowe:

```python
class TestNazwaNarzedzia:
    def test_help_exits_zero(self):
        """--help zwraca exit code 0."""
        result = subprocess.run([sys.executable, TOOL, "--help"], capture_output=True)
        assert result.returncode == 0

    def test_success_returns_json(self):
        """Sukces zwraca valid JSON z ok=True."""
        result = run_tool(["--valid-args"])
        assert result["ok"] is True

    def test_bad_args_exits_two(self):
        """Błędne argumenty → exit code 2."""
        result = subprocess.run([sys.executable, TOOL, "--nonexistent"], capture_output=True)
        assert result.returncode == 2

    def test_runtime_error_returns_json_error(self):
        """Błąd runtime zwraca JSON z ok=False i error."""
        result = run_tool(["--trigger-error"])
        assert result["ok"] is False
        assert result["error"]["type"] is not None
```

Te 4 testy gwarantują stabilność kontraktu interfejsu narzędzia.
Dodatkowe testy (happy path, edge cases, integracyjne) — per moduł wg potrzeb.

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.2 | 2026-03-25 | Review: widełki → twarde limity w 10R, notatka o przyszłym CONV_TESTING przy 11R/16R |
| 1.1 | 2026-03-25 | Enrichment z researchu: 13R (exit codes), 14R (stdout/stderr), 15R (lint config), 16R (testy kontraktowe), allow_abbrev=False w 01R |
| 1.0 | 2026-03-25 | Wersja początkowa — na bazie CODE_STANDARDS.md + inspekcja tools/ i tests/ |
