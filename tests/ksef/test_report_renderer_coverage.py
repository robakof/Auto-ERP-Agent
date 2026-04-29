"""Tests for coverage section in report renderer."""
from __future__ import annotations

from datetime import date, datetime

import pytest

from core.ksef.adapters.erp_counter import EligibleDoc
from core.ksef.adapters.report_renderer import render_html, render_plain, render_subject
from core.ksef.domain.shipment import ShipmentStatus
from core.ksef.usecases.report import CoverageData, ReportData

_SINCE = datetime(2026, 4, 22, 0, 0)
_NOW = datetime(2026, 4, 22, 13, 30)


def _report(coverage: CoverageData | None = None) -> ReportData:
    return ReportData(
        since=_SINCE,
        generated_at=_NOW,
        counts={s: 0 for s in ShipmentStatus},
        total=0,
        errors=[],
        rejected=[],
        pending=[],
        all_sent_today=True,
        coverage=coverage,
    )


def _coverage(missing=None):
    return CoverageData(
        erp_counts={"FS": 5, "FSK": 2, "FSK_SKONTO": 1},
        ksef_counts={"FS": 5, "FSK": 1, "FSK_SKONTO": 1},
        missing=missing or [],
    )


def _eligible(gid, rodzaj="FSK"):
    return EligibleDoc(
        gid=gid, rodzaj=rodzaj,
        nr_faktury=f"{rodzaj}-{gid}/04/26/S",
        data_wystawienia=date(2026, 4, 22),
    )


# ---- plain text --------------------------------------------------------------

def test_plain_no_coverage():
    """When coverage is None, section absent."""
    text = render_plain(_report(coverage=None))
    assert "Pokrycie" not in text


def test_plain_coverage_table():
    cov = _coverage()
    text = render_plain(_report(coverage=cov))
    assert "Pokrycie Comarch vs KSeF" in text
    assert "FS" in text
    assert "FSK" in text


def test_plain_missing_listed():
    missing = [_eligible(42, "FSK")]
    cov = _coverage(missing=missing)
    text = render_plain(_report(coverage=cov))
    assert "Brakujace (1)" in text
    assert "GID=42" in text
    assert "FSK-42/04/26/S" in text


def test_plain_no_missing_section():
    cov = CoverageData(
        erp_counts={"FS": 3, "FSK": 0, "FSK_SKONTO": 0},
        ksef_counts={"FS": 3, "FSK": 0, "FSK_SKONTO": 0},
        missing=[],
    )
    text = render_plain(_report(coverage=cov))
    assert "Pokrycie" in text
    assert "Brakujace" not in text


# ---- HTML --------------------------------------------------------------------

def test_html_no_coverage():
    html = render_html(_report(coverage=None))
    assert "Pokrycie" not in html


def test_html_coverage_table():
    cov = _coverage()
    html = render_html(_report(coverage=cov))
    assert "Pokrycie Comarch vs KSeF" in html
    assert "<table" in html


def test_html_missing_red():
    missing = [_eligible(99)]
    cov = _coverage(missing=missing)
    html = render_html(_report(coverage=cov))
    assert "color:red" in html
    assert "GID=99" in html


def test_html_no_gap_green():
    cov = CoverageData(
        erp_counts={"FS": 3, "FSK": 0, "FSK_SKONTO": 0},
        ksef_counts={"FS": 3, "FSK": 0, "FSK_SKONTO": 0},
        missing=[],
    )
    html = render_html(_report(coverage=cov))
    assert "color:green" in html


# ---- subject + status --------------------------------------------------------

def test_subject_includes_missing():
    missing = [_eligible(1), _eligible(2)]
    cov = _coverage(missing=missing)
    report = _report(coverage=cov)
    subject = render_subject(report)
    assert "2 brakujacych" in subject


def test_status_includes_missing_plain():
    missing = [_eligible(1)]
    cov = _coverage(missing=missing)
    report = _report(coverage=cov)
    text = render_plain(report)
    assert "1 brakujacych" in text
    assert "UWAGA" in text
