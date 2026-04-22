"""KSeF email sender — SMTP multipart (HTML + plain text).

    sender = SmtpEmailSender(host, port, user, password, use_ssl=True)
    sender.send(to="biuro@ceim.pl", from_="raporty@ceim.pl",
                subject="[KSeF] Raport", html=html, plain=plain)
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_LOG = logging.getLogger("ksef.email")


class SmtpEmailSender:
    """Sends multipart email via SMTP. Supports SSL (port 465) and STARTTLS (port 587)."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        *,
        use_ssl: bool = True,
        timeout: float = 30.0,
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._use_ssl = use_ssl
        self._timeout = timeout

    def send(
        self,
        *,
        to: str,
        from_: str,
        subject: str,
        html: str,
        plain: str,
    ) -> None:
        """Send multipart email. Raises on failure."""
        msg = self._build_message(to=to, from_=from_, subject=subject,
                                   html=html, plain=plain)
        self._send_smtp(to, from_, msg)
        _LOG.info('{"event": "email_sent", "to": "%s", "subject": "%s"}',
                  to, subject[:80])

    def _build_message(
        self, *, to: str, from_: str, subject: str, html: str, plain: str,
    ) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_
        msg["To"] = to
        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
        return msg

    def _send_smtp(self, to: str, from_: str, msg: MIMEMultipart) -> None:
        if self._use_ssl:
            with smtplib.SMTP_SSL(self._host, self._port,
                                   timeout=self._timeout) as smtp:
                smtp.login(self._user, self._password)
                smtp.sendmail(from_, [to], msg.as_string())
        else:
            with smtplib.SMTP(self._host, self._port,
                              timeout=self._timeout) as smtp:
                smtp.starttls()
                smtp.login(self._user, self._password)
                smtp.sendmail(from_, [to], msg.as_string())
