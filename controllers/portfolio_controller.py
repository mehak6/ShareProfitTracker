"""
Portfolio Controller - Handles all portfolio business logic
Extracted from MainWindow to follow Single Responsibility Principle
"""

import threading
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass

# Add project root to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.models import Stock, PortfolioSummary
from services.calculator import PortfolioCalculator
from utils.helpers import FormatHelper


@dataclass
class PortfolioState:
    """Centralized portfolio state management"""
    stocks: List[Stock] = None
    portfolio_summary: Optional[PortfolioSummary] = None
    last_update_time: Optional[datetime] = None
    is_updating: bool = False
    
    def __post_init__(self):
        if self.stocks is None:
            self.stocks = []


class PortfolioController:
    """
    Handles all portfolio business logic and coordinates between data and UI layers
    """
    
    def __init__(self, db_manager, price_service=None):
        self.db_manager = db_manager
        self.price_service = price_service
        self.calculator = PortfolioCalculator()
        self.state = PortfolioState()
        
        # Callbacks for UI updates
        self.on_portfolio_updated: Optional[Callable] = None
        self.on_status_updated: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    def set_callbacks(self, 
                     portfolio_updated: Callable = None,
                     status_updated: Callable[[str], None] = None, 
                     error_callback: Callable[[str], None] = None):
        """Set UI callback functions"""
        self.on_portfolio_updated = portfolio_updated
        self.on_status_updated = status_updated
        self.on_error = error_callback
    
    def load_portfolio(self) -> bool:
        """Load portfolio from database"""
        try:
            self._update_status("Loading portfolio...")
            
            stock_data = self.db_manager.get_all_stocks()
            self.state.stocks = [Stock(**data) for data in stock_data]
            
            # Calculate summary
            self.state.portfolio_summary = self.calculator.calculate_portfolio_summary(self.state.stocks)
            
            self._update_status(f"Loaded {len(self.state.stocks)} stocks")
            
            # Notify UI
            if self.on_portfolio_updated:
                self.on_portfolio_updated()
                
            return True
            
        except Exception as e:
            error_msg = f"Failed to load portfolio: {str(e)}"
            self._handle_error(error_msg)
            return False
    
    def add_stock(self, stock_data: Dict[str, Any]) -> bool:
        """Add new stock to portfolio"""
        try:
            self._update_status("Adding stock...")
            
            # Add to database
            stock_id = self.db_manager.add_stock(**stock_data)
            
            if stock_id:
                # Reload portfolio to get updated data
                self.load_portfolio()
                self._update_status(f"Added {stock_data['symbol']} successfully")
                return True
            else:
                self._handle_error("Failed to add stock to database")
                return False
                
        except Exception as e:
            self._handle_error(f"Failed to add stock: {str(e)}")
            return False
    
    def update_stock(self, stock_id: int, stock_data: Dict[str, Any]) -> bool:
        """Update existing stock"""
        try:
            self._update_status("Updating stock...")
            
            self.db_manager.update_stock(stock_id=stock_id, **stock_data)
            
            # Reload portfolio
            self.load_portfolio()
            self._update_status(f"Updated {stock_data['symbol']} successfully")
            return True
            
        except Exception as e:
            self._handle_error(f"Failed to update stock: {str(e)}")
            return False
    
    def delete_stock(self, stock_id: int, symbol: str) -> bool:
        """Delete stock from portfolio"""
        try:
            self._update_status(f"Deleting {symbol}...")
            
            self.db_manager.delete_stock(stock_id)
            
            # Reload portfolio
            self.load_portfolio()
            self._update_status(f"Deleted {symbol} successfully")
            return True
            
        except Exception as e:
            self._handle_error(f"Failed to delete stock: {str(e)}")
            return False
    
    def refresh_prices_async(self, callback: Callable = None) -> None:
        """Refresh stock prices asynchronously"""
        if self.state.is_updating:
            self._update_status("Price update already in progress...")
            return
            
        if not self.state.stocks:
            self._update_status("No stocks to update")
            return
            
        if not self.price_service:
            self._handle_error("Price service not available")
            return
        
        # Start async refresh
        thread = threading.Thread(
            target=self._refresh_prices_background,
            args=(callback,),
            daemon=True
        )
        thread.start()
    
    def _refresh_prices_background(self, callback: Callable = None):
        """Background price refresh operation"""
        self.state.is_updating = True
        self._update_status("Fetching latest prices...")
        
        try:
            symbols = [stock.symbol for stock in self.state.stocks]
            start_time = time.time()
            
            # Get prices using the price service
            if hasattr(self.price_service, 'get_multiple_prices_ultra_fast'):
                # Use ultra-fast method if available
                detailed_results = self.price_service.get_multiple_prices_ultra_fast(symbols)
                price_results = {}
                for symbol, data in detailed_results.items():
                    if isinstance(data, dict) and 'current_price' in data:
                        price_results[symbol] = data['current_price']
            else:
                # Fallback to regular method
                price_results = self.price_service.get_multiple_prices(symbols)
            
            # Update stock objects and database
            updated_count = 0
            for stock in self.state.stocks:
                if stock.symbol in price_results:
                    new_price = price_results[stock.symbol]
                    if new_price and new_price > 0:
                        old_price = stock.current_price
                        stock.current_price = new_price
                        
                        # Update database cache
                        self.db_manager.update_price_cache(stock.symbol, new_price)
                        updated_count += 1
            
            # Recalculate portfolio summary
            self.state.portfolio_summary = self.calculator.calculate_portfolio_summary(self.state.stocks)
            self.state.last_update_time = datetime.now()
            
            fetch_time = time.time() - start_time
            success_msg = f"Updated {updated_count}/{len(symbols)} prices in {fetch_time:.1f}s"
            self._update_status(success_msg)
            
            # Notify UI on main thread
            if self.on_portfolio_updated:
                self.on_portfolio_updated()
                
            # Execute callback if provided
            if callback:
                callback(True, success_msg)
                
        except Exception as e:
            error_msg = f"Price refresh failed: {str(e)}"
            self._handle_error(error_msg)
            if callback:
                callback(False, error_msg)
        finally:
            self.state.is_updating = False
    
    def get_filtered_sorted_stocks(self, search_term: str = "", 
                                  sort_field: str = "symbol", 
                                  ascending: bool = True) -> List[Stock]:
        """Get filtered and sorted stock list"""
        filtered_stocks = self.state.stocks
        
        # Apply search filter
        if search_term:
            search_lower = search_term.lower().strip()
            filtered_stocks = []
            for stock in self.state.stocks:
                if (search_lower in stock.symbol.lower() or 
                    search_lower in (stock.company_name or "").lower()):
                    filtered_stocks.append(stock)
        
        # Apply sorting
        try:
            if sort_field == "symbol":
                filtered_stocks.sort(key=lambda x: x.symbol.lower(), reverse=not ascending)
            elif sort_field == "company":
                filtered_stocks.sort(key=lambda x: (x.company_name or "").lower(), reverse=not ascending)
            elif sort_field == "profit_loss":
                filtered_stocks.sort(key=lambda x: x.profit_loss_amount, reverse=not ascending)
            elif sort_field == "profit_loss_pct":
                filtered_stocks.sort(key=lambda x: x.profit_loss_percentage, reverse=not ascending)
            elif sort_field == "current_value":
                filtered_stocks.sort(key=lambda x: x.current_value, reverse=not ascending)
            elif sort_field == "days_held":
                filtered_stocks.sort(key=lambda x: x.days_held, reverse=not ascending)
        except Exception as e:
            print(f"Warning: Could not sort by {sort_field}: {e}")
        
        return filtered_stocks
    
    def get_portfolio_summary(self) -> Optional[PortfolioSummary]:
        """Get current portfolio summary"""
        return self.state.portfolio_summary
    
    def get_stocks(self) -> List[Stock]:
        """Get current stocks list"""
        return self.state.stocks.copy() if self.state.stocks else []
    
    def find_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        """Find stock by symbol"""
        for stock in self.state.stocks:
            if stock.symbol.upper() == symbol.upper():
                return stock
        return None
    
    def is_updating(self) -> bool:
        """Check if portfolio is currently updating"""
        return self.state.is_updating
    
    def get_last_update_time(self) -> Optional[datetime]:
        """Get last update timestamp"""
        return self.state.last_update_time
    
    def export_portfolio_data(self) -> List[Dict[str, Any]]:
        """Export portfolio data for CSV/reporting"""
        export_data = []
        for stock in self.state.stocks:
            export_data.append({
                "Symbol": stock.symbol,
                "Company": stock.company_name or "",
                "Quantity": stock.quantity,
                "Purchase Price": stock.purchase_price,
                "Purchase Date": stock.purchase_date,
                "Cash Invested": stock.actual_cash_invested,
                "Current Price": stock.current_price or 0,
                "Total Investment": stock.total_investment,
                "Current Value": stock.current_value,
                "Profit/Loss Amount": stock.profit_loss_amount,
                "Profit/Loss %": stock.profit_loss_percentage,
                "Days Held": stock.days_held,
                "Broker": stock.broker or ""
            })
        return export_data
    
    def _update_status(self, message: str):
        """Update status message"""
        if self.on_status_updated:
            self.on_status_updated(message)
    
    def _handle_error(self, error_message: str):
        """Handle error with logging and UI notification"""
        print(f"Portfolio Controller Error: {error_message}")
        if self.on_error:
            self.on_error(error_message)
        else:
            self._update_status(f"Error: {error_message}")