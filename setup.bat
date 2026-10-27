@echo off
setlocal enabledelayedexpansion
title RAG Project - Setup
cd /d "%~dp0"

echo ============================================================
echo   AI-Powered Document Q^&A (RAG) - Setup
echo ============================================================
echo.

REM ------------------------------------------------------------------
REM Step 1: Find a compatible Python (3.10 - 3.12). Very new Python
REM versions (3.13+) often lack ready-made installers for packages
REM like numpy/faiss-cpu, which breaks the install.
REM ------------------------------------------------------------------
set PYCMD=

where py >nul 2>nul
if %errorlevel%==0 (
    for %%V in (3.11 3.12 3.10) do (
        if "!PYCMD!"=="" (
            py -%%V --version >nul 2>nul
            if !errorlevel!==0 (
                set PYCMD=py -%%V
                echo Found Python %%V via the 'py' launcher.
            )
        )
    )
)

if "!PYCMD!"=="" (
    where python >nul 2>nul
    if !errorlevel!==0 (
        set PYCMD=python
        echo Using default 'python' on PATH.
        echo NOTE: if setup fails below, install Python 3.11 from
        echo https://www.python.org/downloads/release/python-3119/
        echo ^(check "Add python.exe to PATH" during install^), then re-run this script.
    )
)

if "!PYCMD!"=="" (
    echo.
    echo [ERROR] No Python installation found on this machine.
    echo Please install Python 3.11 from:
    echo   https://www.python.org/downloads/release/python-3119/
    echo IMPORTANT: check "Add python.exe to PATH" during install.
    echo Then close this window, open a new one, and re-run setup.bat
    echo.
    pause
    exit /b 1
)

echo.
echo ------------------------------------------------------------
echo Creating virtual environment in .\venv ...
echo ------------------------------------------------------------
if exist venv (
    echo Virtual environment already exists, skipping creation.
) else (
    %PYCMD% -m venv venv
    if not exist venv\Scripts\python.exe (
        echo.
        echo [ERROR] Failed to create the virtual environment.
        pause
        exit /b 1
    )
)

echo.
echo ------------------------------------------------------------
echo Installing dependencies ^(this can take a few minutes^)...
echo ------------------------------------------------------------
call venv\Scripts\python.exe -m pip install --upgrade pip >nul
call venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Dependency installation failed. Scroll up to see which
    echo package failed. Common fix: make sure you're using Python
    echo 3.10-3.12 ^(delete the venv folder and re-run setup.bat after
    echo installing a compatible Python version^).
    echo.
    pause
    exit /b 1
)

echo.
echo ------------------------------------------------------------
echo Gemini API key setup
echo ------------------------------------------------------------
if exist .env (
    echo A .env file already exists - keeping your existing API key.
) else (
    echo You need a free Gemini API key from:
    echo   https://aistudio.google.com/apikey
    echo.
    set /p GEMINI_KEY="Paste your Gemini API key here and press Enter: "
    echo GOOGLE_API_KEY=!GEMINI_KEY!> .env
    echo Saved to .env
)

echo.
echo ============================================================
echo   Setup complete! Double-click start.bat to run the app.
echo ============================================================
echo.
pause
