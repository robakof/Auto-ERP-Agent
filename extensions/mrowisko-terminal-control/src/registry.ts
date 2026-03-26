import Database from "better-sqlite3";
import { LiveAgent, LiveAgentRow, rowToLiveAgent } from "./types";

export class Registry {
  private db: Database.Database;

  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.db.pragma("journal_mode = WAL");
    this.db.pragma("foreign_keys = ON");
    this.db.pragma("busy_timeout = 3000");
  }

  /** Pre-register agent before terminal spawn (status='starting'). */
  insert(
    sessionId: string,
    role: string,
    task: string,
    terminalName: string,
    permissionMode: string,
    spawnedBy: string
  ): void {
    this.db
      .prepare(
        `INSERT INTO live_agents (session_id, role, task, terminal_name, status, permission_mode, spawned_by)
         VALUES (?, ?, ?, ?, 'starting', ?, ?)`
      )
      .run(sessionId, role, task, terminalName, permissionMode, spawnedBy);
  }

  /** Get all agents with given status (or all if not specified). */
  getActiveAgents(): LiveAgent[] {
    const rows = this.db
      .prepare(
        "SELECT * FROM live_agents WHERE status IN ('starting', 'active') ORDER BY created_at DESC"
      )
      .all() as LiveAgentRow[];
    return rows.map(rowToLiveAgent);
  }

  getAgentBySessionId(sessionId: string): LiveAgent | null {
    const row = this.db
      .prepare("SELECT * FROM live_agents WHERE session_id = ?")
      .get(sessionId) as LiveAgentRow | undefined;
    return row ? rowToLiveAgent(row) : null;
  }

  getAgentsByRole(role: string): LiveAgent[] {
    const rows = this.db
      .prepare(
        "SELECT * FROM live_agents WHERE role = ? AND status IN ('starting', 'active') ORDER BY created_at DESC"
      )
      .all(role) as LiveAgentRow[];
    return rows.map(rowToLiveAgent);
  }

  updateStatus(
    sessionId: string,
    status: LiveAgent["status"]
  ): void {
    this.db
      .prepare("UPDATE live_agents SET status = ? WHERE session_id = ?")
      .run(status, sessionId);
  }

  /** Mark stopped + set stopped_at for a specific agent. */
  markStopped(sessionId: string): void {
    this.db
      .prepare(
        "UPDATE live_agents SET status = 'stopped', stopped_at = datetime('now') WHERE session_id = ? AND status != 'stopped'"
      )
      .run(sessionId);
  }

  /** Cleanup orphaned agents (starting/active but no terminal). */
  cleanup(): void {
    this.db
      .prepare(
        "UPDATE live_agents SET status = 'stopped', stopped_at = datetime('now') WHERE status IN ('starting', 'active') AND last_activity < datetime('now', '-1 hour')"
      )
      .run();
  }

  dispose(): void {
    this.db.close();
  }
}
