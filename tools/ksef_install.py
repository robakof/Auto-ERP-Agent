r"""KSeF Installer -- copies all required files to a standalone directory.

    py tools/ksef_install.py                          # install to dist/ksef/
    py tools/ksef_install.py --target D:\KSeF          # custom target
    py tools/ksef_install.py --install-deps            # also pip install
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Files to copy (relative to project root)
_FILES = [
    # Launchers
    "ksef_wyslij_demo.bat",
    "ksef_raport_dzienny.bat",
    "ksef_ustawienia.bat",

    # Tools
    "tools/ksef_daemon.py",
    "tools/ksef_watchdog.py",
    "tools/ksef_report.py",
    "tools/ksef_config_gui.py",
    "tools/sql_query.py",
    "tools/lib/__init__.py",
    "tools/lib/sql_client.py",
    "tools/lib/excel_writer.py",
    "tools/lib/output.py",

    # Core — config, guards, exceptions
    "core/__init__.py",
    "core/ksef/__init__.py",
    "core/ksef/config.py",
    "core/ksef/guards.py",
    "core/ksef/exceptions.py",
    "core/ksef/models.py",
    "core/ksef/schema.sql",

    # Core — domain
    "core/ksef/domain/__init__.py",
    "core/ksef/domain/shipment.py",
    "core/ksef/domain/invoice.py",
    "core/ksef/domain/correction.py",
    "core/ksef/domain/events.py",

    # Core — adapters
    "core/ksef/adapters/__init__.py",
    "core/ksef/adapters/repo.py",
    "core/ksef/adapters/http.py",
    "core/ksef/adapters/ksef_api.py",
    "core/ksef/adapters/ksef_auth.py",
    "core/ksef/adapters/encryption.py",
    "core/ksef/adapters/erp_reader.py",
    "core/ksef/adapters/xml_builder.py",
    "core/ksef/adapters/xsd_validator.py",
    "core/ksef/adapters/email_sender.py",
    "core/ksef/adapters/report_renderer.py",

    # Core — usecases
    "core/ksef/usecases/__init__.py",
    "core/ksef/usecases/scan_erp.py",
    "core/ksef/usecases/send_invoice.py",
    "core/ksef/usecases/report.py",

    # XSD schema
    "output/schemat_FA3.xsd",
]

# Files to copy only if they don't exist at target (don't overwrite config)
_CONFIG_FILES = [
    ".env",
]

_REQUIREMENTS = """\
pyodbc>=5.0
python-dotenv>=1.0
httpx>=0.27
tenacity>=8.2
cryptography>=42.0
lxml>=5.0
openpyxl>=3.1
"""


def install(target: Path, *, install_deps: bool = False) -> None:
    print(f"Instalacja KSeF do: {target}")
    print()

    # Copy files
    copied = 0
    missing = []
    for rel in _FILES:
        src = _PROJECT_ROOT / rel
        dst = target / rel
        if not src.exists():
            missing.append(rel)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1

    # Config files — only if not exists
    for rel in _CONFIG_FILES:
        src = _PROJECT_ROOT / rel
        dst = target / rel
        if dst.exists():
            print(f"  [SKIP] {rel} (juz istnieje — nie nadpisuje)")
            continue
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
            print(f"  [NEW]  {rel}")

    # Create empty dirs
    for d in ["data", "output/ksef/upo", "tmp"]:
        (target / d).mkdir(parents=True, exist_ok=True)

    # Write requirements.txt
    req_path = target / "requirements.txt"
    req_path.write_text(_REQUIREMENTS, encoding="utf-8")

    print(f"\nSkopiowano: {copied} plikow")
    if missing:
        print(f"Brakujace (pominiete): {len(missing)}")
        for m in missing:
            print(f"  - {m}")

    # Install deps
    if install_deps:
        print("\nInstalacja zaleznosci pip...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
            check=True,
        )
        print("Zaleznosci zainstalowane.")

    print(f"""
====================================
  Instalacja zakonczona!
====================================

Nastepne kroki:
1. Edytuj .env w {target}
   (lub uruchom ksef_ustawienia.bat)

2. Zainstaluj zaleznosci (jesli nie --install-deps):
   pip install -r {req_path}

3. Uruchom daemon:
   ksef_wyslij_demo.bat

4. Zarejestruj w Task Scheduler:
   - ksef_wyslij_demo.bat  -> przy starcie komputera
   - ksef_raport_dzienny.bat -> codziennie 13:30
""")


def main() -> int:
    p = argparse.ArgumentParser(description="KSeF Installer")
    p.add_argument("--target", type=str,
                   default=str(_PROJECT_ROOT / "dist" / "ksef"),
                   help="Katalog docelowy (default: dist/ksef/)")
    p.add_argument("--install-deps", action="store_true",
                   help="Zainstaluj zaleznosci pip")
    args = p.parse_args()

    target = Path(args.target).resolve()
    install(target, install_deps=args.install_deps)
    return 0


if __name__ == "__main__":
    sys.exit(main())
