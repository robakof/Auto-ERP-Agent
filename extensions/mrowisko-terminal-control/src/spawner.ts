import * as vscode from "vscode";
import * as crypto from "crypto";
import { Registry } from "./registry";
import { SpawnRequest, TerminalMap } from "./types";

export class Spawner {
  constructor(
    private registry: Registry,
    private terminals: TerminalMap
  ) {}

  spawn(request: SpawnRequest): vscode.Terminal {
    const sessionId = crypto.randomUUID();
    const terminalName = `Agent: ${request.role}`;
    const permissionMode =
      request.permissionMode ||
      vscode.workspace
        .getConfiguration("mrowisko")
        .get<string>("defaultPermissionMode", "default");

    // Pre-register in DB before terminal exists
    this.registry.insert(
      sessionId,
      request.role,
      request.task,
      terminalName,
      permissionMode,
      "human"
    );

    // Determine terminal location
    const locationSetting = vscode.workspace
      .getConfiguration("mrowisko")
      .get<string>("terminalLocation", "editor");
    const location =
      locationSetting === "editor"
        ? vscode.TerminalLocation.Editor
        : vscode.TerminalLocation.Panel;

    const terminal = vscode.window.createTerminal({
      name: terminalName,
      location,
    });

    // Build claude command
    const systemPrompt = request.systemPrompt || "";
    const appendPrompt = systemPrompt
      ? `--append-system-prompt "${systemPrompt.replace(/"/g, '\\"')}" `
      : "";

    const cmd = [
      "claude",
      `--name "Agent-${request.role}"`,
      `--session-id "${sessionId}"`,
      appendPrompt,
      `--permission-mode ${permissionMode}`,
    ]
      .filter(Boolean)
      .join(" ");

    terminal.sendText(cmd);

    // Auto-start: send role + task as first message
    terminal.sendText(`${request.role}, ${request.task}`);

    terminal.show();

    // Track terminal locally
    this.terminals.set(sessionId, terminal);

    return terminal;
  }
}
