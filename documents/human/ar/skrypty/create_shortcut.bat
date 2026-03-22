@echo off
powershell -Command "$s=$Env:USERPROFILE+'\Desktop\Etykiety.lnk'; $ws=New-Object -COM WScript.Shell; $sc=$ws.CreateShortcut($s); $sc.TargetPath='%~dp0etykiety.bat'; $sc.WorkingDirectory='%~dp0'; $sc.Save()"
echo Skrot utworzony na Pulpicie.
pause
