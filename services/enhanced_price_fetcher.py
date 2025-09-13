"""
Enhanced price fetcher with NSEPython primary and yfinance fallback
Provides better performance and more comprehensive coverage for Indian stocks
"""

import time
from typing import Dict, Any, Optional
import logging

class EnhancedPriceFetcher:
    def __init__(self):
        self.nse_available = True
        self.yfinance_available = True
        self._test_availability()
    
    def _test_availability(self):
        """Test which libraries are available"""
        try:
            from nsepython import nse_eq
            self.nse_available = True
        except ImportError:
            self.nse_available = False
            print("NSEPython not available, will use yfinance only")
        
        try:
            import yfinance
            self.yfinance_available = True
        except ImportError:
            self.yfinance_available = False
            print("yfinance not available")
    
    def _fetch_from_nsepython(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch price data from NSEPython (fastest for NSE stocks)"""
        if not self.nse_available:
            return None
        
        try:
            from nsepython import nse_eq
            
            # NSEPython expects symbol without .NS suffix
            clean_symbol = symbol.replace('.NS', '').upper()
            
            data = nse_eq(clean_symbol)
            
            if data and isinstance(data, dict):
                # Extract relevant price information
                current_price = None
                previous_close = None
                
                # Try different possible keys for price data
                price_keys = ['lastPrice', 'price', 'ltp', 'close', 'currentPrice']
                for key in price_keys:
                    if key in data:
                        current_price = float(data[key])
                        break
                
                # Try to get previous close
                prev_keys = ['previousClose', 'prevClose', 'pClose']
                for key in prev_keys:
                    if key in data:
                        previous_close = float(data[key])
                        break
                
                if current_price is not None:
                    result = {
                        'symbol': symbol,
                        'current_price': current_price,
                        'previous_close': previous_close,
                        'source': 'nsepython',
                        'raw_data': data
                    }
                    
                    # Add change calculation if both prices available
                    if previous_close:
                        change = current_price - previous_close
                        change_percent = (change / previous_close) * 100
                        result['change'] = change
                        result['change_percent'] = change_percent
                    
                    return result
            
        except Exception as e:
            logging.debug(f"NSEPython fetch failed for {symbol}: {e}")
        
        return None
    
    def _fetch_from_yfinance(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch price data from yfinance (fallback)"""
        if not self.yfinance_available:
            return None
        
        try:
            import yfinance as yf
            
            # Ensure NSE stocks have .NS suffix for yfinance
            yf_symbol = symbol
            if not symbol.endswith('.NS') and not any(symbol.endswith(suffix) for suffix in ['.BO', '.US']):
                # Assume NSE stock if no suffix
                yf_symbol = f"{symbol}.NS"
            
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            if info and 'regularMarketPrice' in info:
                current_price = float(info['regularMarketPrice'])
                previous_close = info.get('regularMarketPreviousClose')
                
                if previous_close:
                    previous_close = float(previous_close)
                
                result = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'previous_close': previous_close,
                    'source': 'yfinance',
                    'raw_data': info
                }
                
                # Add change calculation if both prices available
                if previous_close:
                    change = current_price - previous_close
                    change_percent = (change / previous_close) * 100
                    result['change'] = change
                    result['change_percent'] = change_percent
                
                return result
                
        except Exception as e:
            logging.debug(f"yfinance fetch failed for {symbol}: {e}")
        
        return None
    
    def _try_mock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fallback to mock data if all sources fail"""
        try:
            import sys
            import os
            
            # Add the parent directory to sys.path if not already present
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.append(parent_dir)
            
            from mock_yfinance import MockYFinance
            
            mock_yf = MockYFinance()
            ticker = mock_yf.Ticker(symbol)
            info = ticker.info
            
            if info and 'regularMarketPrice' in info:
                current_price = float(info['regularMarketPrice'])
                previous_close = info.get('regularMarketPreviousClose')
                
                if previous_close:
                    previous_close = float(previous_close)
                
                result = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'previous_close': previous_close,
                    'source': 'mock',
                    'raw_data': info
                }
                
                # Add change calculation if both prices available
                if previous_close:
                    change = current_price - previous_close
                    change_percent = (change / previous_close) * 100
                    result['change'] = change
                    result['change_percent'] = change_percent
                
                return result
                
        except Exception as e:
            logging.debug(f"Mock data fetch failed for {symbol}: {e}")
        
        return None
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current price with intelligent source selection
        Priority: NSEPython -> yfinance -> mock data
        """
        
        # Clean the symbol
        symbol = symbol.strip().upper()
        
        # For NSE stocks, try NSEPython first (fastest and most accurate)
        if symbol.endswith('.NS') or not any(symbol.endswith(suffix) for suffix in ['.BO', '.US']):
            data = self._fetch_from_nsepython(symbol)
            if data:
                return data
        
        # Fallback to yfinance (works for all markets)
        data = self._fetch_from_yfinance(symbol)
        if data:
            return data
        
        # Last resort: mock data
        data = self._try_mock_data(symbol)
        if data:
            return data
        
        # No data available
        return None
    
    def get_multiple_prices(self, symbols: list) -> Dict[str, Dict[str, Any]]:
        """Get prices for multiple symbols with optimized batch processing"""
        results = {}
        
        if not symbols:
            return results
        
        # Try batch processing first for better performance
        if len(symbols) > 1:
            batch_results = self._batch_fetch_prices(symbols)
            if batch_results:
                return batch_results
        
        # Fallback to individual requests with reduced delay
        for i, symbol in enumerate(symbols):
            if i > 0:
                time.sleep(0.05)  # Reduced from 100ms to 50ms
            
            try:
                price_data = self.get_current_price(symbol)
                if price_data:
                    results[symbol] = price_data
                else:
                    print(f"Warning: Could not fetch price for {symbol}")
            except Exception as e:
                print(f"Error fetching price for {symbol}: {e}")
                continue
        
        return results
    
    def _batch_fetch_prices(self, symbols: list) -> Dict[str, Dict[str, Any]]:
        """Optimized batch price fetching with concurrent requests"""
        import concurrent.futures
        import threading
        
        results = {}
        max_workers = min(len(symbols), 5)  # Limit concurrent requests
        
        def fetch_single_price(symbol):
            try:
                return symbol, self.get_current_price(symbol)
            except Exception as e:
                print(f"Batch fetch error for {symbol}: {e}")
                return symbol, None
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_symbol = {executor.submit(fetch_single_price, symbol): symbol for symbol in symbols}
                
                for future in concurrent.futures.as_completed(future_to_symbol, timeout=30):
                    symbol, price_data = future.result()
                    if price_data:
                        results[symbol] = price_data
                    
                    # Small delay between processing results
                    time.sleep(0.01)
        
        except concurrent.futures.TimeoutError:
            print("Batch fetch timeout, some prices may be missing")
        except Exception as e:
            print(f"Batch fetch failed: {e}")
            return {}  # Return empty to trigger fallback
        
        return results
    
    def test_connectivity(self) -> Dict[str, bool]:
        """Test connectivity to all data sources"""
        results = {
            'nsepython': False,
            'yfinance': False,
            'mock': False
        }
        
        # Test NSEPython
        test_data = self._fetch_from_nsepython('RELIANCE')
        results['nsepython'] = test_data is not None
        
        # Test yfinance
        test_data = self._fetch_from_yfinance('RELIANCE.NS')
        results['yfinance'] = test_data is not None
        
        # Test mock
        test_data = self._try_mock_data('RELIANCE')
        results['mock'] = test_data is not None
        
        return results

# Create global instance
enhanced_price_fetcher = EnhancedPriceFetcher()

# Convenience functions for backward compatibility
def get_current_price(symbol: str) -> Optional[float]:
    """Get current price as float (backward compatibility)"""
    data = enhanced_price_fetcher.get_current_price(symbol)
    if data:
        return data.get('current_price')
    return None

def get_detailed_price_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Get detailed price data with metadata"""
    return enhanced_price_fetcher.get_current_price(symbol)

def get_multiple_prices(symbols: list) -> Dict[str, float]:
    """Get multiple prices as symbol->price mapping (backward compatibility)"""
    detailed_results = enhanced_price_fetcher.get_multiple_prices(symbols)
    simple_results = {}
    
    for symbol, data in detailed_results.items():
        if 'current_price' in data:
            simple_results[symbol] = data['current_price']
    
    return simple_results