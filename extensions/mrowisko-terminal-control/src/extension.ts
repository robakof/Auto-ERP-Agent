import * as vscode from "vscode";
import * as path from "path";
import { Registry } from "./registry";
import { Spawner } from "./spawner";
import { Watcher } from "./watcher";
import { registerCommands } from "./commands";
import { TerminalMap } from "./types";

let registry: Registry | undefined;
let watcher: Watcher | undefined;

export function activate(context: vscode.ExtensionContext): void {
  const dbPath = resolveDbPath();
  const terminals: TerminalMap = new Map();

  registry = new Registry(dbPath);
  const spawner = new Spawner(registry, terminals);
  watcher = new Watcher(registry, terminals);

  watcher.activate();
  registerCommands(context, registry, spawner, terminals);

  // Cleanup orphaned agents on startup
  registry.cleanup();
}

export function deactivate(): void {
  watcher?.dispose();
  registry?.dispose();
}

function resolveDbPath(): string {
  const configured = vscode.workspace
    .getConfiguration("mrowisko")
    .get<string>("dbPath", "mrowisko.db");

  if (path.isAbsolute(configured)) {
    return configured;
  }

  // Resolve relative to workspace root
  const folders = vscode.workspace.workspaceFolders;
  if (folders && folders.length > 0) {
    return path.join(folders[0].uri.fsPath, configured);
  }

  return configured;
}
