import * as vscode from "vscode";
import * as crypto from "crypto";
import { Registry } from "./registry";
import { SpawnRequest, TerminalMap } from "./types";

/** Delay (ms) before sending the first user message to Claude Code. */
const STARTUP_DELAY_MS = 4000;

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

    // Build claude command with task context in system prompt
    // TODO(phase-3): escape systemPrompt for PowerShell special chars
    const autoPrompt = `[TRYB AUTONOMICZNY] Rola: ${request.role}. Task: ${request.task}`;
    const extraPrompt = request.systemPrompt
      ? `${autoPrompt} ${request.systemPrompt}`
      : autoPrompt;

    const cmd = [
      "claude",
      `--name "Agent-${request.role}"`,
      `--session-id "${sessionId}"`,
      `--append-system-prompt "${extraPrompt.replace(/"/g, '\\"')}"`,
      `--permission-mode ${permissionMode}`,
    ].join(" ");

    terminal.sendText(cmd);

    // Delay first user message — Claude Code needs ~3-4s to start and accept stdin.
    // The system prompt already contains the task context, so Claude knows what to do.
    // This message triggers session_init via CLAUDE.md routing.
    setTimeout(() => {
      terminal.sendText(`${request.role}, ${request.task}`);
    }, STARTUP_DELAY_MS);

    terminal.show();

    // Track terminal locally
    this.terminals.set(sessionId, terminal);

    return terminal;
  }
}
