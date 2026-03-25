"""AgentBus HTTP server — read-only API over mrowisko.db for renderers and human oversight.

Run: python tools/agent_bus_server.py
Docs: http://localhost:8765/docs
"""

import sys
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.agent_bus import AgentBus

DB_PATH = "mrowisko.db"

app = FastAPI(
    title="AgentBus API",
    description="Read-only HTTP interface for mrowisko.db",
    version="1.0",
)


def get_bus() -> AgentBus:
    return AgentBus(db_path=DB_PATH)


@app.get("/backlog")
def backlog(
    status: Optional[str] = Query(None, description="planned|in_progress|done|cancelled"),
    area: Optional[str] = Query(None, description="Bot|Arch|Dev|ERP|..."),
):
    items = get_bus().get_backlog(status=status)
    if area:
        items = [i for i in items if i.get("area") == area]
    return {"data": items, "count": len(items)}


@app.get("/suggestions")
def suggestions(
    status: Optional[str] = Query(None, description="open|rejected|implemented|deferred"),
    author: Optional[str] = Query(None, description="erp_specialist|analyst|developer|metodolog"),
):
    items = get_bus().get_suggestions(status=status, author=author)
    return {"data": items, "count": len(items)}


@app.get("/inbox")
def inbox(
    role: str = Query(..., description="developer|human|erp_specialist|analyst|metodolog"),
    status: str = Query("unread", description="unread|read|archived"),
):
    items = get_bus().get_inbox(role=role, status=status)
    return {"data": items, "count": len(items)}


@app.get("/session-log")
def session_log(
    role: str = Query(..., description="developer|erp_specialist|analyst|metodolog"),
    limit: int = Query(20, ge=1, le=200),
):
    items = get_bus().get_session_log(role=role, limit=limit)
    return {"data": items, "count": len(items)}


@app.get("/messages")
def messages(
    recipient: str = Query(...),
    status: str = Query("unread", description="unread|read|archived"),
):
    items = get_bus().get_inbox(role=recipient, status=status)
    return {"data": items, "count": len(items)}


@app.get("/health")
def health():
    return {"ok": True, "db": DB_PATH}


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8765)
