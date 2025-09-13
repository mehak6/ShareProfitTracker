# Installation Guide - Share Profit Tracker

## System Requirements

### Windows Installation (Recommended)
- **Operating System**: Windows 7, 8, 10, or 11
- **Python**: 3.9 or higher (includes tkinter GUI library)
- **RAM**: 2GB minimum
- **Storage**: 100MB free space
- **Internet**: Required for stock price updates

### Linux/WSL Installation
- **Python**: 3.9+ with tkinter support
- **Additional packages**: python3-tk, python3-pip

## Installation Methods

### Method 1: Windows with Python (Recommended)

1. **Install Python 3.9+** from https://python.org
   - ✅ Make sure to check "Add Python to PATH"
   - ✅ Python installer includes tkinter automatically

2. **Download the application** to your desired folder

3. **Install dependencies**:
   ```cmd
   pip install yfinance
   ```

4. **Run the application**:
   ```cmd
   python main.py
   ```

### Method 2: Build Windows Executable

1. **Follow Method 1** to install Python and dependencies

2. **Install PyInstaller**:
   ```cmd
   pip install pyinstaller
   ```

3. **Build executable**:
   ```cmd
   pyinstaller --onefile --windowed --name="ShareProfitTracker" main.py
   ```

4. **Find executable** in the `dist` folder - no Python installation needed on target machine

### Method 3: Linux/Ubuntu Installation

1. **Install required packages**:
   ```bash
   sudo apt update
   sudo apt install python3-full python3-tk python3-pip
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install yfinance
   ```

4. **Run application**:
   ```bash
   python main.py
   ```

## Troubleshooting

### "No module named 'tkinter'"
- **Windows**: Reinstall Python with tkinter support
- **Linux**: Install `python3-tk` package
- **WSL**: Use console demo version instead

### "No module named 'yfinance'"
- Run: `pip install yfinance`
- For Linux: Use `pip3` instead of `pip`

### "Permission denied" or pip not found
- **Windows**: Reinstall Python with "Add to PATH" checked
- **Linux**: Install `python3-pip` package
- Use: `python -m pip install yfinance` instead

### Stock prices not updating
- Check internet connection
- Verify stock symbols are correct (e.g., AAPL, GOOGL)
- Some international stocks may not be available

### Database errors
- Ensure write permissions in application folder
- Delete `portfolio.db` to reset database

## Demo Mode (No Internet Required)

If yfinance cannot be installed, the application will use mock data:

```bash
python3 demo_console.py  # Console demo with fake stock prices
```

This demonstrates all features with sample data.

## Quick Start Commands

### Windows:
```cmd
pip install yfinance
python main.py
```

### Linux:
```bash
sudo apt install python3-tk python3-pip
pip3 install yfinance
python3 main.py
```

### Demo (Any platform):
```bash
python3 demo_console.py
```

## File Structure After Installation
```
ShareProfitTracker/
├── main.py              # Start here
├── demo_console.py      # Console demo
├── portfolio.db         # Your data (created automatically)
├── requirements.txt     # Dependencies list
├── README.md           # Full documentation
└── [folders with source code]
```

## Next Steps
1. ✅ Verify installation with demo
2. ✅ Run main application
3. ✅ Add your first stock
4. ✅ Try the refresh prices feature
5. ✅ Export your portfolio data