@echo off
:: Generowanie XML KSeF dla KOREKT RABATOWYCH (skonto + rabat transakcyjny) z danego dnia
:: Uzycie:
::   ksef_generuj_rabat.bat              -> dzisiejsza data, dialog wyboru folderu
::   ksef_generuj_rabat.bat 2026-04-01   -> podana data (YYYY-MM-DD), dialog wyboru folderu

cd /d "%~dp0"

if "%1"=="" (
    for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set DATA=%%a
) else (
    set DATA=%1
)

echo Generowanie korekt rabatowych KSeF za: %DATA%
echo.

:: Dialog wyboru folderu wyjsciowego
for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description = 'Wybierz folder dla plikow XML KSeF (korekty rabatowe)'; $d.SelectedPath = '%~dp0output\ksef'; if ($d.ShowDialog() -eq 'OK') { $d.SelectedPath } else { '%~dp0output\ksef' }"`) do set OUT_DIR=%%F

echo Folder wyjsciowy: %OUT_DIR%
echo.

py tools/ksef_generate_rabat.py --date-from %DATA% --validate output/schemat_FA3.xsd --output-dir "%OUT_DIR%"

echo.
echo Gotowe. Pliki zapisane w: %OUT_DIR%
pause
