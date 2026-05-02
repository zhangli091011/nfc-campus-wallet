@echo off
REM NFC Campus Event System - Quick Start Script (Windows)
REM This script automates the setup process for development

echo ==========================================
echo NFC Campus Event System - Quick Start
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)
echo OK: Python is installed
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo OK: Virtual environment created
) else (
    echo INFO: Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo OK: Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
echo OK: Dependencies installed
echo.

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
    echo WARNING: Please edit .env file with your database credentials
    echo          Then run this script again
    pause
    exit /b 0
) else (
    echo OK: .env file exists
)
echo.

REM Check database connection
echo Checking database connection...
python -c "from core.config import load_settings, get_settings; load_settings(); print('OK: Configuration loaded')"
if errorlevel 1 (
    echo ERROR: Configuration error
    pause
    exit /b 1
)
echo.

REM Run database migration
echo Running database migration...
python scripts\migrate_cash_reconciliation.py
echo OK: Database migration completed
echo.

REM Ask if user wants to create admin
set /p CREATE_ADMIN="Do you want to create an admin user? (y/n): "
if /i "%CREATE_ADMIN%"=="y" (
    python scripts\create_admin.py
)
echo.

REM Ask if user wants to setup demo data
set /p SETUP_DEMO="Do you want to setup demo data? (y/n): "
if /i "%SETUP_DEMO%"=="y" (
    echo.
    echo Setting up demo data...
    python scripts\demo_setup.py
    echo OK: Demo data created
)
echo.

REM Final instructions
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo To start the server, run:
echo    .venv\Scripts\activate.bat
echo    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo.
echo Documentation:
echo    - API Docs: http://localhost:8000/docs
echo    - Health Check: http://localhost:8000/health
echo    - Deployment Guide: DEPLOYMENT_GUIDE.md
echo    - Demo Flow: DEMO_FLOW.md
echo.
echo Happy coding!
echo.
pause
