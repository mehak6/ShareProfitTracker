@echo off
echo Building Share Profit Tracker executable...

REM Install requirements
pip install -r requirements.txt
pip install pyinstaller

REM Build executable
pyinstaller --onefile --windowed --name="ShareProfitTracker" --icon=app.ico main.py

echo.
echo Build complete! Executable is in the 'dist' folder.
echo.
pause