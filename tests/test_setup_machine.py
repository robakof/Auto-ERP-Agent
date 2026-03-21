"""Tests for setup_machine.py — auto-konfiguracja Claude Code."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def mock_project(tmp_path):
    """Tworzy mock struktury projektu z templates."""
    # Struktura katalogów
    (tmp_path / '.claude').mkdir()
    (tmp_path / 'bot' / '.claude').mkdir(parents=True)
    (tmp_path / 'tools').mkdir()

    # Template files (uproszczone)
    settings_template = {
        "permissions": {
            "allow": [
                "Read({{PROJECT_PATH}}/**)",
                "Edit({{PROJECT_PATH}}/**)"
            ]
        }
    }

    settings_local_template = {
        "permissions": {
            "allow": [
                "Bash({{PYTHON_CMD}} tools/test.py:*)"
            ]
        },
        "hooks": {
            "PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{
                    "type": "command",
                    "command": "{{PYTHON_CMD}} tools/hooks/pre_tool_use.py"
                }]
            }]
        }
    }

    bot_template = {
        "permissions": {
            "allow": [
                "Read(//c/{{PROJECT_PATH_WINDOWS}}/**)",
                "Bash(cd \"{{PROJECT_PATH_WINDOWS_ESCAPED}}\" && {{PYTHON_CMD}} bot/main.py)"
            ]
        }
    }

    # Zapis templates
    with open(tmp_path / '.claude' / 'settings.template.json', 'w') as f:
        json.dump(settings_template, f, indent=2)

    with open(tmp_path / '.claude' / 'settings.local.template.json', 'w') as f:
        json.dump(settings_local_template, f, indent=2)

    with open(tmp_path / 'bot' / '.claude' / 'settings.local.template.json', 'w') as f:
        json.dump(bot_template, f, indent=2)

    return tmp_path


class TestSetupMachine:
    def test_detect_python_command(self):
        """Test wykrywania komendy Python."""
        from tools.setup_machine import detect_python_command

        cmd = detect_python_command()
        assert cmd in ['py', 'python', 'python3']

    def test_get_project_path_unix(self, tmp_path):
        """Test konwersji ścieżki do formatu Unix."""
        from tools.setup_machine import get_project_path_unix

        result = get_project_path_unix(tmp_path)
        # Powinno zawierać ~ jeśli w home, albo być absolutną ścieżką
        assert isinstance(result, str)
        assert len(result) > 0
        # Unix path używa /
        assert '\\' not in result or result.startswith('~')

    def test_get_project_path_windows(self, tmp_path):
        """Test konwersji ścieżki do formatu Windows bez dysku."""
        from tools.setup_machine import get_project_path_windows

        result = get_project_path_windows(tmp_path)
        assert isinstance(result, str)
        # Nie powinno zawierać litery dysku (C:)
        assert ':' not in result
        # Powinno używać /
        assert '\\' not in result

    def test_get_project_path_windows_escaped(self, tmp_path):
        """Test konwersji ścieżki do formatu Windows escaped."""
        from tools.setup_machine import get_project_path_windows_escaped

        result = get_project_path_windows_escaped(tmp_path)
        assert isinstance(result, str)
        # Powinno zawierać \\\\ (podwójny escape)
        assert '\\\\' in result

    def test_process_template(self, tmp_path):
        """Test podstawiania placeholderów w template."""
        from tools.setup_machine import process_template

        # Przygotowanie template
        template_path = tmp_path / 'test.template.json'
        output_path = tmp_path / 'test.json'

        template_content = {
            "path": "{{PROJECT_PATH}}",
            "cmd": "{{PYTHON_CMD}}"
        }
        with open(template_path, 'w') as f:
            json.dump(template_content, f)

        replacements = {
            '{{PROJECT_PATH}}': '~/test/path',
            '{{PYTHON_CMD}}': 'py'
        }

        # Wykonanie
        result = process_template(template_path, output_path, replacements)

        # Weryfikacja
        assert result is True
        assert output_path.exists()

        with open(output_path, 'r') as f:
            output = json.load(f)

        assert output['path'] == '~/test/path'
        assert output['cmd'] == 'py'
        # Placeholdery nie powinny pozostać
        assert '{{' not in json.dumps(output)

    def test_process_template_dry_run(self, tmp_path):
        """Test trybu dry-run — nie zapisuje plików."""
        from tools.setup_machine import process_template

        template_path = tmp_path / 'test.template.json'
        output_path = tmp_path / 'test.json'

        with open(template_path, 'w') as f:
            f.write('{"test": "{{VALUE}}"}')

        replacements = {'{{VALUE}}': 'replaced'}

        result = process_template(template_path, output_path, replacements, dry_run=True)

        assert result is True
        # Plik NIE powinien zostać utworzony
        assert not output_path.exists()

    def test_cli_dry_run(self, mock_project):
        """Test CLI w trybie dry-run."""
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / 'tools' / 'setup_machine.py'),
                '--project-path', str(mock_project),
                '--python-cmd', 'py',
                '--dry-run'
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Sprawdź output
        assert 'DRY-RUN' in result.stdout
        assert 'Wygenerowano' in result.stdout

        # Pliki nie powinny zostać utworzone
        assert not (mock_project / '.claude' / 'settings.json').exists()
        assert not (mock_project / '.claude' / 'settings.local.json').exists()

    def test_cli_full_run(self, mock_project):
        """Test pełnego uruchomienia CLI — generowanie plików."""
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / 'tools' / 'setup_machine.py'),
                '--project-path', str(mock_project),
                '--python-cmd', 'py'
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert 'Setup zakończony' in result.stdout

        # Pliki powinny zostać utworzone
        settings_json = mock_project / '.claude' / 'settings.json'
        settings_local_json = mock_project / '.claude' / 'settings.local.json'
        bot_settings_json = mock_project / 'bot' / '.claude' / 'settings.local.json'

        assert settings_json.exists()
        assert settings_local_json.exists()
        assert bot_settings_json.exists()

        # Weryfikacja zawartości — placeholdery powinny być zastąpione
        with open(settings_json, 'r') as f:
            settings = json.load(f)

        # Nie powinno zawierać placeholderów
        settings_str = json.dumps(settings)
        assert '{{PROJECT_PATH}}' not in settings_str
        assert '{{PYTHON_CMD}}' not in settings_str

        # Powinno zawierać rzeczywiste wartości
        assert 'py' in settings_str

        # Weryfikacja hooks w settings.local.json
        with open(settings_local_json, 'r') as f:
            settings_local = json.load(f)

        hooks_str = json.dumps(settings_local)
        assert '{{PYTHON_CMD}}' not in hooks_str
        assert 'py' in hooks_str

    def test_cli_invalid_project_path(self, tmp_path):
        """Test błędu gdy katalog nie jest projektem (brak .claude/)."""
        invalid_path = tmp_path / 'not_a_project'
        invalid_path.mkdir()

        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / 'tools' / 'setup_machine.py'),
                '--project-path', str(invalid_path),
                '--python-cmd', 'py'
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        # Sprawdź stderr (tam trafiają komunikaty błędów) lub stdout
        output = result.stdout + result.stderr
        assert 'nie wygląda na katalog projektu' in output

    def test_missing_template(self, tmp_path):
        """Test gdy template nie istnieje — powinien pominąć."""
        from tools.setup_machine import process_template

        template_path = tmp_path / 'nonexistent.template.json'
        output_path = tmp_path / 'output.json'

        replacements = {'{{TEST}}': 'value'}

        result = process_template(template_path, output_path, replacements)

        assert result is False  # Template nie istnieje
        assert not output_path.exists()
