"""
Popup Notifications Approach - GUARANTEED VISIBILITY

Creates popup dialogs and top banner notifications that are impossible to miss.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import List
import threading
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.corporate_actions_fetcher import CorporateAction, corporate_actions_fetcher


class PopupNotificationsManager:
    """Manager for popup notifications that are impossible to miss"""
    
    def __init__(self, parent_window, stocks: List = None):
        self.parent_window = parent_window
        self.stocks = stocks or []
        self.actions_data: List[CorporateAction] = []
        self.banner_frame = None
        
        print(f"DEBUG: Creating POPUP notifications manager...")
        self.create_top_banner()
        self.refresh_notifications()
    
    def create_top_banner(self):
        """Create a prominent banner at the top of the main window"""
        
        # Create banner frame at the very top
        self.banner_frame = tk.Frame(
            self.parent_window,
            bg="red",
            relief="solid",
            borderwidth=5,
            height=80
        )
        self.banner_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.banner_frame.grid_propagate(False)  # Maintain fixed height
        
        # Banner label
        self.banner_label = tk.Label(
            self.banner_frame,
            text="LOADING CORPORATE ACTIONS...",
            font=("Arial", 16, "bold"),
            bg="red",
            fg="white",
            wraplength=800
        )
        self.banner_label.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Click handler for banner
        self.banner_label.bind("<Button-1>", self.show_popup_details)
        self.banner_frame.bind("<Button-1>", self.show_popup_details)
        
        print(f"DEBUG: Top banner created")
    
    def refresh_notifications(self):
        """Refresh notifications"""
        print(f"DEBUG: Starting POPUP notifications refresh...")
        
        def fetch_notifications():
            try:
                print(f"DEBUG: Fetching for {len(self.stocks)} stocks...")
                
                if not self.stocks:
                    print(f"DEBUG: No stocks, showing empty")
                    self.update_banner([])
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
                
                print(f"DEBUG: Found {len(actions)} actions for POPUP display...")
                self.update_banner(actions)
                
                # Show popup if actions found
                if actions:
                    self.show_popup_notifications(actions)
                
            except Exception as e:
                print(f"ERROR in POPUP fetch: {e}")
                import traceback
                traceback.print_exc()
                self.update_banner([])
        
        threading.Thread(target=fetch_notifications, daemon=True).start()
    
    def update_banner(self, actions: List[CorporateAction]):
        """Update the top banner"""
        print(f"DEBUG: POPUP banner update with {len(actions)} actions")
        
        def update_on_main_thread():
            try:
                self.actions_data = actions
                count = len(actions)
                
                if count == 0:
                    banner_text = "NO CORPORATE ACTIONS FOUND FOR YOUR PORTFOLIO"
                    banner_bg = "gray"
                else:
                    # Create summary
                    action_summary = []
                    for action in actions[:3]:  # Show first 3
                        action_summary.append(f"{action.symbol} {action.action_type}")
                    
                    if len(actions) > 3:
                        summary_text = ", ".join(action_summary) + f" +{len(actions)-3} more"
                    else:
                        summary_text = ", ".join(action_summary)
                    
                    banner_text = f"FOUND {count} CORPORATE ACTIONS: {summary_text} - CLICK FOR DETAILS"
                    banner_bg = "darkgreen"
                
                self.banner_label.config(text=banner_text, bg=banner_bg)
                self.banner_frame.config(bg=banner_bg)
                
                print(f"DEBUG: Banner updated: {banner_text}")
                
            except Exception as e:
                print(f"ERROR updating banner: {e}")
                import traceback
                traceback.print_exc()
        
        # Main thread update
        try:
            self.parent_window.after(0, update_on_main_thread)
            print(f"DEBUG: Scheduled banner update")
        except Exception as e:
            print(f"ERROR scheduling banner update: {e}")
            update_on_main_thread()
    
    def show_popup_notifications(self, actions: List[CorporateAction]):
        """Show popup dialog with notifications"""
        print(f"DEBUG: Showing popup with {len(actions)} actions")
        
        def show_on_main_thread():
            try:
                # Create popup window
                popup = tk.Toplevel(self.parent_window)
                popup.title("Corporate Actions Alert!")
                popup.geometry("600x500")
                popup.configure(bg="lightyellow")
                popup.lift()
                popup.attributes('-topmost', True)  # Keep on top
                
                # Header
                header_label = tk.Label(
                    popup,
                    text=f"FOUND {len(actions)} CORPORATE ACTIONS!",
                    font=("Arial", 18, "bold"),
                    bg="red",
                    fg="white",
                    pady=10
                )
                header_label.pack(fill="x", padx=10, pady=10)
                
                # Scrollable frame for actions
                canvas = tk.Canvas(popup, bg="white")
                scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
                scrollable_frame = ttk.Frame(canvas)
                
                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )
                
                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)
                
                # Add actions to popup
                for i, action in enumerate(actions):
                    self.create_popup_action(scrollable_frame, action, i)
                
                canvas.pack(side="left", fill="both", expand=True, padx=10)
                scrollbar.pack(side="right", fill="y")
                
                # Close button
                close_button = tk.Button(
                    popup,
                    text="CLOSE",
                    font=("Arial", 14, "bold"),
                    bg="blue",
                    fg="white",
                    command=popup.destroy,
                    pady=5
                )
                close_button.pack(pady=10)
                
                print(f"DEBUG: Popup created successfully")
                
            except Exception as e:
                print(f"ERROR creating popup: {e}")
                import traceback
                traceback.print_exc()
        
        try:
            self.parent_window.after(100, show_on_main_thread)  # Small delay
        except Exception as e:
            print(f"ERROR scheduling popup: {e}")
    
    def create_popup_action(self, parent, action: CorporateAction, index: int):
        """Create action display in popup"""
        try:
            # Calculate days until
            days_until = self.calculate_days_until(action.ex_date)
            
            # Action frame
            action_frame = tk.Frame(
                parent,
                relief="solid",
                borderwidth=2,
                bg="lightyellow",
                padx=10,
                pady=8
            )
            action_frame.pack(fill="x", padx=5, pady=3)
            
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
                action_frame,
                text=title_text,
                font=("Arial", 12, "bold"),
                bg=title_bg,
                fg=title_fg
            )
            title_label.pack(fill="x", pady=2)
            
            # Ex-date
            date_text = f"Ex-Date: {action.ex_date} ({days_until})"
            date_label = tk.Label(
                action_frame,
                text=date_text,
                font=("Arial", 10),
                bg="lightyellow"
            )
            date_label.pack(fill="x")
            
            # Details
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
                fg="darkgreen"
            )
            detail_label.pack(fill="x")
            
            print(f"DEBUG: Created popup action for {action.symbol}")
            
        except Exception as e:
            print(f"ERROR creating popup action: {e}")
    
    def show_popup_details(self, event=None):
        """Show popup when banner is clicked"""
        if self.actions_data:
            self.show_popup_notifications(self.actions_data)
        else:
            messagebox.showinfo("Notifications", "No corporate actions found for your portfolio.")
    
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
        print(f"DEBUG: POPUP manager updating stocks ({len(stocks)} stocks)")
        self.stocks = stocks
        self.refresh_notifications()
    
    def get_notification_count(self) -> int:
        """Get notification count"""
        return len(self.actions_data)