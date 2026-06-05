@echo off
setlocal
cd /d "%~dp0"

echo Restoring database SECD from secd.sql ...
echo You will be prompted for MySQL password.
echo.

mysql -u root -p --default-character-set=utf8mb4 < secd.sql

echo.
echo Done.
pause
