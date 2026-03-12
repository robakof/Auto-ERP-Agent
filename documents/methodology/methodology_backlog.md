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

### Model wirtualnej firmy AI — zasady do METHODOLOGY.md

**Źródło:** methodology_suggestions (sesja 2026-03-11)
**Sesja:** 2026-03-11
**Dokument do zmiany:** METHODOLOGY.md (nowa sekcja lub rozszerzenie "Trzy poziomy działania")

Wypracowane zasady czekające na wdrożenie:

1. Podział ról człowiek/AI — rola trafia do tego kto lepiej ją wypełnia w danym momencie.
   Warunek przydziału do AI: decyzje przewidywalne i weryfikowalne.

2. Jednostka pracy — zdefiniuj zanim zaczniesz zbierać refleksje. Definicja należy
   do dokumentu roli w projekcie, nie do metodologii.

3. Struktura organizacyjna przy skali — przepływ refleksji odzwierciedla org chart.
   PM jako warstwa agregująca między developerami a metodologiem.

Ref. methodology_suggestions.md: [2026-03-11] Wirtualna firma AI.

---

### Komunikacja w roju — wzorzec dla warstwy myśli

**Źródło:** sesja metodologiczna 2026-03-12
**Sesja:** 2026-03-12
**Dokument do zmiany:** METHODOLOGY.md — nowa sekcja "Architektura agentocentryczna"

Wypracowany wzorzec dla wspólnej pamięci agentów (warstwa myśli):

**Wzorzec:** Hybryda Blackboard + Tuple Space z uwagą jako sygnałem wartości

Trzy warstwy komunikacji:
1. Dyrektywy — stabilne wytyczne per rola (statyczne, .md lub DB)
2. Wiadomości — kierowana komunikacja punkt-punkt (adresowane)
3. Myśli — wspólna przestrzeń tematyczna (tagowana, bez adresata)

Zasady warstwy myśli:
- Odczyt niedestruktywny (`rd` nie `in`) — myśli persystują po przeczytaniu
- Tagi jako metadata filter + treść semantycznie (hybryda deterministyczny + probabilistyczny)
- Score oparty na uwadze: `score += 1` przy każdym odczycie, `score -= δ` pasywnie
- Ważność wyłania się z wzorca użycia roju — bez ręcznej priorytetyzacji
- Ewaporacja odwrotna: myśli często przywoływane rosną, ignorowane gasną

Research potwierdza: wzorzec jest znany (Blackboard, Tuple Space, ACO), brak gotowej
implementacji dla LLM — do zbudowania. Ref: `research_results_swarm_communication.md`

**Status:** Koncepcja zatwierdzona metodologicznie. Czeka na weryfikację implementacyjną
przez Developera — patrz `handoff_db_architecture.md` (zaktualizowany 2026-03-12).
Ryzyko: pułapka wdrożeniowa — wizjonerska koncepcja może okazać się nieproporcjonalnie
kosztowna lub technicznie niewykonalna w obecnym stacku.

---

## Archiwum

### ✓ [2026-03-11] Wielość ról — zasada 1 jednostka org. = 1 plik refleksji — wdrożona 2026-03-11

Zasada ogólna dodana do METHODOLOGY.md, sekcja "Przepływ refleksji przez poziomy".
Tabela małego projektu zachowana jako przykład.

### ✓ [2026-03-08] Reguła zamykania wątków — wdrożona 2026-03-11

Dodana do METHODOLOGY.md, sekcja "Cykl pracy" jako "Zasada zamykania wątków".

### ✓ [2026-03-10] Poziom interwencji — symptom vs źródło — wdrożony 2026-03-11

Dodany do METHODOLOGY.md, sekcja "Pętla meta-obserwacji".

### ✓ [2026-03-10] Ręczne przetwarzanie jako sygnał narzędzia — wdrożone 2026-03-11

Dodane do METHODOLOGY.md, sekcja "Pętla meta-obserwacji".
