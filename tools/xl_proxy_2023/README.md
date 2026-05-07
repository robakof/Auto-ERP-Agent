# XlProxy 2023.1

Wersja proxy Comarch XL API dla **XL 2023.1** (`cdn_api20231.net.dll`).

Osobny projekt — nie rusza kodu wersji 2025.1.

## Build

```bat
build.bat
```

Wymaga: .NET Framework 4.x (csc.exe z `C:\Windows\Microsoft.NET\Framework\v4.0.30319\`).

## Test na produkcji

1. Skopiuj `XlProxy.exe` na serwer produkcyjny (dowolny folder).
2. Uruchom ręcznie w cmd:

```bat
XlProxy.exe "C:\Program Files (x86)\Comarch ERP XL 2023.1"
```

3. Powinno wypisać: `{"ok":true,"msg":"proxy ready"}`
4. Wpisz JSON logowania:

```json
{"cmd":"login","baza":"NAZWA_BAZY","oper":"LOGIN","haslo":"HASLO","serwer":"SERWER_SQL","tryb_wsadowy":"1"}
```

5. Oczekiwany wynik: `{"ok":true,"sesja_id":NUMER}`
6. Wyloguj: `{"cmd":"logout","sesja_id":NUMER}`

## Jeśli nie zadziała

Możliwe błędy:
- `LOAD_ERROR` — DLL nie nazywa się `cdn_api20231.net.dll` lub brakuje zależności
- `LOGIN_FAIL kod=X` — login failed (zły login/hasło/baza, albo typ `XLLoginInfo_20231` nie istnieje w tej DLL)

W obu przypadkach podaj dokładny komunikat — dostosujemy.

## Konfiguracja w .env (do pełnej integracji)

```env
XL_DLL_DIR=C:\Program Files (x86)\Comarch ERP XL 2023.1
```

Reszta zmiennych (XL_BAZA, XL_LOGIN, XL_PASSWORD, XL_SERWER) — produkcyjne wartości.
