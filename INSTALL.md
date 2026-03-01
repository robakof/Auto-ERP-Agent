# Instrukcja instalacji — Automatyczny Konfigurator ERP

Wymagane uprawnienia administratora.

---

## Krok 1 — Uruchom Claude Code

Zainstaluj Node.js, a następnie Claude Code CLI:

**winget:**
```
winget install OpenJS.NodeJS.LTS
```

**Ręcznie:** https://nodejs.org/ — pobierz LTS (Windows Installer 64-bit), opcje domyślne.

Po instalacji zrestartuj terminal, następnie:
```
npm install -g @anthropic-ai/claude-code
```

Uruchom Claude Code w dowolnym katalogu:
```
claude
```

Zaloguj się gdy pojawi się prośba o autoryzację.

---

## Krok 2 — Przekaż instalację Claude'owi

Wklej poniższy prompt do Claude Code — poprowadzi resztę instalacji:

```
Skonfiguruj środowisko projektu Auto-ERP-Agent na tej maszynie Windows.

Wykonaj kolejno:
1. Zainstaluj Git: winget install Git.Git
2. Zainstaluj Python 3.12: winget install Python.Python.3.12
3. Pobierz i zainstaluj Microsoft ODBC Driver 17 for SQL Server (https://aka.ms/odbc17)
4. Zainstaluj VS Code: winget install Microsoft.VisualStudioCode
5. Sklonuj repozytorium: git clone https://github.com/CyperCyper/Auto-ERP-Agent.git
6. Wejdź do katalogu projektu i uruchom: pip install -r requirements.txt
7. Skopiuj .env.example do .env
8. Zapytaj mnie o hasło SQL Server i wpisz je do .env
9. Zweryfikuj instalację uruchamiając 3 komendy testowe z README.md

Po każdym kroku potwierdź że działa zanim przejdziesz dalej.
```

---

## Synchronizacja z projektem

Pobierz najnowsze zmiany (nowe funkcjonalności, nowe rozwiązania SQL):
```
git pull
```
