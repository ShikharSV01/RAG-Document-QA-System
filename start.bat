@echo off
title RAG Project - Running
cd /d "%~dp0"

if not exist venv\Scripts\streamlit.exe (
    echo.
    echo [ERROR] Setup hasn't been run yet ^(or it failed^).
    echo Please double-click setup.bat first, then try start.bat again.
    echo.
    pause
    exit /b 1
)

if not exist .env (
    echo.
    echo [WARNING] No .env file found with your Gemini API key.
    echo You can still enter the key in the app's sidebar once it opens,
    echo or run setup.bat again to save it permanently.
    echo.
)

echo ============================================================
echo   Starting the RAG Document Q^&A app...
echo   Your browser should open automatically at:
echo   http://localhost:8501
echo.
echo   Close this window (or press Ctrl+C) to stop the app.
echo ============================================================
echo.

venv\Scripts\streamlit.exe run app.py

pause
