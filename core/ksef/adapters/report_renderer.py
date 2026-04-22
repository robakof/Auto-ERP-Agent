"""KSeF report renderer — builds HTML and plain text from ReportData.

No template engine. Python f-strings + loops. Zero external deps.
"""
from __future__ import annotations

from core.ksef.domain.shipment import ShipmentStatus, Wysylka
from core.ksef.usecases.report import ReportData


def render_subject(report: ReportData, prefix: str = "[KSeF]") -> str:
    """Email subject line with status indicator."""
    date_str = report.since.strftime("%Y-%m-%d")
    if report.has_problems:
        n_err = len(report.errors) + len(report.rejected)
        n_pending = len(report.pending)
        parts = []
        if n_err:
            parts.append(f"{n_err} bledow")
        if n_pending:
            parts.append(f"{n_pending} oczekujacych")
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
    if r.all_sent_today:
        return "  Status dnia: WSZYSTKIE FAKTURY WYSLANE"
    parts = []
    if r.errors:
        parts.append(f"{len(r.errors)} bledow")
    if r.rejected:
        parts.append(f"{len(r.rejected)} odrzuconych")
    if r.pending:
        parts.append(f"{len(r.pending)} oczekujacych")
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
    if r.all_sent_today:
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


def _footer_html(r: ReportData) -> str:
    gen = r.generated_at.strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"<hr style='margin-top:16px'>"
        f"<p style='color:#666;font-size:12px'>Wygenerowano: {gen}</p>"
    )
