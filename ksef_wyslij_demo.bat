@echo off
:: KSeF Demo — daemon z watchdogiem (auto-restart, heartbeat monitoring)
::
:: Uzycie:
::   ksef_wyslij_demo.bat              -> watchdog + daemon, tick co 15 min
::   ksef_wyslij_demo.bat 300          -> tick co 5 min (sekundy)
::   ksef_wyslij_demo.bat --once       -> jeden scan + wysylka, potem exit (bez watchdog)

cd /d "%~dp0"

if "%1"=="--once" (
    echo [KSeF Demo] Jednorazowy scan + wysylka...
    py tools/ksef_daemon.py --once
    goto :eof
)

set INTERVAL=900
if not "%1"=="" set INTERVAL=%1

echo [KSeF Demo] Watchdog startuje — daemon interval %INTERVAL%s
echo Auto-restart przy crash lub zawieszeniu
echo Ctrl+C aby zatrzymac
echo.

py tools/ksef_watchdog.py --interval %INTERVAL%
