"""
Refactored MainWindow - Now uses controller architecture
Reduced from 1000+ lines to ~300 lines by extracting business logic
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import new architecture components
from controllers.portfolio_controller import PortfolioController
from data.async_database import AsyncDatabaseManager
from services.unified_price_service import UnifiedPriceService
from data.models import Stock, PortfolioSummary
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


class MainWindowRefactored:
    """
    Refactored MainWindow using controller architecture
    - Business logic moved to PortfolioController
    - Database operations moved to AsyncDatabaseManager  
    - Price fetching unified in PriceService
    - UI focused only on presentation
    """
    
    def __init__(self):
        # Initialize UI components
        self.root = tk.Tk()
        self.theme_manager = ThemeManager()
        
        # Initialize services and controllers
        self.db_manager = AsyncDatabaseManager(AppConfig.get_database_path())
        self.price_service = UnifiedPriceService(cache_ttl=60)
        
        # Initialize controller with callbacks
        self.portfolio_controller = PortfolioController(
            db_manager=self.db_manager,
            price_service=self.price_service
        )
        
        # Set up controller callbacks
        self.portfolio_controller.set_callbacks(
            portfolio_updated=self.on_portfolio_updated,
            status_updated=self.on_status_updated,
            error_callback=self.on_error
        )
        
        # UI state variables (much reduced from original)
        self.search_var = tk.StringVar()
        self.sort_var = tk.StringVar(value="symbol")
        self.sort_ascending = True
        self.user_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.cash_balance_var = tk.StringVar()
        
        # UI components  
        self.tree = None
        self.notifications_panel = None
        self.metric_cards = {}
        
        # Initialize UI
        self.setup_window()
        self.configure_modern_ui()
        self.create_widgets()
        
        # Load initial data
        self.portfolio_controller.load_portfolio()
        self.update_cash_balance()
        self.apply_theme()
    
    def setup_window(self):
        """Configure main window"""
        self.root.title(f"{AppConfig.APP_NAME} v{AppConfig.APP_VERSION}")
        self.root.geometry(f"{AppConfig.WINDOW_WIDTH}x{AppConfig.WINDOW_HEIGHT}")
        self.root.minsize(AppConfig.MIN_WINDOW_WIDTH, AppConfig.MIN_WINDOW_HEIGHT)
        
        # Configure grid weights
        self.root.grid_rowconfigure(2, weight=1)  # Main content area
        self.root.grid_columnconfigure(0, weight=1)
    
    def configure_modern_ui(self):
        """Configure modern UI styling"""
        self.style = ModernUI.configure_style(self.root)
    
    def create_widgets(self):
        """Create all UI widgets"""
        # Modern toolbar
        self.create_modern_toolbar()
        
        # Dashboard
        self.create_dashboard()
        
        # Tabbed interface  
        self.create_tabbed_interface()
        
        # Status bar
        self.create_status_bar()
    
    def create_modern_toolbar(self):
        """Create modern toolbar"""
        self.toolbar_frame, self.toolbar_left, self.toolbar_right = ModernUI.create_modern_toolbar(self.root)
        self.toolbar_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        
        # Connect toolbar buttons
        buttons = self.toolbar_left.winfo_children()
        if len(buttons) >= 3:
            buttons[0].configure(command=self.add_stock)
            buttons[1].configure(command=self.refresh_prices)  
            buttons[2].configure(command=self.export_portfolio)
        
        # User selection
        self.create_user_selection()
        
        # Settings button
        settings_buttons = self.toolbar_right.winfo_children()
        if len(settings_buttons) >= 1:
            settings_buttons[0].configure(command=self.open_settings)
    
    def create_user_selection(self):
        """Create user selection dropdown"""
        user_frame = tk.Frame(self.toolbar_frame)
        user_frame.pack(side='left', fill='x', expand=True, padx=20)
        
        center_frame = tk.Frame(user_frame)
        center_frame.pack(anchor='center')
        
        user_label = tk.Label(center_frame, text="User:", font=("Arial", 9, "bold"))
        user_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Get users and populate dropdown
        users = self.db_manager.get_all_users()
        active_user = self.db_manager.get_active_user()
        
        user_values = [user['display_name'] for user in users]
        if active_user:
            self.user_var.set(active_user['display_name'])
        elif user_values:
            self.user_var.set(user_values[0])
        
        self.user_combobox = ttk.Combobox(center_frame, textvariable=self.user_var,
                                         values=user_values, state="readonly", width=15)
        self.user_combobox.pack(side=tk.LEFT)
        self.user_combobox.bind("<<ComboboxSelected>>", self.on_user_changed)
        
        self.user_mapping = {user['display_name']: user['id'] for user in users}
    
    def create_dashboard(self):
        """Create dashboard with metrics"""
        self.dashboard_frame, self.metrics_frame = ModernUI.create_dashboard_summary(self.root)
        self.dashboard_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 0))
    
    def create_tabbed_interface(self):
        """Create tabbed interface"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=2, column=0, sticky="nsew", padx=10, pady=(10, 0))
        
        # Portfolio tab
        self.portfolio_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.portfolio_frame, text="📊 Portfolio")
        
        # Notifications tab
        self.notifications_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.notifications_frame, text="📢 Notifications")
        
        # Set up content
        self.create_portfolio_tab()
        self.create_notifications_tab()
    
    def create_portfolio_tab(self):
        """Set up portfolio tab"""
        self.portfolio_frame.grid_rowconfigure(0, weight=1)
        self.portfolio_frame.grid_columnconfigure(0, weight=1)
        
        self.create_portfolio_table(self.portfolio_frame)
        self.create_buttons_frame(self.portfolio_frame)
    
    def create_notifications_tab(self):
        """Set up notifications tab"""
        self.notifications_frame.grid_rowconfigure(0, weight=1)
        self.notifications_frame.grid_columnconfigure(0, weight=1)
        
        # Initialize with empty list, will be updated when portfolio loads
        self.notifications_panel = NotificationsPanel(self.notifications_frame, [])
    
    def create_portfolio_table(self, parent):
        """Create portfolio table with search and filters"""
        container_frame = ttk.Frame(parent)
        container_frame.grid(row=0, column=0, sticky="nsew")
        container_frame.grid_rowconfigure(1, weight=1)
        container_frame.grid_columnconfigure(0, weight=1)
        
        # Search and filter frame
        search_frame = ttk.Frame(container_frame)
        search_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        search_frame.grid_columnconfigure(1, weight=1)
        
        # Search controls
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.search_var.trace("w", self.on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        
        # Sort controls
        ttk.Label(search_frame, text="Sort by:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        sort_options = ["symbol", "company", "profit_loss", "profit_loss_pct", "current_value", "days_held"]
        sort_combo = ttk.Combobox(search_frame, textvariable=self.sort_var, values=sort_options,
                                 state="readonly", width=12)
        sort_combo.grid(row=0, column=3, padx=(0, 10))
        sort_combo.bind("<<ComboboxSelected>>", self.on_sort_changed)
        
        # Sort order button
        self.sort_order_btn = ttk.Button(search_frame, text="↑ Asc", command=self.toggle_sort_order)
        self.sort_order_btn.grid(row=0, column=4, padx=(0, 10))
        
        # Clear button
        ttk.Button(search_frame, text="Clear", command=self.clear_search).grid(row=0, column=5)
        
        # Create treeview
        tree_frame = ttk.Frame(container_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Portfolio table
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
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Bind double-click
        self.tree.bind("<Double-1>", self.on_stock_double_click)
    
    def create_buttons_frame(self, parent):
        """Create action buttons"""
        buttons_frame = ttk.Frame(parent, padding="10")
        buttons_frame.grid(row=1, column=0, sticky="ew")
        
        buttons = [
            ("Add Stock", self.add_stock),
            ("Edit Stock", self.edit_stock),
            ("Delete Stock", self.delete_stock),
            ("Refresh Portfolio", self.refresh_portfolio),
            ("Export CSV", self.export_portfolio),
            ("Cash I Have", self.manage_cash),
            ("Other Funds", self.manage_expenses),
            ("Tax Report", self.show_tax_report)
        ]
        
        for i, (text, command) in enumerate(buttons):
            ttk.Button(buttons_frame, text=text, command=command).grid(
                row=0, column=i, padx=(0, 10)
            )
    
    def create_status_bar(self):
        """Create status bar"""
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        status_frame.grid_columnconfigure(0, weight=1)
        
        # Status message
        self.status_var.set("Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                               relief="sunken", padding="5")
        status_label.grid(row=0, column=0, sticky="ew")
        
        # Cash balance
        self.cash_balance_var.set("Available Cash: ₹0.00")
        cash_label = ttk.Label(status_frame, textvariable=self.cash_balance_var,
                             relief="sunken", padding="5", font=("Arial", 10, "bold"))
        cash_label.grid(row=0, column=1, sticky="e", padx=(10, 0))
    
    # Controller callback methods
    def on_portfolio_updated(self):
        """Called when portfolio data is updated"""
        self.update_portfolio_display()
        self.update_dashboard()
        
        # Update notifications panel
        if self.notifications_panel:
            stocks = self.portfolio_controller.get_stocks()
            self.notifications_panel.update_stocks(stocks)
    
    def on_status_updated(self, message: str):
        """Called when status message changes"""
        self.status_var.set(message)
    
    def on_error(self, error_message: str):
        """Called when an error occurs"""
        messagebox.showerror("Error", error_message)
    
    # UI update methods (simplified from original)
    def update_portfolio_display(self):
        """Update portfolio table display"""
        # Get filtered and sorted stocks from controller
        search_term = self.search_var.get()
        sort_field = self.sort_var.get()
        
        filtered_stocks = self.portfolio_controller.get_filtered_sorted_stocks(
            search_term=search_term,
            sort_field=sort_field,
            ascending=self.sort_ascending
        )
        
        # Clear and repopulate tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for stock in filtered_stocks:
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
            
            # Apply profit/loss coloring
            tags = []
            if stock.current_price is not None:
                if stock.profit_loss_amount > 0:
                    tags.append("profit")
                    values[8] = f"+{FormatHelper.format_currency(stock.profit_loss_amount)[1:]}"
                elif stock.profit_loss_amount < 0:
                    tags.append("loss")
            
            self.tree.insert("", "end", values=values, tags=tags)
        
        # Configure tag colors
        self.tree.tag_configure("profit", foreground=AppConfig.COLORS['profit'])
        self.tree.tag_configure("loss", foreground=AppConfig.COLORS['loss'])
    
    def update_dashboard(self):
        """Update dashboard metrics"""
        # Clear existing cards
        for card in self.metric_cards.values():
            card.destroy()
        self.metric_cards.clear()
        
        # Get metrics from controller
        stocks = self.portfolio_controller.get_stocks()
        metrics = MetricCalculator.calculate_portfolio_metrics(stocks)
        
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
        
        # Configure column weights
        for i in range(len(cards_data)):
            self.metrics_frame.grid_columnconfigure(i, weight=1)
    
    def update_cash_balance(self):
        """Update cash balance display"""
        try:
            balance = self.db_manager.get_current_cash_balance()
            self.cash_balance_var.set(f"Available Cash: {FormatHelper.format_currency(balance)}")
        except Exception as e:
            self.cash_balance_var.set("Available Cash: ₹0.00")
    
    # Action methods (simplified - delegate to controller)
    def add_stock(self):
        """Add new stock"""
        try:
            dialog = AddStockDialog(self.root)
            self.root.wait_window(dialog.dialog)
            
            if dialog.result:
                success = self.portfolio_controller.add_stock(dialog.result)
                if success:
                    messagebox.showinfo("Success", f"Added {dialog.result['symbol']} to portfolio")
                    self.update_cash_balance()
        except Exception as e:
            self.on_error(f"Failed to add stock: {str(e)}")
    
    def edit_stock(self):
        """Edit selected stock"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a stock to edit")
            return
        
        try:
            # Get stock symbol from selected row
            item_values = self.tree.item(selected_item[0])['values']
            symbol = item_values[0]
            
            # Find stock object
            stock = self.portfolio_controller.find_stock_by_symbol(symbol)
            if not stock:
                messagebox.showerror("Error", f"Could not find stock data for {symbol}")
                return
            
            # Create edit dialog
            dialog = AddStockDialog(self.root, stock)
            self.root.wait_window(dialog.dialog)
            
            if dialog.result:
                success = self.portfolio_controller.update_stock(stock.id, dialog.result)
                if success:
                    messagebox.showinfo("Success", f"Updated {symbol}")
        except Exception as e:
            self.on_error(f"Failed to edit stock: {str(e)}")
    
    def delete_stock(self):
        """Delete selected stock"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a stock to delete")
            return
        
        try:
            item_values = self.tree.item(selected_item[0])['values']
            symbol = item_values[0]
            
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {symbol}?"):
                stock = self.portfolio_controller.find_stock_by_symbol(symbol)
                if stock:
                    success = self.portfolio_controller.delete_stock(stock.id, symbol)
                    if success:
                        messagebox.showinfo("Success", f"Deleted {symbol}")
        except Exception as e:
            self.on_error(f"Failed to delete stock: {str(e)}")
    
    def refresh_prices(self):
        """Refresh stock prices"""
        if self.portfolio_controller.is_updating():
            self.on_status_updated("Price update already in progress...")
            return
        
        def refresh_callback(success: bool, message: str):
            if success:
                self.update_cash_balance()
        
        self.portfolio_controller.refresh_prices_async(callback=refresh_callback)
    
    def refresh_portfolio(self):
        """Refresh entire portfolio"""
        self.portfolio_controller.load_portfolio()
        self.update_cash_balance()
    
    def export_portfolio(self):
        """Export portfolio to CSV"""
        try:
            export_data = self.portfolio_controller.export_portfolio_data()
            if export_data and FileHelper.export_to_csv(export_data):
                self.on_status_updated("Portfolio exported successfully")
            else:
                self.on_status_updated("No data to export")
        except Exception as e:
            self.on_error(f"Failed to export portfolio: {str(e)}")
    
    # Event handlers
    def on_stock_double_click(self, event):
        """Handle double-click on stock"""
        self.edit_stock()
    
    def on_user_changed(self, event=None):
        """Handle user selection change"""
        selected_user = self.user_var.get()
        if selected_user and selected_user in self.user_mapping:
            user_id = self.user_mapping[selected_user]
            self.db_manager.set_active_user(user_id)
            self.portfolio_controller.load_portfolio()
            self.update_cash_balance()
    
    def on_search_changed(self, *args):
        """Handle search text changes"""
        self.update_portfolio_display()
    
    def on_sort_changed(self, event=None):
        """Handle sort field changes"""
        self.update_portfolio_display()
    
    def toggle_sort_order(self):
        """Toggle sort order"""
        self.sort_ascending = not self.sort_ascending
        sort_text = "↑ Asc" if self.sort_ascending else "↓ Desc"
        self.sort_order_btn.configure(text=sort_text)
        self.update_portfolio_display()
    
    def clear_search(self):
        """Clear search field"""
        self.search_var.set("")
    
    # Dialog methods (delegate to original implementations)
    def manage_cash(self):
        """Open cash management dialog"""
        try:
            from gui.cash_management_dialog import CashManagementDialog
            CashManagementDialog(self.root)
            self.update_cash_balance()
        except Exception as e:
            self.on_error(f"Failed to open cash management: {str(e)}")
    
    def manage_expenses(self):
        """Open expenses dialog"""
        try:
            from gui.expenses_dialog import ExpensesDialog
            ExpensesDialog(self.root)
        except Exception as e:
            self.on_error(f"Failed to open expenses management: {str(e)}")
    
    def show_tax_report(self):
        """Open tax report dialog"""
        try:
            from gui.tax_report_dialog import TaxReportDialog
            TaxReportDialog(self.root)
        except Exception as e:
            self.on_error(f"Failed to open tax report: {str(e)}")
    
    def open_settings(self):
        """Open settings dialog"""
        try:
            from gui.settings_dialog import SettingsDialog
            SettingsDialog(self.root)
        except Exception as e:
            self.on_error(f"Failed to open settings: {str(e)}")
    
    def apply_theme(self):
        """Apply current theme"""
        try:
            self.theme_manager.configure_ttk_styles(self.root)
            colors = self.theme_manager.get_theme_colors()
            self.tree.tag_configure("profit", foreground=colors["profit_color"])
            self.tree.tag_configure("loss", foreground=colors["loss_color"])
        except Exception as e:
            print(f"Warning: Could not apply theme: {e}")
    
    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()
        finally:
            # Clean up resources
            if hasattr(self.db_manager, 'close'):
                self.db_manager.close()


# For testing the refactored version
if __name__ == "__main__":
    app = MainWindowRefactored()
    app.run()