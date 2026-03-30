import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { MrowiskoDB } from "./db";
import { RoleLayout } from "./layout";
import { Spawner } from "./spawner";
import { TerminalMap } from "./types";

function loadRoles(): vscode.QuickPickItem[] {
  try {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders) {
      return [];
    }
    const configPath = path.join(folders[0].uri.fsPath, "config", "session_init_config.json");
    const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
    return Object.keys(config).map((role) => ({ label: role }));
  } catch {
    return [
      { label: "developer" },
      { label: "erp_specialist" },
      { label: "analyst" },
      { label: "architect" },
      { label: "prompt_engineer" },
      { label: "metodolog" },
    ];
  }
}

export function registerCommands(
  context: vscode.ExtensionContext,
  db: MrowiskoDB,
  spawner: Spawner,
  terminals: TerminalMap,
  layout: RoleLayout
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("mrowisko.spawnAgent", () =>
      spawnAgent(db)
    ),
    vscode.commands.registerCommand("mrowisko.listAgents", () =>
      listAgents(db, terminals)
    ),
    vscode.commands.registerCommand("mrowisko.stopAgent", () =>
      stopAgent(db, spawner, terminals)
    ),
    vscode.commands.registerCommand("mrowisko.focusAgent", () =>
      focusAgent(layout)
    ),
    vscode.commands.registerCommand("mrowisko.rotateTab", () =>
      rotateTab(layout)
    )
  );
}

async function spawnAgent(db: MrowiskoDB): Promise<void> {
  const role = await vscode.window.showQuickPick(loadRoles(), {
    placeHolder: "Wybierz role agenta",
  });
  if (!role) {
    return;
  }

  const task = await vscode.window.showInputBox({
    prompt: "Opisz zadanie dla agenta",
    placeHolder: "np. sprawdz backlog i wykonaj najwyzszy priorytet",
  });
  if (!task) {
    return;
  }

  db.insertInvocation("human", "human", role.label, task, "spawn");
  vscode.window.showInformationMessage(
    `Invocation created: ${role.label} — czeka na approval`
  );
}

async function listAgents(
  db: MrowiskoDB,
  terminals: TerminalMap
): Promise<void> {
  const agents = db.getActiveAgents();

  if (agents.length === 0) {
    vscode.window.showInformationMessage("Brak aktywnych agentow.");
    return;
  }

  const items = agents.map((a) => ({
    label: `${a.role ?? "unknown"} [${a.status}]`,
    description: a.task || "",
    detail: `session: ${(a.sessionId ?? a.spawnToken ?? "?").slice(0, 8)}... | ${a.createdAt}`,
    spawnToken: a.spawnToken ?? "",
    sessionId: a.sessionId ?? "",
  }));

  const selected = await vscode.window.showQuickPick(items, {
    placeHolder: "Aktywni agenci (wybierz aby przejsc do terminala)",
  });

  if (selected) {
    const key = selected.spawnToken || selected.sessionId;
    const terminal = key ? terminals.get(key) : undefined;
    if (terminal) {
      terminal.show();
    } else {
      vscode.window.showWarningMessage(
        "Terminal nie jest dostepny w tym oknie."
      );
    }
  }
}

async function stopAgent(
  db: MrowiskoDB,
  spawner: Spawner,
  terminals: TerminalMap
): Promise<void> {
  const agents = db.getActiveAgents();

  if (agents.length === 0) {
    vscode.window.showInformationMessage("Brak aktywnych agentow do zatrzymania.");
    return;
  }

  const items = agents.map((a) => ({
    label: `${a.role ?? "unknown"} [${a.status}]`,
    description: a.task || "",
    detail: `session: ${(a.sessionId ?? a.spawnToken ?? "?").slice(0, 8)}...`,
    spawnToken: a.spawnToken ?? "",
    sessionId: a.sessionId ?? "",
  }));

  const selected = await vscode.window.showQuickPick(items, {
    placeHolder: "Wybierz agenta do zatrzymania",
  });

  if (!selected) {
    return;
  }

  const sessionId = selected.sessionId || selected.spawnToken;
  if (sessionId) {
    spawner.stop(sessionId);
  }

  vscode.window.showInformationMessage(
    `Agent ${selected.label} zatrzymany.`
  );
}

async function focusAgent(layout: RoleLayout): Promise<void> {
  const roles = loadRoles();
  const selected = await vscode.window.showQuickPick(roles, {
    placeHolder: "Wybierz rolę do sfokusowania",
  });
  if (!selected) {
    return;
  }
  const found = layout.focusRole(selected.label);
  if (!found) {
    vscode.window.showWarningMessage(
      `Brak aktywnego terminala dla roli: ${selected.label}`
    );
  }
}

function rotateTab(layout: RoleLayout): void {
  const role = layout.rotateNext();
  if (!role) {
    vscode.window.showWarningMessage("Brak aktywnych terminali.");
  }
}
