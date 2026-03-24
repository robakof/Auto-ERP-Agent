## TL;DR — 3-5 kierunków godnych prototypu (z uzasadnieniem)

1. **Windows Terminal + podzielone panele + jawne tytuły paneli/okien**  
   Najmniejszy próg wejścia po stronie Windows. Oficjalnie wspiera wiele paneli w jednym tabie, sterowanie fokusem między panelami oraz nadawanie tytułów panelom przy starcie. Daje „widzę wiele sesji naraz” bez dodatkowej warstwy orkiestracji.

2. **VS Code z terminalami osadzonymi w editor area + zapisany layout + terminal tabs**  
   VS Code potrafi pokazać terminale nie tylko jako zakładki w panelu, ale też jako pełnoprawne edytory ułożone w gridzie. Do tego dochodzą trwałe sesje, przeciąganie terminali między oknami, nazwy terminali i status/progress w terminal tabs. To jest najbardziej „IDE-native” kierunek.

3. **tmux przez WSL + git worktrees + ewentualna warstwa statusowa**  
   To jest najsilniej udokumentowany wzorzec po stronie Claude Code: równoległe sesje w oddzielnych worktree. Sam tmux daje klasyczny model sesja/okno/panel, a społeczność dobudowuje do niego status bary i dashboardy (np. tmux-agent-status, recon). To jest raczej kierunek „bardziej operatorski” niż „zero-config”.

4. **Zellij przez WSL + layouts/sessions/resurrection**  
   Jeśli celem jest szybkie odtwarzanie tego samego układu agentów, Zellij ma gotowe layouty, nazwane sesje i session resurrection. W dokumentacji jest jasno zaznaczone, że na Windows działa przez WSL.

5. **Osobna warstwa monitoringu procesów / agentów (PM2, Overmind, CCManager, Agent Deck)**  
   To nie zastępuje terminala wielopanelowego, ale może rozwiązać część problemu „który agent żyje / czeka / skończył”. W tej grupie trzeba odróżnić narzędzia ogólne do procesów CLI od nieoficjalnych narzędzi AI-specificznych budowanych przez społeczność.

---

## P1: Terminal multipleksery — wyniki

**[silność dowodów: wysoka dla Windows Terminal/tmux/Zellij/ConEmu; średnia dla Cmder jako wariantu ConEmu]**

### Windows Terminal (split panes)
- Oficjalnie wspiera **wiele paneli obok siebie w ramach jednego taba**.
- Ma wbudowane akcje do **przełączania fokusu między panelami** i **zamiany paneli miejscami**.
- Da się nadawać **tytuły panelom** przy uruchamianiu z linii poleceń (`wt --title ... ; split-pane ... --title ...`).
- Da się kierować nowe układy do **nazwanego okna terminala** (`wt -w <name>`), co pomaga organizować zestawy agentów.
- Uwaga praktyczna z dokumentacji: gdy sterujesz `wt.exe` z WSL, trzeba użyć `cmd.exe /c "wt.exe"`, bo aliasy wykonania nie działają z poziomu dystrybucji WSL.
- Wniosek badawczy: Windows Terminal ma najmocniej udokumentowaną, natywną ścieżkę do „wiele agentów na jednym ekranie”, ale sam z siebie nie daje semantycznych stanów typu *idle/busy/error* — trzeba je dorobić przez nazewnictwo, prompt/statusline albo zewnętrzny monitoring.

### tmux przez WSL
- `tmux` ma klasyczny model **sessions / windows / panes** i pozwala widzieć wiele paneli jednocześnie.
- Oficjalne materiały tmux opisują **nazwane okna** jako element podstawowego modelu pracy.
- Po stronie Windows/WSL Microsoft od lat dokumentuje wsparcie dla scenariuszy z `tmux` dzięki obsłudze pseudo-terminali w WSL.
- Mocna strona: ogromny ekosystem dodatkowych warstw (tmuxinator, overmind, status bary, community dashboards).
- Słabsza strona: wymaga WSL i większej ilości konfiguracji niż Windows Terminal.

### Zellij przez WSL
- Dokumentacja Zellij mówi wprost, że **Windows jest wspierany przez WSL**.
- Zellij ma **nazwane sesje**, listowanie sesji, możliwość attachowania po nazwie oraz **layouty jako pliki tekstowe**, więc łatwo odtwarzać stały układ agentów.
- Ma też **session resurrection**, czyli odtwarzanie sesji po zamknięciu lub restarcie.
- Wniosek badawczy: Zellij jest mocny tam, gdzie priorytetem jest powtarzalny layout i odtwarzanie środowiska, a nie maksymalna zgodność z „typowym” ekosystemem tmux.

### ConEmu / Cmder
- ConEmu oficjalnie wspiera **podział ekranu na panele** z dowolną siatką.
- Ma mechanizm **Tasks**, który potrafi startować kilka konsol i predefiniowane splity jednym poleceniem.
- ConEmu jest opisywany jako host dla aplikacji konsolowych, w tym także dla powłok WSL.
- `cmder` nie jest osobnym silnikiem terminala — to **pakiet zbudowany wokół ConEmu**. Dokumentacja ConEmu zaznacza, że cmder dodaje własne modyfikacje, więc część problemów może być specyficzna dla cmder, a nie dla samego ConEmu.
- Wniosek badawczy: ConEmu/Cmder daje natywne splity i taski na Windows, ale ciężar społeczności i nowoczesnej dokumentacji jest dziś wyraźnie słabszy niż przy Windows Terminal + WSL/tmux.

---

## P2: VS Code multi-terminal — wyniki

**[silność dowodów: wysoka]**

### Czy VS Code potrafi pokazać wiele terminali jednocześnie jako widoczne panele?
Tak. Oficjalna dokumentacja potwierdza, że terminale można otwierać **w editor area**, a nie tylko w dolnym panelu. Ponieważ są wtedy traktowane jak edytory, można je układać w **wiele grup edytora** i tworzyć z nich siatkę widoczną jednocześnie.

### Co daje built-in VS Code bez rozszerzeń?
- **Terminale w editor area**.
- **Split terminals** i **terminal tabs**.
- **Przeciąganie terminali** między panelami i między oknami VS Code.
- **Persistent sessions** — VS Code potrafi odtwarzać terminale po restarcie.
- **Zapamiętywanie layoutu** interfejsu między sesjami.
- Możliwość ustawienia `terminal.integrated.defaultLocation`, żeby nowe terminale trafiały domyślnie do editor area.

### Nazwy i szybka ocena statusu
- Terminal można **ręcznie nazwać**.
- Terminal tabs mają rozbudowaną konfigurację tytułu i opisu, w tym zmienne takie jak `${workspaceFolderName}`, `${cwdFolder}`, `${sequence}` oraz `${progress}`.
- VS Code pokazuje też **ikony/stany na terminal tabs**; w praktyce może to być użyteczne do rozróżniania terminali uruchamianych jako taski.
- Od wersji 1.97 VS Code wspiera sekwencję postępu używaną przez **ConEmu**, a `${progress}` można pokazać w tytule/opisie taba.

### Automatyczny start wielu agentów
Dokumentacja `tasks.json` pokazuje, że da się grupować taski tak, by po uruchomieniu otworzyły się jako osobne terminale w tej samej grupie terminali. Etykieta taska jest naturalnym kandydatem na nazwę zakładki/sesji.

### Co z badanymi rozszerzeniami?
- **Terminal Tabs**: rozszerzenie jest **deprecated**, bo terminal tabs są już wbudowane w VS Code.
- **Multi Root Workspace**: przydatne do trzymania wielu repozytoriów/worktree w jednym oknie, ale samo z siebie **nie rozwiązuje** wizualizacji statusu agentów; to raczej warstwa organizacji folderów.
- **Activitus Bar**: odtwarza przyciski activity bar na status barze, więc może odzyskać trochę miejsca na ekranie, ale **nie jest** rozwiązaniem multi-terminalowym.

### Wniosek badawczy
VS Code ma realny, oficjalnie wspierany tryb pracy „wiele terminali widocznych jednocześnie” bez potrzeby doinstalowywania Terminal Tabs. Najciekawsze elementy do dalszego prototypu to: **editor-area terminals, zapisany layout, persistent sessions, nazwy terminali, `${progress}` oraz tasks.json**.

---

## P3: Narzędzia monitorowania procesów CLI — wyniki

**[silność dowodów: średnia; wysoka dla istnienia narzędzi, niższa dla ich dopasowania do interaktywnego multi-agent workspace]**

### PM2
- PM2 ma tryb **`pm2 monit`** do monitorowania CPU i pamięci w terminalu.
- CLI PM2 ma też komendy typu **`list/status/jlist/prettylist/monit/dashboard/logs`**.
- To jest dobre narzędzie do **monitoringu procesów**, ale nie jest naturalnie zaprojektowane jako interaktywny „terminal cockpit” dla wielu ręcznie prowadzonych sesji Claude Code.

### Supervisor
- Supervisor to system kontroli procesów dla **UNIX-like OS**.
- Potrafi utrzymywać procesy długożyjące i raportować ich status, ale nie jest narzędziem do wygodnej interakcji z wieloma aktywnymi TTY na jednym ekranie.

### Foreman / Overmind
- `foreman` uruchamia procesy z **Procfile**; to bardziej launcher niż dashboard.
- `overmind` jest zbudowany wokół **tmux**: startuje procesy Procfile w jednej sesji tmux, pozwala podłączyć się do konkretnego procesu i restartować pojedyncze procesy.
- Dokumentacja Overmind wskazuje wsparcie dla **Linux/*BSD/macOS**, bez natywnego Windows.
- Wniosek badawczy: Overmind jest interesujący jako warstwa „procfile + tmux”, ale badawczo należy go traktować jako rozwiązanie **WSL/tmux-first**, a nie natywne Windows.

### tmuxinator / Zellij layouts
- `tmuxinator` zapisuje złożone sesje tmux w **YAML** i potrafi nawet wygenerować projekt z istniejącej sesji.
- Zellij ma analogiczną ideę w postaci **layoutów** i dodatkowo session resurrection.
- To nie są monitory statusu procesów sensu stricte; to raczej narzędzia do **powtarzalnego odtwarzania środowiska wielu paneli**.

### AI-specific / community tools

#### CCManager
- Repo opisuje to jako **Coding Agent Session Manager** dla wielu agentów/CLI.
- Deklaruje **visual status indicators** (np. busy / waiting / idle) i zarządzanie sesjami bez zależności od tmux.
- To wygląda najbliżej „menedżera wielu agentów” niż klasyczny process manager, ale to narzędzie **społecznościowe, nieoficjalne**.

#### tmux-agent-status
- Narzędzie do status bara tmux pokazującego, które sesje agenta są zajęte, a które idle.
- Autor deklaruje, że **Claude Code support jest hook-based** i stabilny.
- To ważna obserwacja: społeczność rozwiązuje problem statusu Claude Code głównie przez **hooki**, a nie przez oficjalne API sesji.

#### recon
- Repo opisuje je jako **tmux-native dashboard** dla agentów Claude Code.
- Celowo jest pozycjonowane jako dashboard na **side monitor**.

#### Agent Deck
- Repo pozycjonuje to jako **TUI mission control** dla agentów AI.
- Deklaruje szybki podgląd statusu sesji, przełączanie, grupy, powiadomienia i obsługę worktree.
- Autor deklaruje działanie na **Windows przez WSL**.

### Wniosek badawczy
Rynek dzieli się na trzy klasy:
1. **process managers** (PM2, Supervisor) — dobre do statusu procesów, słabsze do interakcji TTY;  
2. **workspace orchestrators** (Overmind, tmuxinator, Zellij layouts) — dobre do layoutu i odtwarzalności;  
3. **community AI dashboards** (CCManager, tmux-agent-status, recon, Agent Deck) — najbliższe problemowi „który agent pracuje / czeka / skończył”, ale z niższą siłą dowodów niż dokumentacja oficjalna.

---

## P4: Wzorce Claude Code multi-agent — wyniki

**[silność dowodów: wysoka dla oficjalnej dokumentacji Claude Code; niska/średnia dla praktyk społeczności]**

### Oficjalny wzorzec Anthropic / Claude Code
Najmocniej udokumentowany wzorzec to **równoległe sesje Claude Code w osobnych git worktree**.

Dokumentacja Claude Code opisuje:
- `claude --worktree <name>` jako mechanizm tworzenia równoległej sesji w osobnym worktree;
- domyślną lokalizację worktree pod `.claude/worktrees/<name>`;
- branch tworzony dla worktree;
- czyszczenie worktree po zakończeniu sesji;
- integrację tego wzorca także w dokumentacji użycia Claude Code z VS Code.

To jest najsilniejsza oficjalna odpowiedź na problem „wielu agentów równolegle bez konfliktów w repo”.

### Agent Teams
Claude Code ma też funkcję **Agent Teams**, ale dokumentacja oznacza ją jako **eksperymentalną**.

Istotne elementy z punktu widzenia środowiska pracy:
- są tryby wyświetlania `in-process` oraz **split panes**;
- tryb split panes wymaga **tmux albo iTerm2**;
- ustawienie `teammateMode` może być `auto / in-process / tmux`;
- gdy pracujesz już wewnątrz sesji tmux, tryb `auto` preferuje **split panes**.

To sugeruje, że po stronie oficjalnego produktu tmux jest uznawany za naturalny mechanizm wizualizacji wielu współpracujących sesji.

### Wzorce społecznościowe
W społeczności powtarzają się trzy motywy:
1. **worktrees są obowiązkowe** przy wielu agentach równoległych;
2. **tmux** jest domyślnym „operacyjnym pulpitem” do trzymania wielu sesji;
3. do każdej sesji przypina się oddzielny kontekst zadania (branch/worktree/CLAUDE.md/prompt wejściowy).

Dowody społeczne są jednak głównie anegdotyczne: wątki Reddit/GitHub/X opisują praktyki użytkowników, a nie stabilny standard produktu.

### Wniosek badawczy
Oficjalny wzorzec Claude Code to nie „dedykowany dashboard”, tylko raczej kombinacja:
- **worktrees do izolacji repo**,
- **równoległe sesje**,
- opcjonalnie **tmux/split panes** tam, gdzie potrzebna jest jednoczesna widoczność.

---

## P5: Status/heartbeat agenta — wyniki

**[silność dowodów: średnia]**

### Co jest oficjalnie udokumentowane jako sygnał stanu?
Claude Code ma rozbudowany system **hooków**. Oficjalnie udokumentowane zdarzenia obejmują m.in.:
- `SessionStart`
- `SessionEnd`
- `Stop`
- `StopFailure`
- `Notification`
- `SubagentStart`
- `SubagentStop`
- `TeammateIdle`
- `TaskCompleted`
- `WorktreeCreate`

To oznacza, że zewnętrzne narzędzie może reagować na konkretne momenty życia sesji/agenta, zamiast zgadywać status wyłącznie po procesie OS.

### Jakie dane są dostępne w hookach?
Dokumentacja hooków pokazuje, że payloady mogą zawierać m.in.:
- **`transcript_path`** / ścieżki do transcriptów,
- **`agent_transcript_path`** dla subagenta,
- **`last_assistant_message`**,
- **`error` / `error_details`** przy `StopFailure`,
- **`reason`** przy `SessionEnd`,
- **`notification_type`** przy `Notification`,
- nazwę teammate lub teamu przy `TeammateIdle`.

To są realne, maszynowo-przetwarzalne sygnały do budowy zewnętrznego dashboardu stanu.

### Exit codes hooków
Dokumentacja jasno opisuje semantykę kodów wyjścia hooka:
- `0` = sukces,
- `2` = zdarzenie blokujące / specjalne zachowanie dla części hooków,
- inne kody = błędy nieblokujące w wielu przypadkach.

To ważne, bo pozwala nie tylko obserwować zdarzenia, ale też sterować przepływem w niektórych punktach cyklu życia sesji.

### Status line i powiadomienia
- Claude Code ma oficjalnie wspieraną **status line**, którą można skonfigurować własnym poleceniem; dokumentacja zawiera również **przykłady dla Windows**.
- Oficjalne workflow opisuje też **Notification hooks** do sygnalizowania, że Claude potrzebuje uwagi użytkownika.
- W ustawieniach istnieje także flaga **`terminalProgressBarEnabled`** dla wspieranych terminali.

### Telemetria / observability
Claude Code ma oficjalną dokumentację **OpenTelemetry monitoring**. Można eksportować metryki/zdarzenia/logi związane z użyciem i sesjami. To jest bardziej warstwa obserwowalności niż prosty „panel sesji”, ale może stanowić źródło sygnałów do własnego monitoringu.

### MCP / oficjalne API statusu
W dokumentacji Agent SDK istnieje `mcpServerStatus()`, ale to dotyczy **statusu podłączonych serwerów MCP**, a nie wielosesyjnego dashboardu interaktywnych sesji Claude Code.

### Najważniejsza odpowiedź na pytanie o heartbeat
Na podstawie znalezionej dokumentacji **nie znalazłem oficjalnie udokumentowanego lokalnego „heartbeat file” lub prostego API „czy ta interaktywna sesja nadal żyje”** dla zwykłych sesji Claude Code.  
Najbliższe temu, co da się dziś sensownie wykorzystać, to:
1. **hooki zdarzeń**,  
2. **ścieżki transcriptów i event payloady**,  
3. **status line / progress bar**,  
4. **OpenTelemetry export**,  
5. ewentualnie społecznościowe warstwy statusowe bazujące na hookach.

---

## Otwarte pytania (nierozstrzygnięte)

1. Czy `terminalProgressBarEnabled` w praktyce daje na Windows Terminal na tyle czytelny sygnał, by bez dodatkowych hooków napędzać status w terminal tabs / tytułach?
2. Na ile stabilnie działa tryb `Agent Teams` + `tmux` na Windows Server 2022 przez WSL w długich sesjach produkcyjnych? Dokumentacja pokazuje model, ale nie znalazłem równie mocnych źródeł z pola dla tego dokładnego środowiska.
3. Które z community dashboards (CCManager / recon / Agent Deck / tmux-agent-status) używają wyłącznie hooków Claude Code, a które dodatkowo polegają na własnym modelu procesów/sesji?
4. Czy istnieje ukryty lub słabiej udokumentowany interfejs CLI/API do enumeracji aktywnych interaktywnych sesji Claude Code poza warstwą hooków i telemetry?
5. Jak dobrze VS Code terminal tabs + `${progress}` współpracują z sygnałami pochodzącymi z Claude Code w realnym, wielosesyjnym układzie na Windows?
