# Plan: Comarch XL API — warstwa Pythonowa

**Data:** 2026-04-27
**Status:** Draft — do zatwierdzenia

---

## Problem

API Comarch XL ma 150+ metod w 20+ domenach (namespaces.json).
Hardcodowanie każdej metody w XlProxy.cs → niemożliwe do utrzymania.

---

## Kluczowa decyzja architektoniczna

XlProxy.cs dostaje **generyczny `invoke`** przez .NET Reflection:

```json
{"cmd":"invoke","method":"XLNowyDokument","sesja_id":1,"params":{"Wersja":20251,"TrNTyp":524288}}
```

XlProxy:
1. Znajduje metodę po nazwie (Reflection)
2. Tworzy odpowiedni Info struct (XL*Info_20251) — typ wyciągany z sygnatury metody
3. Ustawia pola z params dict
4. Wywołuje metodę
5. Odczytuje wszystkie pola wyniku struct → zwraca jako JSON

→ Wszystkie 150+ metod obsłużone BEZ nowego kodu w XlProxy.

---

## Architektura warstwy

```
Python caller
  └── xl_client.py          ← typed API (atrybuty, dokumenty, zamówienia...)
        └── xl_session.py   ← singleton sesji (login/logout, sesja_id)
              └── xl_proxy_client.py  ← subprocess manager (stdin/stdout JSON)
                    └── XlProxy.exe  ← x86 C# subprocess
                          └── cdn_api20251.net.dll
```

---

## Pliki do stworzenia / zmiany

### XlProxy.cs — dodać: generyczny invoke

Nowa komenda obok login/logout/blad:

```csharp
case "invoke": return CmdInvoke(json);
```

`CmdInvoke`:
- GetStr(json, "method") → nazwa metody
- GetStr(json, "params") → JSON string z polami
- Reflection: znajdź metodę, pobierz typy parametrów
- Stwórz Info struct, ustaw pola (SetField per klucz)
- Invoke, obsłuż out params
- Serializuj wszystkie pola Info do JSON → zwróć

Istniejące komendy (login, logout, atrybut, zapytanie, zdarzenie, blad) **zostają** —
nie ma regresji dla xl_attribute_set.py.

### tools/lib/xl_proxy_client.py (nowy)

Subprocess manager:
- `start(dll_dir)` — uruchamia XlProxy.exe, czeka na `{"ok":true,"msg":"proxy ready"}`
- `send(cmd_dict)` → dict — wysyła JSON line, odbiera JSON line
- `stop()` — zamyka subprocess
- Obsługa błędów: timeout, crash proxy, restarT

### tools/lib/xl_session.py (nowy)

Session singleton:
- `get()` → (proxy_client, sesja_id) — lazy init
- `login(baza, oper, haslo, serwer, dll_dir)` — wewnętrznie przez proxy
- `logout()` — wysyła logout, zatrzymuje proxy
- Env vars: XL_BAZA, XL_LOGIN, XL_PASSWORD, XL_SERWER, XL_DLL_DIR
- Thread-safe (Lock)

### tools/lib/xl_client.py (nowy)

Typed wrapper — thin layer nad xl_session.invoke():

```python
class XlClient:
    def invoke(self, method: str, **params) -> dict: ...

    # Atrybuty
    def dodaj_atrybut(self, gid_typ, gid_numer, gid_firma, klasa, wartosc) -> dict: ...

    # Dokumenty handlowe
    def nowy_dokument(self, typ_dok, **params) -> dict: ...
    def dodaj_pozycje(self, doc_id, **params) -> dict: ...
    def zamknij_dokument(self, doc_id, **params) -> dict: ...

    # Zamówienia
    def nowy_dokument_zam(self, **params) -> dict: ...
    def dodaj_pozycje_zam(self, **params) -> dict: ...
    def zamknij_dokument_zam(self, **params) -> dict: ...

    # Kontrahenci
    def nowy_kontrahent(self, **params) -> dict: ...

    # ... kolejne domeny w miarę potrzeby
```

`invoke()` jest publiczne — każda metoda XL API osiągalna bez typed wrapper.

### xl_attribute_set.py — migracja (M2)

Zamienić SqlClient na XlClient.dodaj_atrybut() / invoke().
Istniejący interfejs CLI bez zmian (backward compatibility).

---

## Kolejność implementacji (milestony)

| M | Co | Status |
|---|---|---|
| M2a | XlProxy.cs: generyczny invoke + rebuild .exe | ✓ commit d5faa16 |
| M2b | xl_proxy_client.py + testy | ✓ commit d5faa16 |
| M2c | xl_session.py + testy | ✓ commit d5faa16 |
| M2d | xl_client.py (invoke + typed helpers) + testy | ✓ commit d5faa16 |
| M2e | xl_attribute_set.py: migracja na XlClient | ✓ commit 3ea5288 |
| M3 | xl_attribute_bulk write path — przez set_attribute | ✓ done (bez zmian kodu) |
| M4 | sql_query.py + BI | ZAMKNIĘTE — Opcja A (patrz niżej) |
| M5 | Usuń sql_client.py | ZAMKNIĘTE — Opcja A |

**Decyzja M4/M5:** XLWykonajZapytanie nie zwraca wierszy SELECT.
Wszystkie pozostałe SqlClient usages to SELECT (odczyt) — odczyt przez ODBC nie omija
logiki biznesowej XL. SqlClient zostaje jako "authorized read client".

---

## Co zostaje bez zmian

- `xl_attribute_set.py` CLI — żaden argument nie zmienia się
- `xl_attribute_bulk.py`, `xl_attribute_template.py`, `xl_attribute_app.py` — do M3
- `tests/test_xl_attribute_set.py` — zaktualizowane mocki (XlClient zamiast SqlClient)
- `.env` klucze XL_LOGIN / XL_PASSWORD — te same

---

## Testy

Każdy nowy plik ma plik testowy:
- `tests/test_xl_proxy_client.py` — mock subprocess (stdin/stdout)
- `tests/test_xl_session.py` — mock proxy_client
- `tests/test_xl_client.py` — mock session
- `tests/test_xl_attribute_set.py` — zaktualizowany (mock XlClient)
