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

### Reguła zamykania otwartych wątków

**Źródło:** methodology_suggestions
**Sesja:** 2026-03-08
**Dokument do zmiany:** METHODOLOGY.md (sekcja "Cykl pracy")

Każdy otwarty wątek powinien mieć warunek zamknięcia lub datę przeglądu.
Po tej dacie można archiwizować bez poczucia utraty.
Warto zapisać wprost: archiwizacja to nie utrata — to świadoma decyzja.

---

### Przycinanie ramy teoretycznej

**Źródło:** methodology_suggestions
**Sesja:** 2026-03-08
**Dokument do zmiany:** METHODOLOGY.md (sekcja "Wprowadzenie")

Test operacyjny dla każdego pojęcia: czy zmienia jakąkolwiek decyzję?
Fraktalność — tak (ta sama struktura per poziom złożoności).
Genomiczność, cybernetyka drugiego rzędu — legitymizacja, nie instrukcja.
Zostawić jedną ramę orientacyjną, resztę zastąpić konkretnymi warunkami.

---

### Poziom interwencji — symptom vs. źródło

**Źródło:** developer_suggestions
**Sesja:** 2026-03-10
**Dokument do zmiany:** METHODOLOGY.md (sekcja "Pętla meta-obserwacji")

Przed zapisaniem obserwacji jako nowej reguły należy ustalić poziom interwencji.
Pytania diagnostyczne:
- Czy to problem który można rozwiązać narzędziem zamiast instrukcją?
- Czy można prekomputować dane tak żeby agent nie musiał ich odkrywać?
- Czy zmiana architektury sprawia że problem nie ma prawa wystąpić?

Jeśli odpowiedź na którekolwiek brzmi "tak" — sygnał dla Developera, nie nowa reguła.
Reguła jest ostatnim narzędziem: właściwa gdy strukturalne rozwiązanie jest nieproporcjonalnie kosztowne lub niemożliwe.

Uzasadnienie: obecne pytania pętli meta-obserwacji działają na poziomie single-loop
("co powiedzieć agentowi żeby było lepiej?"). Brakuje pytań double-loop — czy interwencja
powinna istnieć. To jest zastosowanie Argyris/Schön już cytowanych we wprowadzeniu.

---

## Archiwum

*(brak wpisów)*
