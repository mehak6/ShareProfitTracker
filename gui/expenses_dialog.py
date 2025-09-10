import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import DatabaseManager
from utils.helpers import FormatHelper

class ExpensesDialog:
    def __init__(self, parent):
        self.parent = parent
        self.db_manager = DatabaseManager()
        
        self.dialog = tk.Toplevel(parent)
        self.setup_dialog()
        self.create_widgets()
        self.load_expenses_data()
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.center_dialog()
    
    def setup_dialog(self):
        self.dialog.title("Other Funds - Expense Tracking")
        self.dialog.geometry("900x700")
        self.dialog.resizable(True, True)
        
        # Configure grid weights
        self.dialog.grid_rowconfigure(2, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
    
    def create_widgets(self):
        # Header frame
        header_frame = ttk.Frame(self.dialog, padding="20")
        header_frame.grid(row=0, column=0, sticky="ew")
        
        # Title
        title_label = ttk.Label(header_frame, text="Other Funds - Track Your Expenses", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        # Cash balance summary frame
        balance_frame = ttk.Frame(header_frame)
        balance_frame.pack(pady=(10, 0))
        
        # Available cash balance
        self.cash_balance_var = tk.StringVar()
        self.cash_balance_label = ttk.Label(balance_frame, textvariable=self.cash_balance_var, 
                                          font=("Arial", 12, "bold"), foreground="green")
        self.cash_balance_label.pack()
        
        # Remaining cash after expenses
        self.remaining_cash_var = tk.StringVar()
        self.remaining_cash_label = ttk.Label(balance_frame, textvariable=self.remaining_cash_var, 
                                            font=("Arial", 12, "bold"), foreground="blue")
        self.remaining_cash_label.pack()
        
        # Month filter
        filter_frame = ttk.Frame(self.dialog, padding="20")
        filter_frame.grid(row=1, column=0, sticky="ew")
        
        ttk.Label(filter_frame, text="View expenses for:").pack(side="left", padx=(0, 10))
        
        # Month selection
        self.month_var = tk.StringVar()
        current_month = datetime.now().strftime("%B %Y")
        self.month_var.set(current_month)
        
        months = []
        current_date = datetime.now()
        for i in range(12):  # Show last 12 months
            month_date = datetime(current_date.year, current_date.month - i, 1) if current_date.month > i else datetime(current_date.year - 1, 12 - (i - current_date.month), 1)
            months.append(month_date.strftime("%B %Y"))
        
        month_combo = ttk.Combobox(filter_frame, textvariable=self.month_var, values=months, 
                                  state="readonly", width=15)
        month_combo.pack(side="left", padx=(0, 10))
        month_combo.bind("<<ComboboxSelected>>", self.on_month_changed)
        
        ttk.Button(filter_frame, text="Refresh", 
                  command=self.load_expenses_data).pack(side="left", padx=(10, 0))
        
        # Monthly summary
        self.summary_var = tk.StringVar()
        summary_label = ttk.Label(filter_frame, textvariable=self.summary_var, 
                                 font=("Arial", 12, "bold"))
        summary_label.pack(side="right")
        
        # Separator
        ttk.Separator(self.dialog, orient="horizontal").grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        # Main content frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=2, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Add expense frame
        add_frame = ttk.LabelFrame(main_frame, text="Add New Expense", padding="10")
        add_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Category
        ttk.Label(add_frame, text="Category:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.category_var = tk.StringVar()
        categories = ["Electricity", "Water", "Gas", "Internet", "Mobile", "Rent", "Food", "Transport", "Medical", "Other"]
        category_combo = ttk.Combobox(add_frame, textvariable=self.category_var, values=categories, width=15)
        category_combo.grid(row=0, column=1, sticky="w", padx=(0, 10))
        category_combo.set("Electricity")  # Default
        
        # Amount
        ttk.Label(add_frame, text="Amount:").grid(row=0, column=2, sticky="w", padx=(20, 5))
        self.amount_var = tk.StringVar()
        amount_frame = ttk.Frame(add_frame)
        amount_frame.grid(row=0, column=3, sticky="ew", padx=(0, 10))
        ttk.Label(amount_frame, text="Rs.").pack(side="left")
        self.amount_entry = ttk.Entry(amount_frame, textvariable=self.amount_var, width=12)
        self.amount_entry.pack(side="left", fill="x", expand=True)
        
        # Date
        ttk.Label(add_frame, text="Date:").grid(row=0, column=4, sticky="w", padx=(20, 5))
        self.date_var = tk.StringVar()
        self.date_entry = ttk.Entry(add_frame, textvariable=self.date_var, width=12)
        self.date_entry.grid(row=0, column=5, padx=(0, 10))
        
        # Set today's date by default
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Button(add_frame, text="Today", 
                  command=self.set_today_date).grid(row=0, column=6)
        
        # Description (second row)
        ttk.Label(add_frame, text="Description (optional):").grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.description_var = tk.StringVar()
        self.description_entry = ttk.Entry(add_frame, textvariable=self.description_var, width=50)
        self.description_entry.grid(row=1, column=1, columnspan=4, sticky="ew", pady=(5, 0), padx=(0, 10))
        
        # Add button
        ttk.Button(add_frame, text="Add Expense", 
                  command=self.add_expense).grid(row=1, column=5, columnspan=2, pady=(5, 0))
        
        # Configure column weights
        add_frame.grid_columnconfigure(3, weight=1)
        
        # Expenses list frame
        list_frame = ttk.LabelFrame(main_frame, text="Expense History", padding="10")
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview for expenses
        self.tree = ttk.Treeview(list_frame, columns=(
            "date", "category", "description", "amount"
        ), show="headings", height=15)
        
        # Configure columns
        self.tree.heading("date", text="Date")
        self.tree.heading("category", text="Category")
        self.tree.heading("description", text="Description")
        self.tree.heading("amount", text="Amount")
        
        self.tree.column("date", width=100)
        self.tree.column("category", width=120)
        self.tree.column("description", width=400)
        self.tree.column("amount", width=120)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Bottom buttons
        button_frame = ttk.Frame(list_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Delete Selected", 
                  command=self.delete_expense).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Export Month CSV", 
                  command=self.export_month_csv).pack(side="left", padx=(0, 10))
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
    
    def set_today_date(self):
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
    
    def on_month_changed(self, event=None):
        self.load_expenses_data()
    
    def load_expenses_data(self):
        try:
            # Get current cash balance
            current_cash_balance = self.db_manager.get_current_cash_balance()
            self.cash_balance_var.set(f"Available Cash: {FormatHelper.format_currency(current_cash_balance)}")
            
            # Parse selected month
            month_str = self.month_var.get()
            try:
                selected_date = datetime.strptime(month_str, "%B %Y")
                year = selected_date.year
                month = selected_date.month
            except ValueError:
                # Default to current month
                current_date = datetime.now()
                year = current_date.year
                month = current_date.month
            
            # Clear tree
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Load expenses for selected month
            expenses = self.db_manager.get_expenses_by_month(year, month)
            monthly_expenses = 0
            
            for expense in expenses:
                values = [
                    expense['expense_date'],
                    expense['category'],
                    expense['description'],
                    FormatHelper.format_currency(expense['amount'])
                ]
                
                # Color code by category
                tags = [expense['category'].lower()]
                item = self.tree.insert("", "end", values=values, tags=tags)
                monthly_expenses += expense['amount']
            
            # Calculate total expenses across all months
            all_expenses = self.db_manager.get_all_expenses()
            total_all_expenses = sum(expense['amount'] for expense in all_expenses)
            
            # Calculate remaining cash after all expenses
            remaining_cash = current_cash_balance - total_all_expenses
            
            # Update cash balance displays
            month_name = datetime(year, month, 1).strftime("%B %Y")
            self.summary_var.set(f"Expenses for {month_name}: {FormatHelper.format_currency(monthly_expenses)}")
            
            # Show remaining cash with appropriate color
            remaining_color = "blue" if remaining_cash >= 0 else "red"
            remaining_text = f"Remaining Cash After All Expenses: {FormatHelper.format_currency(remaining_cash)}"
            self.remaining_cash_var.set(remaining_text)
            
            # Update the color of the remaining cash label
            try:
                self.remaining_cash_label.configure(foreground=remaining_color)
            except:
                pass
            
            # Configure category colors
            colors = {
                "electricity": "#FFE135", "water": "#4A90E2", "gas": "#F5A623", 
                "internet": "#7ED321", "mobile": "#BD10E0", "rent": "#B8E986",
                "food": "#50E3C2", "transport": "#D0021B", "medical": "#9013FE", "other": "#8E8E93"
            }
            
            for category, color in colors.items():
                self.tree.tag_configure(category, background=color)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load expenses: {str(e)}")
    
    def add_expense(self):
        try:
            # Validate inputs
            category = self.category_var.get().strip()
            if not category:
                messagebox.showerror("Error", "Please select a category")
                return
            
            amount_str = self.amount_var.get().strip()
            if not amount_str:
                messagebox.showerror("Error", "Please enter an amount")
                return
            
            try:
                amount = float(amount_str)
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be positive")
                    return
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid amount")
                return
            
            # Check if there's enough cash available
            current_cash_balance = self.db_manager.get_current_cash_balance()
            all_expenses = self.db_manager.get_all_expenses()
            total_all_expenses = sum(expense['amount'] for expense in all_expenses)
            remaining_cash = current_cash_balance - total_all_expenses
            
            if amount > remaining_cash:
                result = messagebox.askyesno("Insufficient Cash", 
                    f"This expense (Rs.{amount:,.2f}) exceeds your available cash balance.\n\n" +
                    f"Available Cash: {FormatHelper.format_currency(current_cash_balance)}\n" +
                    f"Current Expenses: {FormatHelper.format_currency(total_all_expenses)}\n" +
                    f"Remaining Cash: {FormatHelper.format_currency(remaining_cash)}\n\n" +
                    "Do you want to add this expense anyway?")
                if not result:
                    return
            
            description = self.description_var.get().strip()
            # Description is optional, can be empty
            
            date_str = self.date_var.get().strip()
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Please enter date in YYYY-MM-DD format")
                return
            
            # Add to database
            self.db_manager.add_expense(
                category=category,
                description=description,
                amount=amount,
                expense_date=date_str
            )
            
            # Clear inputs
            self.amount_var.set("")
            self.description_var.set("")
            self.set_today_date()
            
            # Reload data to refresh cash balance and expense list
            self.load_expenses_data()
            
            messagebox.showinfo("Success", f"Expense added successfully!\nRemaining cash updated.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add expense: {str(e)}")
    
    def delete_expense(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an expense to delete")
            return
        
        try:
            # Get expense details
            item_values = self.tree.item(selected_item[0])['values']
            date = item_values[0]
            category = item_values[1]
            description = item_values[2]
            amount = item_values[3]
            
            if messagebox.askyesno("Confirm Delete", 
                                 f"Are you sure you want to delete this {category} expense?\n\n{description}\nAmount: {amount}\nDate: {date}"):
                
                # Find the expense ID by matching values
                # Parse selected month for filtering
                month_str = self.month_var.get()
                selected_date = datetime.strptime(month_str, "%B %Y")
                year = selected_date.year
                month = selected_date.month
                
                expenses = self.db_manager.get_expenses_by_month(year, month)
                for expense in expenses:
                    if (expense['expense_date'] == date and 
                        expense['category'] == category and
                        expense['description'] == description and
                        FormatHelper.format_currency(expense['amount']) == amount):
                        
                        self.db_manager.delete_expense(expense['id'])
                        break
                
                # Reload data to refresh cash balance and expense list
                self.load_expenses_data()
                messagebox.showinfo("Success", "Expense deleted successfully!\nRemaining cash updated.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete expense: {str(e)}")
    
    def export_month_csv(self):
        try:
            # Parse selected month
            month_str = self.month_var.get()
            selected_date = datetime.strptime(month_str, "%B %Y")
            year = selected_date.year
            month = selected_date.month
            
            expenses = self.db_manager.get_expenses_by_month(year, month)
            if not expenses:
                messagebox.showinfo("Info", "No expenses found for selected month")
                return
            
            # Prepare export data
            export_data = []
            for expense in expenses:
                export_data.append({
                    "Date": expense['expense_date'],
                    "Category": expense['category'],
                    "Description": expense['description'],
                    "Amount": expense['amount']
                })
            
            from utils.helpers import FileHelper
            filename = f"expenses_{month_str.replace(' ', '_')}.csv"
            
            if FileHelper.export_to_csv(export_data, filename):
                messagebox.showinfo("Success", f"Expenses exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export expenses: {str(e)}")
    
    def close_dialog(self):
        self.dialog.destroy()