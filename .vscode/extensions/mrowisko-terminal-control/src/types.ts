import * as vscode from "vscode";

export interface LiveAgent {
  id: number;
  sessionId: string | null;
  claudeUuid: string | null;
  role: string | null;
  task: string | null;
  terminalName: string | null;
  status: "starting" | "active" | "stopped";
  spawnedBy: string | null;
  spawnToken: string | null;
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

export interface PendingInvocation {
  id: number;
  invoker_type: string | null;
  invoker_id: string | null;
  target_role: string;
  task: string;
  session_id: string | null;
  status: string;
  created_at: string;
  ended_at: string | null;
  action: string | null;
  target_session_id: string | null;
}

/** Map of session_id → vscode.Terminal for local window tracking. */
export type TerminalMap = Map<string, vscode.Terminal>;
