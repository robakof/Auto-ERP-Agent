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

/** Map of session_id → vscode.Terminal for local window tracking. */
export type TerminalMap = Map<string, vscode.Terminal>;
