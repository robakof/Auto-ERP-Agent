# Instrukcja instalacji — Automatyczny Konfigurator ERP

Środowisko na nowej maszynie Windows. Wymagane uprawnienia administratora.

---

## 1. Git

**winget (zalecane):**
```
winget install Git.Git
```

**Ręcznie:** https://git-scm.com/download/win — instalator 64-bit, opcje domyślne.

Po instalacji zrestartuj terminal i sprawdź:
```
git --version
```

---

## 2. Python 3.12

**winget:**
```
winget install Python.Python.3.12
```

**Ręcznie:** https://www.python.org/downloads/ — pobierz Python 3.12.x (Windows installer 64-bit).
Przy instalacji zaznacz: **"Add Python to PATH"**.

Sprawdź:
```
python --version
pip --version
```

---

## 3. ODBC Driver for SQL Server

Wymagany przez pyodbc (narzędzie sql_query.py).

Pobierz i zainstaluj **Microsoft ODBC Driver 17 for SQL Server**:
https://aka.ms/odbc17

Uruchom instalator, opcje domyślne.

---

## 4. Node.js

Wymagany przez Claude Code CLI.

**winget:**
```
winget install OpenJS.NodeJS.LTS
```

**Ręcznie:** https://nodejs.org/ — pobierz LTS (Windows Installer 64-bit).

Sprawdź:
```
node --version
npm --version
```

---

## 5. Claude Code CLI

```
npm install -g @anthropic-ai/claude-code
```

Sprawdź:
```
claude --version
```

---

## 6. Visual Studio Code

**winget:**
```
winget install Microsoft.VisualStudioCode
```

**Ręcznie:** https://code.visualstudio.com/download — System Installer 64-bit.

---

## 7. Klonowanie repozytorium

Otwórz terminal w lokalizacji gdzie chcesz umieścić projekt (np. pulpit):

```
git clone https://github.com/CyperCyper/Auto-ERP-Agent.git
cd Auto-ERP-Agent
```

---

## 8. Instalacja zależności Python

W katalogu projektu:
```
pip install -r requirements.txt
```

---

## 9. Konfiguracja .env

Skopiuj plik konfiguracyjny:
```
copy .env.example .env
```

Otwórz `.env` w notatniku i uzupełnij dane połączenia z SQL Serverem:
```
SQL_SERVER=SQLSERVER\SQLEXPRESS
SQL_DATABASE=ERPXL_CEIM
SQL_USERNAME=CEiM_Reader
SQL_PASSWORD=twoje_haslo
```

---

## 10. Uruchomienie agenta

Otwórz katalog projektu w VS Code:
```
code .
```

W VS Code uruchom Claude Code (Ctrl+Shift+P → "Claude Code") lub w terminalu:
```
claude
```

Agent jest gotowy do pracy. Zacznij od polecenia w języku naturalnym, np.:
> "Dodaj filtr do Okna Towary..."

---

## Synchronizacja z projektem

Pobierz najnowsze zmiany (nowe funkcjonalności, nowe rozwiązania SQL):
```
git pull
```

---

## Weryfikacja instalacji

Uruchom po kolei — każde powinno zwrócić JSON z `"ok": true`:

```
python tools/search_windows.py "towary"
python tools/search_docs.py "towar*" --useful-only --limit 3
python tools/sql_query.py "SELECT TOP 1 Twr_GIDNumer FROM CDN.TwrKarty"
```

---

## Rozwiązywanie problemów

**`pyodbc` nie może połączyć się z SQL Serverem:**
- Sprawdź czy ODBC Driver 17 jest zainstalowany (Panel Sterowania → Programy)
- Sprawdź dane w `.env` (serwer, baza, login, hasło)
- Sprawdź czy maszyna ma dostęp sieciowy do `SQLSERVER\SQLEXPRESS`

**`python` nie jest rozpoznawane:**
- Przy instalacji Pythona zaznacz "Add Python to PATH"
- Lub dodaj ręcznie: `C:\Users\[user]\AppData\Local\Programs\Python\Python312\` do zmiennej PATH

**`npm` nie jest rozpoznawane:**
- Zrestartuj terminal po instalacji Node.js
