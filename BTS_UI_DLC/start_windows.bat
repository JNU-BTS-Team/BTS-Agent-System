@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 python -m venv .venv
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 pause && exit /b 1

echo.
echo Website starting at http://127.0.0.1:5000/login
echo Press Ctrl+C to stop.
echo.
".venv\Scripts\python.exe" app.py
pause
