# Research Prompt: Środowisko pracy dla wielu agentów Claude Code

## Kontekst

Użytkownik pracuje na Windows Server 2022 w VS Code. Uruchamia równolegle wielu agentów
Claude Code (każdy w osobnym terminalu). Obecny problem: brak widoczności statusu agentów
na jednym ekranie — nie wiadomo który pracuje, który utknął, który zakończył.

Cel: znaleźć optymalne narzędzie lub konfigurację pozwalającą:
1. Widzieć wiele terminali z agentami Claude Code jednocześnie na jednym ekranie
2. Szybko ocenić status każdego agenta (aktywny / czeka / błąd / zakończony)
3. Wchodzić w interakcję z konkretnym agentem gdy potrzeba
4. Środowisko musi działać na Windows (natywnie lub przez WSL)

## Pytania badawcze

### P1: Terminal multiplexery na Windows
Które terminale/multipleksery pozwalają podzielić ekran na wiele paneli z osobnymi procesami?
Oceń: Windows Terminal (split panes), tmux przez WSL, Zellij przez WSL, ConEmu/Cmder.
Kryteria: łatwość konfiguracji, stabilność na Windows, możliwość nazwania paneli.

### P2: VS Code jako środowisko multi-agentowe
Czy VS Code pozwala wyświetlić wiele terminali jednocześnie (nie jako zakładki, ale jako
widoczne panele)? Jakie rozszerzenia lub konfiguracje to umożliwiają?
Sprawdź: panel terminali, rozszerzenie "Terminal Tabs", "Multi Root Workspace", "Activitus Bar".

### P3: Dedykowane narzędzia do monitorowania procesów CLI
Czy istnieją narzędzia zaprojektowane do monitorowania wielu długo-działających procesów CLI?
Sprawdź: `pm2` (node process manager — widok listy), `supervisor`, `foreman`/`overmind`,
`tmuxinator`/`zellij layouts`, narzędzia AI-specificzne (np. Claude Code MCP server status).

### P4: Wzorce pracy z Claude Code multi-agent
Jak inni użytkownicy Claude Code organizują pracę z wieloma agentami równolegle?
Sprawdź: GitHub Anthropic/claude-code discussions, Reddit r/ClaudeAI, X/Twitter wątki.
Czy istnieje oficjalny wzorzec (worktrees + terminal multiplexer)?

### P5: Status/heartbeat agenta z terminala
Czy Claude Code emituje jakiś sygnał który można przechwycić (exit code, plik statusu,
log, MCP event) pozwalający zewnętrznemu narzędziu wiedzieć że agent żyje lub zakończył?
Sprawdź: hooks w settings.json (stop/error hooks), pliki .claude/, exit codes.

## Output contract

Wyniki zapisz do: `documents/dev/research_results_multiagent_workspace.md`

Struktura:
```
## TL;DR — 3-5 kierunków godnych prototypu (z uzasadnieniem)

## P1: Terminal multipleksery — wyniki
[silność dowodów: wysoka/średnia/niska]

## P2: VS Code multi-terminal — wyniki

## P3: Narzędzia monitorowania CLI — wyniki

## P4: Wzorce Claude Code multi-agent — wyniki

## P5: Status/heartbeat agenta — wyniki

## Otwarte pytania (nierozstrzygnięte)
```

Zakaz oceny dopasowania do systemu — to osobny krok po researchu.
Priorytet: rozwiązania działające na Windows bez dużej konfiguracji.
