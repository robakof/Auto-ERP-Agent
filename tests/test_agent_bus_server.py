"""Tests for agent_bus_server — FastAPI endpoints over mrowisko.db."""

import pytest
from fastapi.testclient import TestClient

from tools.lib.agent_bus import AgentBus


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient with isolated DB."""
    db_path = str(tmp_path / "test_server.db")
    monkeypatch.setattr("tools.agent_bus_server.DB_PATH", db_path)

    from tools.agent_bus_server import app
    return TestClient(app), AgentBus(db_path=db_path)


class TestHealth:
    def test_health(self, client):
        c, _ = client
        r = c.get("/health")
        assert r.status_code == 200
        assert r.json()["ok"] is True


class TestBacklog:
    def test_empty(self, client):
        c, _ = client
        r = c.get("/backlog")
        assert r.status_code == 200
        assert r.json()["count"] == 0

    def test_returns_items(self, client):
        c, bus = client
        bus.add_backlog_item("Fix bot", "opis", area="Bot", value="wysoka")
        bus.add_backlog_item("Fix arch", "opis", area="Arch")
        r = c.get("/backlog")
        assert r.json()["count"] == 2

    def test_filter_status(self, client):
        c, bus = client
        bus.add_backlog_item("planned", "opis")
        bid = bus.add_backlog_item("done", "opis")
        bus.update_backlog_status(bid, "done")
        r = c.get("/backlog?status=planned")
        assert r.json()["count"] == 1
        assert r.json()["data"][0]["title"] == "planned"

    def test_filter_area(self, client):
        c, bus = client
        bus.add_backlog_item("bot task", "opis", area="Bot")
        bus.add_backlog_item("arch task", "opis", area="Arch")
        r = c.get("/backlog?area=Bot")
        assert r.json()["count"] == 1
        assert r.json()["data"][0]["area"] == "Bot"


class TestSuggestions:
    def test_empty(self, client):
        c, _ = client
        r = c.get("/suggestions")
        assert r.status_code == 200
        assert r.json()["count"] == 0

    def test_returns_suggestions(self, client):
        c, bus = client
        bus.add_suggestion("erp_specialist", "sugestia 1")
        bus.add_suggestion("analyst", "sugestia 2")
        r = c.get("/suggestions")
        assert r.json()["count"] == 2

    def test_filter_status(self, client):
        c, bus = client
        bus.add_suggestion("erp_specialist", "otwarta")
        sid = bus.add_suggestion("analyst", "wdrożona")
        bus.update_suggestion_status(sid, "implemented")
        r = c.get("/suggestions?status=open")
        assert r.json()["count"] == 1

    def test_filter_author(self, client):
        c, bus = client
        bus.add_suggestion("erp_specialist", "moja")
        bus.add_suggestion("analyst", "inna")
        r = c.get("/suggestions?author=erp_specialist")
        assert r.json()["count"] == 1
        assert r.json()["data"][0]["author"] == "erp_specialist"


class TestInbox:
    def test_empty(self, client):
        c, _ = client
        r = c.get("/inbox?role=developer")
        assert r.status_code == 200
        assert r.json()["count"] == 0

    def test_returns_messages(self, client):
        c, bus = client
        bus.send_message("erp_specialist", "developer", "wiadomość")
        r = c.get("/inbox?role=developer")
        assert r.json()["count"] == 1

    def test_filter_by_role(self, client):
        c, bus = client
        bus.send_message("erp_specialist", "developer", "dla dev")
        bus.send_message("erp_specialist", "human", "dla human")
        r = c.get("/inbox?role=developer")
        assert r.json()["count"] == 1


class TestSessionLog:
    def test_empty(self, client):
        c, _ = client
        r = c.get("/session-log?role=developer")
        assert r.status_code == 200
        assert r.json()["count"] == 0

    def test_returns_logs(self, client):
        c, bus = client
        bus.add_session_log("developer", "wpis 1")
        bus.add_session_log("developer", "wpis 2")
        r = c.get("/session-log?role=developer")
        assert r.json()["count"] == 2

    def test_limit(self, client):
        c, bus = client
        for i in range(10):
            bus.add_session_log("developer", f"wpis {i}")
        r = c.get("/session-log?role=developer&limit=3")
        assert r.json()["count"] == 3
