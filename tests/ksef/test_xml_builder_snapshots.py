"""Snapshot tests — byte-identyczny XML dla realnych danych prod.

Clock zamrozony na 2026-04-14T12:00:00Z. Snapshoty w tests/ksef/snapshots/
zregenerowane z tym clockiem (regresja po refaktorze CLI).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from core.ksef.adapters.xml_builder import XmlBuilder
from tests.ksef.fixtures.domain_samples import (
    make_fs_59, make_fs_60, make_fs_73, make_fsk_1,
)

_SNAP = Path(__file__).parent / "snapshots"
_CLOCK = lambda: datetime(2026, 4, 14, 12, 0, 0)


@pytest.fixture
def builder() -> XmlBuilder:
    return XmlBuilder(clock=_CLOCK)


def test_fs_59_snapshot(builder: XmlBuilder) -> None:
    actual = builder.build_faktura(make_fs_59())
    expected = (_SNAP / "fs_59.xml").read_bytes()
    assert actual == expected


def test_fs_60_snapshot(builder: XmlBuilder) -> None:
    actual = builder.build_faktura(make_fs_60())
    expected = (_SNAP / "fs_60.xml").read_bytes()
    assert actual == expected


def test_fs_73_snapshot(builder: XmlBuilder) -> None:
    actual = builder.build_faktura(make_fs_73())
    expected = (_SNAP / "fs_73.xml").read_bytes()
    assert actual == expected


def test_fsk_1_snapshot(builder: XmlBuilder) -> None:
    actual = builder.build_korekta(make_fsk_1())
    expected = (_SNAP / "fsk_1.xml").read_bytes()
    assert actual == expected


def test_snapshots_match_production_xml_structure() -> None:
    """Sanity check — snapshoty maja struktury zgodne z output/ksef/ (minus DataWytworzeniaFa)."""
    prod_root = Path(__file__).resolve().parents[2] / "ksef_api" / "demo" / "output"
    pairs = [
        ("fs_59.xml", "ksef_FS-59_04_26_SPKR_2026-04-14.xml"),
        ("fs_60.xml", "ksef_FS-60_04_26_SPKR_2026-04-14.xml"),
        ("fs_73.xml", "ksef_FS-73_04_26_FRA_2026-04-14.xml"),
        ("fsk_1.xml", "ksef_kor_FSK-1_04_26_SPKRK_2026-04-14.xml"),
    ]
    for snap_name, prod_name in pairs:
        snap = (_SNAP / snap_name).read_text(encoding="utf-8")
        prod = (prod_root / prod_name).read_text(encoding="utf-8")
        snap_stripped = _strip_data_wytworzenia(snap)
        prod_stripped = _strip_data_wytworzenia(prod)
        assert snap_stripped == prod_stripped, f"Mismatch: {snap_name} vs {prod_name}"


def _strip_data_wytworzenia(xml: str) -> str:
    import re
    return re.sub(r"<DataWytworzeniaFa>[^<]+</DataWytworzeniaFa>",
                  "<DataWytworzeniaFa>STRIPPED</DataWytworzeniaFa>", xml)
