import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        with self.get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    company_name TEXT,
                    quantity REAL NOT NULL,
                    purchase_price REAL NOT NULL,
                    purchase_date TEXT NOT NULL,
                    broker TEXT,
                    cash_invested REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS price_cache (
                    symbol TEXT PRIMARY KEY,
                    current_price REAL,
                    last_updated TEXT
                );
                
                CREATE TABLE IF NOT EXISTS cash_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_type TEXT NOT NULL, -- 'deposit', 'withdrawal'
                    amount REAL NOT NULL,
                    description TEXT,
                    transaction_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS other_expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL, -- 'electricity', 'rent', 'food', etc.
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    expense_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Add cash_invested column to existing tables if it doesn't exist
            try:
                conn.execute('ALTER TABLE stocks ADD COLUMN cash_invested REAL DEFAULT 0')
                conn.commit()
            except:
                pass  # Column already exists
                
            conn.commit()
    
    def add_stock(self, symbol: str, company_name: str, quantity: float, 
                  purchase_price: float, purchase_date: str, broker: str = "", 
                  cash_invested: float = 0) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # If cash_invested is not provided or is 0, calculate it from quantity * price
            if cash_invested == 0:
                cash_invested = quantity * purchase_price
                
            cursor.execute('''
                INSERT INTO stocks (symbol, company_name, quantity, purchase_price, 
                                  purchase_date, broker, cash_invested, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol.upper(), company_name, quantity, purchase_price, 
                  purchase_date, broker, cash_invested, datetime.now().isoformat()))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_stocks(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, pc.current_price, pc.last_updated
                FROM stocks s
                LEFT JOIN price_cache pc ON s.symbol = pc.symbol
                ORDER BY s.symbol
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stock_by_id(self, stock_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, pc.current_price, pc.last_updated
                FROM stocks s
                LEFT JOIN price_cache pc ON s.symbol = pc.symbol
                WHERE s.id = ?
            ''', (stock_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_stock(self, stock_id: int, symbol: str, company_name: str, 
                     quantity: float, purchase_price: float, purchase_date: str, 
                     broker: str = "", cash_invested: float = None):
        with self.get_connection() as conn:
            # If cash_invested is not provided, calculate it from quantity * price
            if cash_invested is None:
                cash_invested = quantity * purchase_price
                
            conn.execute('''
                UPDATE stocks 
                SET symbol = ?, company_name = ?, quantity = ?, purchase_price = ?,
                    purchase_date = ?, broker = ?, cash_invested = ?
                WHERE id = ?
            ''', (symbol.upper(), company_name, quantity, purchase_price, 
                  purchase_date, broker, cash_invested, stock_id))
            conn.commit()
    
    def delete_stock(self, stock_id: int):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM stocks WHERE id = ?', (stock_id,))
            conn.commit()
    
    def update_price_cache(self, symbol: str, current_price: float):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO price_cache (symbol, current_price, last_updated)
                VALUES (?, ?, ?)
            ''', (symbol.upper(), current_price, datetime.now().isoformat()))
            conn.commit()
    
    def get_cached_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT current_price, last_updated
                FROM price_cache
                WHERE symbol = ?
            ''', (symbol.upper(),))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_unique_symbols(self) -> List[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT symbol FROM stocks ORDER BY symbol')
            return [row[0] for row in cursor.fetchall()]
    
    def backup_database(self, backup_path: str):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'rb') as source:
                with open(backup_path, 'wb') as backup:
                    backup.write(source.read())
    
    # Cash Management Methods
    def add_cash_transaction(self, transaction_type: str, amount: float, 
                           description: str = "", transaction_date: str = None) -> int:
        if transaction_date is None:
            transaction_date = datetime.now().strftime("%Y-%m-%d")
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cash_transactions (transaction_type, amount, description, 
                                             transaction_date, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (transaction_type, amount, description, transaction_date, 
                  datetime.now().isoformat()))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_cash_transactions(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM cash_transactions 
                ORDER BY transaction_date DESC, created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_current_cash_balance(self) -> float:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COALESCE(SUM(CASE WHEN transaction_type = 'deposit' THEN amount ELSE 0 END), 0) as deposits,
                    COALESCE(SUM(CASE WHEN transaction_type = 'withdrawal' THEN amount ELSE 0 END), 0) as withdrawals
                FROM cash_transactions
            ''')
            row = cursor.fetchone()
            if row:
                return row['deposits'] - row['withdrawals']
            return 0.0
    
    def delete_cash_transaction(self, transaction_id: int):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM cash_transactions WHERE id = ?', (transaction_id,))
            conn.commit()
    
    # Expense Management Methods
    def add_expense(self, category: str, description: str, amount: float, 
                   expense_date: str = None) -> int:
        if expense_date is None:
            expense_date = datetime.now().strftime("%Y-%m-%d")
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO other_expenses (category, description, amount, 
                                          expense_date, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (category, description, amount, expense_date, 
                  datetime.now().isoformat()))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_expenses(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM other_expenses 
                ORDER BY expense_date DESC, created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_expenses_by_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM other_expenses 
                WHERE strftime('%Y', expense_date) = ? 
                  AND strftime('%m', expense_date) = ?
                ORDER BY expense_date DESC
            ''', (str(year), f"{month:02d}"))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_expense(self, expense_id: int):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM other_expenses WHERE id = ?', (expense_id,))
            conn.commit()