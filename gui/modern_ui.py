import tkinter as tk
from tkinter import ttk
import platform

class ModernUI:
    """Modern UI enhancements for ShareProfitTracker"""
    
    # Enhanced Color scheme with modern gradients
    COLORS = {
        'primary': '#2E3440',      # Dark blue-gray
        'primary_light': '#434C5E', # Lighter primary
        'primary_dark': '#242932',  # Darker primary
        'secondary': '#3B4252',    # Lighter blue-gray
        'accent': '#5E81AC',       # Blue accent
        'accent_light': '#81A1C1', # Light blue accent
        'accent_dark': '#4C729E',  # Dark blue accent
        'success': '#A3BE8C',      # Green
        'success_light': '#B8C9A5', # Light green
        'success_dark': '#8FA373',  # Dark green
        'warning': '#EBCB8B',      # Yellow
        'warning_light': '#F0D5A0', # Light yellow
        'warning_dark': '#E0B871',  # Dark yellow
        'danger': '#BF616A',       # Red
        'danger_light': '#CC7A84',  # Light red
        'danger_dark': '#A54E56',   # Dark red
        'text': '#2E3440',         # Dark text
        'text_light': '#4C566A',   # Light text
        'text_white': '#FFFFFF',   # White text
        'background': '#ECEFF4',   # Light background
        'surface': '#FFFFFF',      # White surface
        'surface_raised': '#F8F9FA', # Slightly raised surface
        'border': '#D8DEE9',       # Light border
        'border_focus': '#88C0D0', # Focus border
        'shadow': 'gray75'         # Shadow color
    }
    
    # Typography
    FONTS = {
        'heading': ('Segoe UI', 14, 'bold'),
        'subheading': ('Segoe UI', 12, 'bold'),
        'body': ('Segoe UI', 10),
        'body_bold': ('Segoe UI', 10, 'bold'),
        'small': ('Segoe UI', 9),
        'caption': ('Segoe UI', 8)
    }
    
    # Unicode icons (work without external files)
    ICONS = {
        'add': '➕',
        'edit': '✏️',
        'delete': '🗑️',
        'refresh': '🔄',
        'save': '💾',
        'export': '📊',
        'import': '📥',
        'settings': '⚙️',
        'info': 'ℹ️',
        'warning': '⚠️',
        'success': '✅',
        'error': '❌',
        'money': '💰',
        'chart': '📈',
        'dividend': '💵',
        'portfolio': '📂',
        'stock': '📊',
        'search': '🔍',
        'calendar': '📅',
        'up_arrow': '↗️',
        'down_arrow': '↘️',
        'menu': '☰',
        'close': '✖️',
        'help': '❓'
    }
    
    @classmethod
    def configure_style(cls, root):
        """Configure modern ttk styles with advanced visual effects"""
        style = ttk.Style()
        
        # Configure highly visible button styles
        style.configure(
            'Modern.TButton',
            padding=(12, 8),
            font=cls.FONTS['body_bold'],
            focuscolor='none',
            relief='raised',
            background='lightgray',
            foreground='black',
            borderwidth=2,
            lightcolor='white',
            darkcolor='gray'
        )
        
        # Hover and press states for Modern.TButton
        style.map('Modern.TButton',
            background=[
                ('active', 'silver'),
                ('pressed', 'darkgray'),
                ('focus', 'lightblue')
            ],
            relief=[
                ('pressed', 'sunken'),
                ('!pressed', 'raised')
            ],
            borderwidth=[
                ('focus', 3),
                ('!focus', 2)
            ]
        )
        
        style.configure(
            'Accent.TButton',
            padding=(12, 8),
            font=cls.FONTS['body_bold'],
            focuscolor='none',
            relief='raised',
            background='lightblue',
            foreground='black',
            borderwidth=2,
            lightcolor='white',
            darkcolor='steelblue'
        )
        
        # Hover and press states for Accent.TButton
        style.map('Accent.TButton',
            background=[
                ('active', 'skyblue'),
                ('pressed', 'steelblue'),
                ('focus', 'dodgerblue')
            ],
            foreground=[
                ('active', 'black'),
                ('pressed', 'black'),
                ('focus', 'black')
            ],
            relief=[
                ('pressed', 'sunken'),
                ('!pressed', 'raised')
            ],
            borderwidth=[
                ('focus', 3),
                ('!focus', 2)
            ]
        )
        
        style.configure(
            'Success.TButton',
            padding=(12, 8),
            font=cls.FONTS['body_bold'],
            focuscolor='none',
            relief='raised',
            background='lightgreen',
            foreground='black',
            borderwidth=2,
            lightcolor='white',
            darkcolor='darkgreen'
        )
        
        # Hover and press states for Success.TButton
        style.map('Success.TButton',
            background=[
                ('active', 'palegreen'),
                ('pressed', 'darkgreen'),
                ('focus', 'limegreen')
            ],
            foreground=[
                ('active', 'black'),
                ('pressed', 'black'),
                ('focus', 'black')
            ],
            relief=[
                ('pressed', 'sunken'),
                ('!pressed', 'raised')
            ],
            borderwidth=[
                ('focus', 3),
                ('!focus', 2)
            ]
        )
        
        style.configure(
            'Warning.TButton',
            padding=(12, 8),
            font=cls.FONTS['body_bold'],
            focuscolor='none',
            relief='raised',
            background='orange',
            foreground='black',
            borderwidth=2,
            lightcolor='yellow',
            darkcolor='darkorange'
        )
        
        # Hover and press states for Warning.TButton
        style.map('Warning.TButton',
            background=[
                ('active', 'yellow'),
                ('pressed', 'darkorange'),
                ('focus', 'gold')
            ],
            relief=[
                ('pressed', 'sunken'),
                ('!pressed', 'raised')
            ],
            borderwidth=[
                ('focus', 3),
                ('!focus', 2)
            ]
        )
        
        style.configure(
            'Danger.TButton',
            padding=(12, 8),
            font=cls.FONTS['body_bold'],
            focuscolor='none',
            relief='raised',
            background='lightcoral',
            foreground='black',
            borderwidth=2,
            lightcolor='white',
            darkcolor='darkred'
        )
        
        # Hover and press states for Danger.TButton
        style.map('Danger.TButton',
            background=[
                ('active', 'mistyrose'),
                ('pressed', 'darkred'),
                ('focus', 'red')
            ],
            foreground=[
                ('active', 'black'),
                ('pressed', 'black'),
                ('focus', 'black')
            ],
            relief=[
                ('pressed', 'sunken'),
                ('!pressed', 'raised')
            ],
            borderwidth=[
                ('focus', 3),
                ('!focus', 2)
            ]
        )
        
        style.configure(
            'Icon.TButton',
            padding=(8, 6),
            font=cls.FONTS['body'],
            focuscolor='none',
            relief='raised',
            background='lightsteelblue',
            foreground='black',
            borderwidth=2,
            lightcolor='white',
            darkcolor='steelblue'
        )
        
        # Hover and press states for Icon.TButton
        style.map('Icon.TButton',
            background=[
                ('active', 'lightblue'),
                ('pressed', 'steelblue'),
                ('focus', 'skyblue')
            ],
            relief=[
                ('pressed', 'sunken'),
                ('!pressed', 'raised')
            ],
            borderwidth=[
                ('focus', 3),
                ('!focus', 2)
            ]
        )
        
        # Configure frame styles
        style.configure(
            'Card.TFrame',
            relief='solid',
            borderwidth=1
        )
        
        style.configure(
            'Dashboard.TFrame',
            padding=10
        )
        
        # Configure label styles
        style.configure(
            'Heading.TLabel',
            font=cls.FONTS['heading']
        )
        
        style.configure(
            'Subheading.TLabel',
            font=cls.FONTS['subheading']
        )
        
        style.configure(
            'Success.TLabel',
            font=cls.FONTS['body_bold'],
            foreground=cls.COLORS['success']
        )
        
        style.configure(
            'Danger.TLabel',
            font=cls.FONTS['body_bold'],
            foreground=cls.COLORS['danger']
        )
        
        style.configure(
            'Metric.TLabel',
            font=cls.FONTS['heading'],
            anchor='center'
        )
        
        return style
    
    @classmethod
    def create_icon_button(cls, parent, text, icon_key, command=None, style='Modern.TButton'):
        """Create a button with icon and text"""
        icon = cls.ICONS.get(icon_key, '')
        button_text = f"{icon} {text}" if icon else text
        
        button = ttk.Button(
            parent,
            text=button_text,
            command=command,
            style=style
        )
        return button
    
    @classmethod
    def create_metric_card(cls, parent, title, value, change=None, change_type=None):
        """Create a metric card for dashboard"""
        card_frame = ttk.Frame(parent, style='Card.TFrame', padding=15)
        
        # Title
        title_label = ttk.Label(
            card_frame,
            text=title,
            style='Subheading.TLabel'
        )
        title_label.pack()
        
        # Value
        value_label = ttk.Label(
            card_frame,
            text=value,
            style='Metric.TLabel'
        )
        value_label.pack(pady=(5, 0))
        
        # Change indicator
        if change is not None:
            icon = cls.ICONS['up_arrow'] if change_type == 'positive' else cls.ICONS['down_arrow']
            color = cls.COLORS['success'] if change_type == 'positive' else cls.COLORS['danger']
            
            change_label = ttk.Label(
                card_frame,
                text=f"{icon} {change}",
                font=cls.FONTS['small'],
                foreground=color
            )
            change_label.pack()
        
        return card_frame
    
    @classmethod
    def create_modern_toolbar(cls, parent):
        """Create a modern toolbar with advanced styled icons"""
        toolbar_frame = ttk.Frame(parent, padding=(15, 8))
        
        # Left side buttons
        left_frame = ttk.Frame(toolbar_frame)
        left_frame.pack(side='left', fill='x', expand=True)
        
        # Enhanced button configuration with new styles
        buttons = [
            ('Add Stock', 'add', 'Success.TButton'),      # Green for positive action
            ('Refresh Prices', 'refresh', 'Accent.TButton'), # Blue accent for main action
            ('Export Report', 'export', 'Modern.TButton')    # Standard for utility
        ]
        
        for text, icon, style in buttons:
            btn = cls.create_icon_button(left_frame, text, icon, style=style)
            btn.pack(side='left', padx=(0, 15))  # Increased spacing
        
        # Right side buttons
        right_frame = ttk.Frame(toolbar_frame)
        right_frame.pack(side='right')
        
        settings_btn = cls.create_icon_button(right_frame, 'Settings', 'settings', style='Icon.TButton')
        settings_btn.pack(side='right')
        
        return toolbar_frame, left_frame, right_frame
    
    @classmethod
    def create_action_buttons(cls, parent, actions):
        """Create a set of action buttons with appropriate styles"""
        button_frame = ttk.Frame(parent, padding=(10, 5))
        
        for action_text, icon_key, action_type, command in actions:
            # Choose style based on action type
            if action_type == 'primary':
                style = 'Accent.TButton'
            elif action_type == 'success':
                style = 'Success.TButton'
            elif action_type == 'warning':
                style = 'Warning.TButton'
            elif action_type == 'danger':
                style = 'Danger.TButton'
            else:
                style = 'Modern.TButton'
            
            btn = cls.create_icon_button(
                button_frame, 
                action_text, 
                icon_key, 
                command=command, 
                style=style
            )
            btn.pack(side='left', padx=(0, 10))
        
        return button_frame
    
    @classmethod
    def create_dashboard_summary(cls, parent):
        """Create dashboard summary section"""
        dashboard_frame = ttk.Frame(parent, style='Dashboard.TFrame')
        
        # Title
        title_label = ttk.Label(
            dashboard_frame,
            text=f"{cls.ICONS['portfolio']} Portfolio Overview",
            style='Heading.TLabel'
        )
        title_label.pack(anchor='w', pady=(0, 15))
        
        # Metrics container
        metrics_frame = ttk.Frame(dashboard_frame)
        metrics_frame.pack(fill='x')
        
        return dashboard_frame, metrics_frame
    
    @classmethod
    def apply_treeview_styling(cls, treeview):
        """Apply modern styling to treeview"""
        style = ttk.Style()
        
        # Configure treeview
        style.configure(
            'Modern.Treeview',
            font=cls.FONTS['body'],
            rowheight=25
        )
        
        style.configure(
            'Modern.Treeview.Heading',
            font=cls.FONTS['body_bold'],
            padding=(5, 5)
        )
        
        treeview.configure(style='Modern.Treeview')
        
        return treeview

class MetricCalculator:
    """Calculate metrics for dashboard"""
    
    @staticmethod
    def calculate_portfolio_metrics(stocks):
        """Calculate portfolio summary metrics"""
        if not stocks:
            return {
                'total_investment': 0.0,
                'current_value': 0.0,
                'total_gain_loss': 0.0,
                'total_gain_loss_pct': 0.0,
                'total_stocks': 0
            }
        
        total_investment = sum(stock.total_investment for stock in stocks)
        current_value = sum(stock.current_value for stock in stocks)
        total_gain_loss = current_value - total_investment
        total_gain_loss_pct = (total_gain_loss / total_investment * 100) if total_investment > 0 else 0.0
        
        return {
            'total_investment': total_investment,
            'current_value': current_value,
            'total_gain_loss': total_gain_loss,
            'total_gain_loss_pct': total_gain_loss_pct,
            'total_stocks': len(stocks)
        }
    
    @staticmethod
    def format_currency(amount):
        """Format currency with proper symbol"""
        if amount >= 0:
            return f"₹{amount:,.2f}"
        else:
            return f"-₹{abs(amount):,.2f}"
    
    @staticmethod
    def format_percentage(pct):
        """Format percentage with proper sign"""
        if pct >= 0:
            return f"+{pct:.2f}%"
        else:
            return f"{pct:.2f}%"