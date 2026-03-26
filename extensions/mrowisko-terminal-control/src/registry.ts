import { execFileSync } from "child_process";
import * as path from "path";
import { LiveAgent } from "./types";

interface DbRow {
  id: number;
  session_id: string;
  role: string;
  task: string | null;
  terminal_name: string | null;
  window_id: string | null;
  status: string;
  spawned_by: string | null;
  permission_mode: string;
  created_at: string;
  last_activity: string | null;
  stopped_at: string | null;
  transcript_path: string | null;
}

function rowToLiveAgent(row: DbRow): LiveAgent {
  return {
    id: row.id,
    sessionId: row.session_id,
    role: row.role,
    task: row.task,
    terminalName: row.terminal_name,
    windowId: row.window_id,
    status: row.status as LiveAgent["status"],
    spawnedBy: row.spawned_by,
    permissionMode: row.permission_mode,
    createdAt: row.created_at,
    lastActivity: row.last_activity,
    stoppedAt: row.stopped_at,
    transcriptPath: row.transcript_path,
  };
}

export class Registry {
  private scriptPath: string;
  private cwd: string;

  constructor(dbPath: string) {
    // dbPath is relative to workspace root — derive workspace root
    this.cwd = path.dirname(dbPath) || process.cwd();
    if (path.basename(dbPath) === "mrowisko.db") {
      this.cwd = path.dirname(dbPath);
    }
    this.scriptPath = path.join(this.cwd, "tools", "agent_launcher_db.py");
  }

  private run(args: string[]): string {
    return execFileSync("py", [this.scriptPath, ...args], {
      cwd: this.cwd,
      encoding: "utf-8",
      timeout: 10000,
    });
  }

  private runJson(args: string[]): unknown {
    const output = this.run(args);
    return JSON.parse(output);
  }

  insert(
    sessionId: string,
    role: string,
    task: string,
    terminalName: string,
    permissionMode: string,
    spawnedBy: string
  ): void {
    this.run([
      "insert",
      "--session-id", sessionId,
      "--role", role,
      "--task", task,
      "--terminal-name", terminalName,
      "--permission-mode", permissionMode,
      "--spawned-by", spawnedBy,
    ]);
  }

  getActiveAgents(): LiveAgent[] {
    const result = this.runJson(["list-active"]) as {
      ok: boolean;
      data: DbRow[];
    };
    return result.data.map(rowToLiveAgent);
  }

  markStopped(sessionId: string): void {
    this.run(["mark-stopped", "--session-id", sessionId]);
  }

  cleanup(): void {
    this.run(["cleanup"]);
  }

  dispose(): void {
    // No persistent connection to close
  }
}
