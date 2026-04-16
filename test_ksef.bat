@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

echo ============================================
echo   KSeF - testy automatyczne
echo ============================================
echo.
echo [1/3] Unit testy KSeF...
echo.
py -m pytest tests/ksef -v --tb=short
set RESULT=!errorlevel!
if !RESULT! neq 0 (
    echo.
    echo !!! UNIT TESTY FAILED (exit code: !RESULT!) !!!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   205 unit testow PASS
echo ============================================
echo.
echo [2/3] ksef_status --summary...
echo.
py tools/ksef_status.py --summary
echo.
echo [3/3] ksef_validate...
echo.
py tools/ksef_validate.py
echo.
echo ============================================
echo   Gotowe. Komendy do testow manualnych:
echo ============================================
echo.
echo   py tools/ksef_generate.py --gid NNN --dry-run
echo   py tools/ksef_generate_kor.py --gid NNN --dry-run
echo   py tools/ksef_send.py --gid NNN --env demo
echo   py tools/ksef_daemon.py --env demo --once --dry-run
echo   py tools/ksef_daemon.py --env demo --once
echo   py -m pytest tests/integration/test_ksef_demo_smoke.py -v
echo.
pause
