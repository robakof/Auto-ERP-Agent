import { execFileSync } from "child_process";
import * as path from "path";
import { LiveAgent } from "./types";

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
    spawnToken: string,
    role: string,
    task: string,
    terminalName: string,
    spawnedBy: string
  ): void {
    this.run([
      "insert",
      "--spawn-token", spawnToken,
      "--role", role,
      "--task", task,
      "--terminal-name", terminalName,
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
