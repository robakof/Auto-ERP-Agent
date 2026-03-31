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
const crypto = __importStar(require("crypto"));
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
class Approver {
    constructor(dbPath, spawner, layout) {
        this.spawner = spawner;
        this.layout = layout;
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
                // Default action for legacy rows without action column
                if (!inv.action) {
                    inv.action = "spawn";
                }
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
            // Poll errors are non-critical
        }
    }
    formatMessage(inv) {
        switch (inv.action) {
            case "stop":
                return `${inv.invoker_id} chce zatrzymać ${inv.target_role}: "${inv.task}"`;
            case "resume":
                return `${inv.invoker_id} chce wznowić ${inv.target_role}: "${inv.task}"`;
            default:
                return `${inv.invoker_id} chce uruchomić ${inv.target_role}: "${inv.task}"`;
        }
    }
    autoApprove(inv) {
        try {
            this.run(["approve-invocation", "--id", String(inv.id)]);
            this.executeAction(inv);
            vscode.window.showInformationMessage(`Auto-approved ${inv.action}: ${inv.invoker_id} → ${inv.target_role}`);
        }
        finally {
            this.processing.delete(inv.id);
        }
    }
    async showApprovalDialog(inv) {
        const approve = "Approve";
        const reject = "Reject";
        const choice = await vscode.window.showWarningMessage(this.formatMessage(inv), approve, reject);
        try {
            if (choice === approve) {
                this.run(["approve-invocation", "--id", String(inv.id)]);
                this.executeAction(inv);
                vscode.window.showInformationMessage(`Approved ${inv.action}: ${inv.target_role}`);
            }
            else {
                this.run(["reject-invocation", "--id", String(inv.id)]);
            }
        }
        finally {
            this.processing.delete(inv.id);
        }
    }
    executeAction(inv) {
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
    executeStop(inv) {
        const terminalName = inv.agent_terminal_name;
        if (!terminalName) {
            vscode.window.showWarningMessage(`Stop ${inv.target_role}: brak terminal_name w DB.`);
            return;
        }
        const terminal = vscode.window.terminals.find((t) => t.name === terminalName);
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
            }
            catch {
                // Non-critical — watcher will catch terminal close
            }
        }
    }
    executeResume(inv) {
        const terminalName = inv.agent_terminal_name;
        if (!terminalName) {
            vscode.window.showWarningMessage(`Resume ${inv.target_role}: brak terminal_name w DB.`);
            return;
        }
        // Dispose stale terminal if it exists (stop may not have cleaned up)
        const existing = vscode.window.terminals.find((t) => t.name === terminalName);
        if (existing) {
            existing.dispose();
        }
        // Always create new terminal with claude --resume
        const roleMatch = terminalName.match(/^Agent:\s*(.+)$/);
        const resumeRole = roleMatch ? roleMatch[1] : "";
        const spawnToken = crypto.randomUUID();
        const locationSetting = vscode.workspace
            .getConfiguration("mrowisko")
            .get("terminalLocation", "editor");
        const location = locationSetting === "editor" && resumeRole
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
        // Sync DB: update spawn_token + status for heartbeat matching
        if (inv.target_session_id) {
            try {
                this.run([
                    "mark-resumed",
                    "--session-id",
                    inv.target_session_id,
                    "--spawn-token",
                    spawnToken,
                ]);
            }
            catch {
                // Non-critical — heartbeat will eventually pick up
            }
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