@echo off
REM Kompilacja XlProxy dla Comarch XL 2023.1 (x86, .NET Framework 4.x)
cd /d "%~dp0"

set CSC=C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe
set OUT=XlProxy.exe

echo Kompilacja %OUT% (x86, .NET 4.x)...
%CSC% /nologo /platform:x86 /optimize /out:%OUT% XlProxy.cs

if %ERRORLEVEL% EQU 0 (
    echo OK: %OUT% gotowy.
) else (
    echo BLAD: kompilacja nie powiodla sie.
    exit /b 1
)
