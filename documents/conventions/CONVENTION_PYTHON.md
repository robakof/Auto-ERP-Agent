---
convention_id: python-convention
version: "1.3"
status: draft
created: 2026-03-25
updated: 2026-03-25
author: architect
owner: architect
approver: dawid
audience: [developer, architect, prompt_engineer]
scope: "Standardy kodu Python w projekcie Mrowisko"
---

# CONVENTION_PYTHON — Standardy kodu Python

## TL;DR

- Każde narzędzie CLI w `tools/` MUSI mieć wzorzec: `argparse → main() → JSON output → sys.exit`
- Wszystkie funkcje MUSZĄ mieć type hints (publiczne i prywatne)
- JSON output = zawsze `{"ok": bool, "data": ..., "error": ..., "meta": ...}` — bez wyjątków
- Importy: stdlib → third-party → local, tylko importy absolutne
- `print()` na stdout zakazany — używaj `print_json()` z `tools/lib/output.py`
- Nazwy plików: `snake_case`, opisowe, bez temporal suffixów (`_new`, `_v2`, `_final`)
- Exit codes: 0 (OK), 1 (runtime error), 2 (usage error) — wspólny enum
- stdout wyłącznie dla JSON, stderr dla diagnostyki — nie mieszaj kanałów
- Każde narzędzie ma minimum 4 testy kontraktowe (help, success, bad args, runtime error)
- Docstrings w języku angielskim (warstwa techniczna = EN)

---

## Zakres

**Pokrywa:**
- Kod Python w `tools/`, `tools/lib/`, `core/`, `tests/`
- Pattern CLI narzędzi (argparse, output, exit codes)
- Pattern bibliotek (`tools/lib/`, `core/`)
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
    parser = argparse.ArgumentParser(description="Tool description.", allow_abbrev=False)
    # arguments...
    args = parser.parse_args()

    result = business_function(args.parameter)
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
    "error": None | {"type": "ERROR_TYPE", "message": "description"},
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

### 03R: Type hints dla wszystkich funkcji

Wszystkie funkcje MUSZĄ mieć type hints dla argumentów i wartości zwracanej.

```python
# Public function
def git_commit(
    message: str = "",
    files: list[str] | None = None,
    add_all: bool = False,
) -> dict:

# Private function — type hints also required
def _parse_status_files(status_output: str) -> list[str]:
```

**Dlaczego wszystkie (nie tylko publiczne):**
- Agent czytający kod widzi sygnaturę → wie jak wywołać
- mypy łapie błędy typów w prywatnych funkcjach też
- Debugging: widzisz co funkcja przyjmuje/zwraca bez czytania ciała

**Zakaz:** Funkcja bez type hints.

---

### 04R: Docstrings w języku angielskim

Docstrings w formacie Google, język angielski (warstwa techniczna = EN).

```python
def get_context(role: str, config: dict, bus: AgentBus) -> dict:
    """Collect session context per configuration.

    Args:
        role: Agent role name (e.g. "developer").
        config: Configuration dict from session_init_config.json.
        bus: AgentBus instance with open DB connection.

    Returns:
        Dict with keys: inbox, backlog, logs (depending on config).
    """
```

**Kiedy wymagane:**
- Argumenty nie są oczywiste z nazwy
- Funkcja ma efekty uboczne (zapis do DB, zapis pliku)
- Funkcja jest punktem integracyjnym (wywoływana przez inne moduły)

**Kiedy można pominąć:**
- Funkcja z self-dokumentującą się sygnaturą i prostą logiką

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

# local (absolute)
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.lib.agent_bus import AgentBus
from tools.lib.output import print_json
```

**Zakaz:** Importy względne (`from . import`, `from .. import`) — używaj absolutnych.

**`sys.path.insert`:** Workaround wymagany ponieważ projekt nie jest zainstalowany jako pakiet Python. Dozwolone w plikach CLI (`tools/*.py`) i testach. W `tools/lib/` i `core/` niedozwolone. Docelowo: `pyproject.toml` z `pip install -e .` wyeliminuje ten hack.

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

### 08R: stdout vs stderr

**`print()` na stdout jest zakazany** w kodzie produkcyjnym (`tools/`, `tools/lib/`, `core/`).
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

**Minimum:** Każda funkcja publiczna ma ≥1 test happy path i ≥1 test failure path.

---

### 12R: Pattern `tools/lib/` — biblioteki

Moduły w `tools/lib/` są bibliotekami — nie mają `if __name__ == "__main__"`.

```python
# tools/lib/output.py
"""Output helpers for CLI tools.

Forces UTF-8 on stdout to avoid cp1250 issues on Windows.
"""

import json
import sys


def print_json(result: dict) -> None:
    """Print dict as JSON to stdout with forced UTF-8."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, default=str))
```

**Obowiązki `tools/lib/`:**
- Klasy enkapsulujące logikę domenową (np. `AgentBus`)
- Funkcje użytkowe współdzielone przez wiele CLI
- Brak `argparse`, brak `sys.exit()`, brak `print()` na stdout

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
# stdout: ONLY machine-readable JSON (print_json)
print_json({"ok": True, "data": result})

# stderr: errors, warnings, debug info
import sys
print("WARNING: config file missing", file=sys.stderr)
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

Projekt ma konfigurację lint/type-check w `pyproject.toml` (wdrożona, backlog #189 done).

**Reguły:**
- Jedna konfiguracja dla całego repo — nie per-narzędzie.
- Kod MUSI przechodzić `ruff check` bez błędów przed commitem.
- `mypy` na `tools/` i `core/` — wymusza 03R (docelowo `disallow_untyped_defs = true`).
- Konfiguracja w `pyproject.toml`, nie w osobnych plikach `.ruff.toml` / `mypy.ini`.

---

### 16R: Testy kontraktowe — minimum per narzędzie CLI

> Uwaga: Gdy powstanie CONVENTION_TESTING (backlog #173), ta reguła zostanie przeniesiona tam.

Każde narzędzie CLI w `tools/` MUSI mieć minimum 4 testy kontraktowe:

1. `test_help_exits_zero` — `--help` zwraca exit code 0
2. `test_success_returns_json` — sukces zwraca valid JSON z `ok=True`
3. `test_bad_args_exits_two` — błędne argumenty → exit code 2
4. `test_runtime_error_returns_json_error` — błąd runtime → JSON z `ok=False`

Te 4 testy gwarantują stabilność kontraktu interfejsu narzędzia.

---

## Przykłady

### Przykład 1: Kompletna struktura narzędzia CLI

```python
"""
tool_name.py — Short description.

CLI:
    python tools/tool_name.py --parameter value
    python tools/tool_name.py --flag

Output: JSON on stdout.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.lib.agent_bus import AgentBus
from tools.lib.output import print_json

DB_PATH = "mrowisko.db"


def business_operation(parameter: str) -> dict:
    """Execute operation and return result in standard format.

    Args:
        parameter: Description of argument.

    Returns:
        Dict with keys ok, data, error, meta.
    """
    start = time.monotonic()
    try:
        result = {"field": "value"}
        return {
            "ok": True,
            "data": result,
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
    parser = argparse.ArgumentParser(description="Short tool description.", allow_abbrev=False)
    parser.add_argument("--parameter", required=True, help="Parameter description")
    args = parser.parse_args()

    result = business_operation(args.parameter)
    print_json(result)


if __name__ == "__main__":
    main()
```

---

### Przykład 2: Klasa biblioteczna

```python
class AgentBus:
    """Agent communication and state management via SQLite.

    Provides message sending, inbox reading, backlog management
    and session logging. All operations are transactional.
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
        """Send a message to recipient.

        Returns:
            ID of the newly created message.
        """
```

---

## Antywzorce

### 01AP: `print()` zamiast `print_json()`

**Źle:**
```python
def main() -> None:
    result = get_backlog()
    print(result)          # breaks UTF-8 on Windows, not JSON
    print("Done")          # not parseable by CLI caller
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

### 03AP: Funkcja bez type hints

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
    pass  # silent failure — caller doesn't know what went wrong

try:
    data = json.loads(content)
except Exception:
    data = {}  # masks parse error
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

### 06AP: Logika biznesowa bezpośrednio w `main()`

**Źle:**
```python
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--role")
    args = parser.parse_args()

    # 50 lines of logic directly here...
    bus = AgentBus()
    messages = bus.get_messages(args.role)
    for msg in messages:
        # processing...
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

## References

- Research: `documents/researcher/research/research_results_convention_code.md`
- pyproject.toml (wdrożony, #189): konfiguracja ruff + mypy + pytest
- Przyszła CONVENTION_TESTING (backlog #173): reguły 11R i 16R zostaną przeniesione

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.3 | 2026-03-25 | Review usera: rename CODE→PYTHON (C1), type hints dla wszystkich funkcji (C2), docstrings EN (C3), wyjaśnienie sys.path.insert (C4), usunięto AP importy względne (obsolete po pyproject). Przykłady w EN. |
| 1.2 | 2026-03-25 | Review: widełki → twarde limity w 10R, notatka o przyszłym CONV_TESTING przy 11R/16R |
| 1.1 | 2026-03-25 | Enrichment z researchu: 13R (exit codes), 14R (stdout/stderr), 15R (lint config), 16R (testy kontraktowe), allow_abbrev=False w 01R |
| 1.0 | 2026-03-25 | Wersja początkowa — na bazie CODE_STANDARDS.md + inspekcja tools/ i tests/ |
