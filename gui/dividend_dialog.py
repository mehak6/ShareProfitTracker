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
from data.enhanced_stock_symbols import get_all_nse_stocks, get_company_name

class DividendDialog:
    def __init__(self, parent):
        self.parent = parent
        self.db_manager = DatabaseManager()
        
        self.dialog = tk.Toplevel(parent)
        self.setup_dialog()
        self.create_widgets()
        self.load_dividend_data()
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.center_dialog()
    
    def setup_dialog(self):
        self.dialog.title("Dividend Tracking")
        self.dialog.geometry("1000x700")
        self.dialog.resizable(True, True)
        
        # Configure grid weights
        self.dialog.grid_rowconfigure(2, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
    
    def create_widgets(self):
        # Header frame
        header_frame = ttk.Frame(self.dialog, padding="20")
        header_frame.grid(row=0, column=0, sticky="ew")
        
        # Title and summary
        title_label = ttk.Label(header_frame, text="Dividend Tracking", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        self.summary_var = tk.StringVar()
        summary_label = ttk.Label(header_frame, textvariable=self.summary_var,
                                 font=("Arial", 10))
        summary_label.pack(pady=(5, 0))
        
        # Separator
        ttk.Separator(self.dialog, orient="horizontal").grid(row=1, column=0, sticky="ew", padx=20)
        
        # Main content frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=2, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Add dividend frame
        add_frame = ttk.LabelFrame(main_frame, text="Add Dividend", padding="15")
        add_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        # Create form fields in a grid
        row = 0
        
        # Stock symbol with autocomplete
        ttk.Label(add_frame, text="Stock Symbol:").grid(row=row, column=0, sticky="w", padx=(0, 10))
        self.symbol_var = tk.StringVar()
        self.symbol_entry = ttk.Entry(add_frame, textvariable=self.symbol_var, width=15)
        self.symbol_entry.grid(row=row, column=1, sticky="ew", padx=(0, 20))
        self.symbol_entry.bind('<FocusOut>', self.on_symbol_change)
        
        # Company name (auto-filled)
        ttk.Label(add_frame, text="Company:").grid(row=row, column=2, sticky="w", padx=(0, 10))
        self.company_var = tk.StringVar()
        self.company_entry = ttk.Entry(add_frame, textvariable=self.company_var, width=25)
        self.company_entry.grid(row=row, column=3, sticky="ew")
        
        row += 1
        
        # Dividend per share
        ttk.Label(add_frame, text="Dividend/Share:").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        self.dps_var = tk.StringVar()
        dps_frame = ttk.Frame(add_frame)
        dps_frame.grid(row=row, column=1, sticky="ew", padx=(0, 20), pady=(10, 0))
        ttk.Label(dps_frame, text="Rs.").pack(side="left")
        ttk.Entry(dps_frame, textvariable=self.dps_var, width=10).pack(side="left", fill="x", expand=True)
        
        # Shares held
        ttk.Label(add_frame, text="Shares Held:").grid(row=row, column=2, sticky="w", padx=(0, 10), pady=(10, 0))
        self.shares_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.shares_var, width=15).grid(row=row, column=3, sticky="ew", pady=(10, 0))
        
        row += 1
        
        # Total dividend (auto-calculated)
        ttk.Label(add_frame, text="Total Dividend:").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        self.total_div_var = tk.StringVar()
        total_frame = ttk.Frame(add_frame)
        total_frame.grid(row=row, column=1, sticky="ew", padx=(0, 20), pady=(10, 0))
        ttk.Label(total_frame, text="Rs.").pack(side="left")
        self.total_entry = ttk.Entry(total_frame, textvariable=self.total_div_var, width=10, state="readonly")
        self.total_entry.pack(side="left", fill="x", expand=True)
        
        # Tax deducted
        ttk.Label(add_frame, text="Tax Deducted:").grid(row=row, column=2, sticky="w", padx=(0, 10), pady=(10, 0))
        self.tax_var = tk.StringVar(value="0")
        tax_frame = ttk.Frame(add_frame)
        tax_frame.grid(row=row, column=3, sticky="ew", pady=(10, 0))
        ttk.Label(tax_frame, text="Rs.").pack(side="left")
        ttk.Entry(tax_frame, textvariable=self.tax_var, width=10).pack(side="left", fill="x", expand=True)
        
        row += 1
        
        # Ex-dividend date
        ttk.Label(add_frame, text="Ex-Dividend Date:").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        self.ex_date_picker = DatePickerEntry(add_frame)
        self.ex_date_picker.grid(row=row, column=1, sticky="w", padx=(0, 20), pady=(10, 0))
        
        # Payment date
        ttk.Label(add_frame, text="Payment Date:").grid(row=row, column=2, sticky="w", padx=(0, 10), pady=(10, 0))
        self.pay_date_picker = DatePickerEntry(add_frame)
        self.pay_date_picker.grid(row=row, column=3, sticky="w", pady=(10, 0))
        
        row += 1
        
        # Dividend type
        ttk.Label(add_frame, text="Type:").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        self.type_var = tk.StringVar(value="regular")
        type_combo = ttk.Combobox(add_frame, textvariable=self.type_var,
                                 values=["regular", "special", "bonus"], state="readonly", width=12)
        type_combo.grid(row=row, column=1, sticky="w", padx=(0, 20), pady=(10, 0))
        
        # Add button
        ttk.Button(add_frame, text="Add Dividend",
                  command=self.add_dividend).grid(row=row, column=3, sticky="e", pady=(10, 0))
        
        # Configure grid weights for add_frame
        add_frame.grid_columnconfigure(1, weight=1)
        add_frame.grid_columnconfigure(3, weight=1)
        
        # Bind calculation events
        self.dps_var.trace('w', self.calculate_total)
        self.shares_var.trace('w', self.calculate_total)
        
        # Dividends list frame
        list_frame = ttk.LabelFrame(main_frame, text="Dividend History", padding="15")
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview for dividends
        columns = ("symbol", "company", "ex_date", "payment_date", "dps", "shares",
                  "total", "tax", "net", "type")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        self.tree.heading("symbol", text="Symbol")
        self.tree.heading("company", text="Company")
        self.tree.heading("ex_date", text="Ex-Date")
        self.tree.heading("payment_date", text="Pay Date")
        self.tree.heading("dps", text="DPS")
        self.tree.heading("shares", text="Shares")
        self.tree.heading("total", text="Total")
        self.tree.heading("tax", text="Tax")
        self.tree.heading("net", text="Net")
        self.tree.heading("type", text="Type")
        
        self.tree.column("symbol", width=80)
        self.tree.column("company", width=150)
        self.tree.column("ex_date", width=90)
        self.tree.column("payment_date", width=90)
        self.tree.column("dps", width=70)
        self.tree.column("shares", width=80)
        self.tree.column("total", width=100)
        self.tree.column("tax", width=70)
        self.tree.column("net", width=100)
        self.tree.column("type", width=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Bottom buttons frame
        button_frame = ttk.Frame(list_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky="ew")
        
        ttk.Button(button_frame, text="Delete Selected",
                  command=self.delete_dividend).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Export CSV",
                  command=self.export_dividends).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Close",
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
    
    def on_symbol_change(self, event=None):
        """Auto-fill company name when symbol changes"""
        symbol = self.symbol_var.get().upper()
        company_name = get_company_name(symbol)
        if company_name != symbol:  # If company name was found
            self.company_var.set(company_name)
    
    def calculate_total(self, *args):
        """Calculate total dividend when DPS or shares change"""
        try:
            dps = float(self.dps_var.get() or 0)
            shares = float(self.shares_var.get() or 0)
            total = dps * shares
            self.total_div_var.set(f"{total:.2f}")
        except ValueError:
            self.total_div_var.set("0.00")
    
    def add_dividend(self):
        try:
            # Validate inputs
            symbol = self.symbol_var.get().strip().upper()
            if not symbol:
                messagebox.showerror("Error", "Please enter a stock symbol")
                return
            
            company = self.company_var.get().strip()
            if not company:
                messagebox.showerror("Error", "Please enter company name")
                return
            
            try:
                dps = float(self.dps_var.get())
                shares = float(self.shares_var.get())
                tax = float(self.tax_var.get() or 0)
                
                if dps <= 0 or shares <= 0:
                    messagebox.showerror("Error", "Dividend per share and shares must be positive")
                    return
                    
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers")
                return
            
            ex_date = self.ex_date_picker.get()
            pay_date = self.pay_date_picker.get()
            div_type = self.type_var.get()
            
            if not ex_date:
                messagebox.showerror("Error", "Please select ex-dividend date")
                return
            
            total_dividend = dps * shares
            
            # Add to database
            self.db_manager.add_dividend(
                symbol=symbol,
                company_name=company,
                dividend_per_share=dps,
                total_dividend=total_dividend,
                shares_held=shares,
                ex_dividend_date=ex_date,
                payment_date=pay_date if pay_date else None,
                dividend_type=div_type,
                tax_deducted=tax
            )
            
            # Clear inputs
            self.clear_form()
            
            # Reload data
            self.load_dividend_data()
            
            messagebox.showinfo("Success", "Dividend added successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add dividend: {str(e)}")
    
    def clear_form(self):
        """Clear all form inputs"""
        self.symbol_var.set("")
        self.company_var.set("")
        self.dps_var.set("")
        self.shares_var.set("")
        self.total_div_var.set("")
        self.tax_var.set("0")
        self.ex_date_picker.set(datetime.now().strftime("%Y-%m-%d"))
        self.pay_date_picker.set("")
        self.type_var.set("regular")
    
    def load_dividend_data(self):
        try:
            # Clear tree
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Load dividends
            dividends = self.db_manager.get_all_dividends()
            self.dividend_map = {}  # Map tree items to dividend IDs
            
            total_gross = 0
            total_tax = 0
            total_net = 0
            
            for dividend in dividends:
                values = [
                    dividend['symbol'],
                    dividend['company_name'][:20] + "..." if len(dividend['company_name']) > 20 else dividend['company_name'],
                    dividend['ex_dividend_date'],
                    dividend['payment_date'] or "-",
                    FormatHelper.format_currency(dividend['dividend_per_share']),
                    f"{dividend['shares_held']:.0f}",
                    FormatHelper.format_currency(dividend['total_dividend']),
                    FormatHelper.format_currency(dividend['tax_deducted']),
                    FormatHelper.format_currency(dividend['net_dividend']),
                    dividend['dividend_type'].title()
                ]
                
                # Color code based on type
                tags = [dividend['dividend_type']]
                item = self.tree.insert("", "end", values=values, tags=tags)
                self.dividend_map[item] = dividend['id']
                
                total_gross += dividend['total_dividend']
                total_tax += dividend['tax_deducted']
                total_net += dividend['net_dividend']
            
            # Configure tags
            self.tree.tag_configure("regular", foreground="darkgreen")
            self.tree.tag_configure("special", foreground="blue")
            self.tree.tag_configure("bonus", foreground="purple")
            
            # Update summary
            current_year = datetime.now().year
            year_dividends = self.db_manager.get_total_dividend_income(current_year)
            
            self.summary_var.set(
                f"Total Dividends: {FormatHelper.format_currency(total_gross)} | "
                f"Tax: {FormatHelper.format_currency(total_tax)} | "
                f"Net: {FormatHelper.format_currency(total_net)} | "
                f"This Year: {FormatHelper.format_currency(year_dividends)}"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dividend data: {str(e)}")
    
    def delete_dividend(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a dividend to delete")
            return
        
        try:
            selected_tree_item = selected_item[0]
            if selected_tree_item not in self.dividend_map:
                messagebox.showerror("Error", "Dividend ID not found")
                return
            
            dividend_id = self.dividend_map[selected_tree_item]
            
            # Get display values for confirmation
            item_values = self.tree.item(selected_tree_item)['values']
            symbol = item_values[0]
            ex_date = item_values[2]
            amount = item_values[6]
            
            if messagebox.askyesno("Confirm Delete",
                                 f"Are you sure you want to delete dividend for {symbol} "
                                 f"on {ex_date} of {amount}?"):
                
                self.db_manager.delete_dividend(dividend_id)
                self.load_dividend_data()
                messagebox.showinfo("Success", "Dividend deleted successfully")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete dividend: {str(e)}")
    
    def export_dividends(self):
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"dividends_{datetime.now().strftime('%Y%m%d')}.csv"
            )
            
            if filename:
                dividends = self.db_manager.get_all_dividends()
                
                with open(filename, 'w', newline='', encoding='utf-8') as file:
                    import csv
                    writer = csv.writer(file)
                    
                    # Write header
                    writer.writerow([
                        "Symbol", "Company", "Ex-Dividend Date", "Payment Date",
                        "Dividend Per Share", "Shares Held", "Total Dividend",
                        "Tax Deducted", "Net Dividend", "Type"
                    ])
                    
                    # Write data
                    for div in dividends:
                        writer.writerow([
                            div['symbol'], div['company_name'], div['ex_dividend_date'],
                            div['payment_date'] or "", div['dividend_per_share'],
                            div['shares_held'], div['total_dividend'], div['tax_deducted'],
                            div['net_dividend'], div['dividend_type']
                        ])
                
                messagebox.showinfo("Success", f"Dividends exported to {filename}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export dividends: {str(e)}")
    
    def close_dialog(self):
        self.dialog.destroy()