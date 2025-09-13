import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.models import Stock
from data.enhanced_stock_symbols import search_stocks, get_company_name
from utils.helpers import ValidationHelper
try:
    from gui.autocomplete_entry import AutocompleteEntry
except ImportError:
    from .autocomplete_entry import AutocompleteEntry

class AddStockDialog:
    def __init__(self, parent, stock: Optional[Stock] = None):
        self.parent = parent
        self.stock = stock
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.setup_dialog()
        self.create_widgets()
        self.populate_fields()
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.center_dialog()
        
        # Focus on first input
        self.symbol_autocomplete.focus()
    
    def setup_dialog(self):
        title = "Edit Stock" if self.stock else "Add Stock"
        self.dialog.title(title)
        self.dialog.geometry("600x400")  # Wider to accommodate autocomplete
        self.dialog.resizable(True, False)  # Allow horizontal resize
        
        # Configure grid weights
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Symbol with autocomplete
        ttk.Label(main_frame, text="Stock Symbol:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.symbol_autocomplete = AutocompleteEntry(
            main_frame, 
            search_function=search_stocks,
            on_selection=self.on_symbol_selected,
            width=25
        )
        self.symbol_autocomplete.grid(row=0, column=1, sticky="ew", pady=(0, 5))
        
        # Helper text
        helper_label = ttk.Label(main_frame, text="Type to search (e.g., RELIANCE, TCS, AAPL)", 
                                font=("Arial", 8), foreground="gray")
        helper_label.grid(row=0, column=2, sticky="w", padx=(10, 0), pady=(0, 5))
        
        # Company Name
        ttk.Label(main_frame, text="Company Name:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        self.company_var = tk.StringVar()
        self.company_entry = ttk.Entry(main_frame, textvariable=self.company_var, width=30)
        self.company_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))
        
        # Quantity
        ttk.Label(main_frame, text="Quantity:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.quantity_var = tk.StringVar()
        self.quantity_entry = ttk.Entry(main_frame, textvariable=self.quantity_var, width=20)
        self.quantity_entry.grid(row=2, column=1, sticky="ew", pady=(0, 5))
        
        # Purchase Price
        ttk.Label(main_frame, text="Purchase Price:").grid(row=3, column=0, sticky="w", pady=(0, 5))
        self.price_var = tk.StringVar()
        price_frame = ttk.Frame(main_frame)
        price_frame.grid(row=3, column=1, sticky="ew", pady=(0, 5))
        ttk.Label(price_frame, text="Rs.").pack(side="left")
        self.price_entry = ttk.Entry(price_frame, textvariable=self.price_var, width=15)
        self.price_entry.pack(side="left", fill="x", expand=True)
        
        # Purchase Date
        ttk.Label(main_frame, text="Purchase Date:").grid(row=4, column=0, sticky="w", pady=(0, 5))
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=4, column=1, sticky="ew", pady=(0, 5))
        
        self.date_var = tk.StringVar()
        self.date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=12)
        self.date_entry.pack(side="left")
        
        ttk.Label(date_frame, text=" (YYYY-MM-DD)").pack(side="left")
        
        today_btn = ttk.Button(date_frame, text="Today", command=self.set_today_date)
        today_btn.pack(side="right")
        
        # Broker (optional)
        ttk.Label(main_frame, text="Broker (optional):").grid(row=5, column=0, sticky="w", pady=(0, 15))
        self.broker_var = tk.StringVar()
        self.broker_entry = ttk.Entry(main_frame, textvariable=self.broker_var, width=30)
        self.broker_entry.grid(row=5, column=1, sticky="ew", pady=(0, 15))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save_stock).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side="left")
        
        # Configure column weights
        main_frame.grid_columnconfigure(1, weight=2)  # Entry column gets more space
        main_frame.grid_columnconfigure(2, weight=1)  # Helper text column
        
        # Bind Enter key to save
        self.dialog.bind('<Return>', lambda e: self.save_stock())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
    
    def on_symbol_selected(self, symbol: str, company: str):
        """Callback when a stock symbol is selected from autocomplete"""
        # Set company name immediately for better UX
        if company:
            self.company_var.set(company)
        else:
            # Try to get company name asynchronously to avoid blocking
            import threading
            def get_company_async():
                try:
                    from data.enhanced_stock_symbols import get_company_name
                    company_name = get_company_name(symbol)
                    if company_name:
                        self.dialog.after(0, lambda: self.company_var.set(company_name))
                except Exception as e:
                    print(f"Could not fetch company name: {e}")
            
            threading.Thread(target=get_company_async, daemon=True).start()
        
        # Move focus to quantity field immediately
        self.quantity_entry.focus()
    
    def populate_fields(self):
        if self.stock:
            self.symbol_autocomplete.set(self.stock.symbol)
            self.company_var.set(self.stock.company_name or "")
            self.quantity_var.set(str(self.stock.quantity))
            self.price_var.set(str(self.stock.purchase_price))
            self.date_var.set(self.stock.purchase_date)
            self.broker_var.set(self.stock.broker or "")
        else:
            # Set default date to today
            self.set_today_date()
    
    def set_today_date(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self.date_var.set(today)
    
    def center_dialog(self):
        # Update dialog to ensure it has the correct size
        self.dialog.update_idletasks()
        
        # Calculate position
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def validate_input(self) -> bool:
        # Validate symbol
        symbol = self.symbol_autocomplete.get().strip().upper()
        if not ValidationHelper.validate_stock_symbol(symbol):
            messagebox.showerror("Validation Error", 
                               "Please enter a valid stock symbol (e.g., RELIANCE.NS, TCS.NS)")
            self.symbol_autocomplete.focus()
            return False
        
        # Validate quantity
        quantity_str = self.quantity_var.get().strip()
        if not ValidationHelper.validate_positive_number(quantity_str):
            messagebox.showerror("Validation Error", 
                               "Please enter a valid positive quantity")
            self.quantity_entry.focus()
            return False
        
        # Validate price
        price_str = self.price_var.get().strip()
        if not ValidationHelper.validate_positive_number(price_str):
            messagebox.showerror("Validation Error", 
                               "Please enter a valid positive purchase price")
            self.price_entry.focus()
            return False
        
        # Validate date
        date_str = self.date_var.get().strip()
        if not ValidationHelper.validate_date(date_str):
            messagebox.showerror("Validation Error", 
                               "Please enter a valid date in YYYY-MM-DD format")
            self.date_entry.focus()
            return False
        
        # Check if date is not in the future
        try:
            purchase_date = datetime.strptime(date_str, "%Y-%m-%d")
            if purchase_date.date() > datetime.now().date():
                messagebox.showerror("Validation Error", 
                                   "Purchase date cannot be in the future")
                self.date_entry.focus()
                return False
        except ValueError:
            pass  # Already handled above
        
        return True
    
    def save_stock(self):
        if not self.validate_input():
            return
        
        # Show saving indicator
        self.dialog.config(cursor="wait")
        
        def save_async():
            try:
                # Prepare result data
                symbol = self.symbol_autocomplete.get().strip().upper()
                company_name = self.company_var.get().strip()
                
                # Auto-fill company name if not provided (non-blocking)
                if not company_name:
                    try:
                        company_name = get_company_name(symbol)
                    except Exception:
                        company_name = None  # Don't block on company name fetch
                
                result = {
                    'symbol': symbol,
                    'company_name': company_name or None,
                    'quantity': float(self.quantity_var.get().strip()),
                    'purchase_price': float(self.price_var.get().strip()),
                    'purchase_date': self.date_var.get().strip(),
                    'broker': self.broker_var.get().strip() or ""
                }
                
                # Update UI on main thread
                self.dialog.after(0, lambda: self._finish_save(result))
                
            except Exception as e:
                self.dialog.after(0, lambda: messagebox.showerror("Error", f"Failed to process input: {str(e)}"))
                self.dialog.after(0, lambda: self.dialog.config(cursor=""))
        
        # Run save in background thread for better performance
        import threading
        threading.Thread(target=save_async, daemon=True).start()
    
    def _finish_save(self, result):
        """Complete the save operation on the main thread"""
        self.result = result
        self.dialog.config(cursor="")
        self.dialog.destroy()
    
    def cancel(self):
        self.result = None
        self.dialog.destroy()