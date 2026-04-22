@echo off
:: KSeF — raport dzienny (email)
:: Uruchamiac przez Windows Task Scheduler codziennie o 13:30
::
:: Uzycie reczne:
::   ksef_raport_dzienny.bat              -> email (domyslnie)
::   ksef_raport_dzienny.bat --stdout     -> terminal
::   ksef_raport_dzienny.bat --since 7d   -> ostatnie 7 dni

cd /d "%~dp0"

if "%1"=="" (
    py tools/ksef_report.py --send-email
) else (
    py tools/ksef_report.py %*
)
