import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import DatabaseManager
from utils.helpers import FormatHelper
from gui.date_picker import DatePickerEntry
from data.enhanced_stock_symbols import get_all_nse_stocks

class StockAdjustmentDialog:
    def __init__(self, parent):
        self.parent = parent
        self.db_manager = DatabaseManager()
        
        self.dialog = tk.Toplevel(parent)
        self.setup_dialog()
        self.create_widgets()
        self.load_adjustment_data()
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.center_dialog()
    
    def setup_dialog(self):
        self.dialog.title("Stock Splits & Bonus Adjustments")
        self.dialog.geometry("900x650")
        self.dialog.resizable(True, True)
        
        # Configure grid weights
        self.dialog.grid_rowconfigure(2, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
    
    def create_widgets(self):
        # Header frame
        header_frame = ttk.Frame(self.dialog, padding="20")
        header_frame.grid(row=0, column=0, sticky="ew")
        
        title_label = ttk.Label(header_frame, text="Stock Splits & Bonus Issues", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        info_label = ttk.Label(header_frame,
                              text="Track stock splits and bonus issues. Split ratios automatically adjust your holdings.",
                              font=("Arial", 9))
        info_label.pack(pady=(5, 0))
        
        # Separator
        ttk.Separator(self.dialog, orient="horizontal").grid(row=1, column=0, sticky="ew", padx=20)
        
        # Main content frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=2, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Add adjustment frame
        add_frame = ttk.LabelFrame(main_frame, text="Add Stock Adjustment", padding="15")
        add_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        # Form fields
        row = 0
        
        # Stock symbol
        ttk.Label(add_frame, text="Stock Symbol:").grid(row=row, column=0, sticky="w", padx=(0, 10))
        self.symbol_var = tk.StringVar()
        self.symbol_entry = ttk.Entry(add_frame, textvariable=self.symbol_var, width=15)
        self.symbol_entry.grid(row=row, column=1, sticky="ew", padx=(0, 20))
        self.symbol_entry.bind('<FocusOut>', self.load_current_holdings)
        
        # Adjustment type
        ttk.Label(add_frame, text="Type:").grid(row=row, column=2, sticky="w", padx=(0, 10))
        self.adj_type_var = tk.StringVar(value="split")
        type_combo = ttk.Combobox(add_frame, textvariable=self.adj_type_var,
                                 values=["split", "bonus", "rights"], state="readonly", width=12)
        type_combo.grid(row=row, column=3, sticky="ew")
        type_combo.bind('<<ComboboxSelected>>', self.on_type_change)
        
        row += 1
        
        # Adjustment date
        ttk.Label(add_frame, text="Date:").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        self.adj_date_picker = DatePickerEntry(add_frame)
        self.adj_date_picker.grid(row=row, column=1, sticky="w", padx=(0, 20), pady=(10, 0))
        
        # Ratio
        ttk.Label(add_frame, text="Ratio:").grid(row=row, column=2, sticky="w", padx=(0, 10), pady=(10, 0))
        ratio_frame = ttk.Frame(add_frame)
        ratio_frame.grid(row=row, column=3, sticky="ew", pady=(10, 0))
        
        self.ratio_from_var = tk.StringVar(value="1")
        self.ratio_to_var = tk.StringVar(value="2")
        
        ttk.Entry(ratio_frame, textvariable=self.ratio_from_var, width=4).pack(side="left")
        ttk.Label(ratio_frame, text=" : ").pack(side="left")
        ttk.Entry(ratio_frame, textvariable=self.ratio_to_var, width=4).pack(side="left")
        ttk.Label(ratio_frame, text=" (old:new)").pack(side="left", padx=(5, 0))
        
        row += 1
        
        # Current holdings display
        ttk.Label(add_frame, text="Current Holdings:").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        self.holdings_var = tk.StringVar(value="Select symbol to view holdings")
        holdings_label = ttk.Label(add_frame, textvariable=self.holdings_var, font=("Arial", 9))
        holdings_label.grid(row=row, column=1, columnspan=2, sticky="w", padx=(0, 20), pady=(10, 0))
        
        row += 1
        
        # Description
        ttk.Label(add_frame, text="Description:").grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=(10, 0))
        self.desc_var = tk.StringVar()
        desc_entry = ttk.Entry(add_frame, textvariable=self.desc_var, width=40)
        desc_entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(0, 20), pady=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(add_frame)
        button_frame.grid(row=row, column=3, pady=(10, 0))
        
        ttk.Button(button_frame, text="Add & Apply",
                  command=self.add_and_apply_adjustment).pack(side="top", fill="x", pady=(0, 5))
        ttk.Button(button_frame, text="Add Only",
                  command=self.add_adjustment).pack(side="top", fill="x")
        
        # Configure grid weights
        add_frame.grid_columnconfigure(1, weight=1)
        add_frame.grid_columnconfigure(3, weight=1)
        
        # Adjustments list frame
        list_frame = ttk.LabelFrame(main_frame, text="Adjustment History", padding="15")
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview
        columns = ("symbol", "type", "date", "ratio", "description", "applied")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        # Configure columns
        self.tree.heading("symbol", text="Symbol")
        self.tree.heading("type", text="Type")
        self.tree.heading("date", text="Date")
        self.tree.heading("ratio", text="Ratio")
        self.tree.heading("description", text="Description")
        self.tree.heading("applied", text="Applied")
        
        self.tree.column("symbol", width=80)
        self.tree.column("type", width=80)
        self.tree.column("date", width=100)
        self.tree.column("ratio", width=100)
        self.tree.column("description", width=300)
        self.tree.column("applied", width=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Bottom buttons
        bottom_frame = ttk.Frame(list_frame)
        bottom_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky="ew")
        
        ttk.Button(bottom_frame, text="Apply Selected",
                  command=self.apply_selected_adjustment).pack(side="left", padx=(0, 10))
        ttk.Button(bottom_frame, text="Delete Selected",
                  command=self.delete_adjustment).pack(side="left", padx=(0, 10))
        ttk.Button(bottom_frame, text="Close",
                  command=self.close_dialog).pack(side="right")
    
    def center_dialog(self):
        self.dialog.update_idletasks()
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def on_type_change(self, event=None):
        """Update description based on adjustment type"""
        adj_type = self.adj_type_var.get()
        symbol = self.symbol_var.get().upper()
        
        if adj_type == "split":
            self.desc_var.set(f"{symbol} Stock Split")
        elif adj_type == "bonus":
            self.desc_var.set(f"{symbol} Bonus Issue")
        else:
            self.desc_var.set(f"{symbol} Rights Issue")
    
    def load_current_holdings(self, event=None):
        """Load current holdings for selected symbol"""
        symbol = self.symbol_var.get().upper()
        if not symbol:
            return
        
        try:
            stocks = self.db_manager.get_all_stocks()
            symbol_holdings = [s for s in stocks if s['symbol'] == symbol]
            
            if symbol_holdings:
                total_shares = sum(s['quantity'] for s in symbol_holdings)
                avg_price = sum(s['quantity'] * s['purchase_price'] for s in symbol_holdings) / total_shares
                self.holdings_var.set(f"{total_shares:.0f} shares @ avg Rs.{avg_price:.2f}")
            else:
                self.holdings_var.set("No holdings found for this symbol")
                
            self.on_type_change()  # Update description
            
        except Exception as e:
            self.holdings_var.set("Error loading holdings")
    
    def add_adjustment(self):
        """Add adjustment without applying to holdings"""
        try:
            symbol = self.symbol_var.get().strip().upper()
            if not symbol:
                messagebox.showerror("Error", "Please enter a stock symbol")
                return
            
            adj_type = self.adj_type_var.get()
            adj_date = self.adj_date_picker.get()
            description = self.desc_var.get().strip()
            
            if not adj_date:
                messagebox.showerror("Error", "Please select adjustment date")
                return
            
            try:
                ratio_from = int(self.ratio_from_var.get())
                ratio_to = int(self.ratio_to_var.get())
                
                if ratio_from <= 0 or ratio_to <= 0:
                    raise ValueError("Ratios must be positive")
                    
            except ValueError as e:
                messagebox.showerror("Error", "Please enter valid positive integers for ratio")
                return
            
            # Add to database
            self.db_manager.add_stock_adjustment(
                symbol=symbol,
                adjustment_type=adj_type,
                adjustment_date=adj_date,
                ratio_from=ratio_from,
                ratio_to=ratio_to,
                description=description
            )
            
            self.clear_form()
            self.load_adjustment_data()
            
            messagebox.showinfo("Success", "Adjustment added successfully (not applied to holdings)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add adjustment: {str(e)}")
    
    def add_and_apply_adjustment(self):
        """Add adjustment and immediately apply to holdings"""
        try:
            symbol = self.symbol_var.get().strip().upper()
            if not symbol:
                messagebox.showerror("Error", "Please enter a stock symbol")
                return
            
            # Check if holdings exist
            stocks = self.db_manager.get_all_stocks()
            symbol_holdings = [s for s in stocks if s['symbol'] == symbol]
            
            if not symbol_holdings:
                messagebox.showwarning("Warning", 
                                     f"No holdings found for {symbol}. Adding adjustment without applying.")
                self.add_adjustment()
                return
            
            adj_type = self.adj_type_var.get()
            
            try:
                ratio_from = int(self.ratio_from_var.get())
                ratio_to = int(self.ratio_to_var.get())
            except ValueError:
                messagebox.showerror("Error", "Please enter valid positive integers for ratio")
                return
            
            # Confirm application
            total_shares = sum(s['quantity'] for s in symbol_holdings)
            new_shares = total_shares * (ratio_to / ratio_from)
            
            if messagebox.askyesno("Confirm Application",
                                 f"This will adjust {symbol} holdings:\n"
                                 f"Current: {total_shares:.0f} shares\n"
                                 f"After {adj_type}: {new_shares:.0f} shares\n\n"
                                 f"Continue?"):
                
                # Add adjustment first
                self.add_adjustment()
                
                # Apply to holdings
                if adj_type in ["split", "bonus"]:
                    self.db_manager.apply_stock_split_to_holdings(symbol, ratio_from, ratio_to)
                    messagebox.showinfo("Success", 
                                      f"Adjustment applied successfully!\n"
                                      f"Holdings updated: {total_shares:.0f} → {new_shares:.0f} shares")
                else:
                    messagebox.showinfo("Success", 
                                      "Rights issue adjustment added. "
                                      "You may need to manually update holdings.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply adjustment: {str(e)}")
    
    def apply_selected_adjustment(self):
        """Apply a previously added adjustment to holdings"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an adjustment to apply")
            return
        
        try:
            selected_tree_item = selected_item[0]
            if selected_tree_item not in self.adjustment_map:
                messagebox.showerror("Error", "Adjustment ID not found")
                return
            
            adjustment_id = self.adjustment_map[selected_tree_item]
            adjustments = self.db_manager.get_stock_adjustments()
            adjustment = next((a for a in adjustments if a['id'] == adjustment_id), None)
            
            if not adjustment:
                messagebox.showerror("Error", "Adjustment not found")
                return
            
            symbol = adjustment['symbol']
            adj_type = adjustment['adjustment_type']
            ratio_from = adjustment['ratio_from']
            ratio_to = adjustment['ratio_to']
            
            # Check holdings
            stocks = self.db_manager.get_all_stocks()
            symbol_holdings = [s for s in stocks if s['symbol'] == symbol]
            
            if not symbol_holdings:
                messagebox.showwarning("Warning", f"No current holdings found for {symbol}")
                return
            
            total_shares = sum(s['quantity'] for s in symbol_holdings)
            new_shares = total_shares * (ratio_to / ratio_from)
            
            if messagebox.askyesno("Confirm Application",
                                 f"Apply {adj_type} adjustment to {symbol}?\n"
                                 f"Current: {total_shares:.0f} shares\n"
                                 f"After: {new_shares:.0f} shares"):
                
                if adj_type in ["split", "bonus"]:
                    self.db_manager.apply_stock_split_to_holdings(symbol, ratio_from, ratio_to)
                    messagebox.showinfo("Success", "Adjustment applied to holdings")
                else:
                    messagebox.showinfo("Info", 
                                      "Rights issue noted. Please manually update holdings as needed.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply adjustment: {str(e)}")
    
    def clear_form(self):
        """Clear form inputs"""
        self.symbol_var.set("")
        self.adj_type_var.set("split")
        self.adj_date_picker.set(datetime.now().strftime("%Y-%m-%d"))
        self.ratio_from_var.set("1")
        self.ratio_to_var.set("2")
        self.desc_var.set("")
        self.holdings_var.set("Select symbol to view holdings")
    
    def load_adjustment_data(self):
        try:
            # Clear tree
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Load adjustments
            adjustments = self.db_manager.get_stock_adjustments()
            self.adjustment_map = {}
            
            for adjustment in adjustments:
                values = [
                    adjustment['symbol'],
                    adjustment['adjustment_type'].title(),
                    adjustment['adjustment_date'],
                    f"{adjustment['ratio_from']}:{adjustment['ratio_to']}",
                    adjustment['description'] or "",
                    "Yes" if adjustment['shares_after'] else "No"
                ]
                
                tags = [adjustment['adjustment_type']]
                item = self.tree.insert("", "end", values=values, tags=tags)
                self.adjustment_map[item] = adjustment['id']
            
            # Configure tags
            self.tree.tag_configure("split", foreground="blue")
            self.tree.tag_configure("bonus", foreground="green")
            self.tree.tag_configure("rights", foreground="orange")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load adjustment data: {str(e)}")
    
    def delete_adjustment(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an adjustment to delete")
            return
        
        try:
            selected_tree_item = selected_item[0]
            if selected_tree_item not in self.adjustment_map:
                messagebox.showerror("Error", "Adjustment ID not found")
                return
            
            adjustment_id = self.adjustment_map[selected_tree_item]
            item_values = self.tree.item(selected_tree_item)['values']
            symbol = item_values[0]
            adj_type = item_values[1]
            date = item_values[2]
            
            if messagebox.askyesno("Confirm Delete",
                                 f"Delete {adj_type} adjustment for {symbol} on {date}?\n"
                                 f"Note: This won't reverse any applied changes to holdings."):
                
                self.db_manager.delete_stock_adjustment(adjustment_id)
                self.load_adjustment_data()
                messagebox.showinfo("Success", "Adjustment deleted successfully")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete adjustment: {str(e)}")
    
    def close_dialog(self):
        self.dialog.destroy()