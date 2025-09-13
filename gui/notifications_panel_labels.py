"""
Ultra Simple Notifications Panel - LABELS ONLY VERSION

Uses simple labels instead of text widgets for guaranteed visibility.
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


class LabelNotificationsPanel:
    """Ultra simple notifications panel using only labels"""
    
    def __init__(self, parent_frame: ttk.Frame, stocks: List = None):
        self.parent_frame = parent_frame
        self.stocks = stocks or []
        self.notifications_frame = None
        self.actions_data: List[CorporateAction] = []
        self.notification_labels = []  # Store label widgets
        self.last_refresh = None
        
        print(f"DEBUG: Creating LABEL-BASED notifications panel...")
        self.create_label_panel()
        self.refresh_notifications()
    
    def create_label_panel(self):
        """Create ultra simple label-based notifications panel"""
        
        # Main frame with red border for visibility
        self.notifications_frame = ttk.LabelFrame(
            self.parent_frame, 
            text="CORPORATE ACTIONS NOTIFICATIONS", 
            padding="15"
        )
        self.notifications_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.notifications_frame.grid_columnconfigure(0, weight=1)
        
        # Header label - always visible
        self.header_label = tk.Label(
            self.notifications_frame,
            text="LOADING NOTIFICATIONS...",
            font=("Arial", 14, "bold"),
            bg="yellow",
            fg="black",
            relief="solid",
            borderwidth=2,
            padx=10,
            pady=5
        )
        self.header_label.grid(row=0, column=0, sticky="ew", pady=5)
        
        # Refresh button
        self.refresh_button = tk.Button(
            self.notifications_frame,
            text="REFRESH NOTIFICATIONS",
            font=("Arial", 12, "bold"),
            bg="lightblue",
            fg="black",
            command=self.manual_refresh,
            relief="raised",
            borderwidth=3
        )
        self.refresh_button.grid(row=1, column=0, pady=5)
        
        # Scrollable frame for notifications
        self.canvas = tk.Canvas(self.notifications_frame, bg="white", height=400)
        self.scrollbar = ttk.Scrollbar(self.notifications_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.grid(row=2, column=0, sticky="nsew", pady=5)
        self.scrollbar.grid(row=2, column=1, sticky="ns")
        
        self.notifications_frame.grid_rowconfigure(2, weight=1)
        
        print(f"DEBUG: Label-based panel created successfully")
    
    def refresh_notifications(self):
        """Refresh notifications in background thread"""
        print(f"DEBUG: Starting label-based notifications refresh...")
        
        def fetch_notifications():
            try:
                print(f"DEBUG: Fetching notifications for {len(self.stocks)} stocks...")
                
                if not self.stocks:
                    print(f"DEBUG: No stocks, showing empty message")
                    self.update_labels([])
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
                
                print(f"DEBUG: Found {len(actions)} actions for labels update...")
                self.update_labels(actions)
                
            except Exception as e:
                print(f"ERROR in label notifications fetch: {e}")
                import traceback
                traceback.print_exc()
                self.update_labels([])
        
        # Run in background thread
        threading.Thread(target=fetch_notifications, daemon=True).start()
    
    def update_labels(self, actions: List[CorporateAction]):
        """Update labels with corporate actions - MAIN THREAD ONLY"""
        print(f"DEBUG: Updating labels with {len(actions)} actions")
        
        def update_on_main_thread():
            try:
                self.actions_data = actions
                self.last_refresh = datetime.now()
                
                # Update header
                count = len(actions)
                if count == 0:
                    header_text = "NO UPCOMING CORPORATE ACTIONS FOUND"
                    header_bg = "lightgray"
                else:
                    header_text = f"FOUND {count} CORPORATE ACTIONS FOR YOUR PORTFOLIO!"
                    header_bg = "lightgreen"
                
                self.header_label.config(text=header_text, bg=header_bg)
                print(f"DEBUG: Header updated: {header_text}")
                
                # Clear existing notification labels
                for label in self.notification_labels:
                    label.destroy()
                self.notification_labels.clear()
                
                if actions:
                    # Create labels for each action
                    for i, action in enumerate(actions):
                        self.create_action_label(action, i)
                        
                print(f"DEBUG: Created {len(self.notification_labels)} notification labels")
                
            except Exception as e:
                print(f"ERROR updating labels: {e}")
                import traceback
                traceback.print_exc()
        
        # Schedule on main thread
        try:
            self.notifications_frame.after(0, update_on_main_thread)
            print(f"DEBUG: Scheduled label update on main thread")
        except Exception as e:
            print(f"ERROR scheduling label update: {e}")
            # Direct call as fallback
            update_on_main_thread()
    
    def create_action_label(self, action: CorporateAction, index: int):
        """Create a single action label"""
        try:
            # Calculate days until
            days_until = self.calculate_days_until(action.ex_date)
            
            # Create main action frame
            action_frame = tk.Frame(
                self.scrollable_frame,
                relief="solid",
                borderwidth=2,
                bg="lightyellow",
                padx=10,
                pady=8
            )
            action_frame.grid(row=index, column=0, sticky="ew", padx=5, pady=3)
            self.scrollable_frame.grid_columnconfigure(0, weight=1)
            action_frame.grid_columnconfigure(0, weight=1)
            
            # Action title
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
                action_frame,
                text=title_text,
                font=("Arial", 12, "bold"),
                bg=title_bg,
                fg=title_fg,
                anchor="w"
            )
            title_label.grid(row=0, column=0, sticky="ew", pady=2)
            
            # Ex-date info
            date_text = f"Ex-Date: {action.ex_date} ({days_until})"
            date_label = tk.Label(
                action_frame,
                text=date_text,
                font=("Arial", 10),
                bg="lightyellow",
                anchor="w"
            )
            date_label.grid(row=1, column=0, sticky="ew")
            
            # Action details
            if action.action_type.lower() == 'dividend' and action.dividend_amount:
                detail_text = f"Dividend: Rs. {action.dividend_amount} per share"
            elif action.action_type.lower() == 'split' and action.ratio_from and action.ratio_to:
                detail_text = f"Split Ratio: {action.ratio_from}:{action.ratio_to}"
            elif action.action_type.lower() == 'bonus' and action.ratio_from and action.ratio_to:
                detail_text = f"Bonus Ratio: {action.ratio_from}:{action.ratio_to}"
            else:
                detail_text = f"{action.action_type.capitalize()} announced"
            
            detail_label = tk.Label(
                action_frame,
                text=detail_text,
                font=("Arial", 10, "bold"),
                bg="lightyellow",
                fg="darkgreen",
                anchor="w"
            )
            detail_label.grid(row=2, column=0, sticky="ew")
            
            # Eligibility warning
            warning_text = f"IMPORTANT: Own shares BEFORE {action.ex_date} to qualify!"
            warning_label = tk.Label(
                action_frame,
                text=warning_text,
                font=("Arial", 9),
                bg="lightyellow",
                fg="red",
                anchor="w"
            )
            warning_label.grid(row=3, column=0, sticky="ew", pady=2)
            
            # Store the frame reference
            self.notification_labels.append(action_frame)
            
            print(f"DEBUG: Created label for {action.symbol} {action.action_type}")
            
        except Exception as e:
            print(f"ERROR creating action label: {e}")
    
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
        """Update the stocks list and refresh notifications"""
        print(f"DEBUG: Label panel updating stocks ({len(stocks)} stocks)")
        self.stocks = stocks
        self.refresh_notifications()
    
    def manual_refresh(self):
        """Manual refresh button clicked"""
        print(f"DEBUG: Manual refresh clicked (label version)")
        self.refresh_button.config(state="disabled", text="REFRESHING...")
        
        def enable_button():
            try:
                self.refresh_button.config(state="normal", text="REFRESH NOTIFICATIONS")
            except:
                pass
        
        # Re-enable button after 3 seconds
        self.notifications_frame.after(3000, enable_button)
        
        # Refresh notifications
        self.refresh_notifications()
    
    def get_notification_count(self) -> int:
        """Get the number of active notifications"""
        return len(self.actions_data)