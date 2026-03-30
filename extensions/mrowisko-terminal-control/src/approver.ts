import * as vscode from "vscode";
import * as crypto from "crypto";
import { execFileSync } from "child_process";
import * as path from "path";
import { Spawner } from "./spawner";
import { RoleLayout } from "./layout";

type InvocationAction = "spawn" | "stop" | "resume";

interface PendingInvocation {
  id: number;
  invoker_type: string;
  invoker_id: string;
  target_role: string;
  task: string;
  action: InvocationAction;
  target_session_id: string | null;
  agent_terminal_name: string | null;
  agent_claude_uuid: string | null;
  created_at: string;
}

export class Approver {
  private timer: ReturnType<typeof setInterval> | undefined;
  private scriptPath: string;
  private cwd: string;
  private processing = new Set<number>();

  constructor(
    dbPath: string,
    private spawner: Spawner,
    private layout: RoleLayout
  ) {
    this.cwd = path.dirname(dbPath);
    this.scriptPath = path.join(this.cwd, "tools", "agent_launcher_db.py");
  }

  private run(args: string[]): string {
    return execFileSync("py", [this.scriptPath, ...args], {
      cwd: this.cwd,
      encoding: "utf-8",
      timeout: 10000,
    });
  }

  /** Start polling for pending invocations. */
  start(intervalMs: number): void {
    this.timer = setInterval(() => this.poll(), intervalMs);
  }

  /** Check if invoker→target pair is trusted (auto-approve without dialog). */
  private isTrustedPair(invoker: string, target: string): boolean {
    const trusted = vscode.workspace
      .getConfiguration("mrowisko")
      .get<string[]>("trustedPairs", []);
    return trusted.includes(`${invoker}>${target}`);
  }

  private poll(): void {
    try {
      const output = this.run(["pending-invocations"]);
      const result = JSON.parse(output) as {
        ok: boolean;
        data: PendingInvocation[];
      };
      if (!result.ok) {
        return;
      }
      for (const inv of result.data) {
        // Default action for legacy rows without action column
        if (!inv.action) {
          inv.action = "spawn";
        }
        if (!this.processing.has(inv.id)) {
          this.processing.add(inv.id);
          if (this.isTrustedPair(inv.invoker_id, inv.target_role)) {
            this.autoApprove(inv);
          } else {
            this.showApprovalDialog(inv);
          }
        }
      }
    } catch {
      // Poll errors are non-critical
    }
  }

  private formatMessage(inv: PendingInvocation): string {
    switch (inv.action) {
      case "stop":
        return `${inv.invoker_id} chce zatrzymać ${inv.target_role}: "${inv.task}"`;
      case "resume":
        return `${inv.invoker_id} chce wznowić ${inv.target_role}: "${inv.task}"`;
      default:
        return `${inv.invoker_id} chce uruchomić ${inv.target_role}: "${inv.task}"`;
    }
  }

  private autoApprove(inv: PendingInvocation): void {
    try {
      this.run(["approve-invocation", "--id", String(inv.id)]);
      this.executeAction(inv);
      vscode.window.showInformationMessage(
        `Auto-approved ${inv.action}: ${inv.invoker_id} → ${inv.target_role}`
      );
    } finally {
      this.processing.delete(inv.id);
    }
  }

  private async showApprovalDialog(inv: PendingInvocation): Promise<void> {
    const approve = "Approve";
    const reject = "Reject";

    const choice = await vscode.window.showWarningMessage(
      this.formatMessage(inv),
      approve,
      reject
    );

    try {
      if (choice === approve) {
        this.run(["approve-invocation", "--id", String(inv.id)]);
        this.executeAction(inv);
        vscode.window.showInformationMessage(
          `Approved ${inv.action}: ${inv.target_role}`
        );
      } else {
        this.run(["reject-invocation", "--id", String(inv.id)]);
      }
    } finally {
      this.processing.delete(inv.id);
    }
  }

  private executeAction(inv: PendingInvocation): void {
    switch (inv.action) {
      case "spawn":
        this.spawner.spawn({ role: inv.target_role, task: inv.task });
        break;
      case "stop":
        this.executeStop(inv);
        break;
      case "resume":
        this.executeResume(inv);
        break;
    }
  }

  private executeStop(inv: PendingInvocation): void {
    const terminalName = inv.agent_terminal_name;
    if (!terminalName) {
      vscode.window.showWarningMessage(
        `Stop ${inv.target_role}: brak terminal_name w DB.`
      );
      return;
    }
    const terminal = vscode.window.terminals.find(
      (t) => t.name === terminalName
    );
    if (terminal) {
      terminal.sendText("/exit");
      setTimeout(() => terminal.dispose(), 3000);
    }
    // Mark stopped in DB
    if (inv.target_session_id) {
      try {
        this.run([
          "mark-stopped",
          "--session-id",
          inv.target_session_id,
        ]);
      } catch {
        // Non-critical — watcher will catch terminal close
      }
    }
  }

  private executeResume(inv: PendingInvocation): void {
    const terminalName = inv.agent_terminal_name;
    if (!terminalName) {
      vscode.window.showWarningMessage(
        `Resume ${inv.target_role}: brak terminal_name w DB.`
      );
      return;
    }
    const existing = vscode.window.terminals.find(
      (t) => t.name === terminalName
    );
    if (existing) {
      existing.sendText("/resume");
      vscode.window.showInformationMessage(
        `Resume wysłany do: ${terminalName}`
      );
    } else {
      // Terminal gone — create new and start claude --resume <uuid>
      const roleMatch = terminalName.match(/^Agent:\s*(.+)$/);
      const resumeRole = roleMatch ? roleMatch[1] : "";
      const spawnToken = crypto.randomUUID();
      const locationSetting = vscode.workspace
        .getConfiguration("mrowisko")
        .get<string>("terminalLocation", "editor");
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
      const claudeUuid = inv.agent_claude_uuid || "";
      const resumeCmd = claudeUuid
        ? `claude --resume "${claudeUuid}"`
        : "claude --resume";
      newTerminal.sendText(resumeCmd);
      newTerminal.show();
    }
  }

  dispose(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = undefined;
    }
  }
}
