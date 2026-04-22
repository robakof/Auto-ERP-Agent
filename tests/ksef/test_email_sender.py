"""Tests for email sender and report renderer."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.ksef.domain.shipment import ShipmentStatus, Wysylka
from core.ksef.usecases.report import ReportData
from core.ksef.adapters.report_renderer import render_subject, render_plain, render_html
from core.ksef.adapters.email_sender import SmtpEmailSender


# ---- helpers -----------------------------------------------------------------

def _wysylka(id=1, status=ShipmentStatus.ACCEPTED, error_msg=None, **kw):
    defaults = dict(
        id=id, gid_erp=100 + id, rodzaj="FS",
        nr_faktury=f"FS-{id}/04/26", data_wystawienia=date(2026, 4, 22),
        xml_path=f"out/ksef_{id}.xml", xml_hash=f"hash{id}",
        status=status,
        ksef_session_ref=None, ksef_invoice_ref=None, ksef_number=None,
        upo_path=None, error_code=None, error_msg=error_msg,
        attempt=1, created_at=datetime(2026, 4, 22, 10, 0),
        queued_at=None, sent_at=None, accepted_at=None,
        rejected_at=None, errored_at=None,
    )
    defaults.update(kw)
    return Wysylka(**defaults)


def _report(
    errors=None, rejected=None, pending=None, all_sent=True,
):
    counts = {s: 0 for s in ShipmentStatus}
    counts[ShipmentStatus.ACCEPTED] = 5
    if errors:
        counts[ShipmentStatus.ERROR] = len(errors)
    if rejected:
        counts[ShipmentStatus.REJECTED] = len(rejected)
    total = sum(counts.values())
    return ReportData(
        since=datetime(2026, 4, 22, 0, 0),
        generated_at=datetime(2026, 4, 22, 13, 30),
        counts=counts,
        total=total,
        errors=errors or [],
        rejected=rejected or [],
        pending=pending or [],
        all_sent_today=all_sent,
    )


# ---- renderer tests ----------------------------------------------------------

class TestRenderSubject:
    def test_all_ok(self):
        r = _report()
        subject = render_subject(r, prefix="[KSeF]")
        assert "[KSeF]" in subject
        assert "wszystkie wyslane" in subject
        assert "2026-04-22" in subject

    def test_with_errors(self):
        r = _report(
            errors=[_wysylka(1, ShipmentStatus.ERROR, error_msg="timeout")],
            all_sent=False,
        )
        subject = render_subject(r, prefix="[KSeF]")
        assert "x" in subject.lower() or "bledo" in subject.lower()

    def test_custom_prefix(self):
        r = _report()
        subject = render_subject(r, prefix="[KSeF Demo]")
        assert subject.startswith("[KSeF Demo]")


class TestRenderPlain:
    def test_contains_summary(self):
        r = _report()
        text = render_plain(r)
        assert "Zaakceptowane" in text
        assert "Razem" in text

    def test_all_sent_status(self):
        r = _report()
        text = render_plain(r)
        assert "WSZYSTKIE FAKTURY WYSLANE" in text

    def test_errors_listed(self):
        err = _wysylka(28, ShipmentStatus.ERROR, error_msg="API timeout")
        r = _report(errors=[err], all_sent=False)
        text = render_plain(r)
        assert "#28" in text
        assert "API timeout" in text

    def test_pending_listed(self):
        pending = _wysylka(5, ShipmentStatus.QUEUED)
        r = _report(pending=[pending], all_sent=False)
        text = render_plain(r)
        assert "Oczekujace" in text
        assert "QUEUED" in text


class TestRenderHtml:
    def test_is_html(self):
        r = _report()
        html = render_html(r)
        assert html.startswith("<html>")
        assert "</html>" in html

    def test_contains_status(self):
        r = _report()
        html = render_html(r)
        assert "WSZYSTKIE FAKTURY WYSLANE" in html
        assert "green" in html

    def test_errors_red(self):
        err = _wysylka(1, ShipmentStatus.ERROR, error_msg="fail")
        r = _report(errors=[err], all_sent=False)
        html = render_html(r)
        assert "red" in html
        assert "UWAGA" in html


# ---- email sender tests (mock SMTP) -----------------------------------------

class TestSmtpEmailSender:
    def test_send_ssl(self):
        with patch("core.ksef.adapters.email_sender.smtplib") as mock_lib:
            mock_smtp = MagicMock()
            mock_lib.SMTP_SSL.return_value.__enter__ = MagicMock(return_value=mock_smtp)
            mock_lib.SMTP_SSL.return_value.__exit__ = MagicMock(return_value=False)

            sender = SmtpEmailSender(
                host="smtp.test.pl", port=465,
                user="test@test.pl", password="pass",
                use_ssl=True,
            )
            sender.send(
                to="biuro@test.pl", from_="raporty@test.pl",
                subject="Test", html="<p>hi</p>", plain="hi",
            )

            mock_lib.SMTP_SSL.assert_called_once()
            mock_smtp.login.assert_called_once_with("test@test.pl", "pass")
            mock_smtp.sendmail.assert_called_once()

    def test_send_starttls(self):
        with patch("core.ksef.adapters.email_sender.smtplib") as mock_lib:
            mock_smtp = MagicMock()
            mock_lib.SMTP.return_value.__enter__ = MagicMock(return_value=mock_smtp)
            mock_lib.SMTP.return_value.__exit__ = MagicMock(return_value=False)

            sender = SmtpEmailSender(
                host="smtp.test.pl", port=587,
                user="test@test.pl", password="pass",
                use_ssl=False,
            )
            sender.send(
                to="biuro@test.pl", from_="raporty@test.pl",
                subject="Test", html="<p>hi</p>", plain="hi",
            )

            mock_lib.SMTP.assert_called_once()
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once()

    def test_build_message_multipart(self):
        sender = SmtpEmailSender(
            host="smtp.test.pl", port=465,
            user="test@test.pl", password="pass",
        )
        msg = sender._build_message(
            to="biuro@test.pl", from_="raporty@test.pl",
            subject="[KSeF] Test", html="<p>hi</p>", plain="hi",
        )
        assert msg["Subject"] == "[KSeF] Test"
        assert msg["To"] == "biuro@test.pl"
        assert msg["From"] == "raporty@test.pl"
        payloads = msg.get_payload()
        assert len(payloads) == 2  # plain + html
