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
exports.Registry = void 0;
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
function rowToLiveAgent(row) {
    return {
        id: row.id,
        sessionId: row.session_id,
        role: row.role,
        task: row.task,
        terminalName: row.terminal_name,
        windowId: row.window_id,
        status: row.status,
        spawnedBy: row.spawned_by,
        permissionMode: row.permission_mode,
        createdAt: row.created_at,
        lastActivity: row.last_activity,
        stoppedAt: row.stopped_at,
        transcriptPath: row.transcript_path,
    };
}
class Registry {
    constructor(dbPath) {
        // dbPath is relative to workspace root — derive workspace root
        this.cwd = path.dirname(dbPath) || process.cwd();
        if (path.basename(dbPath) === "mrowisko.db") {
            this.cwd = path.dirname(dbPath);
        }
        this.scriptPath = path.join(this.cwd, "tools", "agent_launcher_db.py");
    }
    run(args) {
        return (0, child_process_1.execFileSync)("py", [this.scriptPath, ...args], {
            cwd: this.cwd,
            encoding: "utf-8",
            timeout: 10000,
        });
    }
    runJson(args) {
        const output = this.run(args);
        return JSON.parse(output);
    }
    insert(sessionId, role, task, terminalName, permissionMode, spawnedBy) {
        this.run([
            "insert",
            "--session-id", sessionId,
            "--role", role,
            "--task", task,
            "--terminal-name", terminalName,
            "--permission-mode", permissionMode,
            "--spawned-by", spawnedBy,
        ]);
    }
    getActiveAgents() {
        const result = this.runJson(["list-active"]);
        return result.data.map(rowToLiveAgent);
    }
    markStopped(sessionId) {
        this.run(["mark-stopped", "--session-id", sessionId]);
    }
    cleanup() {
        this.run(["cleanup"]);
    }
    dispose() {
        // No persistent connection to close
    }
}
exports.Registry = Registry;
//# sourceMappingURL=registry.js.map