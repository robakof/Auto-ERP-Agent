"""Deploy Serce: sync from monorepo → kaboraco-svg/serce → VPS.

Usage:
    py tools/deploy_serce.py                  # sync + push + VPS pull
    py tools/deploy_serce.py --sync-only      # sync + push (bez VPS)
    py tools/deploy_serce.py --pull-only      # tylko VPS pull
    py tools/deploy_serce.py --message "opis" # custom commit message
"""
import argparse
import subprocess
import sys
from pathlib import Path

MONOREPO = Path(__file__).resolve().parent.parent
SERCE_DEPLOY = MONOREPO.parent / "serce-deploy"
VPS_HOST = "serce@194.164.198.25"
VPS_APP_DIR = "/home/serce/app"


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"    {result.stdout.strip()}")
    if result.returncode != 0 and check:
        print(f"    ERROR: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result


def sync_and_push(message: str) -> bool:
    """Sync monorepo serce/ to local serce-deploy clone, commit, push."""
    if not SERCE_DEPLOY.exists():
        print(f"ERROR: Brak klonu serce-deploy: {SERCE_DEPLOY}", file=sys.stderr)
        print("  Sklonuj: git clone git@github-priv:kaboraco-svg/serce.git", file=sys.stderr)
        sys.exit(1)

    # Pull latest
    print("[1/4] Pull latest serce-deploy...")
    run(["git", "pull", "--ff-only", "origin", "main"], cwd=SERCE_DEPLOY, check=False)

    # Run sync script
    print("[2/4] Sync from monorepo...")
    sync_script = SERCE_DEPLOY / "scripts" / "sync_from_mrowisko.py"
    if not sync_script.exists():
        print(f"ERROR: Brak sync script: {sync_script}", file=sys.stderr)
        sys.exit(1)
    run([sys.executable, str(sync_script)], cwd=SERCE_DEPLOY)

    # Stage and check for real changes (ignores CRLF/LF noise)
    run(["git", "add", "-A"], cwd=SERCE_DEPLOY)
    result = run(["git", "diff", "--cached", "--stat"], cwd=SERCE_DEPLOY)
    if not result.stdout.strip():
        print("  Brak zmian do deploymentu.")
        return False

    # Commit + push
    print(f"[3/4] Commit: {message}")
    run(["git", "commit", "-m", message], cwd=SERCE_DEPLOY)

    print("[4/4] Push to kaboraco-svg/serce...")
    run(["git", "push", "origin", "main"], cwd=SERCE_DEPLOY)
    return True


def vps_pull() -> None:
    """Pull latest on VPS and rebuild if needed."""
    print("[VPS] Pull latest...")
    run(["ssh", VPS_HOST, f"cd {VPS_APP_DIR} && git pull origin main"])

    print("[VPS] Rebuild backend...")
    run(["ssh", VPS_HOST, f"cd {VPS_APP_DIR} && docker compose up -d --build backend"])

    print("[VPS] Run migrations...")
    run(["ssh", VPS_HOST, f"cd {VPS_APP_DIR} && docker compose exec backend alembic upgrade head"])

    print("[VPS] Health check...")
    result = run(["ssh", VPS_HOST, "curl -s http://127.0.0.1:8000/api/v1/health"], check=False)
    if '"ok"' in result.stdout:
        print("  Health: OK")
    else:
        print("  WARNING: Health check failed!", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy Serce to VPS")
    parser.add_argument("--sync-only", action="store_true", help="Sync + push only (no VPS)")
    parser.add_argument("--pull-only", action="store_true", help="VPS pull only (no sync)")
    parser.add_argument("--message", "-m", default=None, help="Custom commit message")
    args = parser.parse_args()

    if args.pull_only:
        vps_pull()
        return 0

    message = args.message or "sync: update from Mrowisko"

    changed = sync_and_push(message)

    if not args.sync_only:
        if changed:
            vps_pull()
        else:
            print("Skip VPS — nic nie zmienione.")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
