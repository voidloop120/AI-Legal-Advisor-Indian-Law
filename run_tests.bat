@echo off
title AI Legal Advisor - Test Suite
cd /d "%~dp0"
echo ========================================================
echo   Running All Automated Unit Tests (Pytest)
echo ========================================================
echo.
".venv\Scripts\python.exe" -m pytest -v
echo.
pause
