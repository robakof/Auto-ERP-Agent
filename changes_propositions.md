# Plan implementacji — Kamień milowy 2 (erp_windows.json)

Data: 2026-02-27

---

## Zakres

Stworzenie `solutions/erp_windows.json` — katalogu okien ERP.
Minimalny MVP: jedno okno pokryte istniejącymi solutions/ — "Okno towary".

---

## Schemat wpisu

Per ARCHITECTURE.md sekcja 7 i 11 (pola czytane przez search_windows.py):

```
id              — unikalny identyfikator
name            — nazwa wyświetlana w ERP
aliases         — popularne nazwy nieformalne
primary_table   — główna tabela SQL okna
related_tables  — tabele joinowane typowo w tym oknie
config_types    — co można konfigurować
```

---

## Proponowana zawartość

### Skąd dane

- Widok "Towary według EAN": `from cdn.TwrKarty` (atrybuty.sql, filtr.sql prefiks Twr_)
- Widok "Towary według grup": `from cdn.TwrKarty JOIN cdn.TwrGrupy` (Kod EAN.sql),
  filtr.sql z prefiksem TwG_ → TwrGrupy jako kontekst grupowania
- cdn.Atrybuty — joinowana w atrybuty.sql
- primary_table = CDN.TwrKarty (główna tabela kartoteki towarowej w obu widokach)

### Plik

`solutions/erp_windows.json`:

```json
[
  {
    "id": "okno_towary",
    "name": "Okno towary",
    "aliases": ["towary", "kartoteki towarowe"],
    "primary_table": "CDN.TwrKarty",
    "related_tables": ["CDN.TwrGrupy", "CDN.Atrybuty"],
    "config_types": ["columns", "filters"]
  }
]
```

---

## Poza zakresem MVP

Kolejne okna (zamówienia, dokumenty, kontrahenci) dodawane w miarę rozbudowy solutions/.

---

*Plan przygotowany: 2026-02-27*
