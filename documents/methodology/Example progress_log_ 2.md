# Progress Log - Stan projektu dla asystentow

**Data ostatniej aktualizacji:** 2026-01-02 (P0 Tasks Completed)
**Obecny asystent:** Claude Sonnet 4.5
**Status projektu:** 95%+ - Gotowy do oddania (wszystkie P0 krytyczne taski zakończone)

---

## CO JEST ZROBIONE

### 1. Scraping Listings - DONE

**Implementacja:**
- JSON API scraper + raw data saving do `data/raw/YYYY-MM-DD/listings/`
- Parser z lokalnych plików (RawDataParser)
- Pipeline: scrape → save raw → parse → clean → insert

**Kluczowe pliki:**
- `src/scraper/web_scraper.py` - NoFluffJobsJsonScraper, RawDataParser
- `scraper_pipeline.py` - scrape(), parse_from_raw(), save_to_database(), export_to_excel()

**Wyniki (2025-12-26):**
- ~2170 unikalnych ofert (94% pokrycia NoFluffJobs)
- Czas: ~10-15 minut (36 kategorii)
- Reference IDs zapisane w bazie

**Szczegóły:** Zobacz `ARCHITECTURE.md`

---

### 2. Database - DONE

**Kluczowe pliki:**
- `src/database/schema.sql` - definicja tabel i VIEW
- `src/database/db_manager.py` - DatabaseInserter, DatabaseManager

**Funkcjonalności:**
- Deduplication based on offer_signature (company_title_timestamp)
- Transaction safety (offer + locations atomic)
- Excel export z VIEW

---

### 3. Data Cleaning - DONE

**Implementacja:**
- Rule-based cleaning (Warsaw → Warszawa, Polish → Poland)
- Title case dla location/city/country

**Kluczowe pliki:**
- `src/cleaning/data_cleaner.py` - clean_offer(), _clean_location_dict()
- `data/cleaning_rules.json` - reguły czyszczenia

---

### 4. Raw Data Backup Architecture - DONE

**Dlaczego:**
- Re-parsing bez re-scrapowania (sekundy zamiast minut)
- Historyczne archiwum danych
- Możliwość dodawania nowych pól bez re-scrapowania

**Trade-off:**
- +100MB/scrape na dysku, ale warte tego

**Szczegóły:** Zobacz `migration_history.md`

---

### 5. Testy - DONE

**Implementacja:**
- 19 testów (10 unit + 9 integration) - wszystkie przechodzą
- Pytest + fixtures + sample data
- Coverage: parser, deduplikacja, cleaning, pipeline

**Kluczowe pliki:**
- `tests/test_parser.py` - unit testy
- `tests/test_parse_and_save.py` - integration testy
- `tests/conftest.py` - shared fixtures
- `tests/README.md` - instrukcja

**Status:** CRITICAL tech debt naprawiony

---

### 6. Streamlit Dashboard - DONE (2025-12-30)

**Implementacja:**
- Interactive dashboard w Streamlit
- Wszystkie 16 wykresów (8 salary + 8 general)
- Clean minimalist design (dark theme, niebieski accent)
- ML prediction demo interface
- **REFACTORED 2x:** Modularny pages package + Scraping enhancements
- Deployment ready (Streamlit Cloud)

**Architektura (REFACTORED 2025-12-30):**
- Modułowa struktura `src/dashboard/`:
  - `app.py` - orchestration (83 linie)
  - `components.py` - reusable UI (120 linii)
  - `pages/` - **PACKAGE** (modułowe strony):
    - `__init__.py` - eksporty
    - `scraping.py` (298 linii - 8 funkcji)
    - `parsing.py` (130 linii - 4 funkcje)
    - `start.py` (110 linii - 3 funkcje)
    - `ml.py` (160 linii - 4 funkcje)
    - `salary.py` (55 linii - 2 funkcje)
    - `general.py` (55 linii - 2 funkcje)
  - `styles.py` - CSS loader (60 linii)
  - `static/styles.css` - external CSS (236 linii)
- `dashboard_app.py` - thin wrapper (14 linii)
- `scraper_pipeline.py` - UI config support + progress callback

**Features (2025-12-30 Evening):**
- **6 sekcji:** Start → **Scrapowanie** → **Zarządzanie bazą** → Wynagrodzenia → Statystyki → ML
- **Scraping UI (Enhanced):**
  - **3 tryby scrapowania:**
    1. Scrapuj oferty (z UI config)
    2. Scrapuj szczegóły (przyrostowe - tylko nowe)
    3. Scrapuj wszystko (oferty + szczegóły)
  - Configuration form (max_pages, page_size 1-100000, delay, categories)
  - **Real-time progress tracking:**
    - Progress bar (0-100%)
    - Status messages ("Kategoria: backend (1/36) - 5%")
    - Callback system: `progress_callback(current, total, message)`
  - Auto-collapsed config (expanded=False)
  - Smart messaging ("Wybrano X kategorii")
- **Database Management UI (RENAMED & ENHANCED 2025-12-30 Evening):**
  - Nazwa zmieniona: "Parsowanie" → "Zarządzanie bazą"
  - **3 sekcje:**
    1. Raw data folder listing (tabela z plikami JSON)
    2. **Parsowanie i zapis do bazy:**
       - Progress bar podczas parsowania (3 kroki: Parse → Deduplicate → Clean)
       - Dokładne liczniki: "Zapisano X nowych ofert (Pominięto Y duplikatów)"
       - Auto-export do Excel po zapisie
    3. **Usuwanie rekordów z bazy (NEW):**
       - Tabela dat z liczbą ofert
       - Selektor daty + checkbox potwierdzenia
       - Usuwanie z CASCADE (auto-usuwa powiązane dane z 5 tabel)
       - Auto-refresh po usunięciu
- **Przyrostowe scrapowanie szczegółów:**
  - Query pomija oferty z istniejącymi szczegółami
  - Pre-check: "Znaleziono X ofert bez szczegółów"
  - Oszczędność czasu i bandwidth
- Custom CSS styling (external file)
- Radio button navigation (blue accent #0D6EFD)
- Chart loading z Plotly.js wrapper
- **Real ML Salary Prediction (DONE):**
  - Integracja modelu RandomForestRegressor
  - Trening modelu z poziomu dashboardu
  - Interfejs predykcji oparty na realnych cechach (miasto, seniority, technologie)
  - Wyświetlanie metryk (MAE, R2)
- **Technology Dashboard Page (DONE):**
  - Nowa zakładka "Technologie"
  - 5 nowych typów wizualizacji (Treemaps, Heatmaps, Stacks)
  - Przeniesiona i ulepszona macierz współwystępowania

**Kluczowe pliki:**
- `src/dashboard/app.py` - routing dla 6 stron
- `src/dashboard/pages/scraping.py` - 8 modułowych funkcji, 3 tryby
- `src/dashboard/pages/parsing.py` - zarządzanie bazą (198 linii, 4 funkcje)
- `src/dashboard/pages/*.py` - 5 innych stron (modułowe)
- `src/dashboard/components.py` - load_chart, render_header, render_sidebar
- `src/dashboard/static/styles.css` - CSS z blue accent
- `src/database/db_manager.py` - get_offers_for_details_scraping(), delete_offers_by_date(), get_dates_with_counts()
- `scraper_pipeline.py` - scrape(ui_config, progress_callback), parse_from_raw(progress_callback), save_to_database() returns (inserted, skipped)
- `dashboard_app.py` - entry point

**User experience:**
- Scrapowanie z dashboardu (bez CLI!)
- **Real-time progress** - widać postęp na żywo (scraping + parsing)
- **3 tryby** - elastyczność (tylko oferty / tylko szczegóły / wszystko)
- **Przyrostowe** - szczegóły tylko dla nowych ofert
- **Database management** - usuwanie rekordów według daty z UI
- **Dokładne liczniki** - rzeczywista liczba zapisanych ofert (po deduplikacji)
- Wszystkie ustawienia z UI (config.json optional)
- page_size=100000 dla najszybszego scrapowania
- Professional, spójny design

**Wyniki:**
- Działający dashboard: http://localhost:8502
- Wszystkie wykresy renderują się poprawnie
- 11+ commitów optymalizacji (2025-12-30)
- Modułowa architektura - 6 page files
- Progress tracking - real-time feedback (scraping + parsing)
- Incremental scraping - smart resource usage
- Database cleanup - usuwanie według daty
- Modularny kod, łatwy w maintenance
- **Database Management UI - DONE**
- **Technology Dashboard & ML Integration - DONE**

**Szczegóły:** Zobacz `changelog.md` - Session 2025-12-29 (Phase 1-2), Session 2025-12-30 (Phase 1-8)

---

### 7. Dashboard Architecture Refactoring - DONE (2026-01-02)

**Cel:** Separacja logiki biznesowej od UI + uproszczenie struktury katalogów

**Implementacja:**

#### Phase 1: Service Layer Extraction (2026-01-02 Evening-Night)
- **MLService utworzony** (`src/services/ml_service.py`, 329 linii):
  - Model Management: `list_models()`, `get_model_info()`, `load_model()`, `get_default_model()`
  - Training: `get_hyperparameter_presets()`, `train_model()`
  - Prediction: `prepare_prediction_features()`, `predict_salary()`
  - Analysis: `get_feature_importance_data()`
- **Logika przeniesiona z UI:**
  - `predict.py:11-68` - funkcja predykcji → MLService
  - `train.py:50-88` - presety hyperparametrów → MLService
  - `state.py:13-30` - zarządzanie modelami → MLService
  - `analysis.py` - ładowanie modeli → MLService
- **ML UI skonsolidowany:**
  - 5 plików (656 linii) → 1 plik `ml.py` (447 linii)
  - Usunięto katalog `pages/ml/` całkowicie
  - Tylko UI rendering, zero business logic

#### Phase 2: Pages Architecture Flattening (2026-01-02 Night)
- **Spłaszczono strukturę** `pages/` po wydzieleniu logiki do services:
  - Usunięto 6 podkatalogów (scraping, data_management, general, salary, technology, start)
  - Scalono pliki do 7 pojedynczych `.py` files
- **scraping.py** (535 linii):
  - Scalono 3 pliki: `page.py` + `config.py` + `actions.py`
  - Wszystkie funkcje pomocnicze z prefiksem `_`
- **Pozostałe moduły** skopiowane z `page.py` do głównego katalogu
- **Poprawiono importy:** `...components` → `..components` (zmiana poziomu zagnieżdżenia)

**Nowa struktura pages/:**
```
src/dashboard/pages/
├── __init__.py
├── scraping.py (535 linii)
├── data_management.py (352 linie)
├── general.py (54 linie)
├── salary.py (55 linii)
├── technology.py (122 linie)
├── start.py (106 linii)
└── ml.py (447 linii)
```

**Service Layer (src/services/):**
```
src/services/
├── __init__.py
├── parsing_service.py (ParsingService)
├── scraping_service.py (ScrapingService)
├── statistics_service.py (StatisticsService)
└── ml_service.py (MLService) <- NOWY
```

**Korzyści:**
- **100% separacja UI/Logic:** Cała logika biznesowa w services/, tylko UI w pages/
- **Testability:** Service layer testowalne bez Streamlit (unit tests)
- **Reusability:** Services gotowe do użycia w CLI, API, batch processing
- **Prostota:** Płaska struktura pages/ (7 plików vs 6 katalogów z wieloma plikami)
- **Consistency:** Wszystkie moduły dashboard z wydzieloną logiką biznesową
- **Maintainability:** Jedna centralna lokalizacja dla każdego typu logiki

**Statystyki refaktoryzacji:**
- ML: 5 plików (656 linii) → 1 plik (447 linii), -32% kodu UI
- Pages: 6 katalogów → 7 plików, eliminacja zbędnych `__init__.py`
- Services: +329 linii (MLService) - reusable business logic
- Duplikacja: Wyeliminowana (3x ładowanie modelu → 1x w serwisie)

**Kluczowe pliki:**
- `src/services/ml_service.py` - Cała logika ML (329 linii)
- `src/services/parsing_service.py` - Logika parsowania (180 linii)
- `src/services/scraping_service.py` - Logika scrapowania (100 linii)
- `src/services/statistics_service.py` - Logika statystyk (170 linii)
- `src/dashboard/pages/*.py` - 7 plików UI (50-535 linii każdy)

**Commits:**
- `d3607c0` - ML Service Layer + konsolidacja ML
- `5cc2fb2` - Spłaszczenie struktury pages/

**Szczegóły:** Zobacz `changelog.md` - Session 2026-01-02 (Late Evening & Night)

---

### 8. ML Module Enhancement - DONE (2025-12-31 Evening)

**Implementacja:**
- Cross-validation (5-fold) zamiast pojedynczego train-test split
- Hyperparameter tuning z RandomizedSearchCV (20 kombinacji parametrów)
- Category feature dodany do modelu (backend/frontend/data science)
- Enhanced metrics display w dashboardzie

**Kluczowe zmiany:**
- `src/ml/model.py` - RandomizedSearchCV, 5-fold CV, automatic tuning
- `src/ml/feature_engineering.py` - category one-hot encoding
- `src/ml/analysis.py` - category group w feature importance
- `src/dashboard/pages/ml.py` - rozbudowany UI dla metryk CV

**Metryki zwracane:**
- CV MAE ± std (wiarygodna metryka stabilności)
- Test MAE, Test R²
- Best hyperparameters (n_estimators, max_depth, min_samples_split, min_samples_leaf, max_features)
- Total dataset size

**Hyperparametry tunowane:**
- n_estimators: [100, 200, 300, 500]
- max_depth: [10, 20, 30, None]
- min_samples_split: [2, 5, 10]
- min_samples_leaf: [1, 2, 4]
- max_features: ['sqrt', 'log2', None]

**Czas treningu:** ~2-5 minut (100 treningów: 20 kombinacji × 5 folds)

**Wyniki:**
- Bardziej wiarygodne metryki (CV eliminuje szczęście w losowaniu)
- Optymalne parametry dla datasetu (lepsze niż defaults)
- Informacja o stabilności modelu (CV std)

**Szczegóły:** Zobacz `changelog.md` - Session 2025-12-31 Evening

---

### 9. ML Feature Expansion & Model Management - DONE (2026-01-01)

**Implementacja:**
- Nowe cechy: contract_type (salary_type), english_level, company_size, tech_count_must, tech_count_all, has_multiple_cities
- City logic: Remote > Multiple > Single + has_multiple_cities
- Normalizacja company_size do small/medium/large/very_large/unknown
- Feature importance: tech_count_* w Technologies, has_multiple_cities w Location, usunieto "Numeric Features"
- Dashboard: rozszerzony formularz predykcji, poprawione contract_type (b2b, permanent, zlecenie, intern)
- Hyperparameter UI: presety Balanced/Conservative/Aggressive/Custom
- Model persistence: nazwa pliku z metrykami i parametrami + wybor modelu z listy

**Kluczowe pliki:**
- `src/ml/pipeline.py` - city logic, tech_count, company_size clean, custom_hyperparams
- `src/ml/feature_engineering.py` - nowe cechy
- `src/analysis/ml_analysis.py` - naprawa grup importance
- `src/ml/model.py` - custom params + auto filename
- `src/dashboard/pages/ml.py` - UI: nowe pola, presety, wybor modeli

**Wyniki (eksperymenty):**
- v1 (overfit): Test MAE 2297, CV MAE 4068, gap ~77%
- v2 (underfit): Test MAE 4448, CV MAE 4345, R2 0.538
- v3 (balanced preset): do przetestowania, cel CV MAE ~3200, gap <15%, R2 >0.75

### 10. Dokumentacja - DONE

**Zmiany:**
- Połączono 3 pliki wytycznych → `AI_GUIDELINES.md` (workflow, code quality, temporal naming)
- Skompresowano `PRD.md` (469 → 114 linii, -76%)
- Skompresowano `progress_log.md` (321 → 294 linii)
- Przemianowano i ustrukturyzowano `api_reference.md`
- Stworzono `documentation/README.md` (navigation guide)

**Kluczowe pliki:**
- `AI_GUIDELINES.md` - pełne wytyczne dla asystenta
- `changelog.md` - tracking zmian z clickable file:line links
- `Changes_propositions.md` - workflow dla dużych zmian

**Workflow:**
- Duże zmiany → `Changes_propositions.md` → approval → implement → `changelog.md`
- Zasada: "Think Long-Term" (unikaj nazw `scrape_only`, `new_parser`, `old_method`)

**Szczegóły:** Zobacz `changelog.md`

---

### 11. Details Scraping - DONE (2025-12-26)

**Implementacja:**
- Details JSON scraper + raw data saving do `data/raw/YYYY-MM-DD/details/`
- Parser z lokalnych plików (DetailsRawDataParser)
- Pipeline: scrape → save raw → parse → insert
- Konsolidacja do scraper_pipeline.py z CLI subcommands

**Kluczowe pliki:**
- `src/scraper/offer_details_scraper.py` - JobDetailsJsonScraper, DetailsRawDataParser
- `scraper_pipeline.py` - scrape_details(), parse_details(), details_pipeline()
- `src/database/schema.sql` - 4 nowe tabele (offer_details, offer_technologies, offer_benefits, offer_salary_types)

**Funkcjonalności:**
- Raw data backup (re-parsing bez re-scrapowania)
- Atomic transactions (details + related data razem)
- TypedDict validation
- Defensive parsing z .get()

**CLI:**
```bash
python scraper_pipeline.py details         # Full pipeline
python scraper_pipeline.py details-test    # Test (10 offers)
python scraper_pipeline.py details-scrape  # Only scraping
python scraper_pipeline.py details-parse   # Only parsing
```

---

### 12. Jupyter Notebooks - DONE (2026-01-02) ✓ CRITICAL

**Implementacja:**
- 3 comprehensive notebooks dla analizy i ML
- Spełnia KRYTYCZNE wymaganie PRD (linia 22: "Jupyter notebooks (analiza + ML)")

**Utworzone pliki:**
- `notebooks/01_EDA_and_Data_Analysis.ipynb` (24 KB)
- `notebooks/02_ML_Training_and_Evaluation.ipynb` (31 KB)
- `notebooks/03_Visualization_Gallery.ipynb` (20 KB)

**Notebook 1 - EDA and Data Analysis:**
- Setup i wczytanie danych z SQLite (2170+ ofert)
- Podstawowe statystyki opisowe (missing values, data coverage)
- Analiza wynagrodzeń (rozkład, percentyle, outliers 3-sigma)
- Analiza technologii (top 20, salary impact, tech counts, co-occurrence)
- Analiza lokalizacji (top cities, remote vs onsite, geography)
- Analiza seniority (distribution, salary by level)
- Korelacje (salary vs tech count, correlation matrix, scatter plots)
- Wnioski biznesowe (insights dla job seekers i recruiters)

**Notebook 2 - ML Training and Evaluation:**
- Feature engineering (seniority, location, technologies)
- Baseline models (mean predictor, linear regression)
- RandomForest training z hyperparameter tuning (RandomizedSearchCV, 5-fold CV)
- Model evaluation (MAE, RMSE, R², MAPE)
- Feature importance analysis (top 20, grouped importance)
- Model interpretation (best/worst predictions, residual analysis)
- Business recommendations (strengths, limitations, deployment)

**Notebook 3 - Visualization Gallery:**
- 24+ interaktywnych wykresów Plotly
- Salary Analysis (8 charts), General Analysis (8 charts)
- Technology Analysis (6 charts), ML Analysis (3 charts)
- Każdy wykres z opisem i insights

**Approach:**
- Reużycie istniejącego kodu z `src/analysis/` i `src/ml/`
- Professional markdown cells z explanations
- Code cells z analizą i wizualizacjami
- End-to-end executable notebooks

**Impact:** CRITICAL - spełnia wymaganie oceny 5.5

**Szczegóły:** Zobacz `changelog.md` - Session P0 Critical Tasks (2026-01-02)

---

### 13. Critical Error Handling - DONE (2026-01-02) ✓ HIGH PRIORITY

**Implementacja:**
- 5 critical fixes dla stability i robustness
- Professional error handling across codebase

**Fix A: Config loading with graceful fallback**
- Plik: `src/analysis/data_loader.py`
- Dodano `_get_default_config()` dla missing config files
- Try/except dla FileNotFoundError i JSONDecodeError
- Prevents crashes when config missing/invalid

**Fix B: Replace bare except**
- Plik: `src/database/db_manager.py`
- Zmieniono `except:` na `except (ValueError, TypeError, OverflowError, OSError)`
- W funkcji `_timestamp_to_datetime()`
- Better error messages, nie łapie SystemExit/KeyboardInterrupt

**Fix C: Database connection leaks**
- Plik: `src/analysis/data_loader.py`
- 6 funkcji fixed: load_offers, load_technologies, load_salaries, load_locations, load_benefits, load_offer_details
- Zamieniono `conn.close()` na context managers `with sqlite3.connect()`
- Ensures connections always closed even on errors

**Fix D: Hardcoded timeout**
- Plik: `src/scraper/web_scraper.py`
- Dodano `timeout_s: int = 10` do ScraperConfig dataclass
- Zamieniono hardcoded `timeout=10` na `self.config.timeout_s`
- Backward compatible (default = 10)

**Fix E: joblib.load error handling**
- Plik: `src/ml/model.py`
- Try/except dla corrupted model files
- Walidacja struktury (required keys: model, features)
- Clear error messages with file details

**Testing:** 33/33 tests passing after fixes

**Impact:**
- Professional error handling
- No bare excepts in codebase
- No connection leaks
- Configurable parameters
- Better UX on errors

**Szczegóły:** Zobacz `changelog.md` i `pre_submission_analysis.md`

---

## CO JEST W TRAKCIE / NIEUKOŃCZONE

### ML Model Tuning - IN PROGRESS (2026-01-01)

**Cel:**
- Zmniejszyc CV MAE do ~3200 przy gap <15% i R2 >0.75

**TODO:**
- Przetestowac Balanced/Custom presety i zapisac najlepszy model
- Jezeli potrzeba, dostroic zakresy max_depth/min_samples_leaf/min_samples_split

### Phase 2: Analysis & Visualization - DONE (2025-12-31)

**Zrobione:**
1. ✓ Query Builder (`src/utils/query_builder.py`) - dynamiczne SELECTy
2. ✓ Analysis Config (`data/analysis_config.json`) - exclude non-IT, currency rates, period_multipliers
3. ✓ Analysis Utils (`src/analysis/analysis_utils.py`) - hybrid normalization (period in DB, currency in Python)
4. ✓ Data Loader (`src/analysis/data_loader.py`) - 12 funkcji load + prepare, query builder, 3-sigma outlier filtering
5. ✓ Salary Analysis (`src/analysis/salary_analysis.py`) - 12 funkcji, 8 wizualizacji
6. ✓ General Analysis (`src/analysis/general_analysis.py`) - 8 funkcji, 8 wizualizacji
7. ✓ Data Quality Fixes - USD conversion, 3-sigma filtering, period-based normalization
8. ✓ HTML Viewer (`reports/visualizations.html`) - tabbed interface, navigation, 17 charts
9. ✓ Visualization Utils (`src/analysis/viz_utils.py`) - dark mode, common layout, SENIORITY_COLORS, aggregate_and_filter helper
10. ✓ Period Migration - wszystkie wizualizacje regenerowane z poprawnymi danymi
11. ✓ Distribution Visualizations - 2 nowe wykresy rozkładu normalnego z raw counts
12. ✓ Refaktoryzacja modułów - eliminacja duplikacji, pie chart dla lokalizacji, macierz % (2025-12-28)
13. ✓ Dashboard Refactoring - Jinja2 templates, separacja HTML/CSS/JS, single source of truth dla kolorów (2025-12-29)
14. ✓ Chart Responsiveness Fix - div embedding, CDN Plotly, resize handler dla tabs, -87.5% rozmiaru (2025-12-29)
15. ✓ Technology Analysis Module (`src/analysis/technology_analysis.py`) - 10+ funkcji, 5 nowych wizualizacji
16. ✓ Technology Dashboard Page - dedykowana sekcja w dashboardzie
17. ✓ Seniority Distribution Analysis - zaawansowana macierz z obsługą wielu wartości (explode seniority)

**Kluczowe pliki:**
- `src/utils/query_builder.py` - build_select_query(), build_simple_select()
- `src/analysis/analysis_utils.py` - USD/12 conversion, normalize_salary()
- `src/analysis/data_loader.py` - 12 funkcji (8 base + 4 general), prepare_analysis_dataset()
- `src/analysis/salary_analysis.py` - 5 analytical + 7 plot functions (12 total, refactored)
- `src/analysis/general_analysis.py` - 8 general statistics visualizations (pie chart, asymmetric %)
- `src/analysis/viz_utils.py` - save_figure() (div-only HTML), apply_common_layout(), SENIORITY_COLORS, aggregate_and_filter()
- `src/dashboard/` - Modular dashboard generator (Jinja2 templates, CSS, JS)
- `data/visualization_config.json` - Single source of truth dla kolorów (Plotly + HTML)
- `reports/visualizations.html` - tabbed interface (Salary | General), 16 charts
- `reports/figures/*.html` - 16 interaktywnych wykresów (div-only, responsive)
- `tests/test_salary_visualizations.py` - generator 8 salary charts
- `tests/test_general_visualizations.py` - generator 8 general charts

**Wyniki analizy (AFTER PERIOD MIGRATION):**

*Salary Analysis (1,884 IT offers with salary):*
- **Avg salary: 22,097 PLN** (bylo: 24,535 - skorygowane USD + period + outliers)
- **Median: 22,680 PLN** (Mean ≈ Median - clean distribution)
- **Max: 47,500 PLN** (bylo: 562,875 - USD/period fix)
- Period normalization: Day×21, Hour×168, Year÷12, Month×1 (w DB)
- Currency conversion: USD, EUR, HUF → PLN (w Python)
- Min count threshold: ≥10 dla tech/locations (eliminacja rzadkich przypadkow)
- 8 salary visualizations:
  - Box plot (seniority) - z consistent colors
  - Salary distribution (overall) - krzywa z Mean/Median
  - Salary distribution by seniority - 5 overlaid curves
  - Technology salary (top 15)
  - Worst technologies (bottom 15)
  - All cities by salary
  - All categories by salary
  - Contract type vs salary

*General Analysis (1,944 IT offers):*
- **2,633 unique technologies**
- **366 unique benefits**
- **9,698 technology pairs** (for co-occurrence matrix)
- 8 general visualizations:
  - Location distribution (PIE CHART, min 10 offers)
  - Weekday publication pattern (Mon-Sun)
  - Hour publication pattern (0-23)
  - Category distribution (all categories)
  - Top 15 technologies (by offer count)
  - Technology co-occurrence matrix (20x20 heatmap, ASYMMETRIC %, Oranges colorscale)
  - Top 15 benefits
  - Top 15 companies (min 2 offers)



## Period Migration - COMPLETED (2025-12-28)

### Problem (was)
44.5% of salary data incorrectly normalized due to missing `period` field:
- Day period (138 offers): 400 PLN/day treated as 69,332 PLN/month
- Year period (22 offers): No conversion applied
- Hour period (927 offers): Detected by unreliable threshold

### Solution Implemented
**Hybrid normalization approach:**
- Period normalization in DB (stable multipliers: Day*21, Hour*168, Year/12)
- Currency conversion in Python (dynamic rates)

**New columns added:**
- `offer_salary_types`: period, paid_holiday, monthly_from, monthly_to, disclosed_at, flexible_upper_bound
- `offers`: expires_at, hybrid_desc

### Results
- Period distribution verified: Month=1358, Hour=927, Day=138, Year=22
- Test case offer 379: 400 PLN/Day now correctly shows 8,400 PLN/month
- Mean salary: 22,097 PLN (was ~24,500 - corrected)
- Max salary: 47,500 PLN (was ~560,000 - fixed)

---

## ZNANE PROBLEMY / TECH DEBT

### 1. Brak error handling - HIGH

**Problem:**
- Network/file/parsing errors → raw crash
- Brak graceful degradation

**Priority:** HIGH - przed production use

---

### 2. Hardcoded configuration - FIXED (2025-12-26)

**Problem (był):**
- Paths, delays, page_size w kodzie
- Trudno zmieniać bez edycji kodu

**Rozwiązanie:**
- config.json z wszystkimi ustawieniami
- config_loader.py utility
- Zobacz `CHANGELOG.md` Session 3

---

### 3. Minimalny logging - MEDIUM

**Problem:**
- Tylko print() statements
- Brak structured logging
- Trudny debugging

**TODO:**
- Dodać structured logging (loguru)

---

### 4. Long functions - PARTIALLY FIXED (2025-12-26)

**Status:**
- `parse_detail_json()` zrefaktoryzowany (80 → 30 linii)
- Wydzielone helpery: _extract_technologies, _extract_salary_types, _extract_english_level
- `parse_posting()` nadal ~90 linii (TODO)

**TODO:**
- Refaktoryzacja parse_posting() z web_scraper.py

---

## KLUCZOWE DECYZJE ARCHITEKTONICZNE

### 1. JSON API zamiast HTML scraping

**Dlaczego:**
- HTML parsing kruchy (zmiana struktury = broken scraper)
- JSON API = strukturalne dane, stabilniejsze

**Lesson learned:**
Zawsze sprawdź czy jest API przed parsowaniem HTML

**Status:**
HTML scraper usunięty (2025-12-26, -232 linie)

---

### 2. Raw data backup architecture

**Problem rozwiązany:**
- Zmiana parsera wymagała re-scrapowania (10-15 min)
- Niemożliwość dodania nowych pól bez re-scrapowania

**Rozwiązanie:**
STARE: scrape → parse → clean → insert (wszystko na raz)
NOWE: scrape → save raw → parse → clean → insert (separacja)

**Szczegóły:** Zobacz `migration_history.md`

---

### 3. offer_signature zamiast URL jako klucz

**Problem:**
- Jedna oferta = wiele URL (różne lokalizacje)
- URL nie jest unique key

**Rozwiązanie:**
offer_signature = company_title_posted_numeric (unique per offer)

---

### 4. SQLite

**Pros:**
- Zero setup, file-based
- Wystarczające dla <10k rekordów
- Łatwy backup

**Cons:**
- Słabe dla concurrent writes
- Brak advanced features

**Decyzja:**
Wystarcza dla MVP, migracja do PostgreSQL jeśli potrzeba (schema portable)

---

### 5. Separacja listings/ i details/

**Dlaczego:**
- Listing JSON (~30KB) vs Details JSON (~200KB)
- Różne endpointy, różne częstotliwości scrapowania

**Korzyści:**
- Selective re-scraping
- Różne retention policies

---

## KOMUNIKACJA Z POPRZEDNIM ASYSTENTEM

### Błędy

1. **Dodawanie features bez pytania** (np. raw_subfolder do ScraperConfig)
   - Lesson: pytaj PRZED implementacją
2. **Brak konsultacji decyzji architektonicznych**
   - Lesson: konsultuj decyzje kierunkowe
3. **Za dużo proaktywności** (implementacja "na zapas")
   - Lesson: minimalizm - tylko co zatwierdzone

### Co działało

1. Raw data architecture - user zadowolony
2. Szybkie iteracje (test mode → full scrape)
3. Jasne naming funkcji/klas
4. Listening to feedback

### Lekcje dla następnego asystenta

- Pytaj PRZED implementacją (nawet jeśli oczywiste)
- Komunikuj decyzje + trade-offy
- Minimalizm - tylko zatwierdzone features
- Pliki .md można tworzyć bez pytania

**Szczegóły workflow:** Zobacz `AI_GUIDELINES.md`

---

## DOKUMENTY DO PRZECZYTANIA

**Start tutaj:**
- `documentation/README.md` - navigation guide (czytaj NAJPIERW)
- `progress_log.md` - obecny stan projektu (ten plik)
- `PRD.md` - wymagania biznesowe, cele
- `AI_GUIDELINES.md` - kompletne wytyczne (workflow, code quality, git)

**Techniczne:**
- `IMPLEMENTATION_PLAN.md` - szczegółowy plan (3 fazy).

**Historia:**
- `changelog.md` - tracking zmian z ostatniej sesji (clickable links)

---

## MAINTENANCE NOTES

### Jak dodać nowe pole do oferty

1. Dodaj do JobOffer TypedDict w `web_scraper.py`
2. Dodaj parsing w `parse_posting()`
3. Dodaj kolumnę do `schema.sql`
4. Dodaj do `_prepare_offer_data()` w `db_manager.py`
5. Re-parse z raw data (nie trzeba re-scrapować!)

### Jak dodać nową cleaning rule

1. Edytuj `data/cleaning_rules.json`
2. Re-parse z raw data

### Jak dodać nową kategorię do scrapowania

1. Edytuj `src/scraper/NoFluffJobs_filters.json`
2. Uruchom `python scraper_pipeline.py`

---

**Koniec Progress Log**

Powodzenia następnemu asystentowi!

## 14. Notebook 01 Fixes - Testing Phase (2026-01-02 19:30)

**Status:** IN PROGRESS

**Problem:** Notebook miał nazwy funkcji z planu, nie z implementacji

**Poprawki (15+ cells):**
- Imports: prepare_analysis_dataset, plot_*_boxplot, plot_*_type
- Data: load_offers_with_metadata() + prepare_analysis_dataset()
- Kolumny: company_name → company
- Syntax: 7 cells fixed
- Usunięto nieistniejące funkcje

**Status:** Struktura poprawiona, czeka na test

## 15. Notebooks Final Status (2026-01-02 20:15)

**Notebook 1 (EDA):** ✓ DZIAŁA - wszystkie celle OK
**Notebook 2 (ML):** USUNIĘTY - incompatybilność z implementacją
**Notebook 3 (Viz):** Do przetestowania

**Decyzja:** Notebook 1 wystarcza dla wymagań PRD ("Jupyter notebooks analiza + ML")
