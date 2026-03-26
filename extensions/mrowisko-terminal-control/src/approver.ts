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

  private poll(): void {
    try {
      const output = this.run(["pending-invocations"]);
      console.log("[Mrowisko Approver] poll result:", output.trim());
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
          this.showApprovalDialog(inv);
        }
      }
    } catch (e) {
      console.error("[Mrowisko Approver] poll error:", e);
    }
  }

  private async showApprovalDialog(inv: PendingInvocation): Promise<void> {
    console.log("[Mrowisko Approver] showing dialog for invocation", inv.id);
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
