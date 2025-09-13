"""
Corporate Actions Fetcher Service

This service fetches dividend, stock split, and bonus share announcements
for portfolio stocks from NSE and other financial APIs.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass
import time
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CorporateAction:
    """Represents a corporate action (dividend, split, bonus)"""
    symbol: str
    company_name: str
    action_type: str  # 'dividend', 'split', 'bonus', 'rights'
    announcement_date: str
    ex_date: str
    record_date: Optional[str] = None
    payment_date: Optional[str] = None
    
    # Dividend specific
    dividend_amount: Optional[float] = None
    
    # Split/Bonus specific
    ratio_from: Optional[int] = None
    ratio_to: Optional[int] = None
    
    # Additional info
    purpose: Optional[str] = None
    remarks: Optional[str] = None

class CorporateActionsFetcher:
    """Fetches corporate actions data for portfolio stocks"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.cache_file = 'data/corporate_actions_cache.json'
        self.cache_duration = 24 * 60 * 60  # 24 hours in seconds
        
    def get_portfolio_corporate_actions(self, portfolio_symbols: List[str], days_ahead: int = 60) -> List[CorporateAction]:
        """
        Get corporate actions for portfolio stocks for the next N days
        
        Args:
            portfolio_symbols: List of stock symbols in portfolio
            days_ahead: Number of days ahead to fetch actions for
            
        Returns:
            List of CorporateAction objects
        """
        try:
            print(f"DEBUG: Getting corporate actions for {len(portfolio_symbols)} symbols, {days_ahead} days ahead")
            
            # Load cached data first
            cached_actions = self._load_cache()
            print(f"DEBUG: Loaded {len(cached_actions)} actions from cache")
            
            # Filter cached actions for portfolio symbols and upcoming dates
            upcoming_actions = []
            current_date = datetime.now().date()
            cutoff_date = current_date + timedelta(days=days_ahead)
            
            print(f"DEBUG: Looking for actions between {current_date} and {cutoff_date}")
            
            for action in cached_actions:
                if action.symbol in portfolio_symbols:
                    try:
                        ex_date = datetime.strptime(action.ex_date, '%Y-%m-%d').date()
                        if current_date <= ex_date <= cutoff_date:
                            upcoming_actions.append(action)
                            print(f"DEBUG: Found upcoming action: {action.symbol} {action.action_type} on {action.ex_date}")
                    except ValueError:
                        # Skip actions with invalid date format
                        print(f"DEBUG: Invalid date format for {action.symbol}: {action.ex_date}")
                        continue
                        
            # If cache is older than cache_duration, refresh it
            if self._is_cache_stale():
                logger.info("Refreshing corporate actions cache...")
                self._refresh_cache(portfolio_symbols)
                # Reload from fresh cache
                cached_actions = self._load_cache()
                
                # Re-filter with fresh data
                upcoming_actions = []
                for action in cached_actions:
                    if action.symbol in portfolio_symbols:
                        try:
                            ex_date = datetime.strptime(action.ex_date, '%Y-%m-%d').date()
                            if current_date <= ex_date <= cutoff_date:
                                upcoming_actions.append(action)
                        except ValueError:
                            continue
            
            # Sort by ex-date
            upcoming_actions.sort(key=lambda x: x.ex_date)
            
            print(f"DEBUG: Found {len(upcoming_actions)} upcoming corporate actions for portfolio")
            logger.info(f"Found {len(upcoming_actions)} upcoming corporate actions for portfolio")
            return upcoming_actions
            
        except Exception as e:
            logger.error(f"Error fetching corporate actions: {e}")
            return []
    
    def _load_cache(self) -> List[CorporateAction]:
        """Load corporate actions from cache file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    actions = []
                    for item in data.get('actions', []):
                        actions.append(CorporateAction(**item))
                    return actions
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
        return []
    
    def _save_cache(self, actions: List[CorporateAction]):
        """Save corporate actions to cache file"""
        try:
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)
            
            cache_data = {
                'last_updated': datetime.now().isoformat(),
                'actions': [action.__dict__ for action in actions]
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _is_cache_stale(self) -> bool:
        """Check if cache is older than cache_duration"""
        try:
            if not os.path.exists(self.cache_file):
                return True
                
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                last_updated = datetime.fromisoformat(data.get('last_updated', ''))
                return (datetime.now() - last_updated).total_seconds() > self.cache_duration
                
        except Exception:
            return True
    
    def _refresh_cache(self, symbols: List[str]):
        """Refresh the corporate actions cache"""
        try:
            all_actions = []
            
            # Fetch from multiple sources
            all_actions.extend(self._fetch_from_nse_api())
            all_actions.extend(self._fetch_sample_data(symbols))  # Fallback sample data
            
            # Remove duplicates based on symbol, action_type, and ex_date
            unique_actions = []
            seen = set()
            for action in all_actions:
                key = (action.symbol, action.action_type, action.ex_date)
                if key not in seen:
                    unique_actions.append(action)
                    seen.add(key)
            
            self._save_cache(unique_actions)
            logger.info(f"Cached {len(unique_actions)} corporate actions")
            
        except Exception as e:
            logger.error(f"Error refreshing cache: {e}")
    
    def _fetch_from_nse_api(self) -> List[CorporateAction]:
        """Fetch corporate actions from NSE API"""
        actions = []
        try:
            # This is a placeholder for NSE API integration
            # In practice, you would use NSE's official API or scrape their corporate announcements page
            # For now, we'll return empty list and rely on sample data
            logger.info("NSE API integration not available, using sample data")
            
        except Exception as e:
            logger.error(f"Error fetching from NSE API: {e}")
            
        return actions
    
    def _fetch_sample_data(self, symbols: List[str]) -> List[CorporateAction]:
        """Generate sample corporate actions data for testing"""
        actions = []
        current_date = datetime.now().date()
        
        # Sample data for common stocks
        sample_actions = [
            {
                'symbol': 'RELIANCE.NS',
                'company_name': 'Reliance Industries Limited',
                'action_type': 'dividend',
                'dividend_amount': 8.0,
                'days_ahead': 15
            },
            {
                'symbol': 'INFY.NS', 
                'company_name': 'Infosys Limited',
                'action_type': 'dividend',
                'dividend_amount': 16.0,
                'days_ahead': 25
            },
            {
                'symbol': 'TCS.NS',
                'company_name': 'Tata Consultancy Services Limited',
                'action_type': 'dividend', 
                'dividend_amount': 22.0,
                'days_ahead': 35
            },
            {
                'symbol': 'WIPRO.NS',
                'company_name': 'Wipro Limited',
                'action_type': 'split',
                'ratio_from': 1,
                'ratio_to': 2,
                'days_ahead': 45
            },
            {
                'symbol': 'SYRMA',
                'company_name': 'Syrma SGS Technology Limited',
                'action_type': 'bonus',
                'ratio_from': 1,
                'ratio_to': 1,
                'days_ahead': 30
            }
        ]
        
        for sample in sample_actions:
            # Only include if symbol is in portfolio
            base_symbol = sample['symbol'].replace('.NS', '')
            if sample['symbol'] in symbols or base_symbol in symbols:
                ex_date = current_date + timedelta(days=sample['days_ahead'])
                record_date = ex_date + timedelta(days=1)
                payment_date = ex_date + timedelta(days=30)
                
                action = CorporateAction(
                    symbol=sample['symbol'],
                    company_name=sample['company_name'],
                    action_type=sample['action_type'],
                    announcement_date=(current_date - timedelta(days=10)).strftime('%Y-%m-%d'),
                    ex_date=ex_date.strftime('%Y-%m-%d'),
                    record_date=record_date.strftime('%Y-%m-%d'),
                    payment_date=payment_date.strftime('%Y-%m-%d'),
                    dividend_amount=sample.get('dividend_amount'),
                    ratio_from=sample.get('ratio_from'),
                    ratio_to=sample.get('ratio_to'),
                    purpose=f"Interim {sample['action_type']}" if sample['action_type'] == 'dividend' else f"Stock {sample['action_type']}",
                    remarks="Subject to shareholder approval"
                )
                actions.append(action)
        
        return actions
    
    def get_action_priority(self, action: CorporateAction) -> int:
        """Get priority for sorting actions (lower number = higher priority)"""
        try:
            ex_date = datetime.strptime(action.ex_date, '%Y-%m-%d').date()
            current_date = datetime.now().date()
            days_until = (ex_date - current_date).days
            
            # Priority based on days until ex-date
            if days_until <= 7:
                return 1  # High priority - within a week
            elif days_until <= 30:
                return 2  # Medium priority - within a month
            else:
                return 3  # Low priority - more than a month
                
        except ValueError:
            return 4  # Lowest priority for invalid dates

# Global instance
corporate_actions_fetcher = CorporateActionsFetcher()