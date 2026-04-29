"""KSeF report renderer — builds HTML and plain text from ReportData.

No template engine. Python f-strings + loops. Zero external deps.
"""
from __future__ import annotations

from core.ksef.domain.shipment import ShipmentStatus, Wysylka
from core.ksef.usecases.report import CoverageData, ReportData


def render_subject(report: ReportData, prefix: str = "[KSeF]") -> str:
    """Email subject line with status indicator."""
    date_str = report.since.strftime("%Y-%m-%d")
    if report.has_problems:
        n_err = len(report.errors) + len(report.rejected)
        n_pending = len(report.pending)
        n_missing = report.coverage.total_missing if report.coverage else 0
        parts = []
        if n_err:
            parts.append(f"{n_err} bledow")
        if n_pending:
            parts.append(f"{n_pending} oczekujacych")
        if n_missing:
            parts.append(f"{n_missing} brakujacych")
        detail = ", ".join(parts)
        return f"{prefix} Raport {date_str} — x {detail}"
    return f"{prefix} Raport {date_str} — wszystkie wyslane"


def render_plain(report: ReportData) -> str:
    """Plain text report body."""
    lines = [
        _header_plain(report),
        _status_line(report),
        "",
        _counts_plain(report),
    ]
    if report.errors:
        lines.append(_errors_plain(report.errors, "Bledy"))
    if report.rejected:
        lines.append(_errors_plain(report.rejected, "Odrzucone"))
    if report.pending:
        lines.append(_pending_plain(report.pending))
    if report.coverage is not None:
        lines.append(_coverage_plain(report.coverage))
    lines.append(_footer_plain(report))
    return "\n".join(lines)


def render_html(report: ReportData) -> str:
    """HTML report body — readable on mobile."""
    return (
        "<html><body style='font-family:monospace;font-size:14px;"
        "max-width:600px;margin:0 auto;padding:16px'>"
        f"{_header_html(report)}"
        f"{_status_html(report)}"
        f"{_counts_html(report)}"
        f"{_errors_html(report.errors, 'Bledy') if report.errors else ''}"
        f"{_errors_html(report.rejected, 'Odrzucone') if report.rejected else ''}"
        f"{_pending_html(report.pending) if report.pending else ''}"
        f"{_coverage_html(report.coverage) if report.coverage is not None else ''}"
        f"{_footer_html(report)}"
        "</body></html>"
    )


# ---- plain text builders -----------------------------------------------------

def _header_plain(r: ReportData) -> str:
    date_str = r.since.strftime("%Y-%m-%d")
    return (
        f"{'=' * 45}\n"
        f"  KSeF — podsumowanie dnia {date_str}\n"
        f"{'=' * 45}\n"
    )


def _status_line(r: ReportData) -> str:
    if not r.has_problems:
        return "  Status dnia: WSZYSTKIE FAKTURY WYSLANE"
    parts = []
    if r.errors:
        parts.append(f"{len(r.errors)} bledow")
    if r.rejected:
        parts.append(f"{len(r.rejected)} odrzuconych")
    if r.pending:
        parts.append(f"{len(r.pending)} oczekujacych")
    if r.coverage and r.coverage.has_gap:
        parts.append(f"{r.coverage.total_missing} brakujacych")
    detail = ", ".join(parts)
    return f"  Status dnia: UWAGA: {detail}!"


def _counts_plain(r: ReportData) -> str:
    lines = ["  -- Wysylki dnia ---------------------"]
    order = [
        (ShipmentStatus.ACCEPTED, "Zaakceptowane"),
        (ShipmentStatus.SENT, "Wyslane"),
        (ShipmentStatus.QUEUED, "Oczekujace"),
        (ShipmentStatus.ERROR, "Bledy"),
        (ShipmentStatus.REJECTED, "Odrzucone"),
    ]
    for status, label in order:
        count = r.counts.get(status, 0)
        lines.append(f"  {label + ':':<25} {count:>4}")
    lines.append(f"  {'-' * 37}")
    lines.append(f"  {'Razem:':<25} {r.total:>4}")
    lines.append("")
    return "\n".join(lines)


def _errors_plain(items: list[Wysylka], title: str) -> str:
    lines = [f"  -- {title} ({len(items)}) -------------------"]
    for w in items:
        msg = (w.error_msg or "brak opisu")[:60]
        lines.append(f"  #{w.id:<4} {w.nr_faktury:<20} GID={w.gid_erp}  {msg}")
    lines.append("")
    return "\n".join(lines)


def _pending_plain(items: list[Wysylka]) -> str:
    lines = [f"  -- Oczekujace ({len(items)}) -----------------"]
    for w in items:
        lines.append(
            f"  #{w.id:<4} {w.nr_faktury:<20} GID={w.gid_erp}  "
            f"status={w.status.value}"
        )
    lines.append("")
    return "\n".join(lines)


def _coverage_plain(c: CoverageData) -> str:
    lines = ["  -- Pokrycie Comarch vs KSeF -----------"]
    lines.append(f"  {'Typ':<14} {'Comarch':>7}  {'KSeF':>4}  {'Brak':>4}")
    for r in ("FS", "FSK", "FSK_SKONTO"):
        erp = c.erp_counts.get(r, 0)
        ksef = c.ksef_counts.get(r, 0)
        miss = erp - ksef
        lines.append(f"  {r:<14} {erp:>7}  {ksef:>4}  {miss:>4}")
    lines.append(f"  {'-' * 37}")
    lines.append(
        f"  {'Razem':<14} {c.total_erp:>7}  {c.total_ksef:>4}  {c.total_missing:>4}"
    )
    lines.append("")
    if c.missing:
        lines.append(f"  -- Brakujace ({c.total_missing}) ----------------------")
        for doc in c.missing:
            lines.append(f"  GID={doc.gid:<6} {doc.nr_faktury}")
        lines.append("")
    return "\n".join(lines)


def _footer_plain(r: ReportData) -> str:
    gen = r.generated_at.strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"{'=' * 45}\n"
        f"  Wygenerowano: {gen}\n"
        f"{'=' * 45}"
    )


# ---- HTML builders -----------------------------------------------------------

def _header_html(r: ReportData) -> str:
    date_str = r.since.strftime("%Y-%m-%d")
    return (
        f"<h2 style='border-bottom:2px solid #333;padding-bottom:8px'>"
        f"KSeF — podsumowanie dnia {date_str}</h2>"
    )


def _status_html(r: ReportData) -> str:
    if not r.has_problems:
        return (
            "<p style='color:green;font-weight:bold;font-size:16px'>"
            "Status: WSZYSTKIE FAKTURY WYSLANE</p>"
        )
    parts = []
    if r.errors:
        parts.append(f"{len(r.errors)} bledow")
    if r.rejected:
        parts.append(f"{len(r.rejected)} odrzuconych")
    if r.pending:
        parts.append(f"{len(r.pending)} oczekujacych")
    if r.coverage and r.coverage.has_gap:
        parts.append(f"{r.coverage.total_missing} brakujacych")
    detail = ", ".join(parts)
    return (
        f"<p style='color:red;font-weight:bold;font-size:16px'>"
        f"Status: UWAGA — {detail}!</p>"
    )


def _counts_html(r: ReportData) -> str:
    order = [
        (ShipmentStatus.ACCEPTED, "Zaakceptowane"),
        (ShipmentStatus.SENT, "Wyslane"),
        (ShipmentStatus.QUEUED, "Oczekujace"),
        (ShipmentStatus.ERROR, "Bledy"),
        (ShipmentStatus.REJECTED, "Odrzucone"),
    ]
    rows = ""
    for status, label in order:
        count = r.counts.get(status, 0)
        color = "red" if status in (ShipmentStatus.ERROR, ShipmentStatus.REJECTED) and count > 0 else "#333"
        rows += f"<tr><td>{label}</td><td style='text-align:right;color:{color}'>{count}</td></tr>"
    rows += (
        f"<tr style='border-top:1px solid #999;font-weight:bold'>"
        f"<td>Razem</td><td style='text-align:right'>{r.total}</td></tr>"
    )
    return (
        "<h3>Wysylki dnia</h3>"
        "<table style='border-collapse:collapse;width:100%'>"
        f"{rows}</table>"
    )


def _errors_html(items: list[Wysylka], title: str) -> str:
    rows = ""
    for w in items:
        msg = (w.error_msg or "brak opisu")[:60]
        rows += (
            f"<tr><td>#{w.id}</td><td>{w.nr_faktury}</td>"
            f"<td>GID={w.gid_erp}</td><td>{msg}</td></tr>"
        )
    return (
        f"<h3 style='color:red'>{title} ({len(items)})</h3>"
        f"<table style='border-collapse:collapse;width:100%;font-size:13px'>"
        f"{rows}</table>"
    )


def _pending_html(items: list[Wysylka]) -> str:
    rows = ""
    for w in items:
        rows += (
            f"<tr><td>#{w.id}</td><td>{w.nr_faktury}</td>"
            f"<td>GID={w.gid_erp}</td><td>{w.status.value}</td></tr>"
        )
    return (
        f"<h3 style='color:orange'>Oczekujace ({len(items)})</h3>"
        f"<table style='border-collapse:collapse;width:100%;font-size:13px'>"
        f"{rows}</table>"
    )


def _coverage_html(c: CoverageData) -> str:
    color = "red" if c.has_gap else "green"
    title = f"<h3 style='color:{color}'>Pokrycie Comarch vs KSeF</h3>"
    rows = ""
    for r in ("FS", "FSK", "FSK_SKONTO"):
        erp = c.erp_counts.get(r, 0)
        ksef = c.ksef_counts.get(r, 0)
        miss = erp - ksef
        rc = "red" if miss > 0 else "#333"
        rows += (
            f"<tr><td>{r}</td>"
            f"<td style='text-align:right'>{erp}</td>"
            f"<td style='text-align:right'>{ksef}</td>"
            f"<td style='text-align:right;color:{rc};font-weight:bold'>{miss}</td></tr>"
        )
    rows += (
        f"<tr style='border-top:1px solid #999;font-weight:bold'>"
        f"<td>Razem</td>"
        f"<td style='text-align:right'>{c.total_erp}</td>"
        f"<td style='text-align:right'>{c.total_ksef}</td>"
        f"<td style='text-align:right;color:{color}'>{c.total_missing}</td></tr>"
    )
    table = (
        "<table style='border-collapse:collapse;width:100%'>"
        "<tr style='border-bottom:1px solid #999'>"
        "<th style='text-align:left'>Typ</th>"
        "<th style='text-align:right'>Comarch</th>"
        "<th style='text-align:right'>KSeF</th>"
        "<th style='text-align:right'>Brak</th></tr>"
        f"{rows}</table>"
    )
    missing_html = ""
    if c.missing:
        m_rows = ""
        for doc in c.missing:
            m_rows += f"<tr><td>GID={doc.gid}</td><td>{doc.nr_faktury}</td></tr>"
        missing_html = (
            f"<h3 style='color:red'>Brakujace ({c.total_missing})</h3>"
            f"<table style='border-collapse:collapse;width:100%;font-size:13px'>"
            f"{m_rows}</table>"
        )
    return title + table + missing_html


def _footer_html(r: ReportData) -> str:
    gen = r.generated_at.strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"<hr style='margin-top:16px'>"
        f"<p style='color:#666;font-size:12px'>Wygenerowano: {gen}</p>"
    )
