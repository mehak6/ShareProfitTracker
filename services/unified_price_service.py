"""
Unified Price Service - Single interface for all price fetching
Replaces 3 duplicate price fetchers with clean architecture
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import threading

# Cache implementation
class TTLCache:
    """Simple Time-To-Live cache"""
    
    def __init__(self, maxsize: int = 1000, ttl: int = 60):
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache = {}
        self.timestamps = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self.cache:
                return None
            
            # Check if expired
            if datetime.now() - self.timestamps[key] > timedelta(seconds=self.ttl):
                del self.cache[key]
                del self.timestamps[key]
                return None
            
            return self.cache[key]
    
    def set(self, key: str, value: Any):
        with self._lock:
            # Remove oldest entries if cache is full
            if len(self.cache) >= self.maxsize:
                oldest_key = min(self.timestamps.keys(), key=self.timestamps.get)
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
            
            self.cache[key] = value
            self.timestamps[key] = datetime.now()
    
    def clear(self):
        with self._lock:
            self.cache.clear()
            self.timestamps.clear()


class StrategyStatus(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable" 
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class PriceData:
    """Standardized price data structure"""
    symbol: str
    current_price: float
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    source: str = "unknown"
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        # Calculate change if we have previous close
        if self.previous_close and self.change is None:
            self.change = self.current_price - self.previous_close
            self.change_percent = (self.change / self.previous_close) * 100


class CircuitBreaker:
    """Circuit breaker pattern for API reliability"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_counts = {}
        self.last_failure_times = {}
        self._lock = threading.RLock()
    
    def is_closed(self, service_name: str) -> bool:
        """Check if circuit is closed (service available)"""
        with self._lock:
            failures = self.failure_counts.get(service_name, 0)
            
            if failures < self.failure_threshold:
                return True
            
            # Check if recovery time has passed
            last_failure = self.last_failure_times.get(service_name)
            if last_failure and datetime.now() - last_failure > timedelta(seconds=self.recovery_timeout):
                # Reset failures and allow retry
                self.failure_counts[service_name] = 0
                return True
            
            return False
    
    def record_success(self, service_name: str):
        """Record successful operation"""
        with self._lock:
            self.failure_counts[service_name] = 0
    
    def record_failure(self, service_name: str):
        """Record failed operation"""
        with self._lock:
            self.failure_counts[service_name] = self.failure_counts.get(service_name, 0) + 1
            self.last_failure_times[service_name] = datetime.now()


class PriceStrategy(ABC):
    """Abstract base class for price fetching strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.status = StrategyStatus.UNAVAILABLE
        self._test_availability()
    
    @abstractmethod
    def _test_availability(self):
        """Test if this strategy is available"""
        pass
    
    @abstractmethod
    def fetch_price(self, symbol: str) -> Optional[PriceData]:
        """Fetch price for a single symbol"""
        pass
    
    @abstractmethod
    def fetch_prices(self, symbols: List[str]) -> Dict[str, PriceData]:
        """Fetch prices for multiple symbols"""
        pass


class NSEPythonStrategy(PriceStrategy):
    """NSE Python price fetching strategy"""
    
    def __init__(self):
        super().__init__("nsepython")
    
    def _test_availability(self):
        try:
            from nsepython import nse_eq
            self.status = StrategyStatus.AVAILABLE
        except ImportError:
            self.status = StrategyStatus.UNAVAILABLE
            logging.info("NSEPython not available")
    
    def fetch_price(self, symbol: str) -> Optional[PriceData]:
        if self.status != StrategyStatus.AVAILABLE:
            return None
        
        try:
            from nsepython import nse_eq
            
            clean_symbol = symbol.replace('.NS', '').upper()
            data = nse_eq(clean_symbol)
            
            if data and isinstance(data, dict):
                # Extract price with multiple fallbacks
                current_price = None
                for key in ['lastPrice', 'price', 'ltp', 'close', 'currentPrice']:
                    if key in data:
                        current_price = float(data[key])
                        break
                
                if current_price is not None:
                    # Get previous close
                    previous_close = None
                    for key in ['previousClose', 'prevClose', 'pClose']:
                        if key in data:
                            previous_close = float(data[key])
                            break
                    
                    return PriceData(
                        symbol=symbol,
                        current_price=current_price,
                        previous_close=previous_close,
                        source=self.name
                    )
        
        except Exception as e:
            logging.debug(f"NSEPython fetch failed for {symbol}: {e}")
        
        return None
    
    def fetch_prices(self, symbols: List[str]) -> Dict[str, PriceData]:
        results = {}
        for symbol in symbols:
            price_data = self.fetch_price(symbol)
            if price_data:
                results[symbol] = price_data
            # Small delay to avoid rate limiting
            time.sleep(0.01)
        return results


class YFinanceStrategy(PriceStrategy):
    """Yahoo Finance price fetching strategy"""
    
    def __init__(self):
        super().__init__("yfinance")
    
    def _test_availability(self):
        try:
            import yfinance
            self.status = StrategyStatus.AVAILABLE
        except ImportError:
            self.status = StrategyStatus.UNAVAILABLE
            logging.info("yfinance not available")
    
    def fetch_price(self, symbol: str) -> Optional[PriceData]:
        if self.status != StrategyStatus.AVAILABLE:
            return None
        
        try:
            import yfinance as yf
            
            # Ensure proper symbol format
            yf_symbol = symbol
            if not symbol.endswith('.NS') and not any(symbol.endswith(suffix) for suffix in ['.BO', '.US']):
                yf_symbol = f"{symbol}.NS"
            
            ticker = yf.Ticker(yf_symbol)
            
            # Try fast_info first
            try:
                fast_info = ticker.fast_info
                current_price = fast_info.get('lastPrice')
                previous_close = fast_info.get('previousClose')
            except:
                # Fallback to regular info
                info = ticker.info
                current_price = info.get('regularMarketPrice') or info.get('currentPrice')
                previous_close = info.get('regularMarketPreviousClose')
            
            if current_price:
                return PriceData(
                    symbol=symbol,
                    current_price=float(current_price),
                    previous_close=float(previous_close) if previous_close else None,
                    source=self.name
                )
        
        except Exception as e:
            logging.debug(f"yfinance fetch failed for {symbol}: {e}")
        
        return None
    
    def fetch_prices(self, symbols: List[str]) -> Dict[str, PriceData]:
        results = {}
        for symbol in symbols:
            price_data = self.fetch_price(symbol)
            if price_data:
                results[symbol] = price_data
        return results


class MockDataStrategy(PriceStrategy):
    """Mock data strategy for testing/fallback"""
    
    def __init__(self):
        super().__init__("mock")
        
    def _test_availability(self):
        try:
            # Try direct import first
            from mock_yfinance import Ticker
            self.status = StrategyStatus.AVAILABLE
        except ImportError:
            try:
                # Try adding parent directory to path
                import sys
                import os
                parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if parent_dir not in sys.path:
                    sys.path.append(parent_dir)
                
                from mock_yfinance import Ticker
                self.status = StrategyStatus.AVAILABLE
            except ImportError as e:
                self.status = StrategyStatus.UNAVAILABLE
                print(f"Mock data not available: {e}")
    
    def fetch_price(self, symbol: str) -> Optional[PriceData]:
        if self.status != StrategyStatus.AVAILABLE:
            return None
        
        try:
            from mock_yfinance import Ticker
            
            ticker = Ticker(symbol)
            info = ticker.info
            
            if info and 'regularMarketPrice' in info:
                current_price = float(info['regularMarketPrice'])
                previous_close = info.get('regularMarketPreviousClose')
                
                return PriceData(
                    symbol=symbol,
                    current_price=current_price,
                    previous_close=float(previous_close) if previous_close else None,
                    source=self.name
                )
        
        except Exception as e:
            logging.debug(f"Mock fetch failed for {symbol}: {e}")
        
        return None
    
    def fetch_prices(self, symbols: List[str]) -> Dict[str, PriceData]:
        results = {}
        for symbol in symbols:
            price_data = self.fetch_price(symbol)
            if price_data:
                results[symbol] = price_data
        return results


class UnifiedPriceService:
    """
    Unified price service that replaces all separate fetchers
    Features: caching, circuit breaker, multiple strategies, async support
    """
    
    def __init__(self, cache_ttl: int = 60, max_workers: int = 5):
        # Initialize strategies in order of preference
        self.strategies = [
            NSEPythonStrategy(),
            YFinanceStrategy(),
            MockDataStrategy()
        ]
        
        # Filter to only available strategies
        self.strategies = [s for s in self.strategies if s.status == StrategyStatus.AVAILABLE]
        
        if not self.strategies:
            raise RuntimeError("No price fetching strategies available")
        
        self.cache = TTLCache(maxsize=1000, ttl=cache_ttl)
        self.circuit_breaker = CircuitBreaker()
        self.max_workers = max_workers
        
        logging.info(f"Initialized UnifiedPriceService with strategies: {[s.name for s in self.strategies]}")
    
    def get_price(self, symbol: str) -> Optional[PriceData]:
        """Get price for single symbol"""
        symbol = symbol.strip().upper()
        
        # Check cache first
        cached_data = self.cache.get(symbol)
        if cached_data:
            return cached_data
        
        # Try strategies in order
        for strategy in self.strategies:
            if not self.circuit_breaker.is_closed(strategy.name):
                continue
            
            try:
                price_data = strategy.fetch_price(symbol)
                if price_data:
                    self.circuit_breaker.record_success(strategy.name)
                    self.cache.set(symbol, price_data)
                    return price_data
            except Exception as e:
                self.circuit_breaker.record_failure(strategy.name)
                logging.warning(f"Strategy {strategy.name} failed for {symbol}: {e}")
        
        return None
    
    def get_prices(self, symbols: List[str]) -> Dict[str, PriceData]:
        """Get prices for multiple symbols"""
        if not symbols:
            return {}
        
        results = {}
        uncached_symbols = []
        
        # Check cache for all symbols
        for symbol in symbols:
            symbol = symbol.strip().upper()
            cached_data = self.cache.get(symbol)
            if cached_data:
                results[symbol] = cached_data
            else:
                uncached_symbols.append(symbol)
        
        if not uncached_symbols:
            return results
        
        # Fetch uncached symbols concurrently
        fresh_results = self._fetch_concurrent(uncached_symbols)
        
        # Cache fresh results
        for symbol, price_data in fresh_results.items():
            self.cache.set(symbol, price_data)
        
        results.update(fresh_results)
        return results
    
    def _fetch_concurrent(self, symbols: List[str]) -> Dict[str, PriceData]:
        """Fetch prices concurrently using thread pool"""
        results = {}
        
        def fetch_single(symbol: str) -> Tuple[str, Optional[PriceData]]:
            for strategy in self.strategies:
                if not self.circuit_breaker.is_closed(strategy.name):
                    continue
                
                try:
                    price_data = strategy.fetch_price(symbol)
                    if price_data:
                        self.circuit_breaker.record_success(strategy.name)
                        return symbol, price_data
                except Exception as e:
                    self.circuit_breaker.record_failure(strategy.name)
                    logging.debug(f"Strategy {strategy.name} failed for {symbol}: {e}")
            
            return symbol, None
        
        # Use thread pool for concurrent fetching
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all fetch tasks
            future_to_symbol = {executor.submit(fetch_single, symbol): symbol for symbol in symbols}
            
            # Collect results
            for future in as_completed(future_to_symbol, timeout=30):
                try:
                    symbol, price_data = future.result()
                    if price_data:
                        results[symbol] = price_data
                except Exception as e:
                    symbol = future_to_symbol[future]
                    logging.error(f"Failed to fetch price for {symbol}: {e}")
        
        return results
    
    # Backward compatibility methods
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Backward compatibility - returns symbol -> price mapping"""
        detailed_results = self.get_prices(symbols)
        return {symbol: data.current_price for symbol, data in detailed_results.items()}
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Backward compatibility - returns just the price"""
        price_data = self.get_price(symbol)
        return price_data.current_price if price_data else None
    
    def get_multiple_prices_ultra_fast(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Backward compatibility - returns detailed data in dict format"""
        detailed_results = self.get_prices(symbols)
        return {
            symbol: {
                'current_price': data.current_price,
                'previous_close': data.previous_close,
                'change': data.change,
                'change_percent': data.change_percent,
                'source': data.source,
                'timestamp': data.timestamp.isoformat()
            }
            for symbol, data in detailed_results.items()
        }
    
    def clear_cache(self):
        """Clear price cache"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cached_items': len(self.cache.cache),
            'cache_ttl': self.cache.ttl,
            'available_strategies': [s.name for s in self.strategies],
            'circuit_breaker_failures': dict(self.circuit_breaker.failure_counts)
        }


# Global instance for backward compatibility (lazy initialization)
_unified_price_service = None

def get_global_price_service():
    """Get or create global price service instance"""
    global _unified_price_service
    if _unified_price_service is None:
        _unified_price_service = UnifiedPriceService()
    return _unified_price_service

# Backward compatibility functions
def get_current_price(symbol: str) -> Optional[float]:
    return get_global_price_service().get_current_price(symbol)

def get_multiple_prices(symbols: List[str]) -> Dict[str, float]:
    return get_global_price_service().get_multiple_prices(symbols)

def get_multiple_prices_ultra_fast(symbols: List[str]) -> Dict[str, float]:
    return get_global_price_service().get_multiple_prices(symbols)

def get_detailed_price_data_ultra_fast(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    return get_global_price_service().get_multiple_prices_ultra_fast(symbols)