import os
from typing import Any, Dict

class AppConfig:
    # Application settings
    APP_NAME = "Share Profit Tracker"
    APP_VERSION = "1.0"
    
    # Database settings
    DATABASE_NAME = "portfolio.db"
    
    # API settings
    PRICE_UPDATE_INTERVAL = 900  # 15 minutes in seconds
    REQUEST_TIMEOUT = 10  # seconds
    
    # UI settings
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 700
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 500
    
    # Currency settings
    CURRENCY_SYMBOL = "Rs."
    CURRENCY_NAME = "INR"
    
    # Export settings
    DEFAULT_EXPORT_FORMAT = "csv"
    
    # Colors
    COLORS = {
        'profit': '#008000',
        'loss': '#FF0000', 
        'neutral': '#000000',
        'background': '#FFFFFF',
        'header': '#F0F0F0'
    }
    
    @classmethod
    def get_database_path(cls) -> str:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(app_dir, cls.DATABASE_NAME)
    
    @classmethod
    def get_backup_path(cls) -> str:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(app_dir, "backups")
    
    @classmethod
    def ensure_directories(cls):
        backup_dir = cls.get_backup_path()
        os.makedirs(backup_dir, exist_ok=True)