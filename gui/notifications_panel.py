"""
Notifications Panel - Display notifications within the notifications tab
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import List
import threading
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.corporate_actions_fetcher import CorporateAction, corporate_actions_fetcher


class NotificationsPanel:
    """Panel for displaying notifications within the notifications tab"""
    
    def __init__(self, parent_frame, stocks: List = None):
        self.parent_frame = parent_frame
        self.stocks = stocks or []
        self.actions_data: List[CorporateAction] = []
        
        self.setup_ui()
        print(f"DEBUG: Created notifications panel for {len(self.stocks)} stocks")
        
        # Auto-refresh on startup
        self.refresh_notifications()
    
    def setup_ui(self):
        """Setup the notifications UI"""
        
        # Title and refresh button frame
        title_frame = ttk.Frame(self.parent_frame)
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        # Title
        title_label = ttk.Label(title_frame, text="Corporate Actions & Notifications", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        # Refresh button
        self.refresh_btn = ttk.Button(title_frame, text="Refresh Notifications", 
                                     command=self.refresh_notifications)
        self.refresh_btn.grid(row=0, column=1, padx=(20, 0))
        
        # Status label
        self.status_label = ttk.Label(title_frame, text="Loading...", 
                                     foreground="blue")
        self.status_label.grid(row=0, column=2, padx=(20, 0))
        
        title_frame.grid_columnconfigure(0, weight=1)
        
        # Notifications display area
        self.setup_notifications_area()
    
    def setup_notifications_area(self):
        """Setup the main notifications display area"""
        
        # Create frame for notifications
        notifications_frame = ttk.Frame(self.parent_frame)
        notifications_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Configure grid weights
        self.parent_frame.grid_rowconfigure(1, weight=1)
        self.parent_frame.grid_columnconfigure(0, weight=1)
        notifications_frame.grid_rowconfigure(0, weight=1)
        notifications_frame.grid_columnconfigure(0, weight=1)
        
        # Create scrollable text widget
        self.text_frame = ttk.Frame(notifications_frame)
        self.text_frame.grid(row=0, column=0, sticky="nsew")
        self.text_frame.grid_rowconfigure(0, weight=1)
        self.text_frame.grid_columnconfigure(0, weight=1)
        
        # Text widget with scrollbar
        self.text_widget = tk.Text(
            self.text_frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            bg="white",
            fg="black",
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=10
        )
        
        scrollbar = ttk.Scrollbar(self.text_frame, orient="vertical", 
                                 command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        self.text_widget.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure text tags for styling
        self.text_widget.tag_configure("header", font=("Arial", 12, "bold"), 
                                      foreground="darkblue")
        self.text_widget.tag_configure("dividend", foreground="green", 
                                      font=("Arial", 11, "bold"))
        self.text_widget.tag_configure("split", foreground="orange", 
                                      font=("Arial", 11, "bold"))
        self.text_widget.tag_configure("bonus", foreground="purple", 
                                      font=("Arial", 11, "bold"))
        self.text_widget.tag_configure("date", foreground="red", 
                                      font=("Arial", 10, "bold"))
        self.text_widget.tag_configure("description", foreground="black", 
                                      font=("Arial", 10))
    
    def refresh_notifications(self):
        """Refresh notifications"""
        print(f"DEBUG: Starting notifications refresh...")
        
        # Update status
        self.status_label.config(text="Refreshing...", foreground="orange")
        self.refresh_btn.config(state="disabled")
        
        def fetch_notifications():
            try:
                print(f"DEBUG: Fetching for {len(self.stocks)} stocks...")
                
                if not self.stocks:
                    print(f"DEBUG: No stocks, showing empty")
                    self.update_display([])
                    return
                
                # Get portfolio symbols
                portfolio_symbols = []
                for stock in self.stocks:
                    portfolio_symbols.append(stock.symbol)
                    if not stock.symbol.endswith('.NS'):
                        portfolio_symbols.append(f"{stock.symbol}.NS")
                
                print(f"DEBUG: Portfolio symbols: {portfolio_symbols[:5]}...")
                
                # Fetch corporate actions
                actions = corporate_actions_fetcher.get_portfolio_corporate_actions(
                    portfolio_symbols, days_ahead=60
                )
                
                print(f"DEBUG: Found {len(actions)} actions for display...")
                self.update_display(actions)
                
            except Exception as e:
                print(f"DEBUG: Error fetching notifications: {e}")
                self.update_display([])
        
        # Run in background thread
        thread = threading.Thread(target=fetch_notifications, daemon=True)
        thread.start()
    
    def update_display(self, actions: List[CorporateAction]):
        """Update the notifications display"""
        def update_ui():
            try:
                self.actions_data = actions
                
                # Clear existing content
                self.text_widget.delete(1.0, tk.END)
                
                if not actions:
                    self.text_widget.insert(tk.END, "No upcoming corporate actions found for your portfolio.\n\n")
                    self.text_widget.insert(tk.END, "This could mean:\n")
                    self.text_widget.insert(tk.END, "• No dividends, splits, or bonus shares scheduled\n")
                    self.text_widget.insert(tk.END, "• Actions are beyond 60-day horizon\n")
                    self.text_widget.insert(tk.END, "• Portfolio symbols may need .NS suffix\n\n")
                    self.text_widget.insert(tk.END, f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    self.status_label.config(text="No notifications", foreground="gray")
                else:
                    # Header
                    self.text_widget.insert(tk.END, f"🔔 CORPORATE ACTIONS FOUND ({len(actions)})\n\n", "header")
                    
                    # Group by type
                    dividends = [a for a in actions if a.action_type.lower() == 'dividend']
                    splits = [a for a in actions if 'split' in a.action_type.lower()]
                    bonus = [a for a in actions if 'bonus' in a.action_type.lower()]
                    
                    # Display dividends
                    if dividends:
                        self.text_widget.insert(tk.END, "💰 DIVIDENDS\n", "dividend")
                        self.text_widget.insert(tk.END, "─" * 50 + "\n")
                        for action in dividends:
                            self.text_widget.insert(tk.END, f"• {action.symbol}", "dividend")
                            self.text_widget.insert(tk.END, f" - Ex-Date: {action.ex_date}", "date")
                            
                            # Create description from available data
                            desc_parts = []
                            if hasattr(action, 'company_name') and action.company_name:
                                desc_parts.append(f"Company: {action.company_name}")
                            if hasattr(action, 'dividend_amount') and action.dividend_amount:
                                desc_parts.append(f"Amount: ₹{action.dividend_amount}")
                            if hasattr(action, 'record_date') and action.record_date:
                                desc_parts.append(f"Record Date: {action.record_date}")
                            if hasattr(action, 'payment_date') and action.payment_date:
                                desc_parts.append(f"Payment Date: {action.payment_date}")
                            
                            description = " | ".join(desc_parts) if desc_parts else "Dividend announcement"
                            self.text_widget.insert(tk.END, f"\n  {description}\n\n", "description")
                    
                    # Display splits
                    if splits:
                        self.text_widget.insert(tk.END, "📊 STOCK SPLITS\n", "split")
                        self.text_widget.insert(tk.END, "─" * 50 + "\n")
                        for action in splits:
                            self.text_widget.insert(tk.END, f"• {action.symbol}", "split")
                            self.text_widget.insert(tk.END, f" - Ex-Date: {action.ex_date}", "date")
                            
                            # Create description from available data
                            desc_parts = []
                            if hasattr(action, 'company_name') and action.company_name:
                                desc_parts.append(f"Company: {action.company_name}")
                            if hasattr(action, 'ratio_from') and hasattr(action, 'ratio_to') and action.ratio_from and action.ratio_to:
                                desc_parts.append(f"Split Ratio: {action.ratio_to}:{action.ratio_from}")
                            if hasattr(action, 'record_date') and action.record_date:
                                desc_parts.append(f"Record Date: {action.record_date}")
                            
                            description = " | ".join(desc_parts) if desc_parts else "Stock split announcement"
                            self.text_widget.insert(tk.END, f"\n  {description}\n\n", "description")
                    
                    # Display bonus shares
                    if bonus:
                        self.text_widget.insert(tk.END, "🎁 BONUS SHARES\n", "bonus")
                        self.text_widget.insert(tk.END, "─" * 50 + "\n")
                        for action in bonus:
                            self.text_widget.insert(tk.END, f"• {action.symbol}", "bonus")
                            self.text_widget.insert(tk.END, f" - Ex-Date: {action.ex_date}", "date")
                            
                            # Create description from available data
                            desc_parts = []
                            if hasattr(action, 'company_name') and action.company_name:
                                desc_parts.append(f"Company: {action.company_name}")
                            if hasattr(action, 'ratio_from') and hasattr(action, 'ratio_to') and action.ratio_from and action.ratio_to:
                                desc_parts.append(f"Bonus Ratio: {action.ratio_to}:{action.ratio_from}")
                            if hasattr(action, 'record_date') and action.record_date:
                                desc_parts.append(f"Record Date: {action.record_date}")
                            
                            description = " | ".join(desc_parts) if desc_parts else "Bonus shares announcement"
                            self.text_widget.insert(tk.END, f"\n  {description}\n\n", "description")
                    
                    # Footer
                    self.text_widget.insert(tk.END, "─" * 70 + "\n")
                    self.text_widget.insert(tk.END, f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    self.text_widget.insert(tk.END, "💡 Tip: Click 'Refresh Notifications' to update")
                    
                    self.status_label.config(text=f"{len(actions)} notifications", foreground="green")
                
                # Scroll to top
                self.text_widget.see(1.0)
                
                # Re-enable refresh button
                self.refresh_btn.config(state="normal")
                
                print(f"DEBUG: Updated display with {len(actions)} actions")
                
            except Exception as e:
                print(f"DEBUG: Error updating display: {e}")
                self.status_label.config(text="Error updating", foreground="red")
                self.refresh_btn.config(state="normal")
        
        # Update UI from main thread
        self.parent_frame.after(0, update_ui)
    
    def update_stocks(self, stocks: List):
        """Update the stocks list and refresh"""
        self.stocks = stocks
        print(f"DEBUG: Updated stocks list to {len(stocks)} stocks")
        self.refresh_notifications()
