import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import DatabaseManager
from utils.helpers import FormatHelper

class CashManagementDialog:
    def __init__(self, parent):
        self.parent = parent
        self.db_manager = DatabaseManager()
        
        self.dialog = tk.Toplevel(parent)
        self.setup_dialog()
        self.create_widgets()
        self.load_cash_data()
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.center_dialog()
    
    def setup_dialog(self):
        self.dialog.title("Cash I Have - Management")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        
        # Configure grid weights
        self.dialog.grid_rowconfigure(1, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
    
    def create_widgets(self):
        # Header frame with current balance
        header_frame = ttk.Frame(self.dialog, padding="20")
        header_frame.grid(row=0, column=0, sticky="ew")
        
        # Current balance display
        self.balance_var = tk.StringVar()
        balance_label = ttk.Label(header_frame, textvariable=self.balance_var, 
                                 font=("Arial", 16, "bold"))
        balance_label.pack()
        
        # Separator
        ttk.Separator(self.dialog, orient="horizontal").grid(row=1, column=0, sticky="ew", padx=20)
        
        # Main content frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=2, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Add transaction frame
        add_frame = ttk.LabelFrame(main_frame, text="Add Transaction", padding="10")
        add_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Transaction type
        ttk.Label(add_frame, text="Type:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.type_var = tk.StringVar(value="deposit")
        type_frame = ttk.Frame(add_frame)
        type_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        
        ttk.Radiobutton(type_frame, text="Add Cash", variable=self.type_var, 
                       value="deposit").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(type_frame, text="Withdraw Cash", variable=self.type_var, 
                       value="withdrawal").pack(side="left")
        
        # Amount
        ttk.Label(add_frame, text="Amount:").grid(row=0, column=2, sticky="w", padx=(20, 5))
        self.amount_var = tk.StringVar()
        amount_frame = ttk.Frame(add_frame)
        amount_frame.grid(row=0, column=3, sticky="ew", padx=(0, 10))
        ttk.Label(amount_frame, text="Rs.").pack(side="left")
        self.amount_entry = ttk.Entry(amount_frame, textvariable=self.amount_var, width=15)
        self.amount_entry.pack(side="left", fill="x", expand=True)
        
        # Date with calendar picker
        ttk.Label(add_frame, text="Date:").grid(row=1, column=0, sticky="w", pady=(5, 0))
        from gui.date_picker import DatePickerEntry
        self.date_picker = DatePickerEntry(add_frame, initial_date=datetime.now().strftime("%Y-%m-%d"))
        self.date_picker.grid(row=1, column=1, sticky="w", pady=(5, 0), padx=(0, 10))
        
        # Description
        ttk.Label(add_frame, text="Description:").grid(row=2, column=0, sticky="w", pady=(5, 0))
        self.description_var = tk.StringVar()
        self.description_entry = ttk.Entry(add_frame, textvariable=self.description_var, width=40)
        self.description_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=(5, 0), padx=(0, 10))
        
        # Add button
        ttk.Button(add_frame, text="Add Transaction", 
                  command=self.add_transaction).grid(row=2, column=3, pady=(5, 0))
        
        # Configure column weights
        add_frame.grid_columnconfigure(1, weight=1)
        add_frame.grid_columnconfigure(2, weight=1)
        
        # Transactions list frame
        list_frame = ttk.LabelFrame(main_frame, text="Transaction History", padding="10")
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview for transactions
        self.tree = ttk.Treeview(list_frame, columns=(
            "date", "type", "amount", "description"
        ), show="headings", height=12)
        
        # Configure columns
        self.tree.heading("date", text="Date")
        self.tree.heading("type", text="Type")
        self.tree.heading("amount", text="Amount")
        self.tree.heading("description", text="Description")
        
        self.tree.column("date", width=100)
        self.tree.column("type", width=100)
        self.tree.column("amount", width=120)
        self.tree.column("description", width=300)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Delete button
        delete_frame = ttk.Frame(list_frame)
        delete_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(delete_frame, text="Delete Selected", 
                  command=self.delete_transaction).pack(side="left", padx=(0, 10))
        ttk.Button(delete_frame, text="Close", 
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
    
    def load_cash_data(self):
        try:
            # Update balance
            current_balance = self.db_manager.get_current_cash_balance()
            self.balance_var.set(f"Current Cash Balance: {FormatHelper.format_currency(current_balance)}")
            
            # Clear tree
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Load transactions
            transactions = self.db_manager.get_all_cash_transactions()
            self.transaction_map = {}  # Map tree items to transaction IDs
            
            for transaction in transactions:
                values = [
                    transaction['transaction_date'],
                    transaction['transaction_type'].title(),
                    FormatHelper.format_currency(transaction['amount']),
                    transaction['description'] or ""
                ]
                
                # Color code based on type
                tags = ["deposit" if transaction['transaction_type'] == 'deposit' else "withdrawal"]
                item = self.tree.insert("", "end", values=values, tags=tags)
                # Store the transaction ID mapping
                self.transaction_map[item] = transaction['id']
            
            # Configure tags
            self.tree.tag_configure("deposit", foreground="green")
            self.tree.tag_configure("withdrawal", foreground="red")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load cash data: {str(e)}")
    
    def add_transaction(self):
        try:
            # Validate inputs
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
            
            # Get date from picker
            date_str = self.date_picker.get().strip()
            if not date_str:
                messagebox.showerror("Error", "Please select a date")
                return
            
            try:
                # Validate date format
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format")
                return
            
            transaction_type = self.type_var.get()
            description = self.description_var.get().strip()
            
            # Add to database with custom date
            self.db_manager.add_cash_transaction(
                transaction_type=transaction_type,
                amount=amount,
                description=description,
                transaction_date=date_str
            )
            
            # Clear inputs except date (keep current date for convenience)
            self.amount_var.set("")
            self.description_var.set("")
            
            # Reload data
            self.load_cash_data()
            
            messagebox.showinfo("Success", f"Transaction added successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add transaction: {str(e)}")
    
    def delete_transaction(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a transaction to delete")
            return
        
        try:
            # Get the transaction ID from the mapping
            selected_tree_item = selected_item[0]
            if selected_tree_item not in self.transaction_map:
                messagebox.showerror("Error", "Transaction ID not found")
                return
                
            transaction_id = self.transaction_map[selected_tree_item]
            
            # Get display values for confirmation
            item_values = self.tree.item(selected_tree_item)['values']
            date = item_values[0]
            transaction_type = item_values[1]
            amount = item_values[2]
            
            if messagebox.askyesno("Confirm Delete", 
                                 f"Are you sure you want to delete this {transaction_type.lower()} transaction of {amount} on {date}?"):
                
                # Delete using the stored transaction ID
                self.db_manager.delete_cash_transaction(transaction_id)
                
                # Reload data
                self.load_cash_data()
                messagebox.showinfo("Success", "Transaction deleted successfully")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete transaction: {str(e)}")
    
    def close_dialog(self):
        self.dialog.destroy()