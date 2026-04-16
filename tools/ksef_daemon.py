"""KSeF daemon — auto-scan ERP + send approved invoices.

    py tools/ksef_daemon.py                     # tick co 60s
    py tools/ksef_daemon.py --interval 30       # tick co 30s
    py tools/ksef_daemon.py --once              # single scan + send, exit
    py tools/ksef_daemon.py --dry-run           # scan only, show what would be sent
    py tools/ksef_daemon.py --once --dry-run    # single scan, show only
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from datetime import date
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ksef.adapters.encryption import KSeFEncryption
from core.ksef.adapters.http import KSefHttp
from core.ksef.adapters.ksef_api import KSeFApiClient
from core.ksef.adapters.ksef_auth import EnvTokenProvider, KSefAuth
from core.ksef.adapters.repo import ShipmentRepository
from core.ksef.adapters.xml_builder import XmlBuilder
from core.ksef.adapters.erp_reader import ErpReader
from core.ksef.config import load_config
from core.ksef.domain.shipment import ShipmentStatus
from core.ksef.usecases.scan_erp import PendingDocument, ScanErpUseCase
from core.ksef.usecases.send_invoice import SendInvoiceUseCase, SendResult

_LOG = logging.getLogger("ksef.daemon")

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "ksef.db"
_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "ksef"
_UPO_DIR = _OUTPUT_DIR / "upo"


class KSeFDaemon:
    """Tick loop: scan ERP -> generate XML -> send to KSeF."""

    def __init__(
        self,
        scan: ScanErpUseCase,
        send_factory: Callable[[PendingDocument], SendResult],
        *,
        interval_s: float = 60.0,
        on_tick: Callable[[int, list[PendingDocument]], None] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._scan = scan
        self._send_factory = send_factory
        self._interval = interval_s
        self._on_tick = on_tick or _default_on_tick
        self._sleep = sleep
        self._shutdown = False
        self._tick_count = 0

    def run(self) -> None:
        """Main loop. Ctrl+C = graceful shutdown."""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        _LOG.info('{"event": "daemon_start", "interval_s": %.1f}', self._interval)
        while not self._shutdown:
            self._tick()
            if self._shutdown:
                break
            self._sleep_interruptible(self._interval)
        _LOG.info('{"event": "daemon_stop", "ticks": %d}', self._tick_count)

    def run_once(self) -> list[SendResult]:
        """Single scan + send. Returns results."""
        return self._tick()

    def _tick(self) -> list[SendResult]:
        pending = self._scan.scan()
        self._on_tick(self._tick_count, pending)
        results = []
        for doc in pending:
            if self._shutdown:
                break
            result = self._process_one(doc)
            if result:
                results.append(result)
        self._tick_count += 1
        return results

    def _process_one(self, doc: PendingDocument) -> SendResult | None:
        """Generate XML + send. Errors logged, not raised."""
        try:
            result = self._send_factory(doc)
            status_str = result.status.value
            _LOG.info(
                '{"event": "doc_processed", "gid": %d, "rodzaj": "%s", "status": "%s"}',
                doc.gid, doc.rodzaj, status_str,
            )
            return result
        except Exception as exc:
            _LOG.error(
                '{"event": "doc_error", "gid": %d, "rodzaj": "%s", "error": "%s"}',
                doc.gid, doc.rodzaj, exc,
            )
            return None

    def _handle_shutdown(self, sig, frame) -> None:
        _LOG.info('{"event": "shutdown_requested", "signal": %d}', sig)
        self._shutdown = True

    def _sleep_interruptible(self, seconds: float) -> None:
        """Sleep in 1s increments, checking shutdown flag."""
        elapsed = 0.0
        while elapsed < seconds and not self._shutdown:
            chunk = min(1.0, seconds - elapsed)
            self._sleep(chunk)
            elapsed += chunk


def _default_on_tick(tick: int, pending: list[PendingDocument]) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] Tick #{tick}: {len(pending)} pending documents")
    for doc in pending:
        print(f"  {doc.rodzaj} GID={doc.gid} {doc.nr_faktury} ({doc.data_wystawienia})")


# ---- CLI wiring -------------------------------------------------------------

def _build_send_factory(
    run_query, repo: ShipmentRepository, *, dry_run: bool = False,
):
    """Build a send_factory callable that generates XML + sends."""
    if dry_run:
        return _dry_run_factory

    cfg = load_config()
    http = KSefHttp(base_url=cfg.base_url)
    api = KSeFApiClient(http)
    provider = EnvTokenProvider(token=cfg.ksef_token or "", nip=cfg.nip)
    auth = KSefAuth(api, provider)

    certs = api.get_public_key_certificates()
    sym_cert = next((c for c in certs if "SymmetricKeyEncryption" in c.usage), None)
    if sym_cert is None:
        print("BLAD: Brak certyfikatu SymmetricKeyEncryption z KSeF")
        sys.exit(2)
    encryption = KSeFEncryption(sym_cert.certificate_b64)

    uc = SendInvoiceUseCase(
        api=api, auth=auth, repo=repo, encryption=encryption,
        upo_dir=_UPO_DIR,
    )

    reader = ErpReader(run_query)
    builder = XmlBuilder()

    def factory(doc: PendingDocument) -> SendResult:
        xml_path = _generate_xml(reader, builder, doc)
        return uc.execute(xml_path, doc.gid, doc.rodzaj, doc.nr_faktury, doc.data_wystawienia)

    return factory


def _generate_xml(reader: ErpReader, builder: XmlBuilder, doc: PendingDocument) -> Path:
    """ErpReader -> XmlBuilder -> file on disk."""
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if doc.rodzaj == "FS":
        faktury = reader.fetch_faktury(gids=[doc.gid])
        if not faktury:
            raise ValueError(f"ErpReader zwrocil 0 faktur dla GID={doc.gid}")
        xml_bytes = builder.build_faktura(faktury[0])
    else:
        korekty = reader.fetch_korekty(gids=[doc.gid])
        if not korekty:
            raise ValueError(f"ErpReader zwrocil 0 korekt dla GID={doc.gid}")
        xml_bytes = builder.build_korekta(korekty[0])

    d = doc.data_wystawienia
    prefix = "ksef_kor_" if doc.rodzaj == "FSK" else "ksef_"
    filename = f"{prefix}{doc.rodzaj}-{doc.gid}_{d.strftime('%m_%y')}_{d.isoformat()}.xml"
    path = _OUTPUT_DIR / filename
    path.write_bytes(xml_bytes)
    return path


def _dry_run_factory(doc: PendingDocument) -> SendResult:
    print(f"  [DRY-RUN] Would send {doc.rodzaj} GID={doc.gid} {doc.nr_faktury}")
    return SendResult(
        wysylka_id=0,
        ksef_number=None,
        upo_path=None,
        status=ShipmentStatus.DRAFT,
    )


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    args = _parse_args()

    def run_query(sql):
        from tools.sql_query import run_query as _rq
        return _rq(sql)

    repo = ShipmentRepository(_DB_PATH)
    repo.init_schema()

    scan = ScanErpUseCase(run_query, repo)
    send_factory = _build_send_factory(run_query, repo, dry_run=args.dry_run)

    daemon = KSeFDaemon(
        scan=scan,
        send_factory=send_factory,
        interval_s=args.interval,
    )

    if args.once:
        results = daemon.run_once()
        accepted = sum(1 for r in results if r.status == ShipmentStatus.ACCEPTED)
        total = len(results)
        print(f"\nDone: {accepted}/{total} accepted")
        return 0 if accepted == total or args.dry_run else 1
    else:
        daemon.run()
        return 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="KSeF daemon — auto-scan + send")
    p.add_argument("--interval", type=float, default=60.0, help="Sekundy miedzy tickami (default 60)")
    p.add_argument("--once", action="store_true", help="Single scan + send, exit")
    p.add_argument("--dry-run", action="store_true", help="Scan only, show what would be sent")
    return p.parse_args()


if __name__ == "__main__":
    sys.exit(main())
