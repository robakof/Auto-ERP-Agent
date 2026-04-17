@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   KSeF - wysylka faktur na Demo
echo ============================================
echo.
echo [1/2] Skanowanie ERP (dry-run)...
echo.
py tools/ksef_daemon.py --once --dry-run
echo.

set /p CONFIRM="Wyslac powyzsze faktury na KSeF Demo? (t/n): "
if /i not "!CONFIRM!"=="t" (
    echo Anulowano.
    pause
    exit /b 0
)

echo.
echo [2/2] Wysylka na KSeF Demo...
echo.
py tools/ksef_daemon.py --once

echo.
echo ============================================
echo   Podsumowanie
echo ============================================
echo.
py tools/ksef_status.py --today
echo.
pause
