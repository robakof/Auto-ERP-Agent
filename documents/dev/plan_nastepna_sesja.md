# Plan — następna sesja Developer

Data: 2026-03-15

## Zadanie 1 — Weryfikacja Fazy 1 (conversation w DB)

Zaimplementowaliśmy session_init + hooki ale nie przetestowaliśmy end-to-end bo agenci zaczęli
świrować (naruszenia workflow). Zanim cokolwiek innego — sprawdź czy pipeline działa.

### Kroki weryfikacji

1. Sprawdź czy w mrowisko.db są wpisy w tabeli conversation:
```
python tools/render.py conversation
```

2. Sprawdź czy session_init jest wywoływany przez agentów (czy tmp/session_id.txt jest świeży):
```
python tools/session_init.py --role developer
python tools/render.py conversation
```

3. Sprawdź hook debug files żeby upewnić się że hooki działają:
- tmp/hook_user_prompt_debug.json — czy istnieje i ma prompt?
- tmp/hook_stop_debug.json — czy ma last_assistant_message?

4. Jeśli conversation jest puste lub session_id=NULL wszędzie — zbadaj przyczynę
   (czy hooki są zarejestrowane w settings.local.json?)

### Oczekiwany wynik
- Wpisy human (user_prompt) i agent (agent_stop) w tabeli conversation
- session_id spójny między wpisami jednej sesji


## Zadanie 2 — Refaktor workflow BI (backlog id=61)

Szczegóły w backlogu. Research: documents/dev/research_results_workflow_compliance.md

### Nowa struktura folderów

```
workflows/
  bi_view_creation_workflow.md    ← przepisany ERP_VIEW_WORKFLOW.md
  bi_view_handoff_schema.md       ← nowy: kontrakt handoffu
handoffs/                         ← opcjonalnie osobny folder lub w workflows/
```

Stary ERP_VIEW_WORKFLOW.md → przeniesiony do `documents/archive/` (sesja 2026-03-15).

### Format każdej fazy (zamiast prozy)

```
## Faza N — Nazwa

**Owner:** ERP Specialist | Analityk
**Inputs required:** lista artefaktów
**Steps:**
1. ...
2. ...
**Forbidden:** czego NIE robić
**Exit gate:** warunki PASS — jeśli nie spełnione → BLOCKED
**Output:** ścieżka do artefaktu / wiadomość do roli X
**Self-check:** lista kontrolna przed zamknięciem fazy
```

### Sekcje do rozpuszczenia inline

- "Nazewnictwo widoków" → Inicjalizacja
- "Zasady nazewnictwa kolumn" → Faza 2
- "Zasady tłumaczenia wartości" → Faza 2
- "Ochrona dokumentacji" → skrót do Wstępu
- "Kiedy eskalować" → inline w każdej fazie

### Narzędzia do zbudowania przy refaktorze

| Narzędzie | Co robi | Faza |
|---|---|---|
| bi_init_view.py | stub draft.sql + progress.md | Inicjalizacja |
| bi_test_draft.py | draft → export (jeden krok) | Faza 2 |
| bi_submit_review.py | gate: eksport istnieje → wyślij do Analityka | Faza 1→Analityk |
| solutions_save_view.py | rozszerzenie: sprawdź eksport przed zapisem | Faza 4 |

### Kolejność pracy

1. Stwórz `workflows/` folder + `bi_view_creation_workflow.md` (nowy format)
2. Stwórz `bi_view_handoff_schema.md`
3. Zbuduj narzędzia (TDD, tools/ z testami)
4. Zaktualizuj `ERP_SPECIALIST.md` — usuń sekcje przeniesione do workflow
5. Zaktualizuj `ANALYST.md` — dodaj mapowanie do faz workflow + gate Analityka
6. Commit + push

### Ważne

- ERP_VIEW_WORKFLOW.md to plik chroniony — przed edycją potwierdź z userem
- ERP_SPECIALIST.md to plik chroniony — j.w.
- ANALYST.md to plik chroniony — j.w.
- Nowe pliki w workflows/ NIE są chronione (nowe)


## Kontekst sesji która to przygotowała

- Faza 1 arch uplift wdrożona (session_init, hooki, CLAUDE.md)
- Agenci świrowali: ERP Specialist pominął eksport, Analityk zatwierdził bez weryfikacji
- Research potwierdził: workflow jako proza = antywzorzec; potrzebny gate PASS/BLOCKED
- Bufor-agent (id=60) i dynamiczne prompty (Faza 3) rozwiążą to strukturalnie
- Na teraz: refaktor dokumentu + narzędzia bramkujące = szybszy win
