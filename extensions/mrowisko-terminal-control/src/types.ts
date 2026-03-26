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

/** Map of session_id → vscode.Terminal for local window tracking. */
export type TerminalMap = Map<string, vscode.Terminal>;
