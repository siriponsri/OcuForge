@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\02_phase2_local_data_windows.ps1" %*
set "exit_code=%ERRORLEVEL%"
endlocal & exit /b %exit_code%
