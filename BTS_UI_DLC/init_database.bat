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
echo Initialize MySQL database for this project.
echo If root has a password, type it when prompted. Otherwise press Enter.
echo.
".venv\Scripts\python.exe" setup_database.py
pause
