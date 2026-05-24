@echo off
echo ============================================
echo   TalkToWord — Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Download it from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/2] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/2] Installing dependencies...
pip install -r requirements.txt

echo.
echo ============================================
echo   Setup complete!
echo.
echo   To run TalkToWord:
echo     1. Double-click  start.bat
echo     — or —
echo     2. Run:  venv\Scripts\activate ^& python run.py
echo ============================================
pause
