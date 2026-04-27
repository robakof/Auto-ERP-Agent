@echo off
:: KSeF Service — do uruchamiania przez Task Scheduler
:: Nie zamyka sie — trzyma proces daemon + raport

cd /d "C:\Users\arkadiusz\Desktop\Auto-ERP-Agent"
C:\Windows\py.exe tools\ksef_start.py
