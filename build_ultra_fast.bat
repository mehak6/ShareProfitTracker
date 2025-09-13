@echo off
echo Building ShareProfitTracker Ultra-Fast Executable...
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

REM Clean previous builds
echo Cleaning previous builds...
if exist "dist\ShareProfitTracker_UltraFast.exe" del /f /q "dist\ShareProfitTracker_UltraFast.exe"
if exist "build\ShareProfitTracker_UltraFast" rmdir /s /q "build\ShareProfitTracker_UltraFast"

REM Build the ultra-fast executable
echo.
echo Building ultra-fast executable with advanced optimizations...
pyinstaller --clean ShareProfitTracker_UltraFast.spec

REM Check if build was successful
if exist "dist\ShareProfitTracker_UltraFast.exe" (
    echo.
    echo ============================================
    echo BUILD SUCCESSFUL!
    echo ============================================
    echo Executable: dist\ShareProfitTracker_UltraFast.exe
    echo.
    echo ULTRA-FAST OPTIMIZATIONS:
    echo   * 3-10x faster price refreshes
    echo   * Smart caching (60s TTL)
    echo   * 10 concurrent API requests
    echo   * Connection pooling
    echo   * 8s timeout protection
    echo   * Optimized UI with progress dialog
    echo   * Cache hit rate tracking
    echo   * Automatic cache management
    echo ============================================
    echo.
    echo To use: Just click "Refresh Prices" button
    echo The new dialog shows cache stats and performance!
) else (
    echo.
    echo ============================================
    echo BUILD FAILED!
    echo ============================================
    echo Please check the error messages above.
)

echo.
pause