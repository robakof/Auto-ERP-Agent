import * as vscode from "vscode";
import { Registry } from "./registry";
import { TerminalMap } from "./types";

export class Watcher {
  private disposables: vscode.Disposable[] = [];

  constructor(
    private registry: Registry,
    private terminals: TerminalMap
  ) {}

  activate(): void {
    this.disposables.push(
      vscode.window.onDidCloseTerminal((terminal) =>
        this.onTerminalClosed(terminal)
      )
    );
  }

  private onTerminalClosed(terminal: vscode.Terminal): void {
    // Find session_id for this terminal
    for (const [sessionId, tracked] of this.terminals) {
      if (tracked === terminal) {
        this.registry.markStopped(sessionId);
        this.terminals.delete(sessionId);
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
