import * as vscode from "vscode";
import * as crypto from "crypto";
import * as path from "path";
import * as fs from "fs";
import { MrowiskoDB } from "./db";
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
  const terminals: TerminalMap = new Map();
  const layout = new RoleLayout();
  const policyFile = path.join(workspaceRoot, "config", "spawn_policy.json");
  const spawner = new Spawner(db, terminals, layout, log);
  const watcher = new Watcher(db, terminals, layout, log);
  const approver = new Approver(db, spawner, log, policyFile);

  // 5. Activate components
  watcher.activate();
  registerCommands(context, db, terminals, layout);

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
            const invoker = params.get("invoker") || "human";
            db.insertInvocation("human", invoker, role, task, "spawn");
            log.info("Invocation created via URI", { role, task, invoker });
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
          // URI = direct execution (CLI already checked policy)
          const sessionId = params.get("sessionId");
          const terminalName = params.get("terminalName");
          if (sessionId) {
            spawner.stop(sessionId);
          } else if (terminalName) {
            const terminal = vscode.window.terminals.find((t) => t.name === terminalName);
            if (terminal) {
              terminal.sendText("/exit");
              setTimeout(() => terminal.dispose(), 3000);
            }
          }
        } else if (command === "killAgent") {
          const sessionId = params.get("sessionId");
          if (sessionId) {
            spawner.kill(sessionId);
          }
        } else if (command === "resumeAgent") {
          const terminalName = params.get("terminalName");
          const claudeUuid = params.get("claudeUuid") || "";
          const spawnToken = params.get("spawnToken") || crypto.randomUUID();
          if (terminalName) {
            spawner.resume(terminalName, claudeUuid, spawnToken);
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
