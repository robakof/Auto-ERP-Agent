import * as vscode from "vscode";
import { Registry } from "./registry";
import { Spawner } from "./spawner";
import { TerminalMap } from "./types";

const ROLES = [
  { label: "developer", description: "Rozbudowa narzedzi, architektury" },
  { label: "erp_specialist", description: "Konfiguracja ERP, widoki BI" },
  { label: "analyst", description: "Analiza jakosci danych" },
  { label: "architect", description: "Architektura systemu, code review" },
  { label: "prompt_engineer", description: "Edycja i wersjonowanie promptow" },
  { label: "metodolog", description: "Ocena metody pracy" },
];

export function registerCommands(
  context: vscode.ExtensionContext,
  registry: Registry,
  spawner: Spawner,
  terminals: TerminalMap
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("mrowisko.spawnAgent", () =>
      spawnAgent(spawner)
    ),
    vscode.commands.registerCommand("mrowisko.listAgents", () =>
      listAgents(registry, terminals)
    ),
    vscode.commands.registerCommand("mrowisko.stopAgent", () =>
      stopAgent(registry, terminals)
    )
  );
}

async function spawnAgent(spawner: Spawner): Promise<void> {
  const role = await vscode.window.showQuickPick(ROLES, {
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

  spawner.spawn({ role: role.label, task });
  vscode.window.showInformationMessage(
    `Agent ${role.label} uruchomiony: ${task}`
  );
}

async function listAgents(
  registry: Registry,
  terminals: TerminalMap
): Promise<void> {
  const agents = registry.getActiveAgents();

  if (agents.length === 0) {
    vscode.window.showInformationMessage("Brak aktywnych agentow.");
    return;
  }

  const items = agents.map((a) => ({
    label: `${a.role} [${a.status}]`,
    description: a.task || "",
    detail: `session: ${a.sessionId.slice(0, 8)}... | ${a.createdAt}`,
    sessionId: a.sessionId,
  }));

  const selected = await vscode.window.showQuickPick(items, {
    placeHolder: "Aktywni agenci (wybierz aby przejsc do terminala)",
  });

  if (selected) {
    const terminal = terminals.get(selected.sessionId);
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
  registry: Registry,
  terminals: TerminalMap
): Promise<void> {
  const agents = registry.getActiveAgents();

  if (agents.length === 0) {
    vscode.window.showInformationMessage("Brak aktywnych agentow do zatrzymania.");
    return;
  }

  const items = agents.map((a) => ({
    label: `${a.role} [${a.status}]`,
    description: a.task || "",
    detail: `session: ${a.sessionId.slice(0, 8)}...`,
    sessionId: a.sessionId,
  }));

  const selected = await vscode.window.showQuickPick(items, {
    placeHolder: "Wybierz agenta do zatrzymania",
  });

  if (!selected) {
    return;
  }

  const terminal = terminals.get(selected.sessionId);
  if (terminal) {
    terminal.dispose();
    // onDidCloseTerminal watcher handles DB cleanup
  } else {
    // Terminal not in this window — mark stopped directly
    registry.markStopped(selected.sessionId);
  }

  vscode.window.showInformationMessage(
    `Agent ${selected.label} zatrzymany.`
  );
}
