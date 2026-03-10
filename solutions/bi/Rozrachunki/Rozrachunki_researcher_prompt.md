# Prompt dla agenta researchującego — prefiks (Z) w numerach FSK

## Kontekst

W Comarch ERP XL funkcja `CDN.NazwaObiektu(GIDTyp, GIDNumer, 0, 2)` zwraca numer dokumentu
z prefiksem: `(s)`, `(A)`, `(Z)` lub bez prefiksu.

Budujemy widok BI i musimy replikować tę logikę inline w SQL (bez wywołania funkcji CDN —
konto `CEiM_BI` nie ma uprawnienia EXECUTE).

Zidentyfikowaliśmy reguły dla większości przypadków (pokrycie 99.999%):

```
(Z) — TrN_Stan & 2 = 2  (bit1 ustawiony; Stan=3=binary011)         → potwierdzone dla FSK-42
(A) — GenDokMag = -1 AND typ zakupowy (FZ=1521, FZK=1529, PZ=1489) → potwierdzone
(s) — GenDokMag = -1 AND pozostałe typy                            → potwierdzone
brak — standard                                                     → potwierdzone
```

## Problem — 1 niewyjaśniony wyjątek

Dokument `(Z)FSK-8/01/26/SPKRK` (GIDTyp=2041, GIDNumer=6394119) dostaje prefiks `(Z)`,
ale ma `TrN_Stan=5` (binary 101 — bit1 NIE jest ustawiony).

Sprawdzone pola w CDN.TraNag — wszystkie identyczne jak u sąsiednich `(s)FSK`:

| Pole          | Wartość dla (Z)FSK-8 |
|---------------|----------------------|
| TrN_Stan      | 5                    |
| TrN_GenDokMag | -1                   |
| TrN_NrKorekty | ""  (puste)          |
| TrN_RodzajKor | 0                    |
| TrN_TypDatyKor| 1                    |
| TrN_ZwrTyp    | 2041                 |
| TrN_ZwrNumer  | 0                    |
| TrN_Aktywny   | 0                    |

## Pytanie do zbadania

Jaki warunek w CDN.TraNag (lub powiązanej tabeli) powoduje prefiks `(Z)` dla dokumentu
FSK z `TrN_Stan=5` i `TrN_GenDokMag=-1`?

Wskazówki do zbadania:
- Dokumentacja Comarch ERP XL — opis pola `TrN_Stan` (bitmask) lub `TrN_ZwrTyp/ZwrNumer`
- Czy `(Z)` = "zwrot" dotyczy specyficznego `TrN_RodzajKor` lub `TrN_TypDatyKor`?
- Czy CDN.NazwaObiektu sprawdza tabelę `CDN.ZamNag`, `CDN.Rozrachunki` lub inną?
- Czy Comarch udostępnia gdziekolwiek źródło logiki budowania numeru dokumentu?
- Szukaj fraz: "TrN_Stan bitmask", "NazwaObiektu prefix Z", "zwrot korekta ERP XL",
  "CDN.TraNag ZwrTyp ZwrNumer znaczenie"

## Oczekiwany wynik

Konkretny warunek SQL który można wstawić do CASE w inline budowaniu numeru:

```sql
CASE
    WHEN <warunek na (Z)> THEN '(Z)'
    WHEN TrN_Stan & 2 = 2 AND TrN_GIDTyp IN (2041,1529,2042,2045) THEN '(Z)'
    WHEN TrN_GenDokMag = -1 AND TrN_GIDTyp IN (1521,1529,1489)    THEN '(A)'
    WHEN TrN_GenDokMag = -1                                        THEN '(s)'
    ELSE ''
END
```
