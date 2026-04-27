"""Testy dla tools/lib/xl_client.py."""

from unittest.mock import MagicMock, patch

import pytest

from tools.lib.xl_client import XlClient


def _mock_session(response: dict | None = None) -> tuple[MagicMock, MagicMock]:
    client = MagicMock()
    client.send.return_value = response or {"ok": True, "data": {}}
    proxy = MagicMock(return_value=(client, 7))
    return client, proxy


class TestXlClientInvoke:
    def test_invoke_sends_correct_cmd(self):
        client, proxy = _mock_session()
        with patch("tools.lib.xl_client.xl_session.get", proxy):
            XlClient().invoke("XLNowyDokument", TrNTyp=524288)
        sent = client.send.call_args[0][0]
        assert sent["cmd"] == "invoke"
        assert sent["method"] == "XLNowyDokument"
        assert sent["sesja_id"] == 7
        assert sent["params"]["TrNTyp"] == 524288

    def test_invoke_always_sets_wersja(self):
        client, proxy = _mock_session()
        with patch("tools.lib.xl_client.xl_session.get", proxy):
            XlClient().invoke("XLNowyTowar")
        params = client.send.call_args[0][0]["params"]
        assert params["Wersja"] == 20251

    def test_invoke_extra_params_override_defaults(self):
        client, proxy = _mock_session()
        with patch("tools.lib.xl_client.xl_session.get", proxy):
            XlClient().invoke("XLNowyTowar", Wersja=99999)
        params = client.send.call_args[0][0]["params"]
        assert params["Wersja"] == 99999

    def test_invoke_returns_proxy_response(self):
        resp = {"ok": True, "data": {"GIDNumer": 123}}
        _, proxy = _mock_session(resp)
        with patch("tools.lib.xl_client.xl_session.get", proxy):
            result = XlClient().invoke("XLNowyTowar")
        assert result == resp


class TestXlClientTypedHelpers:
    def _invoke_args(self, method_call) -> dict:
        """Uruchamia method_call, zwraca sent dict."""
        client = MagicMock()
        client.send.return_value = {"ok": True, "data": {}}
        proxy = MagicMock(return_value=(client, 1))
        with patch("tools.lib.xl_client.xl_session.get", proxy):
            method_call(XlClient())
        return client.send.call_args[0][0]

    def test_dodaj_atrybut(self):
        sent = self._invoke_args(
            lambda c: c.dodaj_atrybut(16, 100, 1, "WAGA", "1.5")
        )
        assert sent["method"] == "XLDodajAtrybut"
        assert sent["params"]["GIDTyp"] == 16
        assert sent["params"]["Klasa"] == "WAGA"
        assert sent["params"]["Wartosc"] == "1.5"

    def test_nowy_dokument(self):
        sent = self._invoke_args(lambda c: c.nowy_dokument(524288))
        assert sent["method"] == "XLNowyDokument"
        assert sent["params"]["TrNTyp"] == 524288

    def test_nowy_dokument_zam(self):
        sent = self._invoke_args(lambda c: c.nowy_dokument_zam(ZamTyp=512))
        assert sent["method"] == "XLNowyDokumentZam"

    def test_transakcja_begin(self):
        sent = self._invoke_args(lambda c: c.transakcja(True))
        assert sent["method"] == "XLTransakcja"
        assert sent["params"]["Transakcja"] == 1

    def test_transakcja_commit(self):
        sent = self._invoke_args(lambda c: c.transakcja(False))
        assert sent["params"]["Transakcja"] == 0

    def test_nowy_kontrahent(self):
        sent = self._invoke_args(lambda c: c.nowy_kontrahent(KntAkronim="TEST"))
        assert sent["method"] == "XLNowyKontrahent"


class TestXlClientLogout:
    def test_logout_delegates_to_session(self):
        with patch("tools.lib.xl_client.xl_session.logout") as mock_logout:
            XlClient().logout()
        mock_logout.assert_called_once()
