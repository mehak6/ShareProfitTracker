import csv
import os
from datetime import datetime
from typing import List, Dict, Any

try:
    import tkinter.filedialog as fd
    import tkinter.messagebox as mb
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    # Mock the tkinter functions for testing
    class MockFileDialog:
        @staticmethod
        def asksaveasfilename(*args, **kwargs):
            return "mock_export.csv"
        @staticmethod
        def askopenfilename(*args, **kwargs):
            return "mock_import.csv"
    
    class MockMessageBox:
        @staticmethod
        def showerror(title, message):
            print(f"ERROR: {title} - {message}")
        @staticmethod
        def showinfo(title, message):
            print(f"INFO: {title} - {message}")
    
    fd = MockFileDialog()
    mb = MockMessageBox()

class FileHelper:
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], filename: str = None) -> bool:
        try:
            if filename is None:
                filename = fd.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    initialfile=f"portfolio_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                
                if not filename:
                    return False
            
            if not data:
                mb.showerror("Export Error", "No data to export")
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            return True
            
        except Exception as e:
            mb.showerror("Export Error", f"Failed to export data: {str(e)}")
            return False
    
    @staticmethod
    def import_from_csv(filename: str = None) -> List[Dict[str, Any]]:
        try:
            if filename is None:
                filename = fd.askopenfilename(
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
                )
                
                if not filename:
                    return []
            
            data = []
            with open(filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append(dict(row))
            
            return data
            
        except Exception as e:
            mb.showerror("Import Error", f"Failed to import data: {str(e)}")
            return []

class ValidationHelper:
    @staticmethod
    def validate_stock_symbol(symbol: str) -> bool:
        if not symbol or len(symbol.strip()) == 0:
            return False
        
        # Basic validation - alphanumeric and some special characters
        symbol = symbol.strip().upper()
        
        # Must start with a letter, not a number
        if not symbol[0].isalpha():
            return False
        
        # Allow letters, numbers, dots, hyphens, underscores
        allowed_chars = symbol.replace('.', '').replace('-', '').replace('_', '')
        return allowed_chars.isalnum() and len(symbol) >= 2
    
    @staticmethod
    def validate_positive_number(value: str) -> bool:
        try:
            num = float(value)
            return num > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

class FormatHelper:
    @staticmethod
    def format_currency(amount: float, currency_symbol: str = "Rs.") -> str:
        return f"{currency_symbol}{amount:,.2f}"
    
    @staticmethod
    def format_percentage(percentage: float, decimals: int = 2) -> str:
        return f"{percentage:+.{decimals}f}%"
    
    @staticmethod
    def format_number(number: float, decimals: int = 2) -> str:
        return f"{number:,.{decimals}f}"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 30) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."