"""
ULTRA DIRECT Notifications Panel - NO CANVAS, NO SCROLLING

Direct labels placed in main frame for absolute visibility.
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


class DirectNotificationsPanel:
    """Ultra direct notifications panel - no fancy widgets"""
    
    def __init__(self, parent_frame: ttk.Frame, stocks: List = None):
        self.parent_frame = parent_frame
        self.stocks = stocks or []
        self.notifications_frame = None
        self.actions_data: List[CorporateAction] = []
        self.notification_widgets = []  # Store all notification widgets
        
        print(f"DEBUG: Creating DIRECT notifications panel...")
        self.create_direct_panel()
        self.refresh_notifications()
    
    def create_direct_panel(self):
        """Create ultra direct panel with no complex widgets"""
        
        # Main frame - no fancy stuff
        self.notifications_frame = tk.Frame(self.parent_frame, bg="white", relief="solid", borderwidth=2)
        self.notifications_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ALWAYS VISIBLE test label
        self.test_label = tk.Label(
            self.notifications_frame,
            text="NOTIFICATIONS PANEL LOADED - THIS SHOULD ALWAYS BE VISIBLE",
            font=("Arial", 12, "bold"),
            bg="red",
            fg="white",
            relief="solid",
            borderwidth=3,
            padx=20,
            pady=10
        )
        self.test_label.pack(pady=10)
        
        # Status label
        self.status_label = tk.Label(
            self.notifications_frame,
            text="LOADING NOTIFICATIONS...",
            font=("Arial", 14, "bold"),
            bg="yellow",
            fg="black",
            relief="solid",
            borderwidth=2,
            padx=15,
            pady=8
        )
        self.status_label.pack(pady=5)
        
        # Refresh button
        self.refresh_button = tk.Button(
            self.notifications_frame,
            text="REFRESH NOTIFICATIONS NOW",
            font=("Arial", 12, "bold"),
            bg="blue",
            fg="white",
            command=self.manual_refresh,
            relief="raised",
            borderwidth=3,
            padx=20,
            pady=5
        )
        self.refresh_button.pack(pady=10)
        
        print(f"DEBUG: Direct panel created successfully")
    
    def refresh_notifications(self):
        """Refresh notifications"""
        print(f"DEBUG: Starting DIRECT notifications refresh...")
        
        def fetch_notifications():
            try:
                print(f"DEBUG: Fetching for {len(self.stocks)} stocks...")
                
                if not self.stocks:
                    print(f"DEBUG: No stocks, showing empty")
                    self.update_direct_display([])
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
                
                print(f"DEBUG: Found {len(actions)} actions for DIRECT display...")
                self.update_direct_display(actions)
                
            except Exception as e:
                print(f"ERROR in DIRECT fetch: {e}")
                import traceback
                traceback.print_exc()
                self.update_direct_display([])
        
        threading.Thread(target=fetch_notifications, daemon=True).start()
    
    def update_direct_display(self, actions: List[CorporateAction]):
        """Update display directly - MAIN THREAD"""
        print(f"DEBUG: DIRECT update with {len(actions)} actions")
        
        def update_on_main_thread():
            try:
                self.actions_data = actions
                
                # Clear existing notification widgets
                for widget in self.notification_widgets:
                    widget.destroy()
                self.notification_widgets.clear()
                
                # Update status
                count = len(actions)
                if count == 0:
                    status_text = "NO CORPORATE ACTIONS FOUND"
                    status_bg = "lightgray"
                else:
                    status_text = f"FOUND {count} CORPORATE ACTIONS!"
                    status_bg = "lightgreen"
                
                self.status_label.config(text=status_text, bg=status_bg)
                print(f"DEBUG: Status updated: {status_text}")
                
                # Create notification widgets directly
                if actions:
                    for i, action in enumerate(actions):
                        self.create_direct_notification(action, i)
                        
                print(f"DEBUG: Created {len(self.notification_widgets)} DIRECT widgets")
                
                # Force refresh
                self.notifications_frame.update()
                self.notifications_frame.update_idletasks()
                
            except Exception as e:
                print(f"ERROR in DIRECT update: {e}")
                import traceback
                traceback.print_exc()
        
        # Main thread update
        try:
            self.notifications_frame.after(0, update_on_main_thread)
            print(f"DEBUG: Scheduled DIRECT update")
        except Exception as e:
            print(f"ERROR scheduling DIRECT update: {e}")
            update_on_main_thread()
    
    def create_direct_notification(self, action: CorporateAction, index: int):
        """Create notification widget directly in main frame"""
        try:
            # Calculate days until
            days_until = self.calculate_days_until(action.ex_date)
            
            # Create notification frame
            notification_frame = tk.Frame(
                self.notifications_frame,
                relief="solid",
                borderwidth=3,
                bg="lightyellow",
                padx=15,
                pady=10
            )
            notification_frame.pack(fill="x", padx=5, pady=5)
            
            # Title
            title_text = f"{index+1}. {action.symbol} - {action.action_type.upper()}"
            if "TODAY" in days_until:
                title_bg = "red"
                title_fg = "white"
            elif "Tomorrow" in days_until:
                title_bg = "orange"
                title_fg = "black"
            else:
                title_bg = "lightblue"
                title_fg = "black"
            
            title_label = tk.Label(
                notification_frame,
                text=title_text,
                font=("Arial", 14, "bold"),
                bg=title_bg,
                fg=title_fg,
                relief="solid",
                borderwidth=2,
                padx=10,
                pady=5
            )
            title_label.pack(fill="x", pady=2)
            
            # Ex-date
            date_text = f"EX-DATE: {action.ex_date} ({days_until})"
            date_label = tk.Label(
                notification_frame,
                text=date_text,
                font=("Arial", 12, "bold"),
                bg="lightyellow",
                fg="darkblue"
            )
            date_label.pack(fill="x", pady=2)
            
            # Details
            if action.action_type.lower() == 'dividend' and action.dividend_amount:
                detail_text = f"DIVIDEND: Rs. {action.dividend_amount} per share"
            elif action.action_type.lower() == 'split' and action.ratio_from and action.ratio_to:
                detail_text = f"SPLIT RATIO: {action.ratio_from}:{action.ratio_to}"
            elif action.action_type.lower() == 'bonus' and action.ratio_from and action.ratio_to:
                detail_text = f"BONUS RATIO: {action.ratio_from}:{action.ratio_to}"
            else:
                detail_text = f"{action.action_type.upper()} ANNOUNCED"
            
            detail_label = tk.Label(
                notification_frame,
                text=detail_text,
                font=("Arial", 11, "bold"),
                bg="lightyellow",
                fg="darkgreen"
            )
            detail_label.pack(fill="x", pady=2)
            
            # Warning
            warning_text = f"IMPORTANT: OWN SHARES BEFORE {action.ex_date} TO QUALIFY!"
            warning_label = tk.Label(
                notification_frame,
                text=warning_text,
                font=("Arial", 10, "bold"),
                bg="lightyellow",
                fg="red"
            )
            warning_label.pack(fill="x", pady=2)
            
            # Store widget
            self.notification_widgets.append(notification_frame)
            
            print(f"DEBUG: Created DIRECT widget for {action.symbol} {action.action_type}")
            
        except Exception as e:
            print(f"ERROR creating DIRECT notification: {e}")
    
    def calculate_days_until(self, ex_date_str: str) -> str:
        """Calculate days until ex-date"""
        try:
            ex_date = datetime.strptime(ex_date_str, '%Y-%m-%d').date()
            today = datetime.now().date()
            days_diff = (ex_date - today).days
            
            if days_diff < 0:
                return f"{abs(days_diff)} days ago"
            elif days_diff == 0:
                return "TODAY!"
            elif days_diff == 1:
                return "Tomorrow"
            else:
                return f"in {days_diff} days"
        except:
            return "date unknown"
    
    def update_stocks(self, stocks: List):
        """Update stocks and refresh"""
        print(f"DEBUG: DIRECT panel updating stocks ({len(stocks)} stocks)")
        self.stocks = stocks
        self.refresh_notifications()
    
    def manual_refresh(self):
        """Manual refresh"""
        print(f"DEBUG: DIRECT manual refresh clicked")
        self.refresh_button.config(state="disabled", text="REFRESHING...")
        
        def enable_button():
            try:
                self.refresh_button.config(state="normal", text="REFRESH NOTIFICATIONS NOW")
            except:
                pass
        
        self.notifications_frame.after(3000, enable_button)
        self.refresh_notifications()
    
    def get_notification_count(self) -> int:
        """Get notification count"""
        return len(self.actions_data)