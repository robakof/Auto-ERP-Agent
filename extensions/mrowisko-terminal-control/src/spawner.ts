import * as vscode from "vscode";
import * as crypto from "crypto";
import { MrowiskoDB } from "./db";
import { RoleLayout } from "./layout";
import { SpawnRequest, TerminalMap } from "./types";

function getConfig<T>(key: string, fallback: T): T {
  return vscode.workspace.getConfiguration("mrowisko").get<T>(key, fallback);
}

export class Spawner {
  constructor(
    private db: MrowiskoDB,
    private terminals: TerminalMap,
    private layout: RoleLayout,
    private log: vscode.LogOutputChannel
  ) {}

  spawn(request: SpawnRequest): vscode.Terminal {
    const terminalName = `Agent: ${request.role}`;
    const spawnToken = crypto.randomUUID();
    const permissionMode =
      request.permissionMode ||
      getConfig("defaultPermissionMode", "default");

    // Pre-register in DB before terminal exists
    this.db.insertAgent(
      spawnToken,
      request.role,
      request.task,
      terminalName,
      "human"
    );

    // Determine terminal location — editor mode uses per-role ViewColumn
    const locationSetting = getConfig("terminalLocation", "editor");
    const location =
      locationSetting === "editor"
        ? { viewColumn: this.layout.getViewColumn(request.role) }
        : vscode.TerminalLocation.Panel;

    const terminal = vscode.window.createTerminal({
      name: terminalName,
      location,
      env: { MROWISKO_SPAWN_TOKEN: spawnToken },
    });

    // Build claude command with task context in system prompt
    // TODO(phase-3): escape systemPrompt for PowerShell special chars
    const template = getConfig("autoPromptTemplate", "[TRYB AUTONOMICZNY] Rola: {role}. Task: {task}");
    const autoPrompt = template.replace("{role}", request.role).replace("{task}", request.task);
    const extraPrompt = request.systemPrompt
      ? `${autoPrompt} ${request.systemPrompt}`
      : autoPrompt;

    const cmd = [
      "claude",
      `--name "Agent-${request.role}"`,
      `--append-system-prompt "${extraPrompt.replace(/"/g, '\\"')}"`,
      `--permission-mode ${permissionMode}`,
    ].join(" ");

    terminal.sendText(cmd);

    // Delay first user message — Claude Code needs time to start and accept stdin.
    // The system prompt already contains the task context, so Claude knows what to do.
    // This message triggers session_init via CLAUDE.md routing.
    const delay = getConfig("startupDelayMs", 12000);
    setTimeout(() => {
      // Workaround W1: Claude Code 2.1.83 injects "/" into input after startup.
      // First empty sendText clears the artifact, then actual message follows.
      terminal.sendText("", true);
      setTimeout(() => {
        terminal.sendText(`${request.role}, ${request.task}`);
      }, 500);
    }, delay);

    terminal.show();

    // Track terminal locally (by spawn_token — session_id not known yet)
    this.terminals.set(spawnToken, terminal);
    this.layout.addTerminal(request.role, terminal);

    this.log.info("Agent spawned", { role: request.role, spawnToken, terminalName });
    return terminal;
  }

  resume(terminalName: string, claudeUuid: string, spawnToken: string): void {
    // W4: Resume requires new terminal — dead shell won't accept input
    const existing = vscode.window.terminals.find((t) => t.name === terminalName);
    if (existing) {
      existing.dispose();
    }

    const roleMatch = terminalName.match(/^Agent:\s*(.+)$/);
    const resumeRole = roleMatch ? roleMatch[1] : "";
    const locationSetting = getConfig("terminalLocation", "editor");
    const location =
      locationSetting === "editor" && resumeRole
        ? { viewColumn: this.layout.getViewColumn(resumeRole) }
        : vscode.TerminalLocation.Panel;

    const newTerminal = vscode.window.createTerminal({
      name: terminalName,
      location,
      env: { MROWISKO_SPAWN_TOKEN: spawnToken },
    });

    if (resumeRole) {
      this.layout.addTerminal(resumeRole, newTerminal);
    }

    const resumeCmd = claudeUuid
      ? `claude --resume "${claudeUuid}"`
      : "claude --resume";
    newTerminal.sendText(resumeCmd);
    newTerminal.show();

    this.log.info("Agent resumed", { terminalName, claudeUuid });
  }

  private findTerminal(sessionId: string): vscode.Terminal | undefined {
    // Try sessionId first, then fallback to spawnToken (Map keyed by spawnToken at spawn time)
    return this.terminals.get(sessionId)
      || (() => {
        const spawnToken = this.db.getSpawnTokenBySessionId(sessionId);
        return spawnToken ? this.terminals.get(spawnToken) : undefined;
      })();
  }

  stop(sessionId: string): void {
    const terminal = this.findTerminal(sessionId);
    if (terminal) {
      // W3: /exit + dispose after timeout
      terminal.sendText("/exit");
      setTimeout(() => terminal.dispose(), 3000);
      this.log.info("Agent stop sent", { sessionId });
    } else {
      // Terminal not in this window — mark stopped directly
      this.db.markStopped(sessionId);
      this.log.info("Agent marked stopped (no terminal)", { sessionId });
    }
  }

  kill(sessionId: string): void {
    const terminal = this.findTerminal(sessionId);
    if (terminal) {
      terminal.dispose();
      this.log.info("Agent killed", { sessionId });
    }
    this.db.markStopped(sessionId);
  }
}
