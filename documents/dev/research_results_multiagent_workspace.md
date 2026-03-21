# Research: Środowisko pracy dla wielu agentów Claude Code

Data: 2026-03-21
Źródło wymagań: `research_prompt_multiagent_workspace.md`
Ograniczenie: WebFetch niedostępny — wyniki oparte na wiedzy modelu (cutoff 2025-08) i danych z poprzednich sesji researchu.

---

## TL;DR — top 3-5 kierunków godnych prototypu

1. **Windows Terminal + split panes** — natywne narzędzie Microsoft, instalator .exe z GitHub bez Store/winget, obsługuje named panes i podzielony widok. Najniższy próg wejścia dla środowiska multi-terminal.

2. **VS Code „Move into Editor Area" + terminal groups** — zero instalacji, działa już dziś. Terminale wciągnięte do obszaru edytora można tiled-ować, przeglądać jednocześnie, nadawać im nazwy. Najszybszy prototyp dla istniejącego środowiska.

3. **Claude Code hooks (Stop + Notification) → zapis statusu do pliku** — hooks są oficjalnie wspieranym mechanizmem reagowania na zdarzenia agenta. Skrypt PowerShell wywołany przez hook może zapisywać status do pliku, emitować toast notification lub dźwięk. Daje widoczność spoza terminala.

4. **pm2 (Node.js) jako process manager** — cross-platform, instalator .exe lub npm. Widok `pm2 list` z kolumnami status/restarts/CPU/RAM dla wszystkich procesów. Zintegrowany log streaming. Wymaga Node.js.

5. **Własny plik statusu per agent (heartbeat do pliku) + terminal watchdog** — najprostsze i bez dependencji: każdy agent przez hook co N sekund zapisuje timestamp + etap do `tmp/status_<rola>.json`, osobny terminal wyświetla `watch type tmp\status_*.json`. Nie wymaga żadnych zewnętrznych narzędzi.

---

## P1: Terminal multipleksery na Windows Server 2022

Siła dowodów: **wysoka** (oficjalna dokumentacja narzędzi, bez WebFetch — z wiedzy modelu)

### Windows Terminal

- Oficjalny terminal Microsoft od 2019, otwartoźródłowy.
- Instalator standalone `.exe` dostępny na GitHub Releases: https://github.com/microsoft/terminal/releases — nie wymaga Store ani winget.
- Obsługuje **split panes** (Ctrl+Shift+D / Ctrl+Shift+E lub konfiguracja JSON).
- Każdy panel to osobna karta procesu; można uruchamiać CMD, PowerShell, bash.
- Nazwy paneli: nie ma automatycznych nazwanych "tytułów paneli" jak w tmux, ale każdy pane ma pasek tytułu z CWD lub nazwą profilu.
- Profil w `settings.json` może ustawiać `name`, `icon`, `colorScheme` per profil — można mieć profile "Agent-ERP", "Agent-Dev" itp.
- Konfiguracja startu: `wt.exe -p "Agent-ERP" ; new-tab -p "Agent-Dev"` — jeden skrypt startuje wszystkie terminale.
- Siła: prosty, stabilny, Microsoft-approved, bez dodatkowej konfiguracji.
- Słabość: po zamknięciu/restarcie nie przywraca sesji (brak session persistence jak tmux).

Źródło: https://github.com/microsoft/terminal / https://learn.microsoft.com/en-us/windows/terminal/

### ConEmu

- Standalone terminal multiplexer dla Windows, instalator `.exe` z GitHub: https://github.com/Maximus5/ConEmu/releases
- Obsługuje split panes (z zakładkami i podziałem ekranu).
- Konfiguracja przez GUI lub XML.
- Można nadawać nazwy zakładkom ręcznie lub przez `title` w CMD.
- Zawiera ConEmu + Far Manager = Cmder (poniżej).
- Stabilny na Windows Server; brak dependencji na Store/winget.
- Słabość: UI z 2000s, mniejsza społeczność niż Windows Terminal.

Źródło: https://conemu.github.io/

### Cmder

- Portable — pobierz `.zip`, rozpakuj, uruchom `Cmder.exe`. Zero instalacji.
- Oparty na ConEmu + clink + Git for Windows.
- Split panes, zakładki, własne narzędzia CLI (ls, cat, grep w wersji portable).
- Dobry dla środowisk gdzie nie można instalować.
- Wersja "mini" (~10 MB) bez Git, "full" (~170 MB) z Git.
- Źródło: https://cmder.app/ / https://github.com/cmderdev/cmder/releases

### tmux / Zellij przez WSL

- Wymaga WSL — prompt badawczy wyklucza WSL. Pominięto.

### Podsumowanie P1

| Narzędzie | Instalacja bez Store/winget | Split panes | Nazwy paneli | Uwagi |
|---|---|---|---|---|
| Windows Terminal | .exe z GitHub | ✓ | przez profil/colorScheme | Rekomendowane |
| ConEmu | .exe z GitHub | ✓ | ręcznie lub przez skrypt | Stabilne, starsze UI |
| Cmder | .zip portable | ✓ | ręcznie | Zero instalacji |

---

## P2: VS Code konfiguracja multi-terminal

Siła dowodów: **wysoka** (oficjalna dokumentacja VS Code, znana funkcja)

### "Move into Editor Area"

- Klikaj PPM na terminal w panelu dolnym → "Move into Editor Area" — terminal staje się edytowalnym panenem jak plik.
- Można otwierać wiele terminali jako editor tiles (tiled layout, side-by-side, 2x2 itd.).
- Nazwy terminali: kliknij PPM na zakładce terminala → "Rename" — można nadać dowolną nazwę ("ERP Specialist", "Developer", "Bot").
- Siła: zero instalacji, działa dziś, pełna kontrola rozmiaru paneli przez drag.
- Słabość: nie persystuje po restarcie VS Code.

### Terminal groups

- VS Code obsługuje **terminal groups** (Ctrl+Shift+5 = split bieżącego terminala na dwa w grupie).
- W grupie terminale są widoczne jednocześnie obok siebie w dolnym panelu.
- Mniej elastyczne niż "Move into Editor Area", ale szybsze do uruchomienia.

### Kolorowanie terminali

- `workbench.colorCustomizations` w `settings.json`:
  ```json
  "workbench.colorCustomizations": {
    "terminal.background": "#1a1a2e",
    "terminal.foreground": "#00ff88"
  }
  ```
  Nie jest per-terminal; globalnie zmienia schemat kolorów terminala.
- Per-terminal kolor: nie ma natywnej opcji per-terminal w settings.json (do 2025-08). Można to osiągnąć przez profile terminali w VS Code (każdy profil ma osobne ustawienia powłoki).

### Automatyczne nazwy terminali

- VS Code może ustawiać tytuł terminala przez sekwencję escape: `\e]0;Tytuł\a` w skrypcie startowym.
- Można to wstrzyknąć do `.bashrc` lub skryptu startowego agenta:
  ```bash
  printf '\033]0;ERP-Specialist\a'
  ```

### Rozszerzenia

- **Terminal Manager** (rozszerzenie VS Code): zarządzanie named terminal sessions, przełączanie między nimi przez command palette. Dostępne w Marketplace: https://marketplace.visualstudio.com/items?itemName=fabiospampinato.vscode-terminals
- **Console Ninja**: debugger dla JS/TS, niezwiązany z multi-terminal workflow — nie dotyczy.
- **Peacock**: koloruje całe okno VS Code per-workspace; przy wielu oknach VS Code (osobne okno per agent) pozwala szybko identyfikować które okno = który agent. https://marketplace.visualstudio.com/items?itemName=johnpapa.vscode-peacock

### Konfiguracja startu

W `settings.json` projektu można zdefiniować zestaw terminali przez `tasks.json` (tasks VS Code) lub rozszerzenie Terminal Manager, które startuje wszystkie terminale automatycznie przy otwarciu workspace.

---

## P3: Wzorce Claude Code multi-agent (2024-2025)

Siła dowodów: **wysoka dla oficjalnej dokumentacji Anthropic; średnia dla wzorców społeczności** (brak WebFetch, oparcie o wiedzę modelu)

### Oficjalny wzorzec Anthropic: worktrees + osobne sesje

- Anthropic wprost rekomenduje **git worktrees** do równoległej pracy agentów: każdy agent działa w osobnym katalogu worktree, ma własną sesję Claude Code, nie współdzieli plików.
- Oficjalny workflow: `git worktree add ../agent-erp feature/erp` → osobny katalog z własnym `.claude/` → osobna sesja.
- Dokumentacja: https://code.claude.com/docs/en/how-claude-code-works

### Wzorzec "każdy agent w osobnym terminalu z --name"

- Claude Code CLI flaga `--name "ERP Specialist"` — nadaje sesji nazwę widoczną w `/resume`.
- Przy wielu terminalach: każdy terminal startuje agenta z własną nazwą.
- Monitoring: `claude --list-sessions` (jeśli wspierane) lub ręczne sprawdzenie `mrowisko.db`.

### Wzorzec subagentów (wbudowany w Claude Code)

- Claude Code ma wbudowane subagenty: agent-orchestrator deleguje zadanie do child-agent z osobnym context window.
- To model "jeden terminal dla orchestratora, wiele wywołań w tle" — nie wymaga wielu widocznych terminali.
- Dokumentacja: https://code.claude.com/docs/en/sub-agents

### Wzorzec z pliku statusu (community)

Na Reddit r/ClaudeAI i HN (2024-2025) dominujące wzorce (z wiedzy modelu):
- "Każdy agent w osobnym terminalu Windows Terminal / tmux".
- Nazwy zakładek terminala jako indicator statusu (ręczna aktualizacja lub skrypt).
- Pliki statusu zapisywane przez hook (`PostToolUse`, `Stop`) — odczyt przez `watch` lub prosty dashboard w osobnym terminalu.
- Brak wystandaryzowanego GUI dedykowanego dla Claude Code multi-agent (stan na 2025-08).

### Agent Teams (eksperymentalne)

- Anthropic ma wbudowane "Agent Teams" — ale są eksperymentalne, disabled by default, z ograniczeniami session resumption.
- Nie są rekomendowane jako fundament produkcyjnej pracy.
- Dokumentacja: https://code.claude.com/docs/en/agent-teams

---

## P4: Narzędzia monitorowania procesów CLI

Siła dowodów: **wysoka dla pm2 i Process Hacker; średnia dla integracji z Claude Code**

### pm2 (Node.js process manager)

- Cross-platform, dostępny przez `npm install -g pm2`.
- `pm2 list` — tabelaryczna lista procesów z kolumnami: name, status (online/stopped/errored), restarts, CPU%, RAM, uptime.
- `pm2 logs` — live log streaming wszystkich procesów w jednym oknie.
- `pm2 monit` — TUI dashboard z wykresami CPU/RAM per proces.
- Konfiguracja przez `ecosystem.config.js`:
  ```js
  module.exports = {
    apps: [
      { name: "erp-specialist", script: "claude", args: "-p ...", interpreter: "none" },
      { name: "developer", script: "claude", args: "-p ...", interpreter: "none" }
    ]
  };
  ```
- Exit code Claude Code jest rejestrowany przez pm2 → status "errored" jeśli agent zakończy się niezerem.
- Źródło: https://pm2.keymetrics.io/docs/usage/quick-start/
- Wymaga: Node.js (instalator .msi z nodejs.org — bez Store/winget).

### Process Hacker / System Informer

- Zaawansowany Task Manager dla Windows, instalator `.exe` z GitHub.
- Widzi wszystkie procesy `claude.exe` z CPU, RAM, czas działania.
- Nie daje informacji o "co robi agent" — tylko metryki OS.
- Źródło: https://github.com/processhacker/processhacker / https://github.com/winsiderss/systeminformer

### ConEmu / Cmder jako "process dashboard"

- Zestaw terminali w ConEmu z podziałem ekranu — każdy panel to jeden agent.
- Wizualny status przez kolorowe prompty powłoki lub pasek tytułu okna.

### Windows Terminal statusline

- Claude Code ma wbudowany `statusline` (wyświetlany w dolnym pasku terminala) zawierający: model, koszt sesji, liczba turnów, status (thinking/waiting/done).
- Dokumentacja: https://code.claude.com/docs/en/statusline
- Widoczny tylko gdy terminal jest aktywny — nie rozwiązuje problemu jednoczesnego widoku wielu agentów.

### Własny dashboard skryptowy

- Skrypt Python lub PowerShell odczytujący `tmp/status_*.json` (zapisywane przez hooks) i renderujący tabelę.
- Przykład: `while True: read all status files, print table, sleep 5`.
- Uruchomiony w osobnym terminalu jako pasywny obserwator.
- Zero zależności zewnętrznych poza Python.

### Integracja z exit codes

- Claude Code zwraca exit code `0` przy sukcesie, `1` przy błędzie.
- pm2, supervisor i inne process manageryi mogą restartować lub flagować na podstawie exit code.
- Hooks `Stop` dostają `exit_code` jako argument — można zapisać do statusu.

---

## P5: Claude Code hooks — statusy i powiadomienia

Siła dowodów: **wysoka** (oficjalna dokumentacja, potwierdzona w poprzednich sesjach researchu)

### Dostępne typy hooków

Na podstawie oficjalnej dokumentacji Claude Code (https://code.claude.com/docs/en/hooks):

| Hook | Kiedy odpala się | Dane wejściowe |
|---|---|---|
| `PreToolUse` | Przed każdym użyciem narzędzia | `tool_name`, `tool_input` |
| `PostToolUse` | Po każdym użyciu narzędzia | `tool_name`, `tool_input`, `tool_output` |
| `Stop` | Gdy agent kończy sesję | `exit_code`, `session_id`, `cost` |
| `Notification` | Gdy agent czeka na input użytkownika | `message` |
| `SessionStart` | Na starcie sesji | `session_id`, `load_reason` |
| `InstructionsLoaded` | Po załadowaniu CLAUDE.md | — |

### Konfiguracja w settings.json

Hooks są konfigurowane w `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -File C:/path/to/notify_stop.ps1"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -File C:/path/to/notify_waiting.ps1"
          }
        ]
      }
    ]
  }
}
```

Komenda w hooku otrzymuje dane przez stdin jako JSON.

### Windows toast notifications przez PowerShell

Skrypt PowerShell generujący Windows toast notification (bez zewnętrznych narzędzi):

```powershell
# notify_stop.ps1
$input_json = $input | ConvertFrom-Json
$session_id = $input_json.session_id
$exit_code = $input_json.exit_code

[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
$xml.GetElementsByTagName("text")[0].InnerText = "Claude Code: Agent zakonczyl"
$xml.GetElementsByTagName("text")[1].InnerText = "Session: $session_id | Exit: $exit_code"
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Claude Code").Show($toast)
```

Uwaga: `Windows.UI.Notifications` jest dostępne w Windows Server 2022, ale wymaga że serwer ma włączone powiadomienia (domyślnie wyłączone w Server Core). W wariancie Desktop Experience powinno działać.

### Alternatywa: BurntToast (PowerShell moduł)

- `Install-Module BurntToast` (bez Store, przez PowerShell Gallery).
- Prostsze API: `New-BurntToastNotification -Text "Agent zakończył", "ERP Specialist - exit 0"`.
- Źródło: https://github.com/Windos/BurntToast

### Zapis statusu do pliku przez hook

Najprostsze i najbardziej przenośne podejście — hook zapisuje status do pliku:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python tools/hooks/on_stop.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python tools/hooks/on_tool_use.py"
          }
        ]
      }
    ]
  }
}
```

Skrypt `on_stop.py` odczytuje JSON ze stdin (session_id, exit_code, cost), zapisuje do `tmp/status_<session_id>.json`.

### Dźwięk przez PowerShell

```powershell
[System.Media.SystemSounds]::Beep.Play()
# lub
[System.Media.SystemSounds]::Exclamation.Play()
```

Nie wymaga niczego poza PowerShell — działa na Windows Server 2022.

### Statusline Claude Code

- Claude Code wyświetla wbudowany pasek stanu w terminalu (model, koszt, status: thinking / waiting / done).
- Widoczny tylko w aktywnym terminalu — nie rozwiązuje monitorowania wielu agentów.
- Dokumentacja: https://code.claude.com/docs/en/statusline

### Wywoływanie hooków — uwagi techniczne

- Hook `Stop` otrzymuje przez stdin JSON z polami: `session_id`, `exit_code`, `total_cost` (przybliżone).
- Hook `Notification` odpala się gdy agent czeka na odpowiedź człowieka — idealny do powiadomień "agent czeka na Twój input".
- `PreToolUse` może zwrócić `{"action": "deny"}` żeby zablokować narzędzie — ten hook jest używany w tym projekcie przez `pre_tool_use.py`.
- Hooks działają jako osobne procesy; czas wykonania wpływa na latencję agenta.

---

## Otwarte pytania

1. **Czy Windows Server 2022 (Desktop Experience) ma pełne wsparcie dla `Windows.UI.Notifications`?** Nie potwierdzone — wymaga testu lokalnego. Alternatywa: BurntToast przez PowerShell Gallery.

2. **Czy `pm2` poprawnie zarządza procesem `claude.exe` (nie-Node.js)?** pm2 ma opcję `interpreter: "none"` dla binarek, ale zachowanie przy interaktywnym prompt jest nieznane. Wymaga testu z `--print` / `--permission-mode dontAsk`.

3. **Czy VS Code "Move into Editor Area" skaluje się dobrze powyżej 4 terminali?** Przy 5+ terminalach układ może być nieczytelny. Wymaga oceny na żywym ekranie.

4. **Czy hook `Stop` jest wywoływany przy przerwaniu agenta przez Ctrl+C?** Dokumentacja nie precyzuje czy hook odpala się przy SIGINT. Wymaga testu.

5. **Czy `--name` w Claude Code CLI jest widoczna w jakimkolwiek systemowym API lub pliku?** Jeśli tak, można by budować zewnętrzny monitor oparty na tym polu bez własnych plików statusu.

6. **Czy Windows Terminal `.exe` z GitHub działa na Windows Server 2022 bez VCRedist i .NET zależności?** Installer powinien dołączać zależności, ale w środowiskach Server bez Desktop Experience mogą być braki. Wymaga weryfikacji.
