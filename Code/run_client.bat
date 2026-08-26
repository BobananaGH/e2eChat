@echo off
cd /d "%~dp0"

echo ========================================
echo E2EE CHAT CLIENT
echo ========================================
echo.

python -m client

echo.
echo Client stopped.
pause