"""
Setup nowej maszyny — automatyczna konfiguracja Claude Code.

Wykrywa ścieżki, interpreter Python i generuje pliki settings z templates.

Usage:
    python tools/setup_machine.py [--project-path PATH] [--python-cmd CMD] [--dry-run]

Options:
    --project-path PATH   Ścieżka do projektu (domyślnie: bieżący katalog)
    --python-cmd CMD      Komenda Python (domyślnie: auto-detect)
    --dry-run             Pokazuje co zostanie zrobione bez zapisywania plików
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path


def detect_python_command():
    """Wykrywa dostępny interpreter Python (py, python3, python)."""
    for cmd in ['py', 'python3', 'python']:
        try:
            result = subprocess.run(
                [cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return cmd
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    raise RuntimeError("Nie znaleziono interpretera Python (próbowano: py, python3, python)")


def get_project_path_unix(project_root):
    """Konwertuje ścieżkę projektu do formatu Unix z ~ dla home."""
    home = Path.home()
    project_path = Path(project_root).resolve()

    try:
        relative = project_path.relative_to(home)
        return f"~/{relative.as_posix()}"
    except ValueError:
        # Projekt poza katalogiem domowym
        return project_path.as_posix()


def get_project_path_windows(project_root):
    """Konwertuje ścieżkę projektu do formatu Windows bez dysku."""
    project_path = Path(project_root).resolve()
    path_str = str(project_path)

    # Usuń literę dysku (C:\)
    if len(path_str) >= 3 and path_str[1] == ':':
        path_str = path_str[3:]  # Pomija "C:\"

    return path_str.replace('\\', '/')


def get_project_path_windows_escaped(project_root):
    """Konwertuje ścieżkę projektu do formatu Windows z podwójnym escape."""
    project_path = Path(project_root).resolve()
    return str(project_path).replace('\\', '\\\\')


def process_template(template_path, output_path, replacements, dry_run=False):
    """Przetwarza template — podstawia placeholdery i zapisuje wynik."""
    if not template_path.exists():
        print(f"[WARN] Pominięto: {template_path} (nie istnieje)")
        return False

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Podstawianie placeholderów
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    if dry_run:
        print(f"[DRY-RUN] Wygenerowano: {output_path}")
        return True

    # Zapisanie pliku
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[OK] Wygenerowano: {output_path}")
    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Setup nowej maszyny — konfiguracja Claude Code')
    parser.add_argument('--project-path', type=str, default=None,
                        help='Ścieżka do projektu (domyślnie: bieżący katalog)')
    parser.add_argument('--python-cmd', type=str, default=None,
                        help='Komenda Python (domyślnie: auto-detect)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Pokazuje co zostanie zrobione bez zapisywania plików')

    args = parser.parse_args()

    # Wykrywanie parametrów
    project_root = Path(args.project_path or os.getcwd()).resolve()

    if not (project_root / '.claude').exists():
        print(f"[ERROR] {project_root} nie wygląda na katalog projektu (brak .claude/)")
        print("        Użyj: --project-path <ścieżka do projektu>")
        return 1

    if args.python_cmd:
        python_cmd = args.python_cmd
        print(f"Python: {python_cmd} (podany przez użytkownika)")
    else:
        try:
            python_cmd = detect_python_command()
            print(f"Python: {python_cmd} (wykryty automatycznie)")
        except RuntimeError as e:
            print(f"[ERROR] {e}")
            return 1

    # Generowanie ścieżek
    project_path_unix = get_project_path_unix(project_root)
    project_path_windows = get_project_path_windows(project_root)
    project_path_windows_escaped = get_project_path_windows_escaped(project_root)

    print(f"Projekt: {project_root}")
    print(f"  Unix: {project_path_unix}")
    print(f"  Windows: {project_path_windows}")
    print(f"  Windows escaped: {project_path_windows_escaped}")
    print()

    if args.dry_run:
        print("Tryb DRY-RUN — pliki nie zostaną zapisane\n")

    # Mapowanie placeholderów
    replacements = {
        '{{PROJECT_PATH}}': project_path_unix,
        '{{PYTHON_CMD}}': python_cmd,
        '{{PROJECT_PATH_WINDOWS}}': project_path_windows,
        '{{PROJECT_PATH_WINDOWS_ESCAPED}}': project_path_windows_escaped,
    }

    # Lista plików do wygenerowania
    templates = [
        (
            project_root / '.claude' / 'settings.template.json',
            project_root / '.claude' / 'settings.json'
        ),
        (
            project_root / '.claude' / 'settings.local.template.json',
            project_root / '.claude' / 'settings.local.json'
        ),
        (
            project_root / 'bot' / '.claude' / 'settings.local.template.json',
            project_root / 'bot' / '.claude' / 'settings.local.json'
        ),
    ]

    # Przetwarzanie templates
    success_count = 0
    for template_path, output_path in templates:
        if process_template(template_path, output_path, replacements, args.dry_run):
            success_count += 1

    print()
    print(f"[OK] Wygenerowano {success_count}/{len(templates)} plików")

    if args.dry_run:
        print("\nUruchom bez --dry-run żeby zapisać pliki.")
    else:
        print("\n[OK] Setup zakończony — możesz zacząć pracę w Claude Code.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
