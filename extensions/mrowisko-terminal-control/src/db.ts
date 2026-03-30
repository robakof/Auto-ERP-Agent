import Database from "better-sqlite3";
import * as path from "path";
import { LiveAgent, PendingInvocation } from "./types";

interface DbRow {
  id: number;
  claude_uuid: string | null;
  session_id: string | null;
  role: string | null;
  task: string | null;
  terminal_name: string | null;
  status: string;
  spawned_by: string | null;
  spawn_token: string | null;
  created_at: string;
  last_activity: string | null;
  stopped_at: string | null;
  transcript_path: string | null;
}

function rowToLiveAgent(row: DbRow): LiveAgent {
  return {
    id: row.id,
    sessionId: row.session_id,
    claudeUuid: row.claude_uuid,
    role: row.role,
    task: row.task,
    terminalName: row.terminal_name,
    status: row.status as LiveAgent["status"],
    spawnedBy: row.spawned_by,
    spawnToken: row.spawn_token,
    createdAt: row.created_at,
    lastActivity: row.last_activity,
    stoppedAt: row.stopped_at,
    transcriptPath: row.transcript_path,
  };
}

export class MrowiskoDB {
  private db: Database.Database;

  constructor(dbPath: string) {
    if (!path.isAbsolute(dbPath)) {
      throw new Error(`dbPath must be absolute, got: ${dbPath}`);
    }
    this.db = new Database(dbPath, { readonly: false });
    this.db.pragma("busy_timeout = 3000");
    this.db.pragma("journal_mode = WAL");
  }

  getActiveAgents(): LiveAgent[] {
    const rows = this.db.prepare(
      "SELECT * FROM live_agents WHERE status IN ('starting', 'active')"
    ).all() as DbRow[];
    return rows.map(rowToLiveAgent);
  }

  getPendingInvocations(): PendingInvocation[] {
    return this.db.prepare(
      "SELECT * FROM invocations WHERE status = 'pending' ORDER BY created_at"
    ).all() as PendingInvocation[];
  }

  approveInvocation(id: number): void {
    this.db.prepare(
      "UPDATE invocations SET status = 'approved' WHERE id = ?"
    ).run(id);
  }

  rejectInvocation(id: number): void {
    this.db.prepare(
      "UPDATE invocations SET status = 'rejected' WHERE id = ?"
    ).run(id);
  }

  insertAgent(
    spawnToken: string,
    role: string,
    task: string,
    terminalName: string,
    spawnedBy: string
  ): void {
    this.db.prepare(
      `INSERT INTO live_agents (spawn_token, role, task, terminal_name, spawned_by, status, created_at)
       VALUES (?, ?, ?, ?, ?, 'starting', datetime('now'))`
    ).run(spawnToken, role, task, terminalName, spawnedBy);
  }

  markStopped(sessionId: string): void {
    this.db.prepare(
      "UPDATE live_agents SET status = 'stopped', stopped_at = datetime('now') WHERE session_id = ?"
    ).run(sessionId);
  }

  getSpawnTokenBySessionId(sessionId: string): string | null {
    const row = this.db.prepare(
      "SELECT spawn_token FROM live_agents WHERE session_id = ?"
    ).get(sessionId) as { spawn_token: string } | undefined;
    return row?.spawn_token ?? null;
  }

  cleanup(thresholdMinutes: number = 60): void {
    this.db.prepare(
      `UPDATE live_agents SET status = 'stopped', stopped_at = datetime('now')
       WHERE status IN ('starting', 'active')
       AND last_activity < datetime('now', '-' || ? || ' minutes')`
    ).run(thresholdMinutes);
  }

  dispose(): void {
    this.db.close();
  }
}
