import * as vscode from "vscode";
import * as crypto from "crypto";
import * as path from "path";
import * as fs from "fs";
import { MrowiskoDB } from "./db";
import { Registry } from "./registry";
import { Spawner } from "./spawner";
import { Watcher } from "./watcher";
import { Approver } from "./approver";
import { RoleLayout } from "./layout";
import { registerCommands } from "./commands";
import { TerminalMap } from "./types";

function resolveWorkspaceRoot(): string {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders || folders.length === 0) {
    throw new Error("Mrowisko requires an open workspace folder.");
  }
  return folders[0].uri.fsPath;
}

export function activate(context: vscode.ExtensionContext): void {
  const log = vscode.window.createOutputChannel("Mrowisko", { log: true });

  // 1. Resolve workspace — fail-fast
  let workspaceRoot: string;
  try {
    workspaceRoot = resolveWorkspaceRoot();
  } catch {
    log.error("No workspace folder open. Extension inactive.");
    vscode.window.showErrorMessage("Mrowisko: otwórz folder projektu.");
    return;
  }

  // 2. Resolve DB — absolute path
  const dbPath = path.join(workspaceRoot, "mrowisko.db");
  if (!fs.existsSync(dbPath)) {
    log.warn(`mrowisko.db not found at ${dbPath}. Extension inactive.`);
    return;
  }

  // 3. Initialize DB
  let db: MrowiskoDB;
  try {
    db = new MrowiskoDB(dbPath);
    log.info("Database connected", { dbPath });
  } catch (e) {
    log.error("Failed to open database", { dbPath, error: String(e) });
    vscode.window.showErrorMessage(`Mrowisko: nie można otworzyć bazy danych: ${dbPath}`);
    return;
  }

  // 4. Initialize components
  const registry = new Registry(db);
  const terminals: TerminalMap = new Map();
  const layout = new RoleLayout();
  const spawner = new Spawner(registry, terminals, layout);
  const watcher = new Watcher(registry, terminals, layout);
  // Approver still uses Python proxy (Faza 1 — will be rewritten in Faza 2)
  const approver = new Approver(dbPath, spawner);

  // 5. Activate components
  watcher.activate();
  registerCommands(context, registry, spawner, terminals, layout);

  const pollInterval = vscode.workspace
    .getConfiguration("mrowisko")
    .get<number>("pollIntervalMs", 5000);
  approver.start(pollInterval);

  // 6. URI handler
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
        } else if (command === "focusAgent") {
          const role = params.get("role");
          if (role) {
            const found = layout.focusRole(role);
            if (!found) {
              vscode.window.showWarningMessage(
                `Brak aktywnego terminala dla roli: ${role}`
              );
            }
          }
        } else if (command === "rotateTab") {
          const role = layout.rotateNext();
          if (!role) {
            vscode.window.showWarningMessage("Brak aktywnych terminali.");
          }
        } else if (command === "reload") {
          vscode.commands.executeCommand("workbench.action.reloadWindow");
        } else if (command === "listAgents") {
          vscode.commands.executeCommand("mrowisko.listAgents");
        } else if (command === "stopAgent") {
          const terminalName = params.get("terminalName");
          const sessionId = params.get("sessionId");
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
            setTimeout(() => terminal!.dispose(), 3000);
          } else if (sessionId) {
            registry.markStopped(sessionId);
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
              existing.sendText("/resume");
              vscode.window.showInformationMessage(
                `Resume wysłany do: ${terminalName}`
              );
            } else {
              const roleMatch = terminalName.match(/^Agent:\s*(.+)$/);
              const resumeRole = roleMatch ? roleMatch[1] : "";
              const locationSetting = vscode.workspace
                .getConfiguration("mrowisko")
                .get<string>("terminalLocation", "editor");
              const location =
                locationSetting === "editor" && resumeRole
                  ? { viewColumn: layout.getViewColumn(resumeRole) }
                  : vscode.TerminalLocation.Panel;
              const newTerminal = vscode.window.createTerminal({
                name: terminalName,
                location,
                env: { MROWISKO_SPAWN_TOKEN: spawnToken },
              });
              if (resumeRole) {
                layout.addTerminal(resumeRole, newTerminal);
              }
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

  // 7. Cleanup orphaned agents
  try {
    db.cleanup();
  } catch (e) {
    log.warn("Cleanup failed", { error: String(e) });
  }

  log.info("Extension activated", { workspaceRoot, dbPath });

  // 8. Register disposables — order matters (reverse teardown)
  context.subscriptions.push(
    { dispose: () => approver.dispose() },
    { dispose: () => watcher.dispose() },
    { dispose: () => db.dispose() },
    log
  );
}

export function deactivate(): void {
  // Cleanup handled by context.subscriptions disposables
}
