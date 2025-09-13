@echo off
echo Building ShareProfitTracker Optimized Executable...
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo No virtual environment found, using global Python...
)

REM Install/upgrade required packages
echo Installing required packages...
pip install --upgrade pyinstaller
pip install --upgrade yfinance
pip install --upgrade nsepython
pip install --upgrade requests
REM concurrent.futures is built-in to Python 3.2+

REM Clean previous builds
echo Cleaning previous builds...
if exist "dist\ShareProfitTracker_Optimized" rmdir /s /q "dist\ShareProfitTracker_Optimized"
if exist "build\ShareProfitTracker_Optimized" rmdir /s /q "build\ShareProfitTracker_Optimized"

REM Build the optimized executable
echo.
echo Building optimized executable with performance enhancements...
pyinstaller --clean ShareProfitTracker_Optimized.spec

REM Check if build was successful
if exist "dist\ShareProfitTracker_Optimized\ShareProfitTracker_Optimized.exe" (
    echo.
    echo ============================================
    echo BUILD SUCCESSFUL!
    echo ============================================
    echo Executable location: dist\ShareProfitTracker_Optimized\
    echo Performance optimizations included:
    echo   - Concurrent price fetching
    echo   - Async stock addition
    echo   - Optimized UI updates
    echo   - Reduced startup time
    echo ============================================
) else (
    echo.
    echo ============================================
    echo BUILD FAILED!
    echo ============================================
    echo Please check the error messages above.
)

echo.
pause