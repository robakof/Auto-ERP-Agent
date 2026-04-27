"""Testy dla tools/lib/xl_session.py."""

from unittest.mock import MagicMock, patch

import pytest

import tools.lib.xl_session as xl_session
from tools.lib.xl_proxy_client import XlProxyError


def _mock_client(login_ok: bool = True, sesja_id: int = 7) -> MagicMock:
    client = MagicMock()
    if login_ok:
        client.send.return_value = {"ok": True, "sesja_id": sesja_id}
    else:
        client.send.return_value = {"ok": False, "error": {"type": "LOGIN_FAIL", "message": "bad"}}
    return client


@pytest.fixture(autouse=True)
def reset_session():
    """Resetuje singleton przed każdym testem."""
    xl_session._client = None
    xl_session._sesja_id = 0
    yield
    xl_session._client = None
    xl_session._sesja_id = 0


class TestXlSessionGet:
    def test_lazy_login_on_first_get(self):
        mock = _mock_client(sesja_id=42)
        with patch("tools.lib.xl_session.XlProxyClient", return_value=mock):
            client, sid = xl_session.get()
        assert sid == 42
        mock.start.assert_called_once()

    def test_singleton_returns_same_client(self):
        mock = _mock_client(sesja_id=5)
        with patch("tools.lib.xl_session.XlProxyClient", return_value=mock):
            c1, s1 = xl_session.get()
            c2, s2 = xl_session.get()
        assert c1 is c2
        assert s1 == s2
        mock.start.assert_called_once()

    def test_raises_on_login_fail(self):
        mock = _mock_client(login_ok=False)
        with patch("tools.lib.xl_session.XlProxyClient", return_value=mock):
            with pytest.raises(XlProxyError, match="login failed"):
                xl_session.get()
        mock.stop.assert_called_once()


class TestXlSessionLogout:
    def test_logout_sends_logout_and_stops(self):
        mock = _mock_client(sesja_id=3)
        with patch("tools.lib.xl_session.XlProxyClient", return_value=mock):
            xl_session.get()
        xl_session.logout()
        mock.send.assert_called_with({"cmd": "logout", "sesja_id": 3})
        mock.stop.assert_called_once()
        assert xl_session._client is None
        assert xl_session._sesja_id == 0

    def test_logout_noop_when_not_logged_in(self):
        xl_session.logout()  # nie powinno rzucić wyjątku

    def test_after_logout_get_triggers_new_login(self):
        mock = _mock_client(sesja_id=9)
        with patch("tools.lib.xl_session.XlProxyClient", return_value=mock):
            xl_session.get()
            xl_session.logout()
            xl_session.get()
        assert mock.start.call_count == 2
