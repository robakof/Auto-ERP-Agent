"""Testy dla tools/lib/xl_proxy_client.py."""

import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from tools.lib.xl_proxy_client import XlProxyClient, XlProxyError


def _make_proc(lines: list[str]) -> MagicMock:
    proc = MagicMock()
    proc.stdout.readline.side_effect = [l + "\n" for l in lines]
    proc.stdin = MagicMock()
    return proc


class TestXlProxyClientStart:
    def test_start_reads_ready_line(self):
        proc = _make_proc(['{"ok":true,"msg":"proxy ready"}'])
        with patch("tools.lib.xl_proxy_client.subprocess.Popen", return_value=proc):
            client = XlProxyClient("C:/dll")
            client.start()

    def test_start_raises_on_error_response(self):
        proc = _make_proc(['{"ok":false,"error":{"type":"LOAD_ERROR","message":"dll missing"}}'])
        with patch("tools.lib.xl_proxy_client.subprocess.Popen", return_value=proc):
            client = XlProxyClient("C:/dll")
            with pytest.raises(XlProxyError, match="start failed"):
                client.start()

    def test_start_raises_when_exe_missing(self):
        client = XlProxyClient("C:/dll")
        with patch("tools.lib.xl_proxy_client._PROXY_EXE") as mock_path:
            mock_path.exists.return_value = False
            with pytest.raises(XlProxyError, match="nie znaleziony"):
                client.start()


class TestXlProxyClientSend:
    def _started_client(self, responses: list[str]) -> XlProxyClient:
        ready = '{"ok":true,"msg":"proxy ready"}'
        proc = _make_proc([ready] + responses)
        with patch("tools.lib.xl_proxy_client.subprocess.Popen", return_value=proc):
            client = XlProxyClient("C:/dll")
            client.start()
        client._proc = proc
        return client

    def test_send_writes_json_line(self):
        client = self._started_client(['{"ok":true,"sesja_id":1}'])
        client.send({"cmd": "login", "baza": "TEST"})
        written = client._proc.stdin.write.call_args[0][0]
        parsed = json.loads(written.strip())
        assert parsed["cmd"] == "login"
        assert parsed["baza"] == "TEST"

    def test_send_returns_parsed_response(self):
        client = self._started_client(['{"ok":true,"sesja_id":42}'])
        result = client.send({"cmd": "login"})
        assert result["ok"] is True
        assert result["sesja_id"] == 42

    def test_send_raises_when_not_started(self):
        client = XlProxyClient("C:/dll")
        with pytest.raises(XlProxyError, match="nie uruchomiony"):
            client.send({"cmd": "login"})

    def test_send_raises_on_empty_stdout(self):
        client = self._started_client([""])
        client._proc.stdout.readline.side_effect = [""]
        with pytest.raises(XlProxyError, match="stdout"):
            client.send({"cmd": "login"})


class TestXlProxyClientStop:
    def test_stop_closes_stdin_and_waits(self):
        proc = _make_proc(['{"ok":true,"msg":"proxy ready"}'])
        with patch("tools.lib.xl_proxy_client.subprocess.Popen", return_value=proc):
            client = XlProxyClient("C:/dll")
            client.start()
        client.stop()
        proc.stdin.close.assert_called_once()
        proc.wait.assert_called_once()
        assert client._proc is None

    def test_stop_kills_on_timeout(self):
        proc = _make_proc(['{"ok":true,"msg":"proxy ready"}'])
        proc.wait.side_effect = Exception("timeout")
        with patch("tools.lib.xl_proxy_client.subprocess.Popen", return_value=proc):
            client = XlProxyClient("C:/dll")
            client.start()
        client.stop()
        proc.kill.assert_called_once()
