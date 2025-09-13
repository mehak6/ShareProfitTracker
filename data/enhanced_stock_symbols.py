"""
Enhanced stock symbol database with live NSE data and improved search functionality
Integrates NSEPython and NSETools for comprehensive stock coverage
"""

import json
import os
from typing import List, Tuple, Dict, Optional
import time
from datetime import datetime, timedelta

# Cache configuration
CACHE_FILE = "nse_stocks_cache.json"
CACHE_EXPIRY_HOURS = 24

class EnhancedStockSymbols:
    def __init__(self):
        self.nse_stocks: Dict[str, str] = {}
        self.cache_file_path = os.path.join(os.path.dirname(__file__), CACHE_FILE)
        self._load_stocks()
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not os.path.exists(self.cache_file_path):
            return False
        
        try:
            with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cache_data.get('timestamp', '2000-01-01'))
            return datetime.now() - cache_time < timedelta(hours=CACHE_EXPIRY_HOURS)
        except Exception:
            return False
    
    def _load_from_cache(self) -> bool:
        """Load stocks from cache if valid"""
        try:
            with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            self.nse_stocks = cache_data.get('stocks', {})
            print(f"Loaded {len(self.nse_stocks)} stocks from cache")
            return len(self.nse_stocks) > 0
        except Exception as e:
            print(f"Error loading cache: {e}")
            return False
    
    def _fetch_from_nsepython(self) -> Dict[str, str]:
        """Fetch stock symbols using NSEPython"""
        try:
            from nsepython import nse_eq_symbols
            
            print("Fetching stocks from NSEPython...")
            symbols = nse_eq_symbols()
            
            # NSEPython gives us symbols, we need to create symbol->company mapping
            stocks_dict = {}
            for symbol in symbols:
                # Use symbol as company name initially, will be enhanced later
                stocks_dict[symbol] = symbol
            
            print(f"Fetched {len(stocks_dict)} stocks from NSEPython")
            return stocks_dict
            
        except Exception as e:
            print(f"Error fetching from NSEPython: {e}")
            return {}
    
    def _fetch_from_nsetools(self) -> Dict[str, str]:
        """Fetch stock symbols using NSETools with company names"""
        try:
            from nsetools import Nse
            
            print("Fetching stocks from NSETools...")
            nse = Nse()
            stock_codes = nse.get_stock_codes()
            
            # NSETools returns a list of symbols, need to get company names
            stocks_dict = {}
            
            # Process in batches to avoid overwhelming the API
            batch_size = 50
            total_stocks = len(stock_codes) if isinstance(stock_codes, list) else 0
            
            if isinstance(stock_codes, list):
                for i in range(0, min(100, total_stocks), batch_size):  # Limit to first 100 for now
                    batch = stock_codes[i:i+batch_size]
                    for symbol in batch:
                        try:
                            # Try to get company name from quote
                            quote = nse.get_quote(symbol)
                            if quote and 'companyName' in quote:
                                company_name = quote['companyName']
                            else:
                                company_name = symbol  # Fallback to symbol
                            
                            stocks_dict[symbol] = company_name
                            
                        except Exception:
                            # If quote fails, just use symbol as company name
                            stocks_dict[symbol] = symbol
                    
                    # Small delay to be respectful to the API
                    time.sleep(0.1)
                
                print(f"Fetched {len(stocks_dict)} stocks with company names from NSETools")
            
            return stocks_dict
            
        except Exception as e:
            print(f"Error fetching from NSETools: {e}")
            return {}
    
    def _merge_and_enhance_data(self, nsepython_stocks: Dict[str, str], 
                               nsetools_stocks: Dict[str, str]) -> Dict[str, str]:
        """Merge data from both sources and enhance with company names"""
        
        # Start with comprehensive symbol list from NSEPython
        merged_stocks = nsepython_stocks.copy()
        
        # Enhance with company names from NSETools where available
        for symbol in merged_stocks:
            if symbol in nsetools_stocks:
                merged_stocks[symbol] = nsetools_stocks[symbol]
        
        print(f"Merged data: {len(merged_stocks)} total stocks")
        return merged_stocks
    
    def _save_to_cache(self, stocks: Dict[str, str]) -> None:
        """Save stocks to cache with timestamp"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'stocks': stocks,
                'count': len(stocks)
            }
            
            with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
            print(f"Saved {len(stocks)} stocks to cache")
            
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def _fetch_live_data(self) -> Dict[str, str]:
        """Fetch fresh data from APIs"""
        print("Fetching live stock data...")
        
        # Get symbols from NSEPython (comprehensive list)
        nsepython_stocks = self._fetch_from_nsepython()
        
        # Get enhanced data with company names from NSETools (limited for performance)
        nsetools_stocks = self._fetch_from_nsetools()
        
        # Merge and enhance
        if nsepython_stocks:
            merged_stocks = self._merge_and_enhance_data(nsepython_stocks, nsetools_stocks)
            self._save_to_cache(merged_stocks)
            return merged_stocks
        elif nsetools_stocks:
            # Fallback to nsetools only if nsepython fails
            self._save_to_cache(nsetools_stocks)
            return nsetools_stocks
        else:
            return {}
    
    def _load_stocks(self) -> None:
        """Load stocks from cache or fetch live data"""
        
        if self._is_cache_valid() and self._load_from_cache():
            return
        
        print("Cache invalid or missing, fetching live data...")
        live_stocks = self._fetch_live_data()
        
        if live_stocks:
            self.nse_stocks = live_stocks
        else:
            print("Failed to fetch live data, using fallback symbols")
            # Fallback to a minimal set of popular stocks
            self.nse_stocks = self._get_fallback_stocks()
    
    def _get_fallback_stocks(self) -> Dict[str, str]:
        """Fallback stock list in case APIs fail"""
        return {
            "RELIANCE": "Reliance Industries Limited",
            "TCS": "Tata Consultancy Services Limited", 
            "HDFCBANK": "HDFC Bank Limited",
            "INFY": "Infosys Limited",
            "HINDUNILVR": "Hindustan Unilever Limited",
            "ICICIBANK": "ICICI Bank Limited",
            "SBIN": "State Bank of India",
            "BHARTIARTL": "Bharti Airtel Limited",
            "ITC": "ITC Limited",
            "KOTAKBANK": "Kotak Mahindra Bank Limited"
        }
    
    def get_all_stocks(self) -> Dict[str, str]:
        """Get all available stocks as symbol->company mapping"""
        return self.nse_stocks.copy()
    
    def get_stock_list(self) -> List[str]:
        """Get list of all stock symbols"""
        return list(self.nse_stocks.keys())
    
    def search_stocks(self, query: str, limit: int = 20) -> List[Tuple[str, str]]:
        """
        Enhanced search for stocks by symbol or company name
        Returns list of (symbol, company_name) tuples
        """
        if not query or len(query) < 1:
            # Return popular stocks for empty query
            popular = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", 
                      "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK"]
            results = []
            for symbol in popular:
                if symbol in self.nse_stocks:
                    results.append((symbol, self.nse_stocks[symbol]))
                if len(results) >= limit:
                    break
            return results
        
        query_upper = query.upper()
        matches = []
        
        # Priority 1: Exact symbol matches
        for symbol, company in self.nse_stocks.items():
            if symbol.upper() == query_upper:
                matches.append((symbol, company))
        
        # Priority 2: Symbol starts with query
        for symbol, company in self.nse_stocks.items():
            if symbol.upper().startswith(query_upper) and (symbol, company) not in matches:
                matches.append((symbol, company))
                if len(matches) >= limit:
                    break
        
        # Priority 3: Symbol contains query
        if len(matches) < limit:
            for symbol, company in self.nse_stocks.items():
                if query_upper in symbol.upper() and (symbol, company) not in matches:
                    matches.append((symbol, company))
                    if len(matches) >= limit:
                        break
        
        # Priority 4: Company name contains query
        if len(matches) < limit:
            for symbol, company in self.nse_stocks.items():
                if query_upper in company.upper() and (symbol, company) not in matches:
                    matches.append((symbol, company))
                    if len(matches) >= limit:
                        break
        
        return matches[:limit]
    
    def get_company_name(self, symbol: str) -> str:
        """Get company name for a given symbol"""
        return self.nse_stocks.get(symbol.upper(), symbol)
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """Check if symbol exists in our database"""
        return symbol.upper() in self.nse_stocks
    
    def refresh_data(self) -> bool:
        """Force refresh of stock data"""
        print("Force refreshing stock data...")
        live_stocks = self._fetch_live_data()
        
        if live_stocks:
            self.nse_stocks = live_stocks
            return True
        return False

# Create global instance lazily
_enhanced_stocks = None

def get_enhanced_stocks():
    """Get the global enhanced stocks instance, creating it if needed"""
    global _enhanced_stocks
    if _enhanced_stocks is None:
        _enhanced_stocks = EnhancedStockSymbols()
    return _enhanced_stocks

# Convenience functions for backward compatibility
def search_stocks(query: str, limit: int = 10) -> List[Tuple[str, str]]:
    """Search for stocks by symbol or company name"""
    return get_enhanced_stocks().search_stocks(query, limit)

def get_all_nse_stocks() -> Dict[str, str]:
    """Get all NSE stocks as symbol->company mapping"""
    return get_enhanced_stocks().get_all_stocks()

def get_stock_symbols() -> List[str]:
    """Get list of all stock symbols"""
    return get_enhanced_stocks().get_stock_list()

def get_company_name(symbol: str) -> str:
    """Get company name for a given symbol"""
    return get_enhanced_stocks().get_company_name(symbol)

def is_valid_symbol(symbol: str) -> bool:
    """Check if symbol exists"""
    return get_enhanced_stocks().is_valid_symbol(symbol)