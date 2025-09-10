import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import DatabaseManager
from data.models import Stock
from utils.helpers import FormatHelper, FileHelper

class TaxReportDialog:
    def __init__(self, parent):
        self.parent = parent
        self.db_manager = DatabaseManager()
        
        self.dialog = tk.Toplevel(parent)
        self.setup_dialog()
        self.create_widgets()
        self.load_tax_data()
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.center_dialog()
    
    def setup_dialog(self):
        self.dialog.title("Tax Report - Capital Gains/Losses")
        self.dialog.geometry("1000x700")
        self.dialog.resizable(True, True)
        
        # Configure grid weights
        self.dialog.grid_rowconfigure(2, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
    
    def create_widgets(self):
        # Header frame
        header_frame = ttk.Frame(self.dialog, padding="20")
        header_frame.grid(row=0, column=0, sticky="ew")
        
        # Title
        title_label = ttk.Label(header_frame, text="Capital Gains/Losses Tax Report", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        # Tax year selection frame
        year_frame = ttk.Frame(self.dialog, padding="20")
        year_frame.grid(row=1, column=0, sticky="ew")
        
        ttk.Label(year_frame, text="Tax Year:").pack(side="left", padx=(0, 10))
        
        # Year selection
        current_year = datetime.now().year
        years = [str(year) for year in range(current_year - 5, current_year + 1)]
        
        self.year_var = tk.StringVar(value=str(current_year))
        year_combo = ttk.Combobox(year_frame, textvariable=self.year_var, values=years, 
                                 state="readonly", width=10)
        year_combo.pack(side="left", padx=(0, 20))
        year_combo.bind("<<ComboboxSelected>>", self.on_year_changed)
        
        # Summary labels
        self.summary_frame = ttk.Frame(year_frame)
        self.summary_frame.pack(side="left", padx=(20, 0))
        
        self.short_term_var = tk.StringVar()
        self.long_term_var = tk.StringVar()
        self.total_gains_var = tk.StringVar()
        
        ttk.Label(self.summary_frame, textvariable=self.short_term_var, 
                 font=("Arial", 10, "bold")).pack(anchor="w")
        ttk.Label(self.summary_frame, textvariable=self.long_term_var, 
                 font=("Arial", 10, "bold")).pack(anchor="w")
        ttk.Label(self.summary_frame, textvariable=self.total_gains_var, 
                 font=("Arial", 12, "bold")).pack(anchor="w", pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(year_frame)
        button_frame.pack(side="right")
        
        ttk.Button(button_frame, text="Export Tax Report", 
                  command=self.export_tax_report).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Refresh", 
                  command=self.load_tax_data).pack(side="left")
        
        # Main content frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=2, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Notebook for different tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        
        # Current Holdings Tab
        self.create_current_holdings_tab()
        
        # Realized Gains Tab (for sold stocks - placeholder for now)
        self.create_realized_gains_tab()
        
        # Tax Summary Tab
        self.create_tax_summary_tab()
        
        # Close button
        close_frame = ttk.Frame(self.dialog, padding="10")
        close_frame.grid(row=3, column=0, sticky="ew")
        
        ttk.Button(close_frame, text="Close", command=self.close_dialog).pack(side="right")
    
    def create_current_holdings_tab(self):
        """Create tab for current stock holdings and unrealized gains"""
        holdings_frame = ttk.Frame(self.notebook)
        self.notebook.add(holdings_frame, text="Current Holdings (Unrealized)")
        
        holdings_frame.grid_rowconfigure(0, weight=1)
        holdings_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview for current holdings
        self.holdings_tree = ttk.Treeview(holdings_frame, columns=(
            "symbol", "company", "quantity", "purchase_date", "purchase_price", 
            "current_price", "investment", "current_value", "unrealized_gain", 
            "gain_type", "days_held"
        ), show="headings", height=15)
        
        # Configure columns
        columns_config = [
            ("symbol", "Symbol", 80),
            ("company", "Company", 120),
            ("quantity", "Qty", 60),
            ("purchase_date", "Purchase Date", 100),
            ("purchase_price", "Purchase Price", 100),
            ("current_price", "Current Price", 100),
            ("investment", "Investment", 100),
            ("current_value", "Current Value", 100),
            ("unrealized_gain", "Unrealized Gain", 100),
            ("gain_type", "Term", 80),
            ("days_held", "Days Held", 80)
        ]
        
        for col_id, heading, width in columns_config:
            self.holdings_tree.heading(col_id, text=heading)
            self.holdings_tree.column(col_id, width=width, anchor="center")
        
        # Scrollbars
        v_scrollbar1 = ttk.Scrollbar(holdings_frame, orient="vertical", command=self.holdings_tree.yview)
        h_scrollbar1 = ttk.Scrollbar(holdings_frame, orient="horizontal", command=self.holdings_tree.xview)
        self.holdings_tree.configure(yscrollcommand=v_scrollbar1.set, xscrollcommand=h_scrollbar1.set)
        
        self.holdings_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar1.grid(row=0, column=1, sticky="ns")
        h_scrollbar1.grid(row=1, column=0, sticky="ew")
    
    def create_realized_gains_tab(self):
        """Create tab for realized gains (sold stocks)"""
        realized_frame = ttk.Frame(self.notebook)
        self.notebook.add(realized_frame, text="Realized Gains (Sold)")
        
        # Placeholder for future implementation
        placeholder_label = ttk.Label(realized_frame, 
            text="Realized Gains tracking will be available when you implement\nselling functionality with transaction history.",
            font=("Arial", 12), justify="center")
        placeholder_label.pack(expand=True)
        
        info_label = ttk.Label(realized_frame,
            text="This feature will track:\n• Sold stocks with purchase and sale dates\n• Actual capital gains/losses from sales\n• Short-term vs Long-term classification\n• Tax liability calculations",
            font=("Arial", 10), justify="left")
        info_label.pack(pady=20)
    
    def create_tax_summary_tab(self):
        """Create tab for tax summary and calculations"""
        tax_frame = ttk.Frame(self.notebook)
        self.notebook.add(tax_frame, text="Tax Summary")
        
        tax_frame.grid_rowconfigure(1, weight=1)
        tax_frame.grid_columnconfigure(0, weight=1)
        
        # Tax information frame
        info_frame = ttk.LabelFrame(tax_frame, text="Tax Information (India)", padding="20")
        info_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        tax_info_text = """
Capital Gains Tax Rules (India):

SHORT-TERM CAPITAL GAINS (STCG):
• Holding period: Less than 12 months
• Tax rate: 15% + 4% Health & Education Cess = 15.6%
• Applied on: Listed equity shares and equity mutual funds

LONG-TERM CAPITAL GAINS (LTCG):
• Holding period: More than 12 months  
• Tax rate: 10% (without indexation) + 4% Cess = 10.4%
• Exemption: Up to Rs. 1 lakh per financial year
• Applied on: Listed equity shares and equity mutual funds

Note: This is for informational purposes only. Please consult a tax advisor.
        """
        
        ttk.Label(info_frame, text=tax_info_text, justify="left", 
                 font=("Arial", 9)).pack(anchor="w")
        
        # Current year summary
        summary_frame = ttk.LabelFrame(tax_frame, text="Current Year Summary", padding="20")
        summary_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        self.tax_summary_text = tk.Text(summary_frame, height=10, width=80, 
                                       wrap=tk.WORD, font=("Consolas", 10))
        tax_scrollbar = ttk.Scrollbar(summary_frame, orient="vertical", 
                                     command=self.tax_summary_text.yview)
        self.tax_summary_text.configure(yscrollcommand=tax_scrollbar.set)
        
        self.tax_summary_text.grid(row=0, column=0, sticky="nsew")
        tax_scrollbar.grid(row=0, column=1, sticky="ns")
        
        summary_frame.grid_rowconfigure(0, weight=1)
        summary_frame.grid_columnconfigure(0, weight=1)
    
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
    
    def on_year_changed(self, event=None):
        self.load_tax_data()
    
    def load_tax_data(self):
        """Load and display tax-related data"""
        try:
            # Get current stock holdings
            stock_records = self.db_manager.get_all_stocks()
            stocks = [Stock(**record) for record in stock_records]
            
            # Clear holdings tree
            for item in self.holdings_tree.get_children():
                self.holdings_tree.delete(item)
            
            short_term_gains = 0
            long_term_gains = 0
            total_unrealized = 0
            
            selected_year = int(self.year_var.get())
            
            # Add current holdings to tree
            for stock in stocks:
                # Calculate unrealized gain/loss
                unrealized_gain = stock.profit_loss_amount
                total_unrealized += unrealized_gain
                
                # Determine if it would be short-term or long-term
                gain_type = "Long-term" if stock.days_held >= 365 else "Short-term"
                
                # For current year analysis, consider potential gains
                if gain_type == "Short-term":
                    short_term_gains += unrealized_gain
                else:
                    long_term_gains += unrealized_gain
                
                values = [
                    stock.symbol,
                    FormatHelper.truncate_text(stock.company_name or "", 15),
                    f"{stock.quantity:,.0f}",
                    stock.purchase_date,
                    FormatHelper.format_currency(stock.purchase_price),
                    FormatHelper.format_currency(stock.current_price or 0),
                    FormatHelper.format_currency(stock.total_investment),
                    FormatHelper.format_currency(stock.current_value),
                    FormatHelper.format_currency(unrealized_gain),
                    gain_type,
                    f"{stock.days_held} days"
                ]
                
                # Color coding
                tag = "profit" if unrealized_gain > 0 else "loss" if unrealized_gain < 0 else "neutral"
                item = self.holdings_tree.insert("", "end", values=values, tags=[tag])
            
            # Configure colors
            self.holdings_tree.tag_configure("profit", foreground="green")
            self.holdings_tree.tag_configure("loss", foreground="red")
            self.holdings_tree.tag_configure("neutral", foreground="black")
            
            # Update summary
            self.short_term_var.set(f"Short-term (unrealized): {FormatHelper.format_currency(short_term_gains)}")
            self.long_term_var.set(f"Long-term (unrealized): {FormatHelper.format_currency(long_term_gains)}")
            self.total_gains_var.set(f"Total Unrealized: {FormatHelper.format_currency(total_unrealized)}")
            
            # Update tax summary
            self.update_tax_summary(short_term_gains, long_term_gains, total_unrealized, selected_year)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tax data: {str(e)}")
    
    def update_tax_summary(self, short_term, long_term, total_unrealized, year):
        """Update the tax summary text"""
        self.tax_summary_text.delete(1.0, tk.END)
        
        summary = f"""TAX SUMMARY FOR {year}
{'='*50}

UNREALIZED GAINS/LOSSES (Current Holdings):
Short-term (< 1 year): {FormatHelper.format_currency(short_term)}
Long-term (>= 1 year):  {FormatHelper.format_currency(long_term)}
Total Unrealized:       {FormatHelper.format_currency(total_unrealized)}

POTENTIAL TAX LIABILITY (if sold today):
Short-term tax (15.6%): {FormatHelper.format_currency(max(0, short_term * 0.156))}
Long-term tax (10.4%):  {FormatHelper.format_currency(max(0, (long_term - 100000) * 0.104) if long_term > 100000 else 0)}

NOTES:
• These are unrealized gains - no tax is due until you sell
• LTCG has Rs. 1 lakh exemption per financial year
• Short-term gains are taxed at 15.6% (15% + 4% cess)
• Long-term gains above Rs. 1 lakh taxed at 10.4% (10% + 4% cess)
• This is for equity shares/mutual funds held for investment

DISCLAIMER: This is for informational purposes only.
Please consult a qualified tax advisor for accurate tax planning.
"""
        
        self.tax_summary_text.insert(1.0, summary)
    
    def export_tax_report(self):
        """Export tax report to CSV"""
        try:
            selected_year = self.year_var.get()
            
            # Prepare export data
            export_data = []
            for child in self.holdings_tree.get_children():
                values = self.holdings_tree.item(child)['values']
                export_data.append({
                    "Symbol": values[0],
                    "Company": values[1],
                    "Quantity": values[2],
                    "Purchase Date": values[3],
                    "Purchase Price": values[4],
                    "Current Price": values[5],
                    "Investment Amount": values[6],
                    "Current Value": values[7],
                    "Unrealized Gain/Loss": values[8],
                    "Term (Short/Long)": values[9],
                    "Days Held": values[10]
                })
            
            if not export_data:
                messagebox.showinfo("Info", "No data to export")
                return
            
            filename = f"tax_report_{selected_year}.csv"
            if FileHelper.export_to_csv(export_data, filename):
                messagebox.showinfo("Success", f"Tax report exported to {filename}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export tax report: {str(e)}")
    
    def close_dialog(self):
        self.dialog.destroy()