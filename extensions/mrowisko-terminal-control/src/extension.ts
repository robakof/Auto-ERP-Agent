import * as vscode from 'vscode';

/**
 * E4: Eksperyment kontroli terminali VS Code dla agentów Mrowisko
 *
 * Cel: Sprawdzić czy Claude Code Agent może programmatically:
 * 1. Utworzyć nowy terminal w VS Code
 * 2. Uruchomić komendę (np. claude -p "developer")
 * 3. Zostawić terminal interaktywny dla human
 */

export function activate(context: vscode.ExtensionContext) {
    console.log('Mrowisko Terminal Control activated');

    // Test 1: Prosty terminal z echo (najprostszy test - czy mogę tworzyć terminale)
    const testTerminal = vscode.commands.registerCommand('mrowisko.testTerminal', () => {
        const terminal = vscode.window.createTerminal('Mrowisko Test');
        terminal.show();
        terminal.sendText('echo Mrowisko Terminal Control - test OK');
        terminal.sendText('echo Czy widzisz ten output?');
        terminal.sendText('echo Jesli TAK - wtyczka ma kontrole nad terminalami!');

        vscode.window.showInformationMessage('Terminal utworzony! Sprawdź czy widzisz 3 linie outputu.');
    });

    // Test 2: Spawn agent (Claude Code)
    const spawnAgent = vscode.commands.registerCommand('mrowisko.spawnAgent', async () => {
        // Zapytaj o rolę
        const role = await vscode.window.showQuickPick(
            ['developer', 'erp_specialist', 'analyst', 'prompt_engineer'],
            { placeHolder: 'Wybierz rolę agenta' }
        );

        if (!role) {
            return;
        }

        // Zapytaj o task (uproszczony - box input)
        const task = await vscode.window.showInputBox({
            prompt: 'Wpisz task dla agenta',
            placeHolder: 'np. Sprawdź backlog Dev'
        });

        if (!task) {
            return;
        }

        // Utwórz terminal
        const terminal = vscode.window.createTerminal({
            name: `Agent: ${role}`,
            // Opcjonalnie: shellPath do claude bezpośrednio
            // shellPath: 'claude.cmd',
            // shellArgs: ['-p', role]
        });

        // Pokaż terminal
        terminal.show();

        // Wyślij komendę (Windows wymaga claude.cmd, escapowanie cudzysłowów)
        const systemPrompt = `[TRYB AUTONOMICZNY] Task: ${task}`;
        // Używamy pojedynczych apostrofów wewnątrz dla PowerShell
        const command = `claude.cmd -p ${role} --append-system-prompt "${systemPrompt.replace(/"/g, '\\"')}" --max-turns 10 --max-budget-usd 1.0`;

        terminal.sendText(command);

        vscode.window.showInformationMessage(`Agent ${role} uruchomiony w terminalu. Czy widzisz sesję Claude?`);
    });

    context.subscriptions.push(testTerminal);
    context.subscriptions.push(spawnAgent);
}

export function deactivate() {}
