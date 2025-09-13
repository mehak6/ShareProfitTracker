"""
Simple and fast price refresh - bypasses complexity for maximum speed
"""

import requests
import concurrent.futures
import time
from typing import List, Dict, Optional

class SimpleFastRefresh:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Simple and fast settings
        self.timeout = 5  # Very aggressive timeout
        self.max_workers = 15  # More concurrent requests
        
    def get_price_yfinance_fast(self, symbol: str) -> Optional[float]:
        """Get price using yfinance with maximum speed optimizations"""
        try:
            import yfinance as yf
            
            # Ensure proper symbol format
            if not symbol.endswith('.NS') and not any(symbol.endswith(suffix) for suffix in ['.BO', '.US']):
                symbol = f"{symbol}.NS"
            
            # Use the fastest yfinance method
            ticker = yf.Ticker(symbol)
            
            try:
                # Try fast_info first (much faster than info)
                fast_info = ticker.fast_info
                price = fast_info.get('lastPrice')
                if price and price > 0:
                    return float(price)
            except:
                pass
            
            # Fallback to regular info
            try:
                info = ticker.info
                price = info.get('regularMarketPrice') or info.get('currentPrice')
                if price and price > 0:
                    return float(price)
            except:
                pass
            
        except Exception:
            pass
        
        return None
    
    def get_price_nsepython_fast(self, symbol: str) -> Optional[float]:
        """Get price using NSEPython with maximum speed"""
        try:
            from nsepython import nse_eq
            
            # Clean symbol for NSEPython
            clean_symbol = symbol.replace('.NS', '').upper()
            
            data = nse_eq(clean_symbol)
            
            if data and isinstance(data, dict):
                # Quick price extraction
                for key in ['lastPrice', 'price', 'ltp', 'close']:
                    if key in data and data[key]:
                        return float(data[key])
        except Exception:
            pass
        
        return None
    
    def get_single_price_fast(self, symbol: str) -> Optional[float]:
        """Get single price with maximum speed - tries NSE first, then yfinance"""
        
        # For Indian stocks, try NSEPython first (fastest)
        if symbol.endswith('.NS') or not any(symbol.endswith(suffix) for suffix in ['.BO', '.US']):
            price = self.get_price_nsepython_fast(symbol)
            if price:
                return price
        
        # Fallback to yfinance
        price = self.get_price_yfinance_fast(symbol)
        if price:
            return price
        
        return None
    
    def refresh_multiple_prices_ultra_fast(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Ultra-fast concurrent price refresh - maximum speed"""
        if not symbols:
            return {}
        
        results = {}
        
        def fetch_price_fast(symbol):
            """Single price fetch with timeout protection"""
            try:
                price = self.get_single_price_fast(symbol)
                return symbol, price
            except Exception:
                return symbol, None
        
        # Use maximum concurrency for speed
        max_workers = min(len(symbols), self.max_workers)
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all requests simultaneously
                future_to_symbol = {
                    executor.submit(fetch_price_fast, symbol): symbol 
                    for symbol in symbols
                }
                
                # Collect results with aggressive timeout
                for future in concurrent.futures.as_completed(future_to_symbol, timeout=self.timeout):
                    try:
                        symbol, price = future.result()
                        results[symbol] = price
                    except Exception:
                        continue
        
        except concurrent.futures.TimeoutError:
            print(f"Some requests timed out after {self.timeout}s")
        except Exception as e:
            print(f"Fast refresh error: {e}")
        
        return results

# Global instance for immediate use
simple_fast_refresh = SimpleFastRefresh()

def get_prices_blazing_fast(symbols: List[str]) -> Dict[str, Optional[float]]:
    """Blazing fast price fetch - use this for maximum speed"""
    return simple_fast_refresh.refresh_multiple_prices_ultra_fast(symbols)