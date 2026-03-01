# Instrukcja instalacji — Automatyczny Konfigurator ERP

Wymagane uprawnienia administratora.

> **Uwaga dla Windows Server:** `winget` nie jest dostępny na Windows Server 2022.
> Wszystkie narzędzia instaluj ręcznie (linki poniżej).

---

## Krok 1 — Zainstaluj Git

Sprawdź czy już zainstalowany:
```
git --version
```

Jeśli nie — pobierz i zainstaluj: https://git-scm.com/download/win (Windows 64-bit)

> **Uwaga:** Na Windows Server Git instaluje się często per-user, nie globalnie.
> Jeśli `git --version` działa, ale `where git` zwraca ścieżkę pod
> `C:\Users\<USER>\AppData\Local\Programs\Git\...` — to normalne, instalacja jest prawidłowa.

---

## Krok 2 — Zainstaluj Python 3.12

Sprawdź czy już zainstalowany:
```
python --version
```

Jeśli nie — pobierz ze strony: https://www.python.org/downloads/release/python-3129/
Wybierz: **Windows installer (64-bit)**
Opcje instalacji: zaznacz **Add Python to PATH**, zainstaluj dla wszystkich użytkowników.

---

## Krok 3 — Zainstaluj ODBC Driver 17 for SQL Server

Sprawdź czy już zainstalowany (PowerShell):
```
Get-OdbcDriver | Where-Object { $_.Name -like '*ODBC Driver 17*' }
```

Jeśli brak — pobierz: https://aka.ms/odbc17

---

## Krok 4 — Zainstaluj VS Code

Pobierz: https://code.visualstudio.com/download (Windows, System Installer 64-bit)

---

## Krok 5 — Zainstaluj Node.js i Claude Code

Zainstaluj Node.js (jeśli brak): https://nodejs.org/ — pobierz LTS (Windows Installer 64-bit).

Po instalacji zrestartuj terminal, następnie:
```
npm install -g @anthropic-ai/claude-code
```

### Konfiguracja Git Bash dla Claude Code (wymagane na Windows)

Claude Code wymaga Git Bash. Standardowe ścieżki mogą nie istnieć na Windows Server —
odszukaj właściwą ścieżkę do `bash.exe`:

```powershell
# Znajdź bash.exe w instalacji Git
where git
# Przykład wyniku: C:\Users\<USER>\AppData\Local\Programs\Git\cmd\git.exe
# bash.exe jest wtedy pod: C:\Users\<USER>\AppData\Local\Programs\Git\bin\bash.exe
```

Ustaw zmienną środowiskową `CLAUDE_CODE_GIT_BASH_PATH` (PowerShell jako Administrator):
```powershell
[Environment]::SetEnvironmentVariable(
  "CLAUDE_CODE_GIT_BASH_PATH",
  "C:\Users\<USER>\AppData\Local\Programs\Git\bin\bash.exe",
  "Machine"
)
```

Zastąp `<USER>` swoją nazwą użytkownika. Następnie **zamknij i otwórz terminal** ponownie.

Uruchom Claude Code:
```
claude
```

Zaloguj się gdy pojawi się prośba o autoryzację.

---

## Krok 6 — Przygotuj token GitHub

Repozytorium jest prywatne — wymagany Personal Access Token.

Utwórz **fine-grained token** na: https://github.com/settings/personal-access-tokens/new

Ustawienia:
- **Resource owner:** CyperCyper
- **Repository access:** Only select repositories → `Auto-ERP-Agent`
- **Permissions → Contents:** `Read and write`
- **Permissions → Metadata:** `Read-only` (wymagane automatycznie)

> **Ważne:** `Contents: Read and write` jest niezbędne zarówno do klonowania jak i do pushowania
> commitów. Sam `Read-only` nie wystarczy do pracy z repo.

---

## Krok 7 — Przekaż instalację Claude'owi

Wklej poniższy prompt do Claude Code — poprowadzi resztę instalacji:

```
Skonfiguruj środowisko projektu Auto-ERP-Agent na tej maszynie Windows.

Wykonaj kolejno:
1. Sklonuj repozytorium używając tokena GitHub który podam: git clone
   https://TOKEN@github.com/CyperCyper/Auto-ERP-Agent.git
2. Skonfiguruj remote z tokenem żebym mógł pushować commity
3. Zainstaluj zależności Python: pip install pyodbc python-dotenv openpyxl
4. Skopiuj .env.example do .env
5. Zapytaj mnie o dane połączenia SQL Server (serwer, baza, login, hasło) i wpisz do .env
6. Zweryfikuj połączenie z SQL Server uruchamiając: python experiments/e01_pyodbc_connection.py
7. Zweryfikuj narzędzie agenta uruchamiając: python experiments/e04_mcp_tool.py

Po każdym kroku potwierdź że działa zanim przejdziesz dalej.
```

Gdy Claude poprosi o token — wklej token z Kroku 6.

---

## Krok 8 — Skonfiguruj tożsamość git (dla commitów)

Po sklonowaniu repo, ustaw dane autora commitów:
```
git config user.name "Twoje Imię"
git config user.email "twoj@email.com"
```

---

## Synchronizacja z projektem

Pobierz najnowsze zmiany (nowe funkcjonalności, nowe rozwiązania SQL):
```
cd Auto-ERP-Agent
git pull
```
