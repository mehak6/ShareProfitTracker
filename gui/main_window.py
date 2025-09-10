import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
from typing import List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import DatabaseManager
from data.models import Stock, PortfolioSummary
from services.price_fetcher import PriceFetcher
from services.calculator import PortfolioCalculator
from utils.config import AppConfig
from utils.helpers import FormatHelper, FileHelper
from utils.theme_manager import ThemeManager
try:
    from gui.add_stock_dialog import AddStockDialog
except ImportError:
    from .add_stock_dialog import AddStockDialog

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.db_manager = DatabaseManager(AppConfig.get_database_path())
        self.price_fetcher = PriceFetcher()
        self.calculator = PortfolioCalculator()
        self.theme_manager = ThemeManager()
        
        self.stocks: List[Stock] = []
        self.portfolio_summary: Optional[PortfolioSummary] = None
        self.last_update_time: Optional[datetime] = None
        self.is_updating = False
        
        self.setup_window()
        self.create_widgets()
        self.load_portfolio()
        self.apply_theme()
        
    def setup_window(self):
        self.root.title(f"{AppConfig.APP_NAME} v{AppConfig.APP_VERSION}")
        self.root.geometry(f"{AppConfig.WINDOW_WIDTH}x{AppConfig.WINDOW_HEIGHT}")
        self.root.minsize(AppConfig.MIN_WINDOW_WIDTH, AppConfig.MIN_WINDOW_HEIGHT)
        
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
    
    def create_widgets(self):
        # Header frame
        self.create_header_frame()
        
        # Main content frame
        self.create_main_frame()
        
        # Summary frame
        self.create_summary_frame()
        
        # Status bar
        self.create_status_bar()
    
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
        main_frame.grid(row=1, column=0, sticky="nsew")
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
        
        # Theme Toggle Button
        theme_text = "Dark Mode" if self.theme_manager.current_theme == "light" else "Light Mode"
        self.theme_btn = ttk.Button(buttons_frame, text=theme_text, 
                                   command=self.toggle_theme)
        self.theme_btn.grid(row=0, column=7, padx=(0, 10))
        
        # Tax Report Button
        ttk.Button(buttons_frame, text="Tax Report", 
                  command=self.show_tax_report).grid(row=0, column=8, padx=(0, 10))
    
    def create_summary_frame(self):
        summary_frame = ttk.LabelFrame(self.root, text="Portfolio Summary", padding="10")
        summary_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
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
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief="sunken", padding="5")
        status_bar.grid(row=3, column=0, sticky="ew")
    
    def load_portfolio(self):
        self.status_var.set("Loading portfolio...")
        
        try:
            stock_data = self.db_manager.get_all_stocks()
            self.stocks = [Stock(**data) for data in stock_data]
            
            print(f"DEBUG load_portfolio: Found {len(stock_data)} records in database")
            print(f"DEBUG load_portfolio: Created {len(self.stocks)} stock objects")
            
            self.update_portfolio_display()
            self.update_summary_display()
            
            if self.stocks:
                self.status_var.set(f"Loaded {len(self.stocks)} stocks")
            else:
                self.status_var.set("No stocks in portfolio")
                
        except Exception as e:
            print(f"DEBUG load_portfolio ERROR: {e}")
            messagebox.showerror("Error", f"Failed to load portfolio: {str(e)}")
            self.status_var.set("Error loading portfolio")
    
    def update_portfolio_display(self):
        print(f"DEBUG update_portfolio_display: Updating display with {len(self.stocks)} stocks")
        
        # Clear existing items
        existing_items = self.tree.get_children()
        print(f"DEBUG update_portfolio_display: Clearing {len(existing_items)} existing items")
        for item in existing_items:
            self.tree.delete(item)
        
        # Filter and sort stocks
        try:
            filtered_stocks = self.filter_and_sort_stocks(self.stocks)
        except AttributeError:
            # Fallback if search/sort variables are not initialized yet
            filtered_stocks = self.stocks
        
        print(f"DEBUG update_portfolio_display: Showing {len(filtered_stocks)} filtered stocks")
        
        # Add stocks to table
        for i, stock in enumerate(filtered_stocks):
            print(f"DEBUG update_portfolio_display: Adding stock {i+1}: {stock.symbol}")
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
            
            # Color coding for profit/loss - prepare the values first
            tags = []
            if stock.current_price is not None:
                if stock.profit_loss_amount > 0:
                    tags.append("profit")
                    # Fix the profit/loss display format
                    values[7] = f"+{FormatHelper.format_currency(stock.profit_loss_amount)[1:]}"
                elif stock.profit_loss_amount < 0:
                    tags.append("loss")
            
            # Insert the item with tags
            item = self.tree.insert("", "end", values=values, tags=tags)
            print(f"DEBUG update_portfolio_display: Inserted item {item} for {stock.symbol}")
        
        # Configure tags for colors
        self.tree.tag_configure("profit", foreground=AppConfig.COLORS['profit'])
        self.tree.tag_configure("loss", foreground=AppConfig.COLORS['loss'])
        
        # Force tree update
        self.tree.update_idletasks()
        
        final_items = self.tree.get_children()
        print(f"DEBUG update_portfolio_display: Final tree has {len(final_items)} items")
    
    def update_summary_display(self):
        self.portfolio_summary = self.calculator.calculate_portfolio_summary(self.stocks)
        
        self.total_investment_label.config(
            text=f"Total Investment: {FormatHelper.format_currency(self.portfolio_summary.total_investment)}")
        
        self.current_value_label.config(
            text=f"Current Value: {FormatHelper.format_currency(self.portfolio_summary.current_value)}")
        
        profit_loss_text = f"Total P&L: {FormatHelper.format_currency(self.portfolio_summary.total_profit_loss)} " \
                          f"({FormatHelper.format_percentage(self.portfolio_summary.total_profit_loss_percentage)})"
        
        self.profit_loss_label.config(
            text=profit_loss_text,
            foreground=AppConfig.COLORS[
                'profit' if self.portfolio_summary.total_profit_loss > 0 else 
                'loss' if self.portfolio_summary.total_profit_loss < 0 else 'neutral'
            ]
        )
        
        self.stocks_count_label.config(text=f"Stocks: {self.portfolio_summary.total_stocks}")
        
        # Update cash balance
        try:
            cash_balance = self.db_manager.get_current_cash_balance()
            self.cash_balance_label.config(
                text=f"Available Cash: {FormatHelper.format_currency(cash_balance)}",
                foreground="green" if cash_balance > 0 else "red" if cash_balance < 0 else "black"
            )
        except Exception as e:
            self.cash_balance_label.config(text="Available Cash: ₹0.00")
    
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
        
        # Run price update in background thread
        threading.Thread(target=self._refresh_prices_background, daemon=True).start()
    
    def _refresh_prices_background(self):
        self.is_updating = True
        self.root.after(0, lambda: self.status_var.set("Updating prices..."))
        self.root.after(0, lambda: self.refresh_btn.config(state="disabled"))
        
        try:
            symbols = [stock.symbol for stock in self.stocks]
            prices = self.price_fetcher.get_multiple_prices(symbols)
            
            # Update database and stocks
            for stock in self.stocks:
                if stock.symbol in prices and prices[stock.symbol] is not None:
                    stock.current_price = prices[stock.symbol]
                    self.db_manager.update_price_cache(stock.symbol, stock.current_price)
            
            self.last_update_time = datetime.now()
            
            # Update UI on main thread
            self.root.after(0, self._update_ui_after_refresh)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to update prices: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Error updating prices"))
        
        finally:
            self.is_updating = False
            self.root.after(0, lambda: self.refresh_btn.config(state="normal"))
    
    def _update_ui_after_refresh(self):
        self.update_portfolio_display()
        self.update_summary_display()
        
        update_text = f"Last updated: {self.last_update_time.strftime('%H:%M:%S')}"
        self.update_label.config(text=update_text)
        self.status_var.set("Prices updated successfully")
    
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
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.theme_manager.toggle_theme()
        self.apply_theme()
        
        # Update theme button text
        theme_text = "Dark Mode" if self.theme_manager.current_theme == "light" else "Light Mode"
        self.theme_btn.configure(text=theme_text)
    
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