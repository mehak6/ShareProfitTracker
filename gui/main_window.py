import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import time
from typing import List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.async_database import AsyncDatabaseManager
from data.models import Stock, PortfolioSummary
from services.unified_price_service import (
    get_current_price,
    get_multiple_prices,
    get_multiple_prices_ultra_fast,
    get_detailed_price_data_ultra_fast,
)
from services.calculator import PortfolioCalculator
from utils.config import AppConfig
from utils.helpers import FormatHelper, FileHelper
from utils.theme_manager import ThemeManager
try:
    from gui.add_stock_dialog import AddStockDialog
    from gui.modern_ui import ModernUI, MetricCalculator
    from gui.notifications_panel import NotificationsPanel
    from gui.settings_dialog import SettingsDialog
except ImportError:
    from .add_stock_dialog import AddStockDialog
    from .modern_ui import ModernUI, MetricCalculator
    from .notifications_panel import NotificationsPanel
    from .settings_dialog import SettingsDialog

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.db_manager = AsyncDatabaseManager(AppConfig.get_database_path())
        self.calculator = PortfolioCalculator()
        self.theme_manager = ThemeManager()
        
        self.stocks: List[Stock] = []
        self.portfolio_summary: Optional[PortfolioSummary] = None
        self.last_update_time: Optional[datetime] = None
        self.is_updating = False
        self.notifications_panel = None
        
        self.setup_window()
        self.configure_modern_ui()
        self.create_widgets()
        self.load_portfolio()
        self.apply_theme()
        
    def setup_window(self):
        self.root.title(f"{AppConfig.APP_NAME} v{AppConfig.APP_VERSION}")
        self.root.geometry(f"{AppConfig.WINDOW_WIDTH}x{AppConfig.WINDOW_HEIGHT}")
        self.root.minsize(AppConfig.MIN_WINDOW_WIDTH, AppConfig.MIN_WINDOW_HEIGHT)
        
        # Configure grid weights
        self.root.grid_rowconfigure(3, weight=1)  # Main content frame gets most space
        self.root.grid_columnconfigure(0, weight=1)
    
    def configure_modern_ui(self):
        """Configure modern UI styling"""
        self.style = ModernUI.configure_style(self.root)
    
    def create_widgets(self):
        # Modern toolbar
        self.create_modern_toolbar()
        
        # Dashboard
        self.create_dashboard()
        
        # Create tabbed interface
        self.create_tabbed_interface()
        
        # Status bar with balance only
        self.create_status_bar()
    
    def create_modern_toolbar(self):
        """Create modern toolbar with icons"""
        self.toolbar_frame, self.toolbar_left, self.toolbar_right = ModernUI.create_modern_toolbar(self.root)
        self.toolbar_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        
        # Connect toolbar buttons to existing methods
        buttons = self.toolbar_left.winfo_children()
        if len(buttons) >= 3:
            buttons[0].configure(command=self.add_stock)  # Add Stock
            buttons[1].configure(command=self.refresh_prices)  # Refresh Prices
            buttons[2].configure(command=self.export_portfolio)  # Export Report
        
        # Add user selection dropdown between toolbar sections
        self.create_user_selection()
        
        # Connect settings button
        settings_buttons = self.toolbar_right.winfo_children()
        if len(settings_buttons) >= 1:
            settings_buttons[0].configure(command=self.open_settings)  # Settings
    
    def create_user_selection(self):
        """Create user selection dropdown in the toolbar"""
        # Create a frame for user selection in the center of the toolbar
        user_frame = tk.Frame(self.toolbar_frame)
        user_frame.pack(side='left', fill='x', expand=True, padx=20)
        
        # Create a centered frame within user_frame
        center_frame = tk.Frame(user_frame)
        center_frame.pack(anchor='center')
        
        # Label
        user_label = tk.Label(center_frame, text="User:", font=("Arial", 9, "bold"))
        user_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Get users from database
        users = self.db_manager.get_all_users()
        active_user = self.db_manager.get_active_user()
        
        # User selection dropdown
        self.user_var = tk.StringVar()
        user_values = [f"{user['display_name']}" for user in users]
        
        # Set current active user
        if active_user:
            self.user_var.set(active_user['display_name'])
        elif user_values:
            self.user_var.set(user_values[0])
        
        self.user_combobox = ttk.Combobox(center_frame, textvariable=self.user_var, 
                                         values=user_values, state="readonly", width=15)
        self.user_combobox.pack(side=tk.LEFT)
        self.user_combobox.bind("<<ComboboxSelected>>", self.on_user_changed)
        
        # Store user mapping for quick lookup
        self.user_mapping = {user['display_name']: user['id'] for user in users}
    
    def create_dashboard(self):
        """Create dashboard with key metrics"""
        self.dashboard_frame, self.metrics_frame = ModernUI.create_dashboard_summary(self.root)
        self.dashboard_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 0))
        
        # Create metric cards - will be populated in update_dashboard
        self.metric_cards = {}
    
    def update_dashboard(self):
        """Update dashboard metrics"""
        # Clear existing metric cards
        for card in self.metric_cards.values():
            card.destroy()
        self.metric_cards.clear()
        
        # Calculate metrics
        metrics = MetricCalculator.calculate_portfolio_metrics(self.stocks)
        
        # Create metric cards
        cards_data = [
            ("Total Investment", MetricCalculator.format_currency(metrics['total_investment']), None, None),
            ("Current Value", MetricCalculator.format_currency(metrics['current_value']), None, None),
            ("Total Gain/Loss", MetricCalculator.format_currency(metrics['total_gain_loss']), 
             MetricCalculator.format_percentage(metrics['total_gain_loss_pct']), 
             'positive' if metrics['total_gain_loss'] >= 0 else 'negative'),
            ("Total Stocks", str(metrics['total_stocks']), None, None)
        ]
        
        for i, (title, value, change, change_type) in enumerate(cards_data):
            card = ModernUI.create_metric_card(self.metrics_frame, title, value, change, change_type)
            card.grid(row=0, column=i, padx=(0, 15) if i < len(cards_data)-1 else 0, sticky="ew")
            self.metric_cards[title] = card
        
        # Configure column weights for equal distribution
        for i in range(len(cards_data)):
            self.metrics_frame.grid_columnconfigure(i, weight=1)
    
    def create_tabbed_interface(self):
        """Create tabbed interface with Portfolio and Notifications tabs"""
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=2, column=0, sticky="nsew", padx=10, pady=(10, 0))
        
        # Configure main window to expand
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create Portfolio tab
        self.portfolio_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.portfolio_frame, text="📊 Portfolio")
        
        # Create Notifications tab
        self.notifications_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.notifications_frame, text="📢 Notifications")
        
        # Set up portfolio tab content
        self.create_portfolio_tab()
        
        # Set up notifications tab content
        self.create_notifications_tab()
    
    def create_portfolio_tab(self):
        """Set up portfolio tab content"""
        # Configure grid weights for portfolio frame
        self.portfolio_frame.grid_rowconfigure(0, weight=1)
        self.portfolio_frame.grid_columnconfigure(0, weight=1)
        
        # Create portfolio table inside the portfolio tab
        self.create_portfolio_table(self.portfolio_frame)
        
        # Create buttons frame inside portfolio tab  
        self.create_buttons_frame(self.portfolio_frame)
    
    def create_notifications_tab(self):
        """Set up notifications tab content"""
        # Configure grid weights for notifications frame
        self.notifications_frame.grid_rowconfigure(0, weight=1)
        self.notifications_frame.grid_columnconfigure(0, weight=1)
        
        # Create notifications panel within the tab
        print(f"DEBUG: Creating notifications panel with {len(self.stocks)} stocks")
        self.notifications_panel = NotificationsPanel(self.notifications_frame, self.stocks)
        print(f"DEBUG: Notifications panel created")
    
    def open_settings(self):
        """Open settings dialog"""
        try:
            settings_dialog = SettingsDialog(self.root)
        except Exception as e:
            print(f"Error opening settings: {e}")
            messagebox.showerror("Error", f"Failed to open settings: {e}")
    
    def create_header_frame(self):
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.grid(row=0, column=0, sticky="ew")
        
        # Title
        title_label = ttk.Label(header_frame, text=AppConfig.APP_NAME, 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        # Last update info
        self.update_label = ttk.Label(header_frame, text="No data loaded")
        self.update_label.grid(row=0, column=1, padx=(20, 0), sticky="w")
        
        # Refresh button
        self.refresh_btn = ttk.Button(header_frame, text="Refresh Prices", 
                                     command=self.refresh_prices)
        self.refresh_btn.grid(row=0, column=2, padx=(20, 0))
        
        # Configure column weights
        header_frame.grid_columnconfigure(1, weight=1)
    
    def create_main_frame(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=3, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Portfolio table
        self.create_portfolio_table(main_frame)
        
        # Buttons frame
        self.create_buttons_frame(main_frame)
    
    def create_portfolio_table(self, parent):
        # Create main container frame
        container_frame = ttk.Frame(parent)
        container_frame.grid(row=0, column=0, sticky="nsew")
        container_frame.grid_rowconfigure(1, weight=1)  # Tree gets the space
        container_frame.grid_columnconfigure(0, weight=1)
        
        # Search and filter frame
        search_frame = ttk.Frame(container_frame)
        search_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        search_frame.grid_columnconfigure(1, weight=1)
        
        # Search label and entry
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        
        # Sort dropdown
        ttk.Label(search_frame, text="Sort by:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.sort_var = tk.StringVar(value="symbol")
        sort_options = ["symbol", "company", "profit_loss", "profit_loss_pct", "current_value", "days_held"]
        sort_combo = ttk.Combobox(search_frame, textvariable=self.sort_var, values=sort_options, 
                                 state="readonly", width=12)
        sort_combo.grid(row=0, column=3, padx=(0, 10))
        sort_combo.bind("<<ComboboxSelected>>", self.on_sort_changed)
        
        # Sort order button
        self.sort_ascending = True
        self.sort_order_btn = ttk.Button(search_frame, text="↑ Asc", command=self.toggle_sort_order)
        self.sort_order_btn.grid(row=0, column=4, padx=(0, 10))
        
        # Clear search button
        ttk.Button(search_frame, text="Clear", command=self.clear_search).grid(row=0, column=5)
        
        # Create treeview with scrollbars
        tree_frame = ttk.Frame(container_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_frame, columns=(
            "symbol", "company", "quantity", "purchase_price", 
            "current_price", "cash_invested", "investment", "current_value", 
            "profit_loss", "profit_loss_pct", "days_held"
        ), show="headings")
        
        # Configure columns
        columns_config = [
            ("symbol", "Symbol", 80),
            ("company", "Company", 150),
            ("quantity", "Qty", 80),
            ("purchase_price", "Purchase Price", 100),
            ("current_price", "Current Price", 100),
            ("cash_invested", "Cash Invested", 100),
            ("investment", "Investment", 100),
            ("current_value", "Current Value", 100),
            ("profit_loss", "P&L Amount", 100),
            ("profit_loss_pct", "P&L %", 80),
            ("days_held", "Days", 60)
        ]
        
        for col_id, heading, width in columns_config:
            self.tree.heading(col_id, text=heading)
            self.tree.column(col_id, width=width, anchor="center")
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Bind double-click event
        self.tree.bind("<Double-1>", self.on_stock_double_click)
    
    def create_buttons_frame(self, parent):
        buttons_frame = ttk.Frame(parent, padding="10")
        buttons_frame.grid(row=1, column=0, sticky="ew")
        
        # Buttons
        ttk.Button(buttons_frame, text="Add Stock", 
                  command=self.add_stock).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(buttons_frame, text="Edit Stock", 
                  command=self.edit_stock).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(buttons_frame, text="Delete Stock", 
                  command=self.delete_stock).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(buttons_frame, text="Refresh Portfolio", 
                  command=self.refresh_portfolio).grid(row=0, column=3, padx=(0, 10))
        ttk.Button(buttons_frame, text="Export CSV", 
                  command=self.export_portfolio).grid(row=0, column=4, padx=(0, 10))
        
        # Cash Management Buttons
        ttk.Button(buttons_frame, text="Cash I Have", 
                  command=self.manage_cash).grid(row=0, column=5, padx=(0, 10))
        ttk.Button(buttons_frame, text="Other Funds", 
                  command=self.manage_expenses).grid(row=0, column=6, padx=(0, 10))
        
        # Tax Report Button
        ttk.Button(buttons_frame, text="Tax Report", 
                  command=self.show_tax_report).grid(row=0, column=7, padx=(0, 10))
    
    def create_summary_frame(self):
        summary_frame = ttk.LabelFrame(self.root, text="Portfolio Summary", padding="10")
        summary_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Summary labels - Portfolio row
        self.total_investment_label = ttk.Label(summary_frame, text="Total Investment: ₹0.00")
        self.total_investment_label.grid(row=0, column=0, sticky="w", padx=(0, 20))
        
        self.current_value_label = ttk.Label(summary_frame, text="Current Value: ₹0.00")
        self.current_value_label.grid(row=0, column=1, sticky="w", padx=(0, 20))
        
        self.profit_loss_label = ttk.Label(summary_frame, text="Total P&L: ₹0.00 (0.00%)")
        self.profit_loss_label.grid(row=0, column=2, sticky="w", padx=(0, 20))
        
        self.stocks_count_label = ttk.Label(summary_frame, text="Stocks: 0")
        self.stocks_count_label.grid(row=0, column=3, sticky="w")
        
        # Cash balance row
        self.cash_balance_label = ttk.Label(summary_frame, text="Available Cash: ₹0.00", 
                                           font=("Arial", 10, "bold"))
        self.cash_balance_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
    
    def create_status_bar(self):
        # Create status bar frame to hold both status and cash balance
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        status_frame.grid_columnconfigure(0, weight=1)  # Left side expands
        
        # Status message (left side)
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                relief="sunken", padding="5")
        status_label.grid(row=0, column=0, sticky="ew")
        
        # Cash balance (right side)
        self.cash_balance_var = tk.StringVar()
        self.cash_balance_var.set("Available Cash: ₹0.00")
        self.cash_balance_status = ttk.Label(status_frame, textvariable=self.cash_balance_var,
                                           relief="sunken", padding="5",
                                           font=("Arial", 10, "bold"))
        self.cash_balance_status.grid(row=0, column=1, sticky="e", padx=(10, 0))
    
    def load_portfolio(self):
        self.status_var.set("Loading portfolio...")
        
        def worker():
            import asyncio
            try:
                stock_data = asyncio.run(self.db_manager.get_all_stocks_async())
                
                def apply_results():
                    try:
                        self.stocks = [Stock(**data) for data in stock_data]
                        print(f"DEBUG load_portfolio: Found {len(stock_data)} records in database")
                        print(f"DEBUG load_portfolio: Created {len(self.stocks)} stock objects")
                        self.update_portfolio_display()
                        self.update_summary_display()
                        if hasattr(self, 'notifications_panel') and self.notifications_panel:
                            self.notifications_panel.update_stocks(self.stocks)
                        if self.stocks:
                            self.status_var.set(f"Loaded {len(self.stocks)} stocks")
                        else:
                            self.status_var.set("No stocks in portfolio")
                    except Exception as e:
                        print(f"DEBUG load_portfolio apply ERROR: {e}")
                        messagebox.showerror("Error", f"Failed to render portfolio: {str(e)}")
                        self.status_var.set("Error loading portfolio")
                self.root.after(0, apply_results)
            except Exception as e:
                def on_err():
                    print(f"DEBUG load_portfolio ERROR: {e}")
                    messagebox.showerror("Error", f"Failed to load portfolio: {str(e)}")
                    self.status_var.set("Error loading portfolio")
                self.root.after(0, on_err)
        threading.Thread(target=worker, daemon=True).start()
    
    def update_portfolio_display(self):
        # Filter and sort stocks
        try:
            filtered_stocks = self.filter_and_sort_stocks(self.stocks)
        except AttributeError:
            # Fallback if search/sort variables are not initialized yet
            filtered_stocks = self.stocks
        
        # Get current selection to restore it later
        selected_symbols = []
        for selected_item in self.tree.selection():
            values = self.tree.item(selected_item)['values']
            if values:
                selected_symbols.append(values[0])
        
        # Clear existing items only
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Batch insert items for better performance
        items_to_insert = []
        for stock in filtered_stocks:
            values = [
                stock.symbol,
                FormatHelper.truncate_text(stock.company_name or "", 20),
                FormatHelper.format_number(stock.quantity, 0),
                FormatHelper.format_currency(stock.purchase_price),
                FormatHelper.format_currency(stock.current_price or 0),
                FormatHelper.format_currency(stock.total_investment),
                FormatHelper.format_currency(stock.current_value),
                FormatHelper.format_currency(stock.profit_loss_amount),
                FormatHelper.format_percentage(stock.profit_loss_percentage),
                str(stock.days_held)
            ]
            
            # Color coding for profit/loss
            tags = []
            if stock.current_price is not None:
                if stock.profit_loss_amount > 0:
                    tags.append("profit")
                    # Fix the profit/loss display format
                    values[7] = f"+{FormatHelper.format_currency(stock.profit_loss_amount)[1:]}"
                elif stock.profit_loss_amount < 0:
                    tags.append("loss")
            
            items_to_insert.append((values, tags))
        
        print(f"DEBUG: About to insert {len(items_to_insert)} items into TreeView...")
        
        # Insert all items
        inserted_items = []
        for i, (values, tags) in enumerate(items_to_insert):
            item = self.tree.insert("", "end", values=values, tags=tags)
            inserted_items.append((item, values[0]))  # Store item ID and symbol
            
            # Debug first few insertions
            if i < 3:
                print(f"DEBUG: Inserted item {i+1}: {values[0]} with current_price={values[4]}")
        
        print(f"DEBUG: TreeView updated successfully with {len(items_to_insert)} items")
        
        # Restore selection
        for item_id, symbol in inserted_items:
            if symbol in selected_symbols:
                self.tree.selection_add(item_id)
        
        # Configure tags for colors only once
        self.tree.tag_configure("profit", foreground=AppConfig.COLORS['profit'])
        self.tree.tag_configure("loss", foreground=AppConfig.COLORS['loss'])
        
        # Update dashboard
        self.update_dashboard()
        
        # Update notifications
        if hasattr(self, 'notifications_panel') and self.notifications_panel:
            self.notifications_panel.update_stocks(self.stocks)
    
    def update_summary_display(self):
        self.portfolio_summary = self.calculator.calculate_portfolio_summary(self.stocks)
        
        # Portfolio summary is now only shown in the dashboard
        # No duplicate summary labels needed
        
        # Update cash balance
        try:
            cash_balance = self.db_manager.get_current_cash_balance()
            self.cash_balance_var.set(f"Available Cash: {FormatHelper.format_currency(cash_balance)}")
            # Update color based on balance
            if cash_balance > 0:
                self.cash_balance_status.config(foreground="green")
            elif cash_balance < 0:
                self.cash_balance_status.config(foreground="red")
            else:
                self.cash_balance_status.config(foreground="black")
        except Exception as e:
            self.cash_balance_var.set("Available Cash: ₹0.00")
            self.cash_balance_status.config(foreground="black")
    
    def refresh_portfolio(self):
        """Refresh the entire portfolio from database"""
        self.status_var.set("Refreshing portfolio...")
        try:
            self._force_refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh portfolio: {str(e)}")
            self.status_var.set("Error refreshing portfolio")
    
    def refresh_prices(self):
        if self.is_updating:
            return
        
        if not self.stocks:
            messagebox.showinfo("Info", "No stocks to update")
            return
        
        # Use normal enhanced price refresh
        self._normal_refresh_prices()
    
    def _normal_refresh_prices(self):
        """Normal price refresh using enhanced price fetcher"""
        if self.is_updating:
            return
            
        # Start normal refresh in background
        threading.Thread(target=self._normal_refresh_background, daemon=True).start()
    
    def _normal_refresh_background(self):
        """Normal background refresh with enhanced price fetcher"""
        self.is_updating = True
        self.root.after(0, lambda: self.status_var.set("Refreshing prices..."))
        if hasattr(self, 'refresh_btn'):
            self.root.after(0, lambda: self.refresh_btn.config(state="disabled"))
        
        try:
            symbols = [stock.symbol for stock in self.stocks]
            
            # Show progress
            self.root.after(0, lambda: self.status_var.set(f"Fetching prices for {len(symbols)} stocks..."))
            
            # Use enhanced price fetcher (normal speed)
            start_time = time.time()
            print(f"DEBUG: About to fetch prices for symbols: {symbols[:3]}...")
            price_results = get_multiple_prices(symbols)
            fetch_time = time.time() - start_time
            
            print(f"DEBUG: Price fetcher returned: {type(price_results)}")
            print(f"DEBUG: Sample price results: {dict(list(price_results.items())[:3]) if price_results else 'Empty'}")
            
            # Update stocks with new prices
            updated_count = 0
            successful_updates = []
            
            print(f"DEBUG: Normal refresh got {len(price_results)} price results")
            
            for stock in self.stocks:
                print(f"DEBUG: Processing {stock.symbol}...")
                
                if stock.symbol in price_results:
                    new_price = price_results[stock.symbol]
                    print(f"DEBUG: Found price data for {stock.symbol}: {new_price}")
                    
                    if new_price is not None and new_price > 0:
                        old_price = stock.current_price
                        print(f"DEBUG: {stock.symbol} - Old: {old_price}, New: {new_price}")
                        
                        # Update stock object
                        stock.current_price = new_price
                        print(f"DEBUG: Updated stock object current_price to {stock.current_price}")
                        
                        # Update database with new price
                        try:
                            self.db_manager.update_price_cache(stock.symbol, new_price)
                            print(f"DEBUG: Updated database cache for {stock.symbol}")
                            
                            # Verify database update immediately
                            cached_data = self.db_manager.get_cached_price(stock.symbol)
                            if cached_data:
                                print(f"DEBUG: Verified DB has price {cached_data['current_price']} for {stock.symbol}")
                            else:
                                print(f"ERROR: Database verification failed for {stock.symbol}")
                            
                            updated_count += 1
                            successful_updates.append(f"{stock.symbol}: {FormatHelper.format_currency(new_price)}")
                            
                        except Exception as e:
                            print(f"ERROR: Failed to update {stock.symbol} in database: {e}")
                    else:
                        print(f"DEBUG: Invalid price for {stock.symbol}: {new_price}")
                else:
                    print(f"DEBUG: No price data found for {stock.symbol}")
            
            # Persist updates asynchronously in batch
            try:
                import asyncio
                async def persist_updates_fast():
                    tasks = []
                    for stock in self.stocks:
                        if stock.current_price is not None:
                            tasks.append(self.db_manager.update_price_cache_async(stock.symbol, stock.current_price))
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                asyncio.run(persist_updates_fast())
            except Exception as e:
                print(f"WARN: Batch DB cache update (fast) encountered issues: {e}")

            # Persist updates asynchronously in batch
            try:
                import asyncio
                async def persist_updates_ultra():
                    tasks = []
                    for stock in self.stocks:
                        if stock.current_price is not None:
                            tasks.append(self.db_manager.update_price_cache_async(stock.symbol, stock.current_price))
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                asyncio.run(persist_updates_ultra())
            except Exception as e:
                print(f"WARN: Batch DB cache update (ultra) encountered issues: {e}")

            self.last_update_time = datetime.now()
            
            # Success message
            success_msg = f"Updated {updated_count}/{len(symbols)} prices in {fetch_time:.1f}s"
            print(f"DEBUG: {success_msg}")
            
            # Complete refresh on main thread
            self.root.after(0, lambda: self._normal_refresh_complete(updated_count, len(symbols), fetch_time, success_msg))
            
        except Exception as e:
            print(f"ERROR in normal refresh: {e}")
            error_msg = f"Error during price refresh: {str(e)}"
            self.root.after(0, lambda: self._normal_refresh_error(error_msg))
    
    def _normal_refresh_complete(self, updated_count, total_count, fetch_time, success_msg):
        """Complete normal price refresh"""
        print(f"DEBUG: Completing normal price refresh")
        
        # Reload portfolio asynchronously to avoid blocking UI
        print(f"DEBUG: Triggering async reload after normal refresh")
        self.load_portfolio()
        
        # Update notifications with latest stock data
        if hasattr(self, 'notifications_panel') and self.notifications_panel:
            print(f"DEBUG: Updating notifications panel with {len(self.stocks)} stocks")
            self.notifications_panel.update_stocks(self.stocks)
            print(f"DEBUG: Notifications panel updated")
        else:
            print(f"DEBUG: No notifications panel available for update")
        
        # Update UI elements
        update_text = f"Last updated: {self.last_update_time.strftime('%H:%M:%S')}"
        if hasattr(self, 'update_label'):
            self.update_label.config(text=update_text)
        
        self.status_var.set(f"Price refresh complete: {success_msg}")
        print(f"DEBUG: Status updated: {success_msg}")
        
        # Re-enable refresh button
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.config(state="normal")
        
        self.is_updating = False
        print(f"DEBUG: Normal refresh completed successfully - UI should now show updated prices")
    
    def _normal_refresh_error(self, error_msg):
        """Handle normal refresh error"""
        self.status_var.set(error_msg)
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.config(state="normal")
        self.is_updating = False
        messagebox.showerror("Price Refresh Error", error_msg)
    
    def _blazing_fast_refresh(self):
        """Blazing fast refresh - simplest and fastest method"""
        if self.is_updating:
            return
            
        # Start blazing fast refresh in background
        threading.Thread(target=self._blazing_fast_refresh_background, daemon=True).start()
    
    def _blazing_fast_refresh_background(self):
        """Blazing fast background refresh - maximum speed"""
        self.is_updating = True
        self.root.after(0, lambda: self.status_var.set("Blazing fast refresh starting..."))
        if hasattr(self, 'refresh_btn'):
            self.root.after(0, lambda: self.refresh_btn.config(state="disabled"))
        
        try:
            symbols = [stock.symbol for stock in self.stocks]
            
            # Show progress
            self.root.after(0, lambda: self.status_var.set(f"Fetching {len(symbols)} prices with maximum speed..."))
            
            # Use blazing fast refresh method (mapped to unified normal fetch)
            start_time = time.time()
            price_results = get_multiple_prices(symbols)
            fetch_time = time.time() - start_time
            
            # Update stocks with new prices
            updated_count = 0
            successful_updates = []
            
            print(f"DEBUG: Got prices for {len(price_results)} symbols")
            print(f"DEBUG: Price results: {dict(list(price_results.items())[:3])}...")  # Show first 3
            
            for stock in self.stocks:
                if stock.symbol in price_results and price_results[stock.symbol] is not None:
                    old_price = stock.current_price
                    new_price = price_results[stock.symbol]
                    
                    print(f"DEBUG: {stock.symbol} - Old: {old_price}, New: {new_price}")
                    
                    # Check if price actually changed
                    if old_price != new_price:
                        print(f"DEBUG: Price changed for {stock.symbol}: {old_price} -> {new_price}")
                    else:
                        print(f"DEBUG: Price unchanged for {stock.symbol}: {old_price}")
                    
                    stock.current_price = new_price
                    
                        updated_count += 1
                        successful_updates.append(f"{stock.symbol}: {FormatHelper.format_currency(new_price)}")
                else:
                    print(f"DEBUG: No price data for {stock.symbol}")
            
            print(f"DEBUG: Successfully updated {updated_count} prices: {successful_updates[:3]}...")
            print(f"DEBUG: About to set last_update_time and complete refresh")
            
            self.last_update_time = datetime.now()
            
            # Success message with speed info and details
            success_msg = f"Updated {updated_count}/{len(symbols)} prices in {fetch_time:.1f}s ({len(symbols)/fetch_time:.1f} stocks/sec)"
            print(f"DEBUG: Success message: {success_msg}")
            
            # Add sample of updated prices to success message
            if successful_updates:
                sample_updates = ", ".join(successful_updates[:3])
                success_msg += f" | Examples: {sample_updates}"
            
            # Update UI on main thread
            self.root.after(0, lambda: self._blazing_fast_complete(updated_count, len(symbols), fetch_time, success_msg))
            
        except Exception as e:
            error_msg = f"Fast refresh failed: {str(e)}"
            self.root.after(0, lambda: self.status_var.set(error_msg))
            self.root.after(0, lambda: messagebox.showerror("Refresh Error", f"Failed to refresh prices:\n{str(e)}"))
        
        finally:
            self.is_updating = False
            if hasattr(self, 'refresh_btn'):
                self.root.after(0, lambda: self.refresh_btn.config(state="normal"))
    
    def _blazing_fast_complete(self, updated_count, total_count, fetch_time, success_msg):
        """Complete blazing fast refresh"""
        print(f"DEBUG: Completing blazing fast refresh - updating UI")
        
        # Reload portfolio asynchronously to avoid blocking UI
        print(f"DEBUG: Triggering async reload after blazing fast refresh")
        self.load_portfolio()
        
        # Show performance info
        update_text = f"Last updated: {self.last_update_time.strftime('%H:%M:%S')} (BLAZING FAST: {fetch_time:.1f}s)"
        if hasattr(self, 'update_label'):
            self.update_label.config(text=update_text)
        self.status_var.set(f"BLAZING FAST: {success_msg}")
        
        print(f"DEBUG: All UI updates complete")
        
        # Show success message with more detail
        messagebox.showinfo(
            "Blazing Fast Refresh Complete!",
            f"Successfully refreshed {updated_count}/{total_count} prices\n"
            f"Time taken: {fetch_time:.1f} seconds\n"
            f"Speed: {total_count/fetch_time:.1f} stocks per second!\n\n"
            f"Note: Portfolio display has been updated with new prices.\n"
            f"Check console for detailed debug information."
        )

    def _ultra_fast_direct_refresh(self):
        """Direct ultra-fast refresh without dialog"""
        if self.is_updating:
            return
            
        # Start ultra-fast refresh in background
        threading.Thread(target=self._ultra_fast_refresh_background, daemon=True).start()
    
    def _ultra_fast_refresh_background(self):
        """Ultra-fast background refresh with progress updates"""
        self.is_updating = True
        self.root.after(0, lambda: self.status_var.set("🚀 Ultra-fast refresh starting..."))
        self.root.after(0, lambda: self.refresh_btn.config(state="disabled"))
        
        try:
            symbols = [stock.symbol for stock in self.stocks]
            
            # Show progress
            self.root.after(0, lambda: self.status_var.set(f"⚡ Fetching {len(symbols)} prices concurrently..."))
            
            # Use ultra-fast fetcher with maximum performance
            start_time = time.time()
            detailed_prices = get_detailed_price_data_ultra_fast(symbols)
            fetch_time = time.time() - start_time
            
            # Update database and stocks with better error handling
            updated_count = 0
            cache_hits = 0
            
            for stock in self.stocks:
                if stock.symbol in detailed_prices:
                    price_data = detailed_prices[stock.symbol]
                    if price_data and 'current_price' in price_data:
                        old_price = stock.current_price
                        stock.current_price = price_data['current_price']
                        
                        # Count update if changed
                        if old_price != stock.current_price:
                            updated_count += 1
                        
                        # Track cache hits
                        if 'cached' in price_data.get('source', ''):
                            cache_hits += 1
            
            self.last_update_time = datetime.now()
            
            # Show success with performance stats
            cache_rate = (cache_hits / len(symbols) * 100) if symbols else 0
            success_msg = (f"✅ Updated {updated_count}/{len(symbols)} prices in {fetch_time:.1f}s "
                          f"(Cache: {cache_hits}/{len(symbols)} = {cache_rate:.0f}%)")
            
            # Update UI on main thread with performance info
            self.root.after(0, lambda: self._ultra_fast_refresh_complete(updated_count, len(symbols), fetch_time, success_msg))
            
        except Exception as e:
            error_msg = f"❌ Ultra-fast refresh failed: {str(e)}"
            self.root.after(0, lambda: self.status_var.set(error_msg))
            self.root.after(0, lambda: messagebox.showerror("Refresh Error", f"Failed to refresh prices:\n{str(e)}"))
        
        finally:
            self.is_updating = False
            self.root.after(0, lambda: self.refresh_btn.config(state="normal"))
    
    def _ultra_fast_refresh_complete(self, updated_count, total_count, fetch_time, success_msg):
        """Complete ultra-fast refresh with performance stats"""
        self.update_portfolio_display()
        self.update_summary_display()
        
        # Show performance info
        update_text = f"Last updated: {self.last_update_time.strftime('%H:%M:%S')} ({fetch_time:.1f}s)"
        self.update_label.config(text=update_text)
        self.status_var.set(success_msg)
        
        # Show performance popup for user feedback
        if fetch_time < 5.0:  # Only show if actually fast
            messagebox.showinfo(
                "Ultra-Fast Refresh Complete! 🚀",
                f"Successfully refreshed {updated_count}/{total_count} prices\n"
                f"Time taken: {fetch_time:.1f} seconds\n\n"
                f"Performance: {total_count/fetch_time:.1f} stocks/second!"
            )
    
    def _refresh_prices_background(self):
        self.is_updating = True
        self.root.after(0, lambda: self.status_var.set("Updating prices..."))
        self.root.after(0, lambda: self.refresh_btn.config(state="disabled"))
        
        try:
            symbols = [stock.symbol for stock in self.stocks]
            
            # Use ultra-fast price fetcher with aggressive optimizations
            detailed_prices = get_detailed_price_data_ultra_fast(symbols)
            
            # Update database and stocks with better error handling
            updated_count = 0
            for stock in self.stocks:
                if stock.symbol in detailed_prices:
                    price_data = detailed_prices[stock.symbol]
                    if price_data and 'current_price' in price_data:
                        old_price = stock.current_price
                        stock.current_price = price_data['current_price']
                        
                        # Only update database if price actually changed
                        if old_price != stock.current_price:
                            self.db_manager.update_price_cache(stock.symbol, stock.current_price)
                            updated_count += 1
            
            self.last_update_time = datetime.now()
            
            # Update UI on main thread with progress info
            self.root.after(0, lambda: self._update_ui_after_refresh(updated_count, len(symbols)))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to update prices: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Error updating prices"))
        
        finally:
            self.is_updating = False
            self.root.after(0, lambda: self.refresh_btn.config(state="normal"))
    
    def _update_ui_after_refresh(self, updated_count=0, total_count=0):
        self.update_portfolio_display()
        self.update_summary_display()
        
        update_text = f"Last updated: {self.last_update_time.strftime('%H:%M:%S')}"
        self.update_label.config(text=update_text)
        
        if updated_count > 0:
            self.status_var.set(f"Updated {updated_count}/{total_count} prices successfully")
        else:
            self.status_var.set("Prices refreshed (no changes detected)")
    
    def add_stock(self):
        try:
            dialog = AddStockDialog(self.root)
            
            # Wait for dialog to complete
            self.root.wait_window(dialog.dialog)
            
            if dialog.result:
                stock_data = dialog.result
                
                # Add to database
                stock_id = self.db_manager.add_stock(**stock_data)
                
                # Immediately reload and refresh
                self._force_refresh()
                
                messagebox.showinfo("Success", f"Added {stock_data['symbol']} to portfolio")
                
            else:
                print("Add stock dialog cancelled")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add stock: {str(e)}")
    
    def _force_refresh(self):
        """Force a complete refresh of the portfolio display"""
        try:
            # Clear the tree completely
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Reload from database
            stock_data = self.db_manager.get_all_stocks()
            self.stocks = [Stock(**data) for data in stock_data]
            
            # Rebuild the tree
            for stock in self.stocks:
                values = [
                    stock.symbol,
                    FormatHelper.truncate_text(stock.company_name or "", 20),
                    FormatHelper.format_number(stock.quantity, 0),
                    FormatHelper.format_currency(stock.purchase_price),
                    FormatHelper.format_currency(stock.current_price or 0),
                    FormatHelper.format_currency(stock.actual_cash_invested),
                    FormatHelper.format_currency(stock.total_investment),
                    FormatHelper.format_currency(stock.current_value),
                    FormatHelper.format_currency(stock.profit_loss_amount),
                    FormatHelper.format_percentage(stock.profit_loss_percentage),
                    str(stock.days_held)
                ]
                self.tree.insert("", "end", values=values)
            
            # Update summary
            self.update_summary_display()
            
            # Force GUI update
            self.tree.update()
            self.root.update()
            
            self.status_var.set(f"Portfolio refreshed - {len(self.stocks)} stocks")
            
        except Exception as e:
            print(f"Error in force refresh: {e}")
            messagebox.showerror("Error", f"Failed to refresh display: {str(e)}")
    
    def edit_stock(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a stock to edit")
            return
        
        try:
            # Get stock symbol from selected row
            item_values = self.tree.item(selected_item[0])['values']
            symbol = item_values[0]
            
            # Find the stock object
            stock = next((s for s in self.stocks if s.symbol == symbol), None)
            if not stock:
                messagebox.showerror("Error", f"Could not find stock data for {symbol}")
                return
            
            # Create edit dialog
            dialog = AddStockDialog(self.root, stock)
            
            # Wait for dialog to complete
            self.root.wait_window(dialog.dialog)
            
            if dialog.result:
                result_data = dialog.result
                
                # Update in database
                self.db_manager.update_stock(
                    stock_id=stock.id,
                    symbol=result_data['symbol'],
                    company_name=result_data.get('company_name', ''),
                    quantity=result_data['quantity'],
                    purchase_price=result_data['purchase_price'],
                    purchase_date=result_data['purchase_date'],
                    broker=result_data.get('broker', '')
                )
                
                # Force refresh
                self._force_refresh()
                
                messagebox.showinfo("Success", f"Updated {symbol}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit stock: {str(e)}")
    
    def delete_stock(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a stock to delete")
            return
        
        try:
            # Get stock symbol from selected row
            item_values = self.tree.item(selected_item[0])['values']
            symbol = item_values[0]
            
            # Confirm deletion
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {symbol} from your portfolio?"):
                # Find the stock object
                stock = next((s for s in self.stocks if s.symbol == symbol), None)
                if stock and stock.id:
                    self.db_manager.delete_stock(stock.id)
                    
                    # Force refresh
                    self._force_refresh()
                    
                    messagebox.showinfo("Success", f"Deleted {symbol} from portfolio")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete stock: {str(e)}")
    
    def export_portfolio(self):
        if not self.stocks:
            messagebox.showinfo("Info", "No stocks to export")
            return
        
        try:
            # Prepare data for export
            export_data = []
            for stock in self.stocks:
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
            
            if FileHelper.export_to_csv(export_data):
                self.status_var.set("Portfolio exported successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export portfolio: {str(e)}")
    
    def on_stock_double_click(self, event):
        self.edit_stock()
    
    def on_user_changed(self, event=None):
        """Handle user selection change"""
        selected_user = self.user_var.get()
        if selected_user and selected_user in self.user_mapping:
            user_id = self.user_mapping[selected_user]
            
            # Set the active user in database
            self.db_manager.set_active_user(user_id)
            
            # Reload portfolio data for the new user
            self.load_portfolio()
            self.update_dashboard()
            
            # Cash balance will be updated when dashboard refreshes
    
    def manage_cash(self):
        """Open cash management dialog"""
        try:
            from gui.cash_management_dialog import CashManagementDialog
            CashManagementDialog(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open cash management: {str(e)}")
    
    def manage_expenses(self):
        """Open expenses management dialog"""
        try:
            from gui.expenses_dialog import ExpensesDialog
            ExpensesDialog(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open expenses management: {str(e)}")
    
    def show_tax_report(self):
        """Open tax report dialog"""
        try:
            from gui.tax_report_dialog import TaxReportDialog
            TaxReportDialog(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open tax report: {str(e)}")
    
    def get_theme_button_text(self):
        """Get appropriate text for the theme button - always light mode now"""
        return "Light Mode"
    
    def toggle_theme(self):
        """Apply light theme only"""
        self.theme_manager.toggle_theme()
        self.apply_theme()
    
    def apply_theme(self):
        """Apply current theme to all widgets"""
        try:
            # Configure TTK styles
            self.theme_manager.configure_ttk_styles(self.root)
            
            # Apply theme to treeview with profit/loss colors
            colors = self.theme_manager.get_theme_colors()
            self.tree.tag_configure("profit", foreground=colors["profit_color"])
            self.tree.tag_configure("loss", foreground=colors["loss_color"])
            self.tree.tag_configure("neutral", foreground=colors["neutral_color"])
            
        except Exception as e:
            print(f"Warning: Could not apply theme: {e}")
    
    def on_search_changed(self, *args):
        """Handle search text changes"""
        self.update_portfolio_display()
    
    def on_sort_changed(self, event=None):
        """Handle sort field changes"""
        self.update_portfolio_display()
    
    def toggle_sort_order(self):
        """Toggle between ascending and descending sort"""
        self.sort_ascending = not self.sort_ascending
        sort_text = "↑ Asc" if self.sort_ascending else "↓ Desc"
        self.sort_order_btn.configure(text=sort_text)
        self.update_portfolio_display()
    
    def clear_search(self):
        """Clear search field and refresh display"""
        self.search_var.set("")
        self.update_portfolio_display()
    
    def filter_and_sort_stocks(self, stocks):
        """Filter stocks by search term and sort them"""
        filtered_stocks = stocks
        
        # Apply search filter
        search_term = self.search_var.get().lower().strip()
        if search_term:
            filtered_stocks = []
            for stock in stocks:
                # Search in symbol, company name
                if (search_term in stock.symbol.lower() or 
                    search_term in (stock.company_name or "").lower()):
                    filtered_stocks.append(stock)
        
        # Apply sorting
        sort_field = self.sort_var.get()
        reverse_sort = not self.sort_ascending
        
        try:
            if sort_field == "symbol":
                filtered_stocks.sort(key=lambda x: x.symbol.lower(), reverse=reverse_sort)
            elif sort_field == "company":
                filtered_stocks.sort(key=lambda x: (x.company_name or "").lower(), reverse=reverse_sort)
            elif sort_field == "profit_loss":
                filtered_stocks.sort(key=lambda x: x.profit_loss_amount, reverse=reverse_sort)
            elif sort_field == "profit_loss_pct":
                filtered_stocks.sort(key=lambda x: x.profit_loss_percentage, reverse=reverse_sort)
            elif sort_field == "current_value":
                filtered_stocks.sort(key=lambda x: x.current_value, reverse=reverse_sort)
            elif sort_field == "days_held":
                filtered_stocks.sort(key=lambda x: x.days_held, reverse=reverse_sort)
        except Exception as e:
            print(f"Warning: Could not sort by {sort_field}: {e}")
        
        return filtered_stocks
    
    
    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()
