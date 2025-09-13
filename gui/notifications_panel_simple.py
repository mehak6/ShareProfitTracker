"""
Simple Corporate Actions Notifications Panel - UNICODE SAFE VERSION

Clear, readable format with bullet points and better formatting.
Fixed all Unicode encoding issues for Windows console.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import List, Optional
import threading
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.corporate_actions_fetcher import CorporateAction, corporate_actions_fetcher


def safe_print(message):
    """Print message safely, handling Unicode encoding errors"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Replace Unicode characters with ASCII equivalents
        safe_message = message.encode('ascii', 'replace').decode('ascii')
        print(safe_message)


class SimpleNotificationsPanel:
    """Simple panel for displaying corporate actions notifications"""
    
    def __init__(self, parent_frame: ttk.Frame, stocks: List = None):
        self.parent_frame = parent_frame
        self.stocks = stocks or []
        self.notifications_frame = None
        self.actions_data: List[CorporateAction] = []
        self.last_refresh = None
        
        self.create_simple_panel()
        self.refresh_notifications()
    
    def create_simple_panel(self):
        """Create simple notifications panel UI"""
        safe_print(f"DEBUG: Creating IMPROVED notifications panel...")
        
        # Main frame
        self.notifications_frame = ttk.LabelFrame(
            self.parent_frame, 
            text="Corporate Actions Notifications", 
            padding="10"
        )
        self.notifications_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.notifications_frame.grid_columnconfigure(0, weight=1)
        self.notifications_frame.grid_rowconfigure(2, weight=1)
        
        # Info label
        self.info_label = ttk.Label(
            self.notifications_frame, 
            text="Loading notifications...",
            font=("Arial", 12, "bold")
        )
        self.info_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Header frame for refresh label and button
        header_frame = ttk.Frame(self.notifications_frame)
        header_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Refresh label
        self.refresh_label = ttk.Label(
            header_frame,
            text="",
            font=("Arial", 9)
        )
        self.refresh_label.grid(row=0, column=0, sticky="w")
        
        # Manual refresh button - Unicode safe
        try:
            button_text = "🔄 Refresh Notifications"
        except UnicodeEncodeError:
            button_text = "Refresh Notifications"
            
        self.refresh_button = ttk.Button(
            header_frame,
            text=button_text,
            command=self.manual_refresh
        )
        self.refresh_button.grid(row=0, column=1, sticky="e", padx=(10, 0))
        
        # Enhanced text widget for notifications
        self.notifications_text = tk.Text(
            self.notifications_frame,
            height=20,
            width=95,
            wrap=tk.WORD,
            font=("Segoe UI", 11),  # Better font
            state=tk.DISABLED,
            bg="#f8f9fa",
            fg="#2c3e50",
            relief="sunken",
            borderwidth=2,
            padx=15,
            pady=10
        )
        self.notifications_text.grid(row=2, column=0, sticky="nsew", pady=(0, 5))
        
        # Scrollbar for text widget
        scrollbar = ttk.Scrollbar(self.notifications_frame, orient="vertical", command=self.notifications_text.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.notifications_text.configure(yscrollcommand=scrollbar.set)
        
        safe_print(f"DEBUG: Improved notifications panel created successfully")
    
    def refresh_notifications(self):
        """Refresh notifications in a background thread"""
        safe_print(f"DEBUG: Starting notifications refresh...")
        
        def fetch_notifications():
            try:
                safe_print(f"DEBUG: Fetching notifications for {len(self.stocks)} stocks...")
                
                if not self.stocks:
                    safe_print(f"DEBUG: No stocks, returning empty notifications")
                    self.update_ui_simple([])
                    return
                
                # Get portfolio symbols
                portfolio_symbols = []
                for stock in self.stocks:
                    portfolio_symbols.append(stock.symbol)
                    if not stock.symbol.endswith('.NS'):
                        portfolio_symbols.append(f"{stock.symbol}.NS")
                
                safe_print(f"DEBUG: Portfolio symbols: {portfolio_symbols[:5]}...")
                
                # Fetch corporate actions
                actions = corporate_actions_fetcher.get_portfolio_corporate_actions(
                    portfolio_symbols, days_ahead=60
                )
                
                safe_print(f"DEBUG: Found {len(actions)} actions, updating UI...")
                self.update_ui_simple(actions)
                
            except Exception as e:
                safe_print(f"ERROR in notifications fetch: {e}")
                import traceback
                traceback.print_exc()
                self.update_ui_simple([])
        
        # Run in background thread
        threading.Thread(target=fetch_notifications, daemon=True).start()
    
    def update_ui_simple(self, actions: List[CorporateAction]):
        """Update UI with simple approach - FORCE MAIN THREAD"""
        safe_print(f"DEBUG: UI update with {len(actions)} actions")
        
        # Force this to run on main thread
        def update_on_main_thread():
            safe_print(f"DEBUG: Running UI update on main thread with {len(actions)} actions")
            try:
                self.actions_data = actions
                self.last_refresh = datetime.now()
                
                self._update_ui_components(actions)
                
            except Exception as e:
                safe_print(f"ERROR in main thread UI update: {e}")
                import traceback
                traceback.print_exc()
        
        # Schedule on main thread
        try:
            self.notifications_frame.after(0, update_on_main_thread)
            safe_print(f"DEBUG: Scheduled UI update on main thread")
        except Exception as e:
            safe_print(f"ERROR scheduling UI update: {e}")
            # Direct call as fallback
            update_on_main_thread()
    
    def _update_ui_components(self, actions: List[CorporateAction]):
        """Update all UI components"""
        safe_print(f"DEBUG: Updating UI components with {len(actions)} actions")
        
        try:
            # Update info label with details
            count = len(actions)
            if count == 0:
                info_text = "No upcoming corporate actions found"
            else:
                # Show the actions in the header
                action_list = []
                for action in actions[:4]:  # Show first 4
                    action_list.append(f"{action.symbol} {action.action_type}")
                
                if len(actions) > 4:
                    action_summary = ", ".join(action_list) + f" +{len(actions)-4} more"
                else:
                    action_summary = ", ".join(action_list)
                    
                # Unicode safe info text
                try:
                    info_text = f"🎯 {count} corporate actions: {action_summary}"
                except UnicodeEncodeError:
                    info_text = f"TARGET {count} corporate actions: {action_summary}"
            
            self.info_label.config(text=info_text)
            safe_print(f"DEBUG: Info label updated")
            
            # Update refresh label
            refresh_text = f"Last updated: {self.last_refresh.strftime('%H:%M:%S')}"
            self.refresh_label.config(text=refresh_text)
            safe_print(f"DEBUG: Refresh label updated")
            
            # Update notifications text
            self.update_notifications_text(actions)
            safe_print(f"DEBUG: All UI components updated successfully")
            
        except Exception as e:
            safe_print(f"ERROR in _update_ui_components: {e}")
            import traceback
            traceback.print_exc()
    
    def update_notifications_text(self, actions: List[CorporateAction]):
        """Update the text widget with IMPROVED notifications"""
        safe_print(f"DEBUG: Updating text widget with {len(actions)} actions")
        
        try:
            # Enable editing
            self.notifications_text.config(state=tk.NORMAL)
            
            # Clear existing content
            self.notifications_text.delete(1.0, tk.END)
            
            if not actions:
                # Unicode safe empty message
                try:
                    empty_text = ("📋 NO UPCOMING CORPORATE ACTIONS\n\n"
                                "• No dividends, splits, or bonus shares scheduled for your portfolio\n"
                                "• We'll update you when new announcements are made\n"
                                "• Check back regularly for new notifications")
                    self.notifications_text.insert(tk.END, empty_text)
                except UnicodeEncodeError:
                    empty_text = ("NO UPCOMING CORPORATE ACTIONS\n\n"
                                "• No dividends, splits, or bonus shares scheduled for your portfolio\n"
                                "• We'll update you when new announcements are made\n"
                                "• Check back regularly for new notifications")
                    self.notifications_text.insert(tk.END, empty_text)
            else:
                # Header with count - Unicode safe
                try:
                    header_text = f"🎯 {len(actions)} UPCOMING CORPORATE ACTION(S) FOR YOUR PORTFOLIO\n{'=' * 85}\n\n"
                    self.notifications_text.insert(tk.END, header_text)
                except UnicodeEncodeError:
                    header_text = f"TARGET {len(actions)} UPCOMING CORPORATE ACTION(S) FOR YOUR PORTFOLIO\n{'=' * 85}\n\n"
                    self.notifications_text.insert(tk.END, header_text)
                
                # Sort by date (earliest first)
                sorted_actions = sorted(actions, key=lambda x: x.ex_date)
                
                for i, action in enumerate(sorted_actions):
                    # Format each action clearly
                    text = self.format_action_clear(action, i + 1)
                    safe_print(f"DEBUG: Inserting action {i+1}: {action.symbol} {action.action_type}")
                    safe_print(f"DEBUG: Action text length: {len(text)}")
                    self.notifications_text.insert(tk.END, text)
                    
                    # Add separator between actions
                    if i < len(sorted_actions) - 1:
                        self.notifications_text.insert(tk.END, "\n" + "─" * 85 + "\n\n")
            
            # Disable editing
            self.notifications_text.config(state=tk.DISABLED)
            
            # Scroll to top
            self.notifications_text.see(1.0)
            
            safe_print(f"DEBUG: Text widget updated successfully")
            
            # DEBUG: Check what's actually in the text widget
            current_content = self.notifications_text.get(1.0, tk.END)
            safe_print(f"DEBUG: Current text widget content length: {len(current_content)}")
            safe_print(f"DEBUG: First 200 chars: {current_content[:200]}")
            
        except Exception as e:
            safe_print(f"ERROR updating text widget: {e}")
            import traceback
            traceback.print_exc()
    
    def format_action_clear(self, action: CorporateAction, index: int) -> str:
        """Format a corporate action with clear bullet points - Unicode safe"""
        try:
            # Calculate days until ex-date
            days_until = self.calculate_days_until(action.ex_date)
            urgency = self.get_urgency_text(days_until)
            
            # Main header with icon based on action type - Unicode safe
            try:
                action_icon = self.get_action_icon(action.action_type)
                text = f"{index}. {action_icon} {action.symbol} - {action.action_type.upper()} {urgency}\n"
            except UnicodeEncodeError:
                text = f"{index}. {action.symbol} - {action.action_type.upper()} {urgency}\n"
            
            # Company name - Unicode safe
            if action.company_name:
                try:
                    text += f"   🏢 Company: {action.company_name}\n"
                except UnicodeEncodeError:
                    text += f"   Company: {action.company_name}\n"
            
            # Ex-date with countdown - Unicode safe
            try:
                text += f"   📅 Ex-Date: {action.ex_date} ({days_until})\n"
            except UnicodeEncodeError:
                text += f"   Ex-Date: {action.ex_date} ({days_until})\n"
            
            # Action-specific details with clear explanations - Unicode safe
            if action.action_type.lower() == 'dividend' and action.dividend_amount:
                try:
                    text += f"   💰 Dividend: Rs. {action.dividend_amount} per share\n"
                    text += f"   💡 What you get: Rs. {action.dividend_amount} for each share you own\n"
                except UnicodeEncodeError:
                    text += f"   Dividend: Rs. {action.dividend_amount} per share\n"
                    text += f"   What you get: Rs. {action.dividend_amount} for each share you own\n"
            
            elif action.action_type.lower() == 'split':
                if action.ratio_from and action.ratio_to:
                    try:
                        text += f"   🔄 Split Ratio: {action.ratio_from}:{action.ratio_to}\n"
                        text += f"   💡 What happens: Each {action.ratio_from} share becomes {action.ratio_to} shares\n"
                        text += f"   📌 Note: Share price will adjust proportionally\n"
                    except UnicodeEncodeError:
                        text += f"   Split Ratio: {action.ratio_from}:{action.ratio_to}\n"
                        text += f"   What happens: Each {action.ratio_from} share becomes {action.ratio_to} shares\n"
                        text += f"   Note: Share price will adjust proportionally\n"
                else:
                    try:
                        text += f"   🔄 Stock Split announced\n"
                        text += f"   💡 What happens: More shares at lower price per share\n"
                    except UnicodeEncodeError:
                        text += f"   Stock Split announced\n"
                        text += f"   What happens: More shares at lower price per share\n"
            
            elif action.action_type.lower() == 'bonus':
                if action.ratio_from and action.ratio_to:
                    try:
                        text += f"   🎁 Bonus Ratio: {action.ratio_from}:{action.ratio_to}\n"
                        text += f"   💡 What you get: {action.ratio_to} FREE shares for every {action.ratio_from} shares owned\n"
                    except UnicodeEncodeError:
                        text += f"   Bonus Ratio: {action.ratio_from}:{action.ratio_to}\n"
                        text += f"   What you get: {action.ratio_to} FREE shares for every {action.ratio_from} shares owned\n"
                else:
                    try:
                        text += f"   🎁 Bonus Shares announced\n"
                        text += f"   💡 What you get: Free additional shares\n"
                    except UnicodeEncodeError:
                        text += f"   Bonus Shares announced\n"
                        text += f"   What you get: Free additional shares\n"
            
            # Purpose if available - Unicode safe
            if action.purpose and action.purpose.strip():
                try:
                    text += f"   📝 Purpose: {action.purpose}\n"
                except UnicodeEncodeError:
                    text += f"   Purpose: {action.purpose}\n"
            
            # Important eligibility note - Unicode safe
            try:
                text += f"   ⚠️  ELIGIBILITY: You must own shares BEFORE {action.ex_date} to qualify!\n"
            except UnicodeEncodeError:
                text += f"   WARNING: You must own shares BEFORE {action.ex_date} to qualify!\n"
            
            return text
            
        except Exception as e:
            safe_print(f"ERROR formatting action: {e}")
            return f"{index}. {action.symbol} - {action.action_type.upper()} on {action.ex_date}\n"
    
    def get_action_icon(self, action_type: str) -> str:
        """Get icon for action type - Unicode safe"""
        try:
            action_lower = action_type.lower()
            if action_lower == 'dividend':
                return '💵'
            elif action_lower == 'split':
                return '✂️'
            elif action_lower == 'bonus':
                return '🎁'
            else:
                return '📈'
        except UnicodeEncodeError:
            # Fallback to text symbols
            action_lower = action_type.lower()
            if action_lower == 'dividend':
                return '$'
            elif action_lower == 'split':
                return '*'
            elif action_lower == 'bonus':
                return '+'
            else:
                return '^'
    
    def calculate_days_until(self, ex_date_str: str) -> str:
        """Calculate days until ex-date"""
        try:
            from datetime import datetime
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
    
    def get_urgency_text(self, days_until_str: str) -> str:
        """Get urgency indicator - Unicode safe"""
        try:
            if "TODAY" in days_until_str:
                return "🚨 URGENT!"
            elif "Tomorrow" in days_until_str or "in 1 days" in days_until_str:
                return "⚡ TOMORROW!"
            elif any(x in days_until_str for x in ["in 2 days", "in 3 days", "in 4 days", "in 5 days"]):
                return "⏰ SOON"
            else:
                return ""
        except UnicodeEncodeError:
            if "TODAY" in days_until_str:
                return "URGENT!"
            elif "Tomorrow" in days_until_str or "in 1 days" in days_until_str:
                return "TOMORROW!"
            elif any(x in days_until_str for x in ["in 2 days", "in 3 days", "in 4 days", "in 5 days"]):
                return "SOON"
            else:
                return ""
    
    def update_stocks(self, stocks: List):
        """Update the stocks list and refresh notifications"""
        safe_print(f"DEBUG: Panel updating stocks ({len(stocks)} stocks)")
        self.stocks = stocks
        self.refresh_notifications()
    
    def manual_refresh(self):
        """Manual refresh button clicked"""
        safe_print(f"DEBUG: Manual refresh button clicked")
        
        # Unicode safe button text
        try:
            refreshing_text = "🔄 Refreshing..."
            normal_text = "🔄 Refresh Notifications"
        except UnicodeEncodeError:
            refreshing_text = "Refreshing..."
            normal_text = "Refresh Notifications"
            
        self.refresh_button.config(state="disabled", text=refreshing_text)
        
        def enable_button():
            try:
                self.refresh_button.config(state="normal", text=normal_text)
            except:
                pass
        
        # Re-enable button after 3 seconds
        self.notifications_frame.after(3000, enable_button)
        
        # Refresh notifications
        self.refresh_notifications()
    
    def get_notification_count(self) -> int:
        """Get the number of active notifications"""
        return len(self.actions_data)