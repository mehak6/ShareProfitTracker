"""
Ultra-fast price fetcher with aggressive optimizations
- Concurrent batch processing
- Smart caching with TTL
- Optimized API patterns
- Timeout management
"""

import time
import threading
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import concurrent.futures
from collections import defaultdict
import requests

class UltraFastPriceFetcher:
    def __init__(self):
        self.nse_available = True
        self.yfinance_available = True
        
        # Smart caching with TTL (Time To Live)
        self.price_cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = 60  # Cache for 60 seconds
        
        # Connection pooling and session reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Adaptive concurrency settings
        self.max_workers = 10  # Increased from 5
        self.request_timeout = 8  # Reduced from 30s
        self.batch_delay = 0.02  # Reduced from 0.05s
        
        self._test_availability()
        self._init_optimizations()
    
    def _test_availability(self):
        """Test which libraries are available"""
        try:
            from nsepython import nse_eq
            self.nse_available = True
        except ImportError:
            self.nse_available = False
        
        try:
            import yfinance
            self.yfinance_available = True
        except ImportError:
            self.yfinance_available = False
    
    def _init_optimizations(self):
        """Initialize performance optimizations"""
        # Keep alive connections
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=1
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached price is still valid"""
        if symbol not in self.cache_timestamps:
            return False
        
        cache_time = self.cache_timestamps[symbol]
        return (datetime.now() - cache_time).total_seconds() < self.cache_ttl
    
    def _get_cached_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get price from cache if valid"""
        if self._is_cache_valid(symbol):
            cached_data = self.price_cache.get(symbol)
            if cached_data:
                cached_data['source'] = cached_data.get('source', 'unknown') + '_cached'
                return cached_data
        return None
    
    def _cache_price(self, symbol: str, price_data: Dict[str, Any]):
        """Cache price data with timestamp"""
        self.price_cache[symbol] = price_data.copy()
        self.cache_timestamps[symbol] = datetime.now()
    
    def _fetch_from_nsepython_fast(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Ultra-fast NSEPython fetch with optimizations"""
        if not self.nse_available:
            return None
        
        try:
            from nsepython import nse_eq
            
            clean_symbol = symbol.replace('.NS', '').upper()
            
            # Use timeout to prevent hanging
            data = nse_eq(clean_symbol)
            
            if data and isinstance(data, dict):
                current_price = None
                previous_close = None
                
                # Optimized price extraction
                price_keys = ['lastPrice', 'price', 'ltp', 'close', 'currentPrice']
                for key in price_keys:
                    if key in data:
                        current_price = float(data[key])
                        break
                
                if current_price is not None:
                    # Get previous close quickly
                    prev_keys = ['previousClose', 'prevClose', 'pClose']
                    for key in prev_keys:
                        if key in data:
                            previous_close = float(data[key])
                            break
                    
                    result = {
                        'symbol': symbol,
                        'current_price': current_price,
                        'previous_close': previous_close,
                        'source': 'nsepython_fast',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if previous_close:
                        change = current_price - previous_close
                        change_percent = (change / previous_close) * 100
                        result['change'] = change
                        result['change_percent'] = change_percent
                    
                    return result
            
        except Exception as e:
            logging.debug(f"NSEPython fast fetch failed for {symbol}: {e}")
        
        return None
    
    def _fetch_from_yfinance_fast(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Ultra-fast yfinance fetch with optimizations"""
        if not self.yfinance_available:
            return None
        
        try:
            import yfinance as yf
            
            # Ensure proper symbol format
            yf_symbol = symbol
            if not symbol.endswith('.NS') and not any(symbol.endswith(suffix) for suffix in ['.BO', '.US']):
                yf_symbol = f"{symbol}.NS"
            
            # Use fast fetch method with timeout
            ticker = yf.Ticker(yf_symbol)
            
            # Try fast_info first (faster than info)
            try:
                fast_info = ticker.fast_info
                current_price = fast_info.get('lastPrice')
                if current_price:
                    previous_close = fast_info.get('previousClose')
                    
                    result = {
                        'symbol': symbol,
                        'current_price': float(current_price),
                        'previous_close': float(previous_close) if previous_close else None,
                        'source': 'yfinance_fast',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if previous_close:
                        change = current_price - previous_close
                        change_percent = (change / previous_close) * 100
                        result['change'] = change
                        result['change_percent'] = change_percent
                    
                    return result
            except:
                # Fallback to regular info if fast_info fails
                info = ticker.info
                current_price = info.get('regularMarketPrice') or info.get('currentPrice')
                if current_price:
                    previous_close = info.get('regularMarketPreviousClose')
                    
                    result = {
                        'symbol': symbol,
                        'current_price': float(current_price),
                        'previous_close': float(previous_close) if previous_close else None,
                        'source': 'yfinance_regular',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if previous_close:
                        change = current_price - previous_close
                        change_percent = (change / previous_close) * 100
                        result['change'] = change
                        result['change_percent'] = change_percent
                    
                    return result
                
        except Exception as e:
            logging.debug(f"yfinance fast fetch failed for {symbol}: {e}")
        
        return None
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price with ultra-fast optimizations"""
        symbol = symbol.strip().upper()
        
        # Check cache first
        cached_data = self._get_cached_price(symbol)
        if cached_data:
            return cached_data
        
        # For NSE stocks, try NSEPython first (fastest)
        if symbol.endswith('.NS') or not any(symbol.endswith(suffix) for suffix in ['.BO', '.US']):
            data = self._fetch_from_nsepython_fast(symbol)
            if data:
                self._cache_price(symbol, data)
                return data
        
        # Fallback to yfinance
        data = self._fetch_from_yfinance_fast(symbol)
        if data:
            self._cache_price(symbol, data)
            return data
        
        return None
    
    def get_multiple_prices_ultra_fast(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Ultra-fast batch processing with aggressive optimizations"""
        if not symbols:
            return {}
        
        results = {}
        symbols_to_fetch = []
        
        # Check cache for all symbols first
        for symbol in symbols:
            cached_data = self._get_cached_price(symbol)
            if cached_data:
                results[symbol] = cached_data
            else:
                symbols_to_fetch.append(symbol)
        
        if not symbols_to_fetch:
            return results
        
        print(f"Fetching {len(symbols_to_fetch)} prices concurrently (cached: {len(results)})...")
        
        # Group symbols by type for optimal processing
        nse_symbols = []
        other_symbols = []
        
        for symbol in symbols_to_fetch:
            if symbol.endswith('.NS') or not any(symbol.endswith(suffix) for suffix in ['.BO', '.US']):
                nse_symbols.append(symbol)
            else:
                other_symbols.append(symbol)
        
        # Process NSE symbols with higher concurrency (they're faster)
        if nse_symbols:
            nse_results = self._fetch_batch_concurrent(nse_symbols, prefer_nse=True)
            results.update(nse_results)
        
        # Process other symbols
        if other_symbols:
            other_results = self._fetch_batch_concurrent(other_symbols, prefer_nse=False)
            results.update(other_results)
        
        return results
    
    def _fetch_batch_concurrent(self, symbols: List[str], prefer_nse: bool = True) -> Dict[str, Dict[str, Any]]:
        """Concurrent batch fetch with optimized worker management"""
        results = {}
        
        def fetch_single_optimized(symbol):
            start_time = time.time()
            try:
                if prefer_nse:
                    # Try NSE first for Indian stocks
                    data = self._fetch_from_nsepython_fast(symbol)
                    if data:
                        fetch_time = time.time() - start_time
                        data['fetch_time'] = fetch_time
                        self._cache_price(symbol, data)
                        return symbol, data
                
                # Fallback to yfinance
                data = self._fetch_from_yfinance_fast(symbol)
                if data:
                    fetch_time = time.time() - start_time
                    data['fetch_time'] = fetch_time
                    self._cache_price(symbol, data)
                    return symbol, data
                    
                return symbol, None
                
            except Exception as e:
                logging.debug(f"Optimized fetch failed for {symbol}: {e}")
                return symbol, None
        
        # Use adaptive worker count based on batch size
        worker_count = min(len(symbols), self.max_workers)
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
                # Submit all tasks
                future_to_symbol = {
                    executor.submit(fetch_single_optimized, symbol): symbol 
                    for symbol in symbols
                }
                
                # Collect results with timeout
                for future in concurrent.futures.as_completed(future_to_symbol, timeout=self.request_timeout):
                    symbol, price_data = future.result()
                    if price_data:
                        results[symbol] = price_data
                    
                    # Minimal delay between processing results
                    time.sleep(self.batch_delay)
        
        except concurrent.futures.TimeoutError:
            print(f"Warning: Some price fetches timed out after {self.request_timeout}s")
        except Exception as e:
            print(f"Batch fetch error: {e}")
        
        return results
    
    def clear_cache(self):
        """Clear price cache"""
        self.price_cache.clear()
        self.cache_timestamps.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        valid_cache_count = sum(1 for symbol in self.price_cache.keys() if self._is_cache_valid(symbol))
        
        return {
            'total_cached': len(self.price_cache),
            'valid_cached': valid_cache_count,
            'cache_hit_rate': f"{(valid_cache_count / len(self.price_cache) * 100):.1f}%" if self.price_cache else "0%",
            'cache_ttl_seconds': self.cache_ttl
        }
    
    def set_cache_ttl(self, seconds: int):
        """Set cache time-to-live"""
        self.cache_ttl = max(10, min(300, seconds))  # Between 10s and 5min

# Create global ultra-fast instance
ultra_fast_price_fetcher = UltraFastPriceFetcher()

# Backward compatibility functions
def get_current_price_ultra_fast(symbol: str) -> Optional[float]:
    """Get current price as float (ultra-fast)"""
    data = ultra_fast_price_fetcher.get_current_price(symbol)
    if data:
        return data.get('current_price')
    return None

def get_multiple_prices_ultra_fast(symbols: List[str]) -> Dict[str, float]:
    """Get multiple prices as symbol->price mapping (ultra-fast)"""
    detailed_results = ultra_fast_price_fetcher.get_multiple_prices_ultra_fast(symbols)
    simple_results = {}
    
    for symbol, data in detailed_results.items():
        if 'current_price' in data:
            simple_results[symbol] = data['current_price']
    
    return simple_results

def get_detailed_price_data_ultra_fast(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """Get detailed price data with metadata (ultra-fast)"""
    return ultra_fast_price_fetcher.get_multiple_prices_ultra_fast(symbols)