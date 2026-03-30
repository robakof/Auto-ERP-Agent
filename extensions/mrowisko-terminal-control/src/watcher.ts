import * as vscode from "vscode";
import { MrowiskoDB } from "./db";
import { RoleLayout } from "./layout";
import { TerminalMap } from "./types";

export class Watcher {
  private disposables: vscode.Disposable[] = [];

  constructor(
    private db: MrowiskoDB,
    private terminals: TerminalMap,
    private layout: RoleLayout,
    private log: vscode.LogOutputChannel
  ) {}

  activate(): void {
    this.disposables.push(
      vscode.window.onDidCloseTerminal((terminal) =>
        this.onTerminalClosed(terminal)
      )
    );
  }

  private onTerminalClosed(terminal: vscode.Terminal): void {
    this.layout.removeTerminal(terminal);
    // Find session_id for this terminal
    for (const [sessionId, tracked] of this.terminals) {
      if (tracked === terminal) {
        this.db.markStopped(sessionId);
        this.terminals.delete(sessionId);
        this.log.info("Terminal closed, agent marked stopped", { sessionId });
        return;
      }
    }
  }

  dispose(): void {
    for (const d of this.disposables) {
      d.dispose();
    }
    this.disposables = [];
  }
}
