# Plan implementacji — update_window_catalog.py

Data: 2026-02-27

---

## Zakres

Nowe narzędzie CLI `tools/update_window_catalog.py` — zarządzanie wpisami
w `solutions/erp_windows.json` przez agenta.

Uzupełnia lukę: `search_windows.py` tylko czyta, brak narzędzia do zapisu.

---

## Scenariusze użycia

### 1. Nowe okno (po zapisaniu rozwiązania do nieznanego folderu)

Agent odczytuje `filtr.sql` widoku → identyfikuje primary_table po prefiksie
kolumny (`ZaN_` → CDN.ZamNag) przez `search_docs.py` → tworzy wpis,
pyta użytkownika o aliasy.

### 2. Dopisanie aliasu z rozmowy

Użytkownik mówi "dodaj filtr do listy ZO" → `search_windows.py` nie znajduje
"listy ZO" → agent pyta "nie znam 'lista ZO', czy chodzi o [lista znanych okien]?"
→ użytkownik potwierdza → agent dopisuje alias.

### 3. Aktualizacja related_tables

Agent odkrywa nowy JOIN w generowanym SQL → dopisuje tabelę do related_tables
istniejącego okna.

---

## CLI

```
python tools/update_window_catalog.py \
  --id okno_zamowien \
  [--name "Okno zamówień sprzedaży"] \
  [--primary-table CDN.ZamNag] \
  [--add-alias "lista ZO"] \
  [--add-alias "zamówienia"] \
  [--config-types columns filters]
```

- `--id` wymagane
- Pozostałe pola opcjonalne — aktualizowane selektywnie (upsert)
- `--add-alias` można powtarzać
- Aliasy: deduplikacja case-insensitive
- Jeśli okno nie istnieje → tworzy nowy wpis
- Jeśli okno istnieje → merguje zmiany (aliasy dopisywane, nie zastępowane)

---

## Kontrakt wyjścia

```json
{
  "ok": true,
  "data": {
    "window": { ...aktualny wpis po zmianach... },
    "created": true
  },
  "error": null,
  "meta": {"duration_ms": 5, "truncated": false}
}
```

`created: true` = nowy wpis, `false` = aktualizacja istniejącego.

---

## Funkcje wewnętrzne

- `_load_windows(path) -> list[dict]` — wczytuje JSON, pusta lista gdy plik nie istnieje
- `_save_windows(windows, path)` — zapisuje JSON (indent=2, ensure_ascii=False)
- `_find_window(windows, window_id) -> int | None` — indeks wpisu lub None
- `update_window(window_id, name, primary_table, add_aliases, config_types, solutions_path) -> dict` — główna logika (upsert)
- `main()` — CLI entry point

---

## Testy (test_update_window_catalog.py)

- Nowe okno → wpis istnieje, created=true
- Istniejące okno → created=false, pola zaktualizowane
- `--add-alias` → alias dopisany, brak duplikatów
- `--add-alias` case-insensitive dedup ("Lista ZO" == "lista zo")
- Brak `--id` → ok=false, MISSING_ARGUMENT
- Uszkodzony JSON → ok=false, PARSE_ERROR
- Plik nie istnieje → tworzony automatycznie

---

## Poza zakresem

- Usuwanie wpisów i aliasów (nie potrzebne w MVP)
- Walidacja nazwy tabeli (CDN.XXX) — agent odpowiada za poprawność
- related_tables — redundantne, relacje są w docs.db (tabela `relations`)

---

*Plan przygotowany: 2026-02-27*
