# Backlog metodologiczny

Przetworzone i priorytetyzowane zadania metodologiczne.
Źródło: `methodology_suggestions.md` + metodologiczne wątki z `developer_suggestions.md`.

Zarządza: Metodolog.

## Format wpisu

```
### Tytuł

**Źródło:** methodology_suggestions | developer_suggestions
**Sesja:** data
**Dokument do zmiany:** METHODOLOGY.md | CLAUDE.md | DEVELOPER.md

Opis obserwacji i propozycja zmiany.
```

---

## Aktywne

### Przycinanie ramy teoretycznej

**Źródło:** methodology_suggestions
**Sesja:** 2026-03-08
**Dokument do zmiany:** METHODOLOGY.md (sekcja "Wprowadzenie")

Test operacyjny dla każdego pojęcia: czy zmienia jakąkolwiek decyzję?
Fraktalność — tak (ta sama struktura per poziom złożoności).
Genomiczność, cybernetyka drugiego rzędu — legitymizacja, nie instrukcja.
Zostawić jedną ramę orientacyjną, resztę zastąpić konkretnymi warunkami.

---

### Wielość ról wykonawczych — zasada 1 rola = 1 plik refleksji

**Źródło:** developer_suggestions + backlog.md ([Arch] Separacja pamięci między agentami)
**Sesja:** 2026-03-11
**Dokument do zmiany:** METHODOLOGY.md (sekcja "Przepływ refleksji przez poziomy")

Obecna tabela przepływu refleksji zakłada jeden poziom "Agent" z jednym plikiem sugestii.
Projekt ma już dwie role wykonawcze (Agent ERP, Analityk Danych) — każda z innymi wzorcami
obserwacji. Mieszanie zaszumi plik refleksji.

Pytania do rozstrzygnięcia przed wdrożeniem:
- Czy poziom "Agent" przemianować na "Executor" / "Agenci" w tabeli poziomów?
- Zasada: każda rola wykonawcza = własny plik sugestii (np. agent_erp_suggestions.md,
  analyst_suggestions.md)?
- Co jest jednostką pracy dla Analityka (per sesja? per zakres/widok)?

Ref. dev backlog: [Arch] Separacja pamięci między agentami wykonawczymi (2026-03-10).

---

## Archiwum

### ✓ [2026-03-08] Reguła zamykania wątków — wdrożona 2026-03-11

Dodana do METHODOLOGY.md, sekcja "Cykl pracy" jako "Zasada zamykania wątków".

### ✓ [2026-03-10] Poziom interwencji — symptom vs źródło — wdrożony 2026-03-11

Dodany do METHODOLOGY.md, sekcja "Pętla meta-obserwacji".

### ✓ [2026-03-10] Ręczne przetwarzanie jako sygnał narzędzia — wdrożone 2026-03-11

Dodane do METHODOLOGY.md, sekcja "Pętla meta-obserwacji".
