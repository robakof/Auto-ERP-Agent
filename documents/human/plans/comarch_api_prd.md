# PRD — Comarch XL API Integration

**Data:** 2026-04-23
**Status:** Zatwierdzone

---

## 1. Wprowadzenie i cel

Projekt zastępuje bezpośrednie połączenia ODBC do bazy SQL Comarch XL oficjalnym API
(`cdn_api20251.net.dll`). Cel: operacje na danych ERP przechodzą przez warstwę biznesową XL
(walidacje, triggery, historia zmian) zamiast omijać ją bezpośrednim SQL.

Motywacja: incydent produkcyjny z 2026-04-22 — bezpośredni zapis przez ODBC ominął logikę
biznesową XL i trafił na produkcję bez kontroli.

---

## 2. Użytkownicy i persony

| Persona | Opis |
|---|---|
| Agent ERP Specialist | autonomicznie wykonuje operacje na danych XL (atrybuty, BI) |
| Agent Developer | buduje i utrzymuje warstwę integracyjną |
| Operator Comarch XL | posiada konto (login/hasło) do XL Server — używane przez agentów |

---

## 3. Wymagania funkcjonalne

| ID | Wymaganie |
|---|---|
| F1 | Operacje zapisu atrybutów (`xl_attribute_set`, `xl_attribute_bulk`) przechodzą przez XL API |
| F2 | Wszystkie operacje (odczyt i zapis) przechodzą przez XL API — ODBC usuwane po migracji każdego narzędzia |
| F3 | `XLApiClient` — abstrakcja z interfejsem niezależnym od trybu połączenia |
| F4 | Konfiguracja przez `.env` (`XL_LOGIN`, `XL_PASSWORD`) — zero hardcoded wartości |
| F5 | Istniejące CLI narzędzi bez zmian — backward compatibility absolutna |
| F6 | Każda operacja przez API zwraca ustrukturyzowany wynik (ok/error/meta) — ten sam kontrakt co obecne narzędzia |

---

## 4. Wymagania niefunkcjonalne

| ID | Wymaganie |
|---|---|
| N1 | Tryb połączenia wymienialny bez zmiany kodu klienckiego (interfejs `XLApiClient`) |
| N2 | Migracja przyrostowa — każde narzędzie migrowane osobno, pozostałe działają bez zmian |
| N3 | 100% testów PASS po każdym kroku migracji |
| N4 | Połączenie z XL Server nawiązywane raz na sesję (nie per wywołanie) |
| N5 | Błędy XL API mapowane na ten sam format `{"ok": false, "error": {...}}` co ODBC |

---

## 5. Scope i ograniczenia

**W zakresie:**
- `xl_attribute_set.py`, `xl_attribute_bulk.py`, `xl_attribute_template.py`, `xl_attribute_app.py`
- `sql_query.py` i narzędzia BI
- Warstwa `tools/lib/` — nowy `xl_api_client.py` zastępuje `sql_client.py` dla tych narzędzi

**Poza zakresem (ta iteracja):**
- Bot (`bot/sql_executor.py`) — osobna migracja
- KSeF, JAS — nie dotykają XL
- `session_init.py`, `agent_bus_cli.py` — infrastruktura agentowa, nie ERP

**Ograniczenia:**
- DLL wymaga .NET 6.0 + WindowsDesktop.App (do zainstalowania)
- pythonnet do zainstalowania (`pip install pythonnet`)
- XL client musi być zainstalowany lokalnie na TestServer ✓

---

## 6. Aspekty techniczne

**Stack:**
```
Python 3.13
  └── XlProxy.exe (x86 subprocess, C# + .NET Framework 4.8)
        └── cdn_api20251.net.dll
              └── XL Server (remote, operator z .env)
```

**Pliki warstwy Pythonowej (dostarczone):**
```
tools/xl_proxy/XlProxy.cs      ← x86 subprocess, generyczny invoke przez Reflection
tools/lib/xl_proxy_client.py   ← subprocess manager (start/send/stop)
tools/lib/xl_session.py        ← singleton sesji, lazy login z .env
tools/lib/xl_client.py         ← typed wrapper + invoke() dla wszystkich 150+ metod
```

**Migracja — status:**
```
M1 ✓ XlProxy x86 subprocess + DLL load + login/logout smoke test
M2 ✓ xl_attribute_set przez XL API (XLDodajAtrybut przez generyczny invoke)
M3 ✓ xl_attribute_bulk — write path przez set_attribute (już na XL API)
       xl_attribute_template, xl_attribute_app — tylko odczyt, bez zmian
M4 — ZAMKNIĘTE (Opcja A)
M5 — ZAMKNIĘTE (Opcja A)
```

**Decyzja M4/M5 (2026-04-27):**
XLWykonajZapytanie nie zwraca wierszy SELECT. Narzędzia sql_query.py, bi_discovery.py,
excel_export_bi.py i inne używają SqlClient wyłącznie do odczytu (SELECT).
Odczyt przez ODBC jest dozwolony — problem dotyczył wyłącznie WRITE omijającego warstwę
biznesową XL. Wszystkie write operations są teraz przez XL API.
SqlClient pozostaje jako "authorized read client" — nie zostaje usunięty.
