@echo off
cd /d "%~dp0"

echo ========================================
echo E2EE CHAT - TEST SUITE
echo ========================================
echo.

python -m tests

echo.
echo ========================================
echo TEST SUITE FINISHED
echo ========================================
pause