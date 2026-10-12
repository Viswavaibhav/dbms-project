@echo off
setlocal enabledelayedexpansion
title Grand Azure Hotel DBMS Management System
color 0b

echo ======================================================================
echo    GRAND AZURE LUXURY HOTEL DBMS MANAGEMENT APPLICATION
echo ======================================================================
echo.

:: Detect Python or Windows Py Launcher
set PYTHON_CMD=
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON_CMD=python
) else (
    py --version >nul 2>&1
    if !errorlevel! equ 0 (
        set PYTHON_CMD=py
    )
)

if "!PYTHON_CMD!"=="" (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python 3.9+ from https://www.python.org/
    echo (Make sure to check "Add Python to PATH" during installation)
    echo.
    pause
    exit /b
)

echo [1/3] Using Python: !PYTHON_CMD!
!PYTHON_CMD! --version

echo.
echo [2/3] Checking / Installing Python Dependencies...
!PYTHON_CMD! -m pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [NOTE] Trying pip install with --user flag...
    !PYTHON_CMD! -m pip install -r requirements.txt --user
)

!PYTHON_CMD! -c "import flask" >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Flask is not installed properly.
    echo Please run: !PYTHON_CMD! -m pip install Flask PyMySQL python-dotenv
    echo.
    pause
    exit /b
)

echo.
echo [3/3] Starting Web Application on http://127.0.0.1:5000 ...
echo Opening your browser in 2 seconds...
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"

!PYTHON_CMD! app.py

echo.
echo Server stopped.
pause
