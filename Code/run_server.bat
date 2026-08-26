@echo off
cd /d "%~dp0"

echo ========================================
echo E2EE CHAT SERVER
echo ========================================
echo.

python -m server

echo.
echo Server stopped.
pause