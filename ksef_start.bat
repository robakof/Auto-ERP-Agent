@echo off
:: KSeF — glowny launcher (daemon + watchdog + raport dzienny)
::
:: Uzycie:
::   ksef_start.bat               -> daemon + watchdog + raport o 13:30
::   ksef_start.bat --once        -> jednorazowy scan + wysylka
::   ksef_start.bat --dry-run     -> podglad bez wysylki
::   ksef_start.bat --no-report   -> daemon bez raportu mailowego

cd /d "%~dp0"

echo =============================================
echo   KSeF — uruchamianie systemu
echo =============================================
echo.

C:\Windows\py.exe tools\ksef_start.py %* > data\ksef_start.log 2>&1
