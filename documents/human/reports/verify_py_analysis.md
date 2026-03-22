# Analiza verify.py — narzędzie weryfikacji instalacji

**Lokalizacja:** `verify.py` (root projektu)
**Status:** Przestarzałe — wymaga aktualizacji

---

## Co robi verify.py?

To narzędzie do weryfikacji poprawności instalacji środowiska projektu. Sprawdza:

1. **docs.db** — baza dokumentacji ERP (`erp_docs/index/docs.db`)
2. **solutions/** — baza rozwiązań SQL/ERP
3. **SQL Server** — połączenie z bazą CDN (produkcyjna baza ERP)

**Użycie:** `python verify.py`

---

## Zależności

### Narzędzia (CLI):
- `tools/search_docs.py` ❌ NIE ISTNIEJE (używa starej nazwy)
- `tools/search_windows.py` ❌ NIE ISTNIEJE (używa starej nazwy)
- `tools/sql_query.py` ✓ istnieje

### Aktualne nazwy narzędzi:
- `tools/docs_search.py` ✓ (była `search_docs.py`)
- `tools/windows_search.py` ✓ (była `search_windows.py`)

**Problem:** verify.py używa starych nazw narzędzi sprzed refaktoru nazewnictwa.

### Dane:
- `erp_docs/index/docs.db` — indeks dokumentacji ERP
- `solutions/` — katalog rozwiązań SQL
- `.env` — konfiguracja połączenia SQL Server

---

## Czy verify.py jest używany?

**Raczej NIE.** Powody:

1. **Przestarzałe nazwy** — narzędzia zostały przemianowane
2. **Nie w .gitignore** — ale tracked w repo (czyli kiedyś był potrzebny)
3. **Dokumentacja** — INSTALL.md wspomina o weryfikacji, ale niekoniecznie o tym skrypcie
4. **Użyteczność** — pomocne dla nowego użytkownika sprawdzającego instalację

---

## Opcje działania

### Opcja A: Zaktualizować verify.py (Rekomendowane dla projektu z onboardingiem)
**Korzyści:**
- Użyteczne narzędzie dla nowych użytkowników
- Szybka weryfikacja środowiska

**Co wymaga zmiany:**
```python
# Linia 41: search_docs.py → docs_search.py
resp = run([sys.executable, "tools/docs_search.py", "towar*", "--useful-only", "--limit", "1"])

# Linia 46: search_windows.py → windows_search.py
resp = run([sys.executable, "tools/windows_search.py", "towary"])
```

**Dodatkowe sprawdzenia (opcjonalnie):**
- Czy mrowisko.db istnieje
- Czy bot/config/*.txt istnieją
- Czy .env ma wymagane zmienne

### Opcja B: Przenieść do tools/ (jeśli używany)
```bash
mv verify.py tools/verify.py
```
Spójność — wszystkie narzędzia CLI w tools/

### Opcja C: Usunąć (jeśli nieużywany)
```bash
git rm verify.py
```
Jeśli nikt nie potrzebuje weryfikacji instalacji — można usunąć.

### Opcja D: Zostawić jak jest (status quo)
Nie ruszać. Pozostanie w rootcie jako przestarzałe narzędzie.

---

## Rekomendacja

**Jeśli projekt ma innych użytkowników (nie tylko Ty):**
→ **Opcja A** (zaktualizuj) + przenieś do tools/

**Jeśli projekt tylko Twój:**
→ **Opcja C** (usuń) — znasz środowisko, weryfikacja niepotrzebna

**Jeśli onboarding planowany w przyszłości:**
→ **Opcja A** (zaktualizuj) + zostaw w rootcie (wygodniejsze dla nowych)

---

## Plan implementacji (Opcja A)

1. **Zaktualizuj nazwy narzędzi:**
   ```python
   # verify.py line 41
   - resp = run([sys.executable, "tools/search_docs.py", ...])
   + resp = run([sys.executable, "tools/docs_search.py", ...])

   # verify.py line 46
   - resp = run([sys.executable, "tools/search_windows.py", ...])
   + resp = run([sys.executable, "tools/windows_search.py", ...])
   ```

2. **Test:**
   ```bash
   python verify.py
   ```

3. **Opcjonalnie: Przenieś do tools/**
   ```bash
   mv verify.py tools/verify.py
   ```

4. **Commit:**
   ```bash
   git add verify.py  # lub tools/verify.py
   git commit -m "fix: aktualizacja verify.py — nowe nazwy narzędzi (docs_search, windows_search)"
   ```

---

## Następne kroki

**User decyduje:** Która opcja (A/B/C/D)?

- A → Dev zaktualizuje verify.py
- B → Dev przeniesie do tools/
- C → Dev usunie
- D → Nic nie rób

---

**Lokalizacja analizy:** `documents/human/reports/verify_py_analysis.md`
