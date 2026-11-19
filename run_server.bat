@echo off
title AI Legal Advisor - Server
cd /d "%~dp0"
echo ========================================================
echo   AI Legal Advisor for Indian Law - Backend Server
echo ========================================================
echo.
echo Opening server at: http://127.0.0.1:8000
echo Interactive API docs at: http://127.0.0.1:8000/docs
echo Press Ctrl+C in this window anytime to stop the server.
echo.
".venv\Scripts\python.exe" -m uvicorn backend.main:app --reload
pause
