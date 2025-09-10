import tkinter as tk
from tkinter import ttk
import json
import os

class ThemeManager:
    def __init__(self):
        self.current_theme = "light"
        self.config_file = "theme_config.json"
        self.load_theme_preference()
        
        # Define theme colors
        self.themes = {
            "light": {
                "bg": "#FFFFFF",
                "fg": "#000000",
                "select_bg": "#0078D4",
                "select_fg": "#FFFFFF",
                "entry_bg": "#FFFFFF",
                "entry_fg": "#000000",
                "button_bg": "#F0F0F0",
                "button_fg": "#000000",
                "frame_bg": "#F8F8F8",
                "header_bg": "#E0E0E0",
                "profit_color": "#008000",
                "loss_color": "#FF0000",
                "neutral_color": "#000000",
                "border_color": "#CCCCCC",
                "tree_bg": "#FFFFFF",
                "tree_fg": "#000000",
                "tree_select_bg": "#0078D4",
                "tree_select_fg": "#FFFFFF"
            },
            "dark": {
                "bg": "#2B2B2B",
                "fg": "#FFFFFF",
                "select_bg": "#404040",
                "select_fg": "#FFFFFF",
                "entry_bg": "#404040",
                "entry_fg": "#FFFFFF",
                "button_bg": "#404040",
                "button_fg": "#FFFFFF",
                "frame_bg": "#353535",
                "header_bg": "#404040",
                "profit_color": "#00FF00",
                "loss_color": "#FF6B6B",
                "neutral_color": "#FFFFFF",
                "border_color": "#555555",
                "tree_bg": "#2B2B2B",
                "tree_fg": "#FFFFFF",
                "tree_select_bg": "#0078D4",
                "tree_select_fg": "#FFFFFF"
            }
        }
    
    def load_theme_preference(self):
        """Load saved theme preference"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.current_theme = config.get('theme', 'light')
        except:
            self.current_theme = "light"
    
    def save_theme_preference(self):
        """Save current theme preference"""
        try:
            config = {'theme': self.current_theme}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except:
            pass
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.save_theme_preference()
    
    def get_theme_colors(self):
        """Get current theme colors"""
        return self.themes[self.current_theme]
    
    def is_dark_theme(self):
        """Check if current theme is dark"""
        return self.current_theme == "dark"
    
    def apply_theme_to_widget(self, widget, widget_type="default"):
        """Apply theme to a specific widget"""
        colors = self.get_theme_colors()
        
        try:
            if widget_type == "treeview":
                # Configure treeview styling
                widget.configure(
                    selectbackground=colors["tree_select_bg"],
                    selectforeground=colors["tree_select_fg"]
                )
                
                # Configure treeview tags for profit/loss
                widget.tag_configure("profit", foreground=colors["profit_color"])
                widget.tag_configure("loss", foreground=colors["loss_color"])
                widget.tag_configure("neutral", foreground=colors["neutral_color"])
                
            elif widget_type == "frame":
                widget.configure(bg=colors["frame_bg"])
                
            elif widget_type == "label":
                widget.configure(
                    bg=colors["bg"],
                    fg=colors["fg"]
                )
                
            elif widget_type == "button":
                widget.configure(
                    bg=colors["button_bg"],
                    fg=colors["button_fg"]
                )
                
            elif widget_type == "entry":
                widget.configure(
                    bg=colors["entry_bg"],
                    fg=colors["entry_fg"],
                    insertbackground=colors["fg"]
                )
                
        except Exception:
            # Widget might not support these configurations
            pass
    
    def configure_ttk_styles(self, root):
        """Configure TTK styles for current theme"""
        style = ttk.Style(root)
        colors = self.get_theme_colors()
        
        # Configure Treeview
        style.configure("Treeview",
                       background=colors["tree_bg"],
                       foreground=colors["tree_fg"],
                       fieldbackground=colors["tree_bg"],
                       borderwidth=1,
                       relief="solid",
                       bordercolor=colors["border_color"])
        
        style.configure("Treeview.Heading",
                       background=colors["header_bg"],
                       foreground=colors["fg"],
                       relief="raised",
                       borderwidth=1)
        
        # Configure buttons
        style.configure("TButton",
                       background=colors["button_bg"],
                       foreground=colors["button_fg"],
                       borderwidth=1,
                       focuscolor='none')
        
        # Configure labels
        style.configure("TLabel",
                       background=colors["bg"],
                       foreground=colors["fg"])
        
        # Configure frames
        style.configure("TFrame",
                       background=colors["bg"],
                       borderwidth=1,
                       relief="flat")
        
        # Configure LabelFrame
        style.configure("TLabelframe",
                       background=colors["bg"],
                       foreground=colors["fg"],
                       borderwidth=2,
                       relief="groove")
        
        style.configure("TLabelframe.Label",
                       background=colors["bg"],
                       foreground=colors["fg"])
        
        # Configure Entry
        style.configure("TEntry",
                       fieldbackground=colors["entry_bg"],
                       foreground=colors["entry_fg"],
                       borderwidth=1,
                       insertcolor=colors["fg"])
        
        # Configure Combobox
        style.configure("TCombobox",
                       fieldbackground=colors["entry_bg"],
                       foreground=colors["entry_fg"],
                       background=colors["button_bg"],
                       borderwidth=1,
                       arrowcolor=colors["fg"])
        
        # Map states for hover effects
        style.map("TButton",
                 background=[('active', colors["select_bg"]),
                           ('pressed', colors["select_bg"])])
        
        style.map("Treeview",
                 background=[('selected', colors["tree_select_bg"])],
                 foreground=[('selected', colors["tree_select_fg"])])
        
        # Configure root window
        root.configure(bg=colors["bg"])
        
        return style