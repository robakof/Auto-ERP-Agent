import * as assert from "assert";
import * as path from "path";
import * as fs from "fs";
import * as os from "os";
import { MrowiskoDB } from "../db";

const SCHEMA = `
CREATE TABLE live_agents (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  claude_uuid     TEXT UNIQUE,
  session_id      TEXT UNIQUE,
  role            TEXT,
  terminal_name   TEXT,
  task            TEXT,
  status          TEXT NOT NULL DEFAULT 'starting',
  spawned_by      TEXT,
  spawn_token     TEXT UNIQUE,
  last_activity   TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  stopped_at      TEXT,
  transcript_path TEXT,
  CHECK (status IN ('starting', 'active', 'stopped'))
);

CREATE TABLE invocations (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  invoker_type    TEXT NOT NULL,
  invoker_id      TEXT NOT NULL,
  target_role     TEXT NOT NULL,
  task            TEXT NOT NULL,
  session_id      TEXT,
  status          TEXT NOT NULL DEFAULT 'pending',
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  ended_at        TEXT,
  action          TEXT NOT NULL DEFAULT 'spawn',
  target_session_id TEXT,
  CHECK (invoker_type IN ('human', 'agent', 'orchestrator')),
  CHECK (status IN ('pending', 'approved', 'running', 'completed', 'failed', 'rejected'))
);
`;

function createTestDb(): { db: MrowiskoDB; dbPath: string } {
  const dbPath = path.join(os.tmpdir(), `mrowisko_test_${Date.now()}.db`);
  // Create DB with schema using raw better-sqlite3
  const Database = require("better-sqlite3");
  const raw = new Database(dbPath);
  raw.exec(SCHEMA);
  raw.close();
  return { db: new MrowiskoDB(dbPath), dbPath };
}

function cleanup(dbPath: string): void {
  try { fs.unlinkSync(dbPath); } catch {}
}

describe("MrowiskoDB", () => {
  let db: MrowiskoDB;
  let dbPath: string;

  beforeEach(() => {
    const t = createTestDb();
    db = t.db;
    dbPath = t.dbPath;
  });

  afterEach(() => {
    db.dispose();
    cleanup(dbPath);
  });

  describe("constructor", () => {
    it("rejects relative path", () => {
      assert.throws(() => new MrowiskoDB("mrowisko.db"), /must be absolute/);
    });
  });

  describe("insertAgent + getActiveAgents", () => {
    it("inserts and retrieves agent", () => {
      db.insertAgent("token-1", "developer", "check backlog", "Agent: developer", "human");
      const agents = db.getActiveAgents();
      assert.strictEqual(agents.length, 1);
      assert.strictEqual(agents[0].role, "developer");
      assert.strictEqual(agents[0].task, "check backlog");
      assert.strictEqual(agents[0].status, "starting");
      assert.strictEqual(agents[0].spawnToken, "token-1");
    });

    it("does not return stopped agents", () => {
      db.insertAgent("token-1", "developer", "task", "Agent: developer", "human");
      db.insertAgent("token-2", "analyst", "task2", "Agent: analyst", "human");
      // Manually stop one via raw SQL (simulate session link + stop)
      const Database = require("better-sqlite3");
      const raw = new Database(dbPath, { readonly: false });
      raw.prepare("UPDATE live_agents SET session_id = 'sess-1' WHERE spawn_token = 'token-1'").run();
      raw.close();

      db.markStopped("sess-1");
      const agents = db.getActiveAgents();
      assert.strictEqual(agents.length, 1);
      assert.strictEqual(agents[0].role, "analyst");
    });
  });

  describe("markStopped", () => {
    it("sets status and stopped_at", () => {
      db.insertAgent("token-1", "dev", "task", "Agent: dev", "human");
      const Database = require("better-sqlite3");
      const raw = new Database(dbPath, { readonly: false });
      raw.prepare("UPDATE live_agents SET session_id = 'sess-1' WHERE spawn_token = 'token-1'").run();
      raw.close();

      db.markStopped("sess-1");
      const agents = db.getActiveAgents();
      assert.strictEqual(agents.length, 0);
    });
  });

  describe("getSpawnTokenBySessionId", () => {
    it("returns spawn_token for known session", () => {
      db.insertAgent("token-abc", "dev", "task", "Agent: dev", "human");
      const Database = require("better-sqlite3");
      const raw = new Database(dbPath, { readonly: false });
      raw.prepare("UPDATE live_agents SET session_id = 'sess-xyz' WHERE spawn_token = 'token-abc'").run();
      raw.close();

      assert.strictEqual(db.getSpawnTokenBySessionId("sess-xyz"), "token-abc");
    });

    it("returns null for unknown session", () => {
      assert.strictEqual(db.getSpawnTokenBySessionId("nonexistent"), null);
    });
  });

  describe("invocations", () => {
    it("getPendingInvocations returns pending only", () => {
      const Database = require("better-sqlite3");
      const raw = new Database(dbPath, { readonly: false });
      raw.prepare(
        "INSERT INTO invocations (invoker_type, invoker_id, target_role, task, status) VALUES (?, ?, ?, ?, ?)"
      ).run("agent", "developer", "analyst", "review data", "pending");
      raw.prepare(
        "INSERT INTO invocations (invoker_type, invoker_id, target_role, task, status) VALUES (?, ?, ?, ?, ?)"
      ).run("agent", "developer", "erp_specialist", "done", "approved");
      raw.close();

      const pending = db.getPendingInvocations();
      assert.strictEqual(pending.length, 1);
      assert.strictEqual(pending[0].target_role, "analyst");
    });

    it("approveInvocation changes status", () => {
      const Database = require("better-sqlite3");
      const raw = new Database(dbPath, { readonly: false });
      raw.prepare(
        "INSERT INTO invocations (invoker_type, invoker_id, target_role, task) VALUES (?, ?, ?, ?)"
      ).run("human", "user", "developer", "spawn dev");
      raw.close();

      const pending = db.getPendingInvocations();
      assert.strictEqual(pending.length, 1);

      db.approveInvocation(pending[0].id);
      assert.strictEqual(db.getPendingInvocations().length, 0);
    });

    it("rejectInvocation changes status", () => {
      const Database = require("better-sqlite3");
      const raw = new Database(dbPath, { readonly: false });
      raw.prepare(
        "INSERT INTO invocations (invoker_type, invoker_id, target_role, task) VALUES (?, ?, ?, ?)"
      ).run("human", "user", "developer", "spawn dev");
      raw.close();

      const pending = db.getPendingInvocations();
      db.rejectInvocation(pending[0].id);
      assert.strictEqual(db.getPendingInvocations().length, 0);
    });
  });

  describe("cleanup", () => {
    it("marks stale agents as stopped", () => {
      db.insertAgent("token-1", "dev", "task", "Agent: dev", "human");
      // Set last_activity to 2 hours ago
      const Database = require("better-sqlite3");
      const raw = new Database(dbPath, { readonly: false });
      raw.prepare(
        "UPDATE live_agents SET last_activity = datetime('now', '-120 minutes') WHERE spawn_token = 'token-1'"
      ).run();
      raw.close();

      db.cleanup(60);
      assert.strictEqual(db.getActiveAgents().length, 0);
    });
  });
});
