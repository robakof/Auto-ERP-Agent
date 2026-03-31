"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.Approver = void 0;
const vscode = __importStar(require("vscode"));
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
class Approver {
    constructor(dbPath, spawner) {
        this.spawner = spawner;
        this.processing = new Set();
        this.cwd = path.dirname(dbPath);
        this.scriptPath = path.join(this.cwd, "tools", "agent_launcher_db.py");
    }
    run(args) {
        return (0, child_process_1.execFileSync)("py", [this.scriptPath, ...args], {
            cwd: this.cwd,
            encoding: "utf-8",
            timeout: 10000,
        });
    }
    /** Start polling for pending invocations. */
    start(intervalMs) {
        this.timer = setInterval(() => this.poll(), intervalMs);
    }
    /** Check if invoker→target pair is trusted (auto-approve without dialog). */
    isTrustedPair(invoker, target) {
        const trusted = vscode.workspace
            .getConfiguration("mrowisko")
            .get("trustedPairs", []);
        // Format: ["developer>erp_specialist", "architect>developer"]
        return trusted.includes(`${invoker}>${target}`);
    }
    poll() {
        try {
            const output = this.run(["pending-invocations"]);
            const result = JSON.parse(output);
            if (!result.ok) {
                return;
            }
            for (const inv of result.data) {
                if (!this.processing.has(inv.id)) {
                    this.processing.add(inv.id);
                    if (this.isTrustedPair(inv.invoker_id, inv.target_role)) {
                        this.autoApprove(inv);
                    }
                    else {
                        this.showApprovalDialog(inv);
                    }
                }
            }
        }
        catch {
            // Poll errors are non-critical — extension host may not have py in PATH yet
        }
    }
    autoApprove(inv) {
        try {
            this.run(["approve-invocation", "--id", String(inv.id)]);
            this.spawner.spawn({ role: inv.target_role, task: inv.task });
            vscode.window.showInformationMessage(`Auto-approved: ${inv.invoker_id} → ${inv.target_role}`);
        }
        finally {
            this.processing.delete(inv.id);
        }
    }
    async showApprovalDialog(inv) {
        const approve = "Approve";
        const reject = "Reject";
        const choice = await vscode.window.showWarningMessage(`Agent ${inv.invoker_id} wants to spawn ${inv.target_role}: "${inv.task}"`, approve, reject);
        try {
            if (choice === approve) {
                this.run(["approve-invocation", "--id", String(inv.id)]);
                this.spawner.spawn({ role: inv.target_role, task: inv.task });
                vscode.window.showInformationMessage(`Approved: ${inv.target_role} spawned.`);
            }
            else {
                this.run(["reject-invocation", "--id", String(inv.id)]);
            }
        }
        finally {
            this.processing.delete(inv.id);
        }
    }
    dispose() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = undefined;
        }
    }
}
exports.Approver = Approver;
//# sourceMappingURL=approver.js.map