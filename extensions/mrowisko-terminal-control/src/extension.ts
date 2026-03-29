import * as vscode from "vscode";
import * as crypto from "crypto";
import * as path from "path";
import { Registry } from "./registry";
import { Spawner } from "./spawner";
import { Watcher } from "./watcher";
import { Approver } from "./approver";
import { registerCommands } from "./commands";
import { TerminalMap } from "./types";

let registry: Registry | undefined;
let watcher: Watcher | undefined;
let approver: Approver | undefined;

export function activate(context: vscode.ExtensionContext): void {
  const dbPath = resolveDbPath();
  const terminals: TerminalMap = new Map();

  registry = new Registry(dbPath);
  const spawner = new Spawner(registry, terminals);
  watcher = new Watcher(registry, terminals);
  approver = new Approver(dbPath, spawner);

  watcher.activate();
  registerCommands(context, registry, spawner, terminals);

  // Poll for pending invocations (approval gate)
  const pollInterval = vscode.workspace
    .getConfiguration("mrowisko")
    .get<number>("pollIntervalMs", 5000);
  approver.start(pollInterval);

  // URI handler: allows spawning agents from CLI via
  // code --open-url "vscode://mrowisko.mrowisko-terminal-control?command=spawnAgent&role=developer&task=check+backlog"
  context.subscriptions.push(
    vscode.window.registerUriHandler({
      handleUri(uri: vscode.Uri): void {
        const params = new URLSearchParams(uri.query);
        const command = params.get("command");

        if (command === "spawnAgent") {
          const role = params.get("role");
          const task = params.get("task");
          if (role && task) {
            spawner.spawn({ role, task });
            vscode.window.showInformationMessage(
              `Agent ${role} uruchomiony via URI: ${task}`
            );
          }
        } else if (command === "sendText") {
          const sessionId = params.get("sessionId");
          const text = params.get("text");
          if (sessionId && text) {
            const terminal = terminals.get(sessionId);
            if (terminal) {
              terminal.sendText(text);
            }
          }
        } else if (command === "pokeAgent") {
          const terminalName = params.get("terminalName");
          const message = params.get("message");
          if (terminalName && message) {
            const terminal = vscode.window.terminals.find(
              (t) => t.name === terminalName
            );
            if (terminal) {
              // Workaround: Claude Code 2.1.83 "/" artifact in input
              terminal.sendText("", true);
              setTimeout(() => {
                terminal.sendText(message);
              }, 300);
              vscode.window.showInformationMessage(
                `Poke wysłany do: ${terminalName}`
              );
            } else {
              vscode.window.showWarningMessage(
                `Terminal "${terminalName}" nie znaleziony.`
              );
            }
          }
        } else if (command === "reload") {
          vscode.commands.executeCommand("workbench.action.reloadWindow");
        } else if (command === "listAgents") {
          vscode.commands.executeCommand("mrowisko.listAgents");
        } else if (command === "stopAgent") {
          const terminalName = params.get("terminalName");
          const sessionId = params.get("sessionId");
          // Prefer terminalName (works for all sessions), fallback to sessionId (spawned only)
          let terminal: vscode.Terminal | undefined;
          if (terminalName) {
            terminal = vscode.window.terminals.find(
              (t) => t.name === terminalName
            );
          } else if (sessionId) {
            terminal = terminals.get(sessionId);
          }
          if (terminal) {
            terminal.sendText("/exit");
            // Close terminal after Claude Code exits gracefully
            setTimeout(() => terminal!.dispose(), 3000);
          } else if (sessionId) {
            registry?.markStopped(sessionId);
          }
        } else if (command === "resumeAgent") {
          const terminalName = params.get("terminalName");
          const claudeUuid = params.get("claudeUuid") || "";
          const spawnToken = params.get("spawnToken") || crypto.randomUUID();
          if (terminalName) {
            const existing = vscode.window.terminals.find(
              (t) => t.name === terminalName
            );
            if (existing) {
              // Terminal exists — send /resume
              existing.sendText("/resume");
              vscode.window.showInformationMessage(
                `Resume wysłany do: ${terminalName}`
              );
            } else {
              // Terminal gone — create new and start claude --resume <uuid>
              const locationSetting = vscode.workspace
                .getConfiguration("mrowisko")
                .get<string>("terminalLocation", "editor");
              const location =
                locationSetting === "editor"
                  ? vscode.TerminalLocation.Editor
                  : vscode.TerminalLocation.Panel;
              const newTerminal = vscode.window.createTerminal({
                name: terminalName,
                location,
                env: { MROWISKO_SPAWN_TOKEN: spawnToken },
              });
              const resumeCmd = claudeUuid
                ? `claude --resume "${claudeUuid}"`
                : "claude --resume";
              newTerminal.sendText(resumeCmd);
              newTerminal.show();
              vscode.window.showInformationMessage(
                `Agent wznowiony w nowym terminalu: ${terminalName}`
              );
            }
          }
        }
      },
    })
  );

  // Cleanup orphaned agents on startup
  registry.cleanup();
}

export function deactivate(): void {
  approver?.dispose();
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
