# Strategia: Konwencje vs Runner — co dalej?

Data: 2026-03-25
Autor: Architect
Status: draft — do dyskusji z Dawidem

---

## Diagnoza

### Stan obecny

| Metryka | Wartość |
|---|---|
| Konwencje active | 2 (META, WORKFLOW) |
| Konwencje planowane | ? (brak mapy pokrycia) |
| Open suggestions | 176 (100 obs, 43 rules, 25 disc, 8 tool) |
| Workflows | 6 |
| Siła przerobowa | 1 człowiek + 1 agent/sesja |

### Problem

System generuje wiedzę (sugestie) szybciej niż ją absorbuje. 176 open suggestions
to symptom — nie choroba. Choroba to: **brak genetyki** (konwencji) powoduje, że
każda sesja odkrywa te same wzorce na nowo i zgłasza je jako sugestie.

Analogia z SPIRIT.md: konwencje to DNA mrowiska. Bez DNA każdy mrówek buduje
jak chce — efektem jest chaos, nie emergencja.

---

## Trzy strategie

### A) Konwencje-first (pełne pokrycie, potem runner)

**+** Maksymalna jakość, zero reworku, runner od razu produkuje dobry output
**-** Tygodnie pracy zanim runner ruszy. Sugestie rosną dalej. Frustracujące tempo.

**Ryzyko:** analysis paralysis — nigdy nie skończymy "wszystkich" konwencji.

### B) Runner-first (odpal agentów, konwencje potem)

**+** Natychmiastowy throughput, widoczny postęp
**-** Agenci bez konwencji = rework 80% outputu. Sugestie rosną jeszcze szybciej.
      Sam to zidentyfikowałeś: "będzie wprowadzało rzeczy, które i tak trzeba przepisać."

**Ryzyko:** dług techniczny rośnie szybciej niż go spłacamy.

### C) Critical-path conventions + runner (rekomendacja)

**+** Odblokowanie runnera w ciągu dni, nie tygodni. Jakość "good enough" na start.
**-** Nie wszystko będzie pokryte — ale kontrolowany dług, nie chaos.

---

## Rekomendacja: Strategia C — critical-path conventions

### Krok 1: Mapa konwencji (dzisiaj, ~1h)

Zidentyfikuj WSZYSTKIE aspekty projektu wymagające konwencji.
Nie pisz ich — tylko nazwij i priorytetyzuj.

Prawdopodobna mapa (do zwalidowania):

| Konwencja | Owner | Status | Runner-blocking? |
|---|---|---|---|
| META (struktura konwencji) | Architect | active | --- |
| WORKFLOW (struktura workflow) | PE | active | --- |
| PROMPT (struktura promptów ról) | PE | istnieje? (PROMPT_CONVENTION.md) | tak |
| CODE (Python: naming, structure, error handling) | Architect | brak | tak |
| COMMUNICATION (agent-to-agent, message format) | Architect | brak | nie |
| GIT (commit, branch, PR) | Developer | brak | nie |
| TESTING (co testować, jak, coverage) | Developer | brak | częściowo |
| DATA/SCHEMA (DB, tabele, migracje) | Architect | brak | nie |
| FILE_STRUCTURE (gdzie co żyje w repo) | Architect | brak | częściowo |

Runner-blocking = "czy agent bez tej konwencji wyprodukuje output do wyrzucenia?"

### Krok 2: Napisz 2-3 runner-blocking conventions (3-5 dni)

Tylko te, bez których runner generuje śmieci:
1. **CONVENTION_PROMPT** — bo agenci piszą/modyfikują prompty
2. **CONVENTION_CODE** — bo agenci piszą Python
3. Ewentualnie FILE_STRUCTURE — żeby agenci wiedzieli gdzie kłaść pliki

Reszta może poczekać. Kontrolowany dług > chaos.

### Krok 3: Sugestie — triage, nie pełne przetwarzanie (równolegle z krokiem 2)

176 sugestii to nie 176 tasków. Z doświadczenia:
- ~60% to duplikaty lub obserwacje bez akcji (close as noted)
- ~25% to warianty 5-10 tematów (grupuj → 5-10 backlog items)
- ~15% to real action items

**Kto:** PE ma workflow (suggestions_processing). To jego domena.
Ale 176 sugestii w jednej sesji to za dużo nawet dla PE.

**Propozycja:** Podziel na batche po ~30-40. PE przetwarza 1 batch/sesja.
4-5 sesji i backlog jest czysty. Równolegle z convention writing.

### Krok 4: Runner MVP (po krokach 2-3)

Z 2-3 konwencjami runner może startować. Pierwsze zadania: proste,
powtarzalne, z istniejącymi workflow (np. BI views).

---

## Kto co robi?

| Rola | Zadanie | Kiedy |
|---|---|---|
| **Architect** | Mapa konwencji + draft CONVENTION_CODE | teraz |
| **PE** | Triage sugestii (batch 1/5) + review CONVENTION_PROMPT | równolegle |
| **Developer** | Bez zmian — kontynuuje narzędzia, nie blokowany | ciągle |
| **Dawid** | Approval konwencji, decyzje strategiczne | na żądanie |

---

## Trade-offs

| Zysk | Koszt |
|---|---|
| Runner ruszy w ciągu dni | Nie wszystkie konwencje na start |
| Sugestie przestaną rosnąć (konwencje = mniej odkryć na nowo) | 4-5 sesji PE na triage |
| Kontrolowany dług zamiast chaosu | Dług nadal istnieje (reszta konwencji) |
| Równoległa praca ról (nie sekwencyjna) | Wymaga koordynacji |

---

## Odpowiedź na pytanie "komu zlecić sugestie?"

**PE** — to jego workflow (suggestions_processing v1.0). Ale z ważnym zastrzeżeniem:

PE nie powinien realizować sugestii. PE je triażuje, extrahuje actionable items,
tworzy backlog entries i zamyka. Realizację robią odpowiednie role:
- Rule/pattern → PE aktualizuje prompty
- Tool/feature → Developer
- Architecture → Architect
- Metodologia → Metodolog

---

## Decyzja potrzebna od Dawida

1. Czy strategia C (critical-path conventions) jest OK?
2. Czy mapa konwencji (krok 1) to dobry pierwszy krok?
3. Czy PE ma zacząć triage sugestii równolegle?
