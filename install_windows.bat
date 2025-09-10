@echo off
echo 🔧 Share Profit Tracker - Windows Setup
echo ====================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo 📥 Please install Python from: https://python.org
    echo ✅ Make sure to check "Add Python to PATH"
    echo ✅ Make sure to check "tcl/tk and IDLE"
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Check if tkinter is available
echo 🧪 Testing tkinter...
python -c "import tkinter; print('✅ tkinter is available')" 2>nul
if errorlevel 1 (
    echo ❌ tkinter not found!
    echo 📥 Please reinstall Python with tkinter support
    echo 💡 Download from: https://python.org
    echo ✅ During installation, check "tcl/tk and IDLE"
    pause
    exit /b 1
)

REM Install yfinance
echo 📦 Installing yfinance...
pip install yfinance
if errorlevel 1 (
    echo ❌ Failed to install yfinance
    echo 💡 Try: python -m pip install yfinance
    pause
    exit /b 1
)

echo ✅ yfinance installed successfully

REM Test the application
echo 🧪 Testing application...
python -c "
import sys
import os
sys.path.insert(0, '.')
try:
    from gui.main_window import MainWindow
    print('✅ Application imports working')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

if errorlevel 1 (
    echo ❌ Application test failed
    pause
    exit /b 1
)

echo ✅ All tests passed!
echo 🚀 You can now run: python main.py
echo.
echo 🎯 Quick Start:
echo   1. Double-click main.py OR
echo   2. Run: python main.py
echo   3. Click "Add Stock" to start
echo.
pause