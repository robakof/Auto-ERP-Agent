import * as vscode from "vscode";

export interface LiveAgent {
  id: number;
  sessionId: string;
  role: string;
  task: string | null;
  terminalName: string | null;
  windowId: string | null;
  status: "starting" | "active" | "stopped";
  spawnedBy: string | null;
  permissionMode: string;
  createdAt: string;
  lastActivity: string | null;
  stoppedAt: string | null;
  transcriptPath: string | null;
}

export interface SpawnRequest {
  role: string;
  task: string;
  permissionMode?: string;
  systemPrompt?: string;
}

export interface LiveAgentRow {
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

export function rowToLiveAgent(row: LiveAgentRow): LiveAgent {
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

/** Map of session_id → vscode.Terminal for local window tracking. */
export type TerminalMap = Map<string, vscode.Terminal>;
