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
exports.registerCommands = registerCommands;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
function loadRoles() {
    try {
        const folders = vscode.workspace.workspaceFolders;
        if (!folders) {
            return [];
        }
        const configPath = path.join(folders[0].uri.fsPath, "config", "session_init_config.json");
        const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
        return Object.keys(config).map((role) => ({ label: role }));
    }
    catch {
        return [
            { label: "developer" },
            { label: "erp_specialist" },
            { label: "analyst" },
            { label: "architect" },
            { label: "prompt_engineer" },
            { label: "metodolog" },
        ];
    }
}
function registerCommands(context, registry, spawner, terminals) {
    context.subscriptions.push(vscode.commands.registerCommand("mrowisko.spawnAgent", () => spawnAgent(spawner)), vscode.commands.registerCommand("mrowisko.listAgents", () => listAgents(registry, terminals)), vscode.commands.registerCommand("mrowisko.stopAgent", () => stopAgent(registry, terminals)));
}
async function spawnAgent(spawner) {
    const role = await vscode.window.showQuickPick(loadRoles(), {
        placeHolder: "Wybierz role agenta",
    });
    if (!role) {
        return;
    }
    const task = await vscode.window.showInputBox({
        prompt: "Opisz zadanie dla agenta",
        placeHolder: "np. sprawdz backlog i wykonaj najwyzszy priorytet",
    });
    if (!task) {
        return;
    }
    spawner.spawn({ role: role.label, task });
    vscode.window.showInformationMessage(`Agent ${role.label} uruchomiony: ${task}`);
}
async function listAgents(registry, terminals) {
    const agents = registry.getActiveAgents();
    if (agents.length === 0) {
        vscode.window.showInformationMessage("Brak aktywnych agentow.");
        return;
    }
    const items = agents.map((a) => ({
        label: `${a.role} [${a.status}]`,
        description: a.task || "",
        detail: `session: ${a.sessionId.slice(0, 8)}... | ${a.createdAt}`,
        sessionId: a.sessionId,
    }));
    const selected = await vscode.window.showQuickPick(items, {
        placeHolder: "Aktywni agenci (wybierz aby przejsc do terminala)",
    });
    if (selected) {
        const terminal = terminals.get(selected.sessionId);
        if (terminal) {
            terminal.show();
        }
        else {
            vscode.window.showWarningMessage("Terminal nie jest dostepny w tym oknie.");
        }
    }
}
async function stopAgent(registry, terminals) {
    const agents = registry.getActiveAgents();
    if (agents.length === 0) {
        vscode.window.showInformationMessage("Brak aktywnych agentow do zatrzymania.");
        return;
    }
    const items = agents.map((a) => ({
        label: `${a.role} [${a.status}]`,
        description: a.task || "",
        detail: `session: ${a.sessionId.slice(0, 8)}...`,
        sessionId: a.sessionId,
    }));
    const selected = await vscode.window.showQuickPick(items, {
        placeHolder: "Wybierz agenta do zatrzymania",
    });
    if (!selected) {
        return;
    }
    const terminal = terminals.get(selected.sessionId);
    if (terminal) {
        terminal.dispose();
        // onDidCloseTerminal watcher handles DB cleanup
    }
    else {
        // Terminal not in this window — mark stopped directly
        registry.markStopped(selected.sessionId);
    }
    vscode.window.showInformationMessage(`Agent ${selected.label} zatrzymany.`);
}
//# sourceMappingURL=commands.js.map