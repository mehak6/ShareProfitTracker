@echo off
echo Starting Share Profit Tracker...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.9+ from https://python.org
    echo Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)

REM Check if yfinance is installed
python -c "import yfinance" >nul 2>&1
if errorlevel 1 (
    echo Installing yfinance...
    pip install yfinance
    if errorlevel 1 (
        echo ERROR: Failed to install yfinance
        echo Try running: pip install yfinance
        pause
        exit /b 1
    )
)

REM Start the application
echo Starting application...
python main.py

if errorlevel 1 (
    echo.
    echo Application encountered an error.
    echo Check that you have:
    echo - Python 3.9+ installed
    echo - tkinter support (included with Python on Windows)
    echo - Internet connection for stock prices
    pause
)