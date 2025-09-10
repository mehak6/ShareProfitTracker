try:
    import yfinance as yf
    MOCK_MODE = False
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import mock_yfinance as yf
    MOCK_MODE = True
    print("Warning: Using mock data - install yfinance for real market data")

import requests
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import time

class PriceFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Minimum 100ms between requests
    
    def _rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        try:
            self._rate_limit()
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try different price fields in order of preference
            price_fields = ['currentPrice', 'regularMarketPrice', 'previousClose', 'ask', 'bid']
            
            for field in price_fields:
                if field in info and info[field] is not None:
                    return float(info[field])
            
            return None
            
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        prices = {}
        
        try:
            # Try to get all prices in one request
            symbols_str = " ".join(symbols)
            tickers = yf.Tickers(symbols_str)
            
            for symbol in symbols:
                try:
                    ticker = tickers.tickers[symbol]
                    info = ticker.info
                    
                    price_fields = ['currentPrice', 'regularMarketPrice', 'previousClose', 'ask', 'bid']
                    price = None
                    
                    for field in price_fields:
                        if field in info and info[field] is not None:
                            price = float(info[field])
                            break
                    
                    prices[symbol] = price
                    
                except Exception as e:
                    print(f"Error fetching price for {symbol}: {e}")
                    prices[symbol] = None
                    
        except Exception as e:
            print(f"Error in batch fetch, falling back to individual requests: {e}")
            # Fall back to individual requests
            for symbol in symbols:
                prices[symbol] = self.get_current_price(symbol)
                time.sleep(0.1)  # Small delay between requests
        
        return prices
    
    def get_company_name(self, symbol: str) -> Optional[str]:
        try:
            self._rate_limit()
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try different name fields
            name_fields = ['longName', 'shortName', 'displayName']
            
            for field in name_fields:
                if field in info and info[field]:
                    return str(info[field])
            
            return symbol  # Fallback to symbol if no name found
            
        except Exception as e:
            print(f"Error fetching company name for {symbol}: {e}")
            return symbol
    
    def is_market_open(self) -> bool:
        try:
            # Simple check using SPY (S&P 500 ETF) as proxy
            ticker = yf.Ticker("SPY")
            hist = ticker.history(period="1d", interval="1m")
            
            if hist.empty:
                return False
                
            # If we have data from the last 15 minutes, market is likely open
            latest_time = hist.index[-1]
            now = datetime.now(latest_time.tz)
            time_diff = now - latest_time
            
            return time_diff.total_seconds() < 900  # 15 minutes
            
        except Exception:
            # Default to assuming market is open during weekday business hours
            now = datetime.now()
            if now.weekday() >= 5:  # Weekend
                return False
            
            # Rough US market hours (9:30 AM - 4:00 PM ET)
            market_open = now.replace(hour=9, minute=30)
            market_close = now.replace(hour=16, minute=0)
            
            return market_open <= now <= market_close
    
    def validate_symbol(self, symbol: str) -> bool:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return 'symbol' in info or 'shortName' in info
        except Exception:
            return False