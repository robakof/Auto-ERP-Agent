import * as vscode from "vscode";
import { execFileSync } from "child_process";
import * as path from "path";
import { Spawner } from "./spawner";

interface PendingInvocation {
  id: number;
  invoker_type: string;
  invoker_id: string;
  target_role: string;
  task: string;
  created_at: string;
}

export class Approver {
  private timer: ReturnType<typeof setInterval> | undefined;
  private scriptPath: string;
  private cwd: string;
  private processing = new Set<number>();

  constructor(
    dbPath: string,
    private spawner: Spawner
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
    // Format: ["developer>erp_specialist", "architect>developer"]
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
      // Poll errors are non-critical — extension host may not have py in PATH yet
    }
  }

  private autoApprove(inv: PendingInvocation): void {
    try {
      this.run(["approve-invocation", "--id", String(inv.id)]);
      this.spawner.spawn({ role: inv.target_role, task: inv.task });
      vscode.window.showInformationMessage(
        `Auto-approved: ${inv.invoker_id} → ${inv.target_role}`
      );
    } finally {
      this.processing.delete(inv.id);
    }
  }

  private async showApprovalDialog(inv: PendingInvocation): Promise<void> {
    const approve = "Approve";
    const reject = "Reject";

    const choice = await vscode.window.showWarningMessage(
      `Agent ${inv.invoker_id} wants to spawn ${inv.target_role}: "${inv.task}"`,
      approve,
      reject
    );

    try {
      if (choice === approve) {
        this.run(["approve-invocation", "--id", String(inv.id)]);
        this.spawner.spawn({ role: inv.target_role, task: inv.task });
        vscode.window.showInformationMessage(
          `Approved: ${inv.target_role} spawned.`
        );
      } else {
        this.run(["reject-invocation", "--id", String(inv.id)]);
      }
    } finally {
      this.processing.delete(inv.id);
    }
  }

  dispose(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = undefined;
    }
  }
}
