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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const crypto = __importStar(require("crypto"));
const path = __importStar(require("path"));
const registry_1 = require("./registry");
const spawner_1 = require("./spawner");
const watcher_1 = require("./watcher");
const approver_1 = require("./approver");
const commands_1 = require("./commands");
let registry;
let watcher;
let approver;
function activate(context) {
    const dbPath = resolveDbPath();
    const terminals = new Map();
    registry = new registry_1.Registry(dbPath);
    const spawner = new spawner_1.Spawner(registry, terminals);
    watcher = new watcher_1.Watcher(registry, terminals);
    approver = new approver_1.Approver(dbPath, spawner);
    watcher.activate();
    (0, commands_1.registerCommands)(context, registry, spawner, terminals);
    // Poll for pending invocations (approval gate)
    const pollInterval = vscode.workspace
        .getConfiguration("mrowisko")
        .get("pollIntervalMs", 5000);
    approver.start(pollInterval);
    // URI handler: allows spawning agents from CLI via
    // code --open-url "vscode://mrowisko.mrowisko-terminal-control?command=spawnAgent&role=developer&task=check+backlog"
    context.subscriptions.push(vscode.window.registerUriHandler({
        handleUri(uri) {
            const params = new URLSearchParams(uri.query);
            const command = params.get("command");
            if (command === "spawnAgent") {
                const role = params.get("role");
                const task = params.get("task");
                if (role && task) {
                    spawner.spawn({ role, task });
                    vscode.window.showInformationMessage(`Agent ${role} uruchomiony via URI: ${task}`);
                }
            }
            else if (command === "sendText") {
                const sessionId = params.get("sessionId");
                const text = params.get("text");
                if (sessionId && text) {
                    const terminal = terminals.get(sessionId);
                    if (terminal) {
                        terminal.sendText(text);
                    }
                }
            }
            else if (command === "pokeAgent") {
                const terminalName = params.get("terminalName");
                const message = params.get("message");
                if (terminalName && message) {
                    const terminal = vscode.window.terminals.find((t) => t.name === terminalName);
                    if (terminal) {
                        // Workaround: Claude Code 2.1.83 "/" artifact in input
                        terminal.sendText("", true);
                        setTimeout(() => {
                            terminal.sendText(message);
                        }, 300);
                        vscode.window.showInformationMessage(`Poke wysłany do: ${terminalName}`);
                    }
                    else {
                        vscode.window.showWarningMessage(`Terminal "${terminalName}" nie znaleziony.`);
                    }
                }
            }
            else if (command === "reload") {
                vscode.commands.executeCommand("workbench.action.reloadWindow");
            }
            else if (command === "listAgents") {
                vscode.commands.executeCommand("mrowisko.listAgents");
            }
            else if (command === "stopAgent") {
                const terminalName = params.get("terminalName");
                const sessionId = params.get("sessionId");
                // Prefer terminalName (works for all sessions), fallback to sessionId (spawned only)
                let terminal;
                if (terminalName) {
                    terminal = vscode.window.terminals.find((t) => t.name === terminalName);
                }
                else if (sessionId) {
                    terminal = terminals.get(sessionId);
                }
                if (terminal) {
                    terminal.sendText("/exit");
                    // Close terminal after Claude Code exits gracefully
                    setTimeout(() => terminal.dispose(), 3000);
                }
                else if (sessionId) {
                    registry?.markStopped(sessionId);
                }
            }
            else if (command === "resumeAgent") {
                const terminalName = params.get("terminalName");
                const claudeUuid = params.get("claudeUuid") || "";
                const spawnToken = params.get("spawnToken") || crypto.randomUUID();
                if (terminalName) {
                    const existing = vscode.window.terminals.find((t) => t.name === terminalName);
                    if (existing) {
                        // Terminal exists — send /resume
                        existing.sendText("/resume");
                        vscode.window.showInformationMessage(`Resume wysłany do: ${terminalName}`);
                    }
                    else {
                        // Terminal gone — create new and start claude --resume <uuid>
                        const locationSetting = vscode.workspace
                            .getConfiguration("mrowisko")
                            .get("terminalLocation", "editor");
                        const location = locationSetting === "editor"
                            ? vscode.TerminalLocation.Editor
                            : vscode.TerminalLocation.Panel;
                        const newTerminal = vscode.window.createTerminal({
                            name: terminalName,
                            location,
                            env: { MROWISKO_SPAWN_TOKEN: spawnToken },
                        });
                        const resumeCmd = claudeUuid
                            ? `claude --resume "${claudeUuid}"`
                            : "claude --resume";
                        newTerminal.sendText(resumeCmd);
                        newTerminal.show();
                        vscode.window.showInformationMessage(`Agent wznowiony w nowym terminalu: ${terminalName}`);
                    }
                }
            }
        },
    }));
    // Cleanup orphaned agents on startup
    registry.cleanup();
}
function deactivate() {
    approver?.dispose();
    watcher?.dispose();
    registry?.dispose();
}
function resolveDbPath() {
    const configured = vscode.workspace
        .getConfiguration("mrowisko")
        .get("dbPath", "mrowisko.db");
    if (path.isAbsolute(configured)) {
        return configured;
    }
    // Resolve relative to workspace root
    const folders = vscode.workspace.workspaceFolders;
    if (folders && folders.length > 0) {
        return path.join(folders[0].uri.fsPath, configured);
    }
    return configured;
}
//# sourceMappingURL=extension.js.map