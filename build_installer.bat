@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  FakturyFZ -- build instalatora
echo ============================================
echo.

:: 1. Sprawdz Python
where python >nul 2>&1
if errorlevel 1 (
    echo [BLAD] Python nie znaleziony w PATH
    pause & exit /b 1
)

:: 2. Sprawdz PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instaluje PyInstaller...
    python -m pip install pyinstaller
)

:: 3. Zbuduj exe
echo [1/3] Buduje FakturyFZ.exe (PyInstaller)...
python -m PyInstaller FakturyFZ.spec --clean --noconfirm
if errorlevel 1 (
    echo [BLAD] PyInstaller nie powiodl sie
    pause & exit /b 1
)

:: 4. Sprawdz Inno Setup
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
    set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
)
if not exist %ISCC% (
    echo [BLAD] Inno Setup 6 nie znaleziony.
    echo        Pobierz z: https://jrsoftware.org/isdl.php
    echo        Lub skopiuj dist\FakturyFZ\ na serwer recznie.
    pause & exit /b 1
)

:: 5. Zbuduj instalator
echo [2/3] Buduje instalator setup.exe (Inno Setup)...
%ISCC% installer\setup.iss
if errorlevel 1 (
    echo [BLAD] Inno Setup nie powiodl sie
    pause & exit /b 1
)

echo.
echo [3/3] GOTOWE
echo   Instalator: installer\FakturyFZ_Setup_1.0.exe
echo   Skopiuj na serwer i uruchom jako administrator.
echo.
pause
