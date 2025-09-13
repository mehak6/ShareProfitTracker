"""
Mock yfinance module for demonstration purposes when the real yfinance is not available.
This provides fake stock data for testing the application.
"""

import random
import time
from typing import Dict, Any

class MockTicker:
    def __init__(self, symbol: str):
        self.symbol = symbol
        # Mock stock data (prices in INR for Indian stocks, converted for US stocks)
        self._mock_data = {
            # Indian stocks (NSE)
            'RELIANCE.NS': {'currentPrice': 2450.75, 'longName': 'Reliance Industries Limited'},
            'TCS.NS': {'currentPrice': 3580.40, 'longName': 'Tata Consultancy Services Limited'},
            'HDFCBANK.NS': {'currentPrice': 1620.30, 'longName': 'HDFC Bank Limited'},
            'INFY.NS': {'currentPrice': 1450.60, 'longName': 'Infosys Limited'},
            'HINDUNILVR.NS': {'currentPrice': 2380.90, 'longName': 'Hindustan Unilever Limited'},
            'ICICIBANK.NS': {'currentPrice': 950.25, 'longName': 'ICICI Bank Limited'},
            'SBIN.NS': {'currentPrice': 575.80, 'longName': 'State Bank of India'},
            'BHARTIARTL.NS': {'currentPrice': 865.40, 'longName': 'Bharti Airtel Limited'},
            'ITC.NS': {'currentPrice': 410.75, 'longName': 'ITC Limited'},
            'ASIANPAINT.NS': {'currentPrice': 2980.60, 'longName': 'Asian Paints Limited'},
            'MARUTI.NS': {'currentPrice': 9850.30, 'longName': 'Maruti Suzuki India Limited'},
            'WIPRO.NS': {'currentPrice': 420.45, 'longName': 'Wipro Limited'},
            
            # US stocks (converted to INR - approximately $1 = ₹83)
            'AAPL': {'currentPrice': 12470.75, 'longName': 'Apple Inc.'},
            'GOOGL': {'currentPrice': 228416.40, 'longName': 'Alphabet Inc.'},
            'MSFT': {'currentPrice': 27447.35, 'longName': 'Microsoft Corporation'},
            'TSLA': {'currentPrice': 70599.80, 'longName': 'Tesla, Inc.'},
            'AMZN': {'currentPrice': 265674.70, 'longName': 'Amazon.com Inc.'},
            'NVDA': {'currentPrice': 18322.25, 'longName': 'NVIDIA Corporation'},
            'META': {'currentPrice': 40279.90, 'longName': 'Meta Platforms Inc.'},
            'NFLX': {'currentPrice': 31560.75, 'longName': 'Netflix Inc.'},
        }
    
    @property
    def info(self) -> Dict[str, Any]:
        # Add some random variation to prices (+/- 5%)
        base_data = self._mock_data.get(self.symbol, {
            'currentPrice': 1000.00,  # Default INR price
            'longName': f'{self.symbol} Corp.'
        })
        
        # Add random variation
        base_price = base_data['currentPrice']
        variation = random.uniform(-0.05, 0.05)  # +/- 5%
        current_price = base_price * (1 + variation)
        
        return {
            'symbol': self.symbol,
            'currentPrice': round(current_price, 2),
            'longName': base_data['longName'],
            'regularMarketPrice': round(current_price, 2),
            'previousClose': round(current_price * 0.99, 2),
        }
    
    def history(self, period="1d", interval="1m"):
        # Mock empty history for market open check
        from datetime import datetime, timedelta
        
        class MockDataFrame:
            def __init__(self):
                self.empty = False
                now = datetime.now()
                self.index = [now - timedelta(minutes=i) for i in range(5, 0, -1)]
            
            def __bool__(self):
                return not self.empty
        
        return MockDataFrame()

class MockTickers:
    def __init__(self, symbols_str: str):
        self.symbols = symbols_str.split()
        self.tickers = {symbol: MockTicker(symbol) for symbol in self.symbols}

def Ticker(symbol: str) -> MockTicker:
    return MockTicker(symbol)

def Tickers(symbols_str: str) -> MockTickers:
    return MockTickers(symbols_str)

print("Using mock yfinance module - fake data for demonstration only!")