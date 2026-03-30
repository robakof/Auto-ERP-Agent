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
exports.Spawner = void 0;
const vscode = __importStar(require("vscode"));
const crypto = __importStar(require("crypto"));
function getConfig(key, fallback) {
    return vscode.workspace.getConfiguration("mrowisko").get(key, fallback);
}
class Spawner {
    constructor(registry, terminals, layout) {
        this.registry = registry;
        this.terminals = terminals;
        this.layout = layout;
    }
    spawn(request) {
        const terminalName = `Agent: ${request.role}`;
        const spawnToken = crypto.randomUUID();
        const permissionMode = request.permissionMode ||
            vscode.workspace
                .getConfiguration("mrowisko")
                .get("defaultPermissionMode", "default");
        // Pre-register in DB before terminal exists
        this.registry.insert(spawnToken, request.role, request.task, terminalName, "human");
        // Determine terminal location — editor mode uses per-role ViewColumn
        const locationSetting = getConfig("terminalLocation", "editor");
        const location = locationSetting === "editor"
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
            // Workaround: Claude Code 2.1.83 injects "/" into input after startup.
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
        return terminal;
    }
}
exports.Spawner = Spawner;
//# sourceMappingURL=spawner.js.map