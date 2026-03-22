# Analiza plików w głównym katalogu projektu — cleanup plan

**Data:** 2026-03-22

---

## Pliki tracked w git (główny katalog)

### ✓ Zachować — dokumentacja projektu
- `.env.example` — szablon konfiguracji
- `.gitignore` — konfiguracja git
- `CLAUDE.md` — główny plik instrukcji dla agentów
- `INSTALL.md`, `README.md`, `SETUP_MACHINE.md` — dokumentacja
- `pytest.ini`, `requirements.txt` — konfiguracja projektu Python

### ✗ Usunąć z repo + dodać do .gitignore — pliki biznesowe/robocze
**Wyceny (pliki Excel z danymi klientów):**
- `Wycena 2026 Otorowo Szablon.xlsm` — szablon może zostać, ale czy potrzebny w repo?
- `Wycena AUCHAN.xlsm`
- `Wycena AUCHAN_v4.xlsm`
- `Wycena SOLAR+MIRAGE.xlsm`

**Inne pliki biznesowe:**
- `Etykiety do wypełnienia.docx` — dokument Word
- `dekle.xlsx`, `spody.xlsx`, `tacka.xlsx` — pliki biznesowe

**Uzasadnienie:** Te pliki zawierają dane biznesowe/klientów, nie kod. Nie powinny być w repo kodu. Lepiej w osobnym folderze poza repo lub w OneDrive.

### 🤔 Do decyzji — skrypty uruchamiające
- `Etykiety wysyłkowe.bat`
- `Oferta katalogowa 3x3.bat`
- `Oferta katalogowa.bat`
- `create_shortcut.bat`

**Pytanie:** Czy te .bat są używane przez użytkownika do uruchamiania narzędzi? Jeśli tak — można zostaw

ić. Jeśli to były tylko testy — usunąć.

### 🤔 Do decyzji — dane referencyjne
- `Mapowanie palet JAS.txt` — biznesowa dokumentacja mapowania palet

**Pytanie:** Czy to jest dokumentacja techniczna (potrzebna do zrozumienia kodu) czy dane robocze? Jeśli robocze → przenieść do `documents/Wzory plików/` lub usunąć.

### 🤔 Do decyzji — bazy danych i ikony
- `docs.db` — indeks dokumentacji ERP (generowany przez `docs_build_index.py`)
- `ikona drukowanie.ico.svg` — ikona

**docs.db:** Czy powinien być w .gitignore? (jak mrowisko.db) Jeśli regenerowalny — tak.
**ikona:** Jeśli używana w aplikacji → przenieś do `bot/assets/` lub podobnego. Jeśli nieużywana → usuń.

---

## Pliki untracked (nie w git)

### ✗ Usunąć + dodać do .gitignore
- `nul` — błędny plik (Windows null device), powstał przez pomyłkę
- `documents/human/.obsidian/` — konfiguracja Obsidian (lokalna per użytkownik)
- `documents/architect/research_results_agent_runner_patterns (1).md` — duplikat (błędna kopia)
- `documents/prompt_engineer/research_results_character_designer (1).md` — duplikat
- `documents/prompt_engineer/research_results_language_impact (1).md` — duplikat
- `documents/architect/STRATEGIC_PLAN_2026-03.md` — untracked, ale czy powinien być w repo?

**Akcja:** Usuń `nul`, dodaj `.obsidian/` do .gitignore, usuń duplikaty " (1)", sprawdź STRATEGIC_PLAN.

---

## Propozycja zmian w .gitignore

### Dodać:
```gitignore
# Konfiguracje Obsidian (lokalne per użytkownik)
**/.obsidian/

# Pliki biznesowe — wyceny
Wycena*.xlsm
*.xlsm

# Pliki biznesowe — dokumenty Word
*.docx

# Pliki biznesowe — Excel robocze
dekle.xlsx
spody.xlsx
tacka.xlsx

# Baza danych indeksu dokumentacji (regenerowalna)
docs.db

# Błędne pliki systemowe
nul
```

### Ewentualnie (do decyzji):
```gitignore
# Mapowania biznesowe
Mapowanie*.txt

# Skrypty .bat (jeśli nie są używane produkcyjnie)
*.bat
```

---

## Plan akcji

### Faza 1: Bezpieczne usunięcia (pewne)
1. Usuń `nul`:
   ```bash
   git rm -f nul
   ```
   (jeśli tracked, użyj `git rm`, jeśli nie — zwykły `rm`)

2. Usuń duplikaty " (1)":
   ```bash
   rm "documents/architect/research_results_agent_runner_patterns (1).md"
   rm "documents/prompt_engineer/research_results_character_designer (1).md"
   rm "documents/prompt_engineer/research_results_language_impact (1).md"
   ```

3. Dodaj `.obsidian/` do .gitignore:
   ```bash
   echo "**/.obsidian/" >> .gitignore
   ```

4. Usuń `documents/human/.obsidian/` z dysku:
   ```bash
   rm -rf documents/human/.obsidian/
   ```

### Faza 2: Usunięcie plików biznesowych z repo (po zatwierdzeniu)

**Opcja A: Usunąć z repo, zostawić lokalnie**
```bash
git rm --cached "Wycena AUCHAN.xlsm"
git rm --cached "Wycena AUCHAN_v4.xlsm"
git rm --cached "Wycena SOLAR+MIRAGE.xlsm"
git rm --cached "Etykiety do wypełnienia.docx"
git rm --cached dekle.xlsx spody.xlsx tacka.xlsx
```
(--cached = usuń z repo, ale zostaw lokalnie)

**Opcja B: Usunąć całkowicie (też z dysku)**
```bash
git rm "Wycena AUCHAN.xlsm"
git rm "Wycena AUCHAN_v4.xlsm"
git rm "Wycena SOLAR+MIRAGE.xlsm"
git rm "Etykiety do wypełnienia.docx"
git rm dekle.xlsx spody.xlsx tacka.xlsx
```

### Faza 3: Pytania do User

1. **Skrypty .bat:** Czy są używane? Zachować czy usunąć?
2. **Mapowanie palet JAS.txt:** Czy to dokumentacja techniczna czy dane robocze?
3. **Wycena 2026 Otorowo Szablon.xlsm:** Czy szablon powinien zostać w repo?
4. **docs.db:** Dodać do .gitignore (jak mrowisko.db)?
5. **ikona drukowanie.ico.svg:** Używana czy nie? Przenieść do właściwego folderu?
6. **STRATEGIC_PLAN_2026-03.md:** Czy powinien być tracked? (obecnie untracked)

---

## Trade-offs

### Argument ZA usunięciem plików biznesowych z repo:
- ✓ Repo kodu powinno zawierać kod, nie dane klientów
- ✓ Bezpieczeństwo — wyceny klientów nie powinny być w historii git
- ✓ Rozmiar repo — pliki .xlsm mogą być duże
- ✓ Konflikt merge — pliki binarne ciężko mergować

### Argument PRZECIW (lub za ostrożnością):
- ✗ User może używać repo jako backup
- ✗ Niektóre pliki mogą być potrzebne do działania narzędzi
- ✗ Usunięcie z historii git = złożone (git filter-branch)

**Rekomendacja:** `git rm --cached` (usuń z repo, zostaw lokalnie) + .gitignore. Użytkownik lokalnie ma pliki, ale nie są synchronizowane.

---

## Następne kroki

1. **User approval:** Pytania z Fazy 3
2. **Faza 1:** Bezpieczne usunięcia (nul, duplikaty, .obsidian)
3. **Aktualizacja .gitignore**
4. **Faza 2:** Usunięcie plików biznesowych (po zatwierdzeniu)
5. **Commit zmian**
6. **Opcjonalnie:** Czyszczenie historii git (jeśli dane wrażliwe)

---

**Lokalizacja:** `documents/human/reports/root_cleanup_analysis.md`
