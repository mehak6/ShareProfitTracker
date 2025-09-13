# 📈 Share Profit Tracker

A comprehensive desktop application for tracking your stock portfolio, managing cash, and generating tax reports. Built with Python and Tkinter.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

## ✨ Features

### 📊 **Portfolio Management**
- **Stock Tracking**: Add, edit, and delete stocks with detailed information
- **Real-time Data**: Fetch current stock prices (mock data included for testing)
- **Profit/Loss Analysis**: Track gains/losses with percentage calculations
- **Investment Tracking**: Monitor actual cash invested vs calculated investment

### 🔍 **Advanced Analytics**
- **Smart Search**: Find stocks instantly by symbol or company name
- **Advanced Sorting**: Sort by profit/loss, current value, days held, and more
- **Dark/Light Themes**: Professional UI with theme persistence
- **Portfolio Summary**: Real-time portfolio performance overview

### 💰 **Cash Management**
- **Cash Tracking**: Monitor available cash with deposits and withdrawals
- **Expense Management**: Track monthly expenses by category
- **Budget Integration**: See remaining cash after all expenses
- **Category Analysis**: Detailed breakdown of spending patterns

### 📋 **Tax Reporting**
- **Capital Gains Analysis**: Short-term vs long-term classification
- **Indian Tax Rules**: Built-in STCG (15.6%) and LTCG (10.4%) calculations
- **Tax Planning**: Unrealized gains analysis for tax planning
- **Professional Reports**: Export-ready tax reports for filing

### 📤 **Export & Reports**
- **CSV Export**: Export portfolio, cash transactions, and tax reports
- **Multi-format Support**: Professional formatting for accountants
- **Historical Analysis**: Year-wise tax and performance reports

## Requirements

- Python 3.9+
- Windows 7/8/10/11
- Internet connection for price updates
- 2GB RAM minimum
- 100MB free disk space

## Installation

### Running from Source

1. **Clone or download** the ShareProfitTracker folder
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python main.py
   ```

### Creating Executable (Windows)

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Build executable**:
   ```bash
   pyinstaller --onefile --windowed --name="ShareProfitTracker" main.py
   ```

3. The executable will be created in the `dist` folder

## 🎯 Usage Guide

### Adding Stocks
1. Click **"Add Stock"** button
2. Use the smart autocomplete to search for stocks
3. Enter quantity, purchase price, and date
4. Optionally add broker information and cash invested
5. Click **"Save"** to add to your portfolio

### Cash Management
1. Click **"Cash I Have"** to manage your available cash
2. Add deposits (money added) or withdrawals (money taken out)
3. View your current cash balance
4. Track transaction history with descriptions

### Expense Tracking
1. Click **"Other Funds"** to track expenses
2. Add expenses by category (electricity, rent, food, etc.)
3. View monthly expense breakdown
4. See remaining cash after all expenses

### Tax Planning
1. Click **"Tax Report"** for comprehensive tax analysis
2. View current holdings with gain/loss classification
3. See potential tax liability if sold today
4. Export tax reports for your accountant

### Search & Filter
- Use the **search bar** to quickly find specific stocks
- **Sort by** profit/loss, current value, or days held
- Toggle **ascending/descending** order
- **Clear** search to show all stocks

### Theme Customization
- Click **"Dark Mode"** or **"Light Mode"** to switch themes
- Theme preference is automatically saved
- Professional color schemes for both modes

## File Structure

```
ShareProfitTracker/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── portfolio.db           # SQLite database (created automatically)
├── gui/
│   ├── main_window.py     # Main application window
│   └── add_stock_dialog.py # Add/edit stock dialog
├── data/
│   ├── database.py        # Database operations
│   └── models.py          # Data models
├── services/
│   ├── price_fetcher.py   # Yahoo Finance API integration
│   └── calculator.py      # Profit/loss calculations
└── utils/
    ├── config.py          # Application configuration
    └── helpers.py         # Utility functions
```

## Troubleshooting

### Common Issues

1. **"No module named 'yfinance'"**
   - Solution: Install dependencies with `pip install -r requirements.txt`

2. **Price updates failing**
   - Check internet connection
   - Verify stock symbols are correct
   - Some stocks may have limited data availability

3. **Database errors**
   - Ensure write permissions in application folder
   - Delete `portfolio.db` file to reset database

### API Limitations

- Yahoo Finance API has rate limits
- Some international stocks may not be available
- Market data may have delays
- Weekend/holiday updates may not work

## Data Safety

- Portfolio data is stored locally in `portfolio.db`
- Regular backups are recommended
- No data is sent to external servers except for price updates

## Technical Notes

- Built with Python 3.9+ and Tkinter
- Uses SQLite for data storage
- Yahoo Finance API for market data
- Single executable deployment with PyInstaller

## License

This software is provided as-is for personal use. No warranty is provided.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify all requirements are met
3. Ensure stock symbols are valid