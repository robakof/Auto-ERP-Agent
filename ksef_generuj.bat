@echo off
:: Generowanie XML KSeF dla faktur z danego dnia
:: Uzycie:
::   ksef_generuj.bat              -> dzisiejsza data
::   ksef_generuj.bat 2026-04-01   -> podana data (YYYY-MM-DD)

cd /d "%~dp0"

if "%1"=="" (
    for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set DATA=%%a
) else (
    set DATA=%1
)

echo Generowanie faktur KSeF za: %DATA%
echo.

py tools/ksef_generate.py --date-from %DATA% --validate output/schemat_FA3.xsd

echo.
echo Gotowe. Pliki zapisane w: output\ksef\
pause
