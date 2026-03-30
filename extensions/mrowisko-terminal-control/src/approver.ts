import * as vscode from "vscode";
import * as fs from "fs";
import { MrowiskoDB } from "./db";
import { Spawner } from "./spawner";
import { PendingInvocation } from "./types";

export class Approver {
  private timer: ReturnType<typeof setInterval> | undefined;
  private processing = new Set<number>();

  constructor(
    private db: MrowiskoDB,
    private spawner: Spawner,
    private log: vscode.LogOutputChannel,
    private policyFile: string
  ) {}

  start(intervalMs: number): void {
    this.timer = setInterval(() => this.poll(), intervalMs);
    this.log.info("Approver started", { intervalMs, policyFile: this.policyFile });
  }

  private readPolicy(): Record<string, string> {
    try {
      return JSON.parse(fs.readFileSync(this.policyFile, "utf-8"));
    } catch {
      return {};
    }
  }

  private isTrustedPair(invoker: string, target: string): boolean {
    const trusted = vscode.workspace
      .getConfiguration("mrowisko")
      .get<string[]>("trustedPairs", []);
    return trusted.includes(`${invoker}>${target}`);
  }

  private poll(): void {
    try {
      const pending = this.db.getPendingInvocations();
      for (const inv of pending) {
        if (this.processing.has(inv.id)) {
          continue;
        }
        this.processing.add(inv.id);
        this.handleInvocation(inv);
      }
    } catch (e) {
      this.log.error("Approver poll error", { error: String(e) });
    }
  }

  private async handleInvocation(inv: PendingInvocation): Promise<void> {
    const action = inv.action || "spawn";
    const policy = this.readPolicy();
    const mode = policy[action] || "approval";

    try {
      if (mode === "auto" || this.isTrustedPair(inv.invoker_id || "", inv.target_role)) {
        this.autoApprove(inv, action);
      } else {
        await this.showApprovalDialog(inv, action);
      }
    } finally {
      this.processing.delete(inv.id);
    }
  }

  private autoApprove(inv: PendingInvocation, action: string): void {
    this.db.approveInvocation(inv.id);
    this.log.info(`Auto-approved: ${action} ${inv.target_role} by ${inv.invoker_id}`);
    this.executeAction(inv, action);
  }

  private async showApprovalDialog(inv: PendingInvocation, action: string): Promise<void> {
    const choice = await vscode.window.showWarningMessage(
      `${inv.invoker_id} wants to ${action} ${inv.target_role}: "${inv.task}"`,
      "Approve",
      "Reject"
    );

    if (choice === "Approve") {
      this.db.approveInvocation(inv.id);
      this.executeAction(inv, action);
      this.log.info(`Approved: ${action} ${inv.target_role}`);
    } else {
      this.db.rejectInvocation(inv.id);
      this.log.info(`Rejected: ${action} ${inv.target_role}`);
    }
  }

  private executeAction(inv: PendingInvocation, action: string): void {
    if (action === "spawn") {
      this.spawner.spawn({ role: inv.target_role, task: inv.task });
    } else if (action === "resume") {
      const terminalName = `Agent: ${inv.target_role}`;
      this.spawner.resume(terminalName, inv.target_session_id || "", inv.session_id || "");
    } else if (action === "stop") {
      if (inv.target_session_id) {
        this.spawner.stop(inv.target_session_id);
      }
    } else if (action === "kill") {
      if (inv.target_session_id) {
        this.spawner.kill(inv.target_session_id);
      }
    }
  }

  dispose(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = undefined;
    }
  }
}
