"""
Settings Dialog for ShareProfitTracker

Provides configuration options for notifications, preferences, and application settings.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.modern_ui import ModernUI
from utils.config import AppConfig


class SettingsDialog:
    """Settings dialog for application preferences"""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = None
        self.settings_file = "data/user_settings.json"
        self.settings = self.load_settings()
        
        self.create_dialog()
        
    def create_dialog(self):
        """Create the settings dialog window"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("⚙️ Settings")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()  # Make it modal
        
        # Center the dialog
        self.dialog.transient(self.parent)
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")
        
        # Create main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="⚙️ Application Settings",
            font=ModernUI.FONTS['heading']
        )
        title_label.pack(anchor="w", pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=(0, 20))
        
        # Notifications tab
        self.create_notifications_tab(notebook)
        
        # General tab
        self.create_general_tab(notebook)
        
        # About tab
        self.create_about_tab(notebook)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        # Cancel button
        ttk.Button(
            buttons_frame, 
            text="Cancel", 
            command=self.on_cancel
        ).pack(side="right", padx=(10, 0))
        
        # Save button
        ttk.Button(
            buttons_frame, 
            text="💾 Save Settings", 
            command=self.on_save,
            style='Accent.TButton'
        ).pack(side="right")
        
        # Reset button
        ttk.Button(
            buttons_frame, 
            text="🔄 Reset to Defaults", 
            command=self.on_reset
        ).pack(side="left")
        
    def create_notifications_tab(self, notebook):
        """Create notifications settings tab"""
        notifications_frame = ttk.Frame(notebook, padding="15")
        notebook.add(notifications_frame, text="📢 Notifications")
        
        # Notifications settings
        ttk.Label(
            notifications_frame,
            text="Corporate Actions Notifications",
            font=ModernUI.FONTS['subheading']
        ).pack(anchor="w", pady=(0, 10))
        
        # Days ahead setting
        days_frame = ttk.Frame(notifications_frame)
        days_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(days_frame, text="Show notifications for next:").pack(side="left")
        
        self.days_ahead_var = tk.StringVar(value=str(self.settings.get('notifications_days_ahead', 60)))
        days_spinbox = ttk.Spinbox(
            days_frame,
            from_=7,
            to=365,
            textvariable=self.days_ahead_var,
            width=10,
            state="readonly"
        )
        days_spinbox.pack(side="left", padx=(10, 5))
        
        ttk.Label(days_frame, text="days").pack(side="left")
        
        # Auto-refresh setting
        refresh_frame = ttk.Frame(notifications_frame)
        refresh_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(refresh_frame, text="Auto-refresh notifications every:").pack(side="left")
        
        self.refresh_hours_var = tk.StringVar(value=str(self.settings.get('auto_refresh_hours', 24)))
        refresh_spinbox = ttk.Spinbox(
            refresh_frame,
            from_=1,
            to=168,
            textvariable=self.refresh_hours_var,
            width=10,
            state="readonly"
        )
        refresh_spinbox.pack(side="left", padx=(10, 5))
        
        ttk.Label(refresh_frame, text="hours").pack(side="left")
        
        # Enable notifications checkbox
        self.enable_notifications_var = tk.BooleanVar(value=self.settings.get('enable_notifications', True))
        ttk.Checkbutton(
            notifications_frame,
            text="Enable corporate actions notifications",
            variable=self.enable_notifications_var
        ).pack(anchor="w", pady=(10, 0))
        
        # Show high priority only
        self.high_priority_only_var = tk.BooleanVar(value=self.settings.get('high_priority_only', False))
        ttk.Checkbutton(
            notifications_frame,
            text="Show only high priority notifications (within 7 days)",
            variable=self.high_priority_only_var
        ).pack(anchor="w", pady=(5, 0))
        
    def create_general_tab(self, notebook):
        """Create general settings tab"""
        general_frame = ttk.Frame(notebook, padding="15")
        notebook.add(general_frame, text="⚙️ General")
        
        # Theme settings
        ttk.Label(
            general_frame,
            text="Appearance",
            font=ModernUI.FONTS['subheading']
        ).pack(anchor="w", pady=(0, 10))
        
        # Currency format
        currency_frame = ttk.Frame(general_frame)
        currency_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(currency_frame, text="Currency Symbol:").pack(side="left")
        
        self.currency_var = tk.StringVar(value=self.settings.get('currency_symbol', '₹'))
        currency_combo = ttk.Combobox(
            currency_frame,
            textvariable=self.currency_var,
            values=['₹', '$', '€', '£', '¥'],
            width=5,
            state="readonly"
        )
        currency_combo.pack(side="left", padx=(10, 0))
        
        # Auto-save portfolio
        self.auto_save_var = tk.BooleanVar(value=self.settings.get('auto_save_portfolio', True))
        ttk.Checkbutton(
            general_frame,
            text="Auto-save portfolio changes",
            variable=self.auto_save_var
        ).pack(anchor="w", pady=(10, 0))
        
        # Show debug info
        self.show_debug_var = tk.BooleanVar(value=self.settings.get('show_debug_info', False))
        ttk.Checkbutton(
            general_frame,
            text="Show debug information in console",
            variable=self.show_debug_var
        ).pack(anchor="w", pady=(5, 0))
        
        # Data source priority
        ttk.Label(
            general_frame,
            text="Data Sources",
            font=ModernUI.FONTS['subheading']
        ).pack(anchor="w", pady=(20, 10))
        
        # Price data priority
        price_frame = ttk.Frame(general_frame)
        price_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(price_frame, text="Price data priority:").pack(side="left")
        
        self.price_source_var = tk.StringVar(value=self.settings.get('price_source_priority', 'NSE'))
        price_combo = ttk.Combobox(
            price_frame,
            textvariable=self.price_source_var,
            values=['NSE', 'BSE', 'Yahoo Finance'],
            width=15,
            state="readonly"
        )
        price_combo.pack(side="left", padx=(10, 0))
        
    def create_about_tab(self, notebook):
        """Create about tab"""
        about_frame = ttk.Frame(notebook, padding="15")
        notebook.add(about_frame, text="ℹ️ About")
        
        # App info
        info_frame = ttk.Frame(about_frame)
        info_frame.pack(fill="x", pady=(20, 0))
        
        # App icon and name
        title_frame = ttk.Frame(info_frame)
        title_frame.pack(anchor="w", pady=(0, 15))
        
        ttk.Label(
            title_frame,
            text="📊 ShareProfitTracker",
            font=ModernUI.FONTS['heading']
        ).pack(side="left")
        
        # Version
        ttk.Label(
            info_frame,
            text=f"Version: {AppConfig.APP_VERSION}",
            font=ModernUI.FONTS['body']
        ).pack(anchor="w", pady=(0, 5))
        
        # Description
        description = (
            "A comprehensive portfolio tracking application for Indian and international stocks. "
            "Features include real-time price tracking, profit/loss calculations, dividend tracking, "
            "and corporate actions notifications."
        )
        
        desc_label = ttk.Label(
            info_frame,
            text=description,
            font=ModernUI.FONTS['small'],
            foreground=ModernUI.COLORS['text_light'],
            wraplength=400
        )
        desc_label.pack(anchor="w", pady=(10, 20))
        
        # Features
        features_label = ttk.Label(
            info_frame,
            text="✨ Key Features:",
            font=ModernUI.FONTS['subheading']
        )
        features_label.pack(anchor="w", pady=(0, 10))
        
        features = [
            "📈 Real-time stock price tracking",
            "💰 Profit/loss calculations",
            "📢 Corporate actions notifications",
            "📊 Portfolio performance metrics",
            "💾 Data export capabilities",
            "🎨 Modern user interface"
        ]
        
        for feature in features:
            ttk.Label(
                info_frame,
                text=f"  {feature}",
                font=ModernUI.FONTS['small']
            ).pack(anchor="w", pady=(2, 0))
        
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        default_settings = {
            'notifications_days_ahead': 60,
            'auto_refresh_hours': 24,
            'enable_notifications': True,
            'high_priority_only': False,
            'currency_symbol': '₹',
            'auto_save_portfolio': True,
            'show_debug_info': False,
            'price_source_priority': 'NSE'
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    user_settings = json.load(f)
                    # Merge with defaults
                    default_settings.update(user_settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
            
        return default_settings
    
    def save_settings(self, settings: Dict[str, Any]):
        """Save settings to file"""
        try:
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current settings from UI"""
        return {
            'notifications_days_ahead': int(self.days_ahead_var.get()),
            'auto_refresh_hours': int(self.refresh_hours_var.get()),
            'enable_notifications': self.enable_notifications_var.get(),
            'high_priority_only': self.high_priority_only_var.get(),
            'currency_symbol': self.currency_var.get(),
            'auto_save_portfolio': self.auto_save_var.get(),
            'show_debug_info': self.show_debug_var.get(),
            'price_source_priority': self.price_source_var.get()
        }
    
    def on_save(self):
        """Save settings and close dialog"""
        try:
            current_settings = self.get_current_settings()
            self.save_settings(current_settings)
            
            messagebox.showinfo(
                "Settings Saved", 
                "Settings have been saved successfully.\n\n"
                "Some changes may require restarting the application."
            )
            
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def on_cancel(self):
        """Cancel without saving"""
        self.dialog.destroy()
    
    def on_reset(self):
        """Reset to default settings"""
        if messagebox.askyesno(
            "Reset Settings", 
            "Are you sure you want to reset all settings to defaults?\n\n"
            "This action cannot be undone."
        ):
            # Reset UI to defaults
            self.days_ahead_var.set("60")
            self.refresh_hours_var.set("24")
            self.enable_notifications_var.set(True)
            self.high_priority_only_var.set(False)
            self.currency_var.set("₹")
            self.auto_save_var.set(True)
            self.show_debug_var.set(False)
            self.price_source_var.set("NSE")
            
            messagebox.showinfo("Reset Complete", "Settings have been reset to defaults.")
    
    @staticmethod
    def get_user_setting(key: str, default=None):
        """Get a specific user setting"""
        settings_file = "data/user_settings.json"
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get(key, default)
        except Exception:
            pass
        return default