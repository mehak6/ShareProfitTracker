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
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    company_name TEXT,
                    quantity REAL NOT NULL,
                    purchase_price REAL NOT NULL,
                    purchase_date TEXT NOT NULL,
                    broker TEXT,
                    cash_invested REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
                
                CREATE TABLE IF NOT EXISTS price_cache (
                    symbol TEXT PRIMARY KEY,
                    current_price REAL,
                    last_updated TEXT
                );
                
                CREATE TABLE IF NOT EXISTS cash_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL, -- 'deposit', 'withdrawal'
                    amount REAL NOT NULL,
                    description TEXT,
                    transaction_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
                
                CREATE TABLE IF NOT EXISTS other_expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL, -- 'electricity', 'rent', 'food', etc.
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    expense_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
                
                CREATE TABLE IF NOT EXISTS dividends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    company_name TEXT,
                    dividend_per_share REAL NOT NULL,
                    total_dividend REAL NOT NULL,
                    shares_held REAL NOT NULL,
                    ex_dividend_date TEXT NOT NULL,
                    payment_date TEXT,
                    record_date TEXT,
                    dividend_type TEXT DEFAULT 'regular', -- 'regular', 'special', 'bonus'
                    tax_deducted REAL DEFAULT 0,
                    net_dividend REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
                
                CREATE TABLE IF NOT EXISTS stock_adjustments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    adjustment_type TEXT NOT NULL, -- 'split', 'bonus', 'rights'
                    adjustment_date TEXT NOT NULL,
                    ratio_from INTEGER NOT NULL, -- e.g., 1 in 1:2 split
                    ratio_to INTEGER NOT NULL, -- e.g., 2 in 1:2 split
                    description TEXT,
                    shares_before REAL,
                    shares_after REAL,
                    price_before REAL,
                    price_after REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Create essential indexes for performance (idempotent)
            try:
                conn.execute('CREATE INDEX IF NOT EXISTS idx_stocks_user_symbol ON stocks(user_id, symbol)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_stocks_user_id ON stocks(user_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_price_cache_symbol ON price_cache(symbol)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_price_cache_updated ON price_cache(last_updated)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_cash_transactions_user ON cash_transactions(user_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_cash_transactions_date ON cash_transactions(transaction_date)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_other_expenses_user ON other_expenses(user_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_other_expenses_date ON other_expenses(expense_date)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_dividends_user ON dividends(user_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_dividends_symbol ON dividends(symbol)')
            except Exception:
                # Index creation is idempotent; ignore if unsupported or already exists
                pass
            
            # Add cash_invested column to existing tables if it doesn't exist
            try:
                conn.execute('ALTER TABLE stocks ADD COLUMN cash_invested REAL DEFAULT 0')
                conn.commit()
            except:
                pass  # Column already exists
            
            # Add user_id columns to existing tables if they don't exist
            try:
                conn.execute('ALTER TABLE stocks ADD COLUMN user_id INTEGER DEFAULT 1')
                conn.execute('ALTER TABLE cash_transactions ADD COLUMN user_id INTEGER DEFAULT 1')
                conn.execute('ALTER TABLE other_expenses ADD COLUMN user_id INTEGER DEFAULT 1')
                conn.execute('ALTER TABLE dividends ADD COLUMN user_id INTEGER DEFAULT 1')
                conn.commit()
            except:
                pass  # Columns already exist
                
            conn.commit()
            
            # Initialize default users if none exist
            self.init_default_users()
    
    def add_stock(self, symbol: str, company_name: str, quantity: float, 
                  purchase_price: float, purchase_date: str, broker: str = "", 
                  cash_invested: float = 0) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get active user
            active_user = self.get_active_user()
            if not active_user:
                raise Exception("No active user found")
            
            # If cash_invested is not provided or is 0, calculate it from quantity * price
            if cash_invested == 0:
                cash_invested = quantity * purchase_price
                
            cursor.execute('''
                INSERT INTO stocks (user_id, symbol, company_name, quantity, purchase_price, 
                                  purchase_date, broker, cash_invested, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (active_user['id'], symbol.upper(), company_name, quantity, purchase_price, 
                  purchase_date, broker, cash_invested, datetime.now().isoformat()))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_stocks(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get active user
            active_user = self.get_active_user()
            if not active_user:
                return []
            
            cursor.execute('''
                SELECT s.*, pc.current_price, pc.last_updated
                FROM stocks s
                LEFT JOIN price_cache pc ON s.symbol = pc.symbol
                WHERE s.user_id = ?
                ORDER BY s.symbol
            ''', (active_user['id'],))
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
            
            # Get active user
            active_user = self.get_active_user()
            if not active_user:
                return []
                
            cursor.execute('SELECT DISTINCT symbol FROM stocks WHERE user_id = ? ORDER BY symbol', (active_user['id'],))
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
            
            # Get active user
            active_user = self.get_active_user()
            if not active_user:
                raise Exception("No active user found")
                
            cursor.execute('''
                INSERT INTO cash_transactions (user_id, transaction_type, amount, description, 
                                             transaction_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (active_user['id'], transaction_type, amount, description, transaction_date, 
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
            
            # Get active user
            active_user = self.get_active_user()
            if not active_user:
                return 0.0
                
            cursor.execute('''
                SELECT 
                    COALESCE(SUM(CASE WHEN transaction_type = 'deposit' THEN amount ELSE 0 END), 0) as deposits,
                    COALESCE(SUM(CASE WHEN transaction_type = 'withdrawal' THEN amount ELSE 0 END), 0) as withdrawals
                FROM cash_transactions
                WHERE user_id = ?
            ''', (active_user['id'],))
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
    
    # Dividend methods
    def add_dividend(self, symbol: str, company_name: str, dividend_per_share: float, 
                    total_dividend: float, shares_held: float, ex_dividend_date: str,
                    payment_date: str = None, record_date: str = None, 
                    dividend_type: str = "regular", tax_deducted: float = 0) -> int:
        net_dividend = total_dividend - tax_deducted
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dividends (symbol, company_name, dividend_per_share, 
                                     total_dividend, shares_held, ex_dividend_date,
                                     payment_date, record_date, dividend_type,
                                     tax_deducted, net_dividend, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol.upper(), company_name, dividend_per_share, total_dividend,
                  shares_held, ex_dividend_date, payment_date, record_date,
                  dividend_type, tax_deducted, net_dividend, datetime.now().isoformat()))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_dividends(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM dividends 
                ORDER BY ex_dividend_date DESC, created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_dividends_by_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM dividends 
                WHERE symbol = ?
                ORDER BY ex_dividend_date DESC
            ''', (symbol.upper(),))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_dividends_by_year(self, year: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM dividends 
                WHERE strftime('%Y', ex_dividend_date) = ?
                ORDER BY ex_dividend_date DESC
            ''', (str(year),))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_dividend(self, dividend_id: int):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM dividends WHERE id = ?', (dividend_id,))
            conn.commit()
    
    def get_total_dividend_income(self, year: int = None) -> float:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if year:
                cursor.execute('''
                    SELECT SUM(net_dividend) FROM dividends 
                    WHERE strftime('%Y', ex_dividend_date) = ?
                ''', (str(year),))
            else:
                cursor.execute('SELECT SUM(net_dividend) FROM dividends')
            result = cursor.fetchone()[0]
            return result or 0.0
    
    # Stock adjustment methods
    def add_stock_adjustment(self, symbol: str, adjustment_type: str, adjustment_date: str,
                           ratio_from: int, ratio_to: int, description: str = "",
                           shares_before: float = None, shares_after: float = None,
                           price_before: float = None, price_after: float = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO stock_adjustments (symbol, adjustment_type, adjustment_date,
                                             ratio_from, ratio_to, description,
                                             shares_before, shares_after, price_before,
                                             price_after, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol.upper(), adjustment_type, adjustment_date, ratio_from, ratio_to,
                  description, shares_before, shares_after, price_before, price_after,
                  datetime.now().isoformat()))
            conn.commit()
            return cursor.lastrowid
    
    def get_stock_adjustments(self, symbol: str = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if symbol:
                cursor.execute('''
                    SELECT * FROM stock_adjustments 
                    WHERE symbol = ?
                    ORDER BY adjustment_date DESC
                ''', (symbol.upper(),))
            else:
                cursor.execute('''
                    SELECT * FROM stock_adjustments 
                    ORDER BY adjustment_date DESC, created_at DESC
                ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_stock_adjustment(self, adjustment_id: int):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM stock_adjustments WHERE id = ?', (adjustment_id,))
            conn.commit()
    
    def apply_stock_split_to_holdings(self, symbol: str, ratio_from: int, ratio_to: int):
        """Apply stock split to all holdings of a symbol"""
        multiplier = ratio_to / ratio_from
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Update quantity and adjust purchase price
            cursor.execute('''
                UPDATE stocks 
                SET quantity = quantity * ?, 
                    purchase_price = purchase_price / ?
                WHERE symbol = ?
            ''', (multiplier, multiplier, symbol.upper()))
            conn.commit()
    
    # User Management Methods
    def init_default_users(self):
        """Initialize default users if none exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if users exist
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                # Create default users
                cursor.execute('''
                    INSERT INTO users (username, display_name, is_active) 
                    VALUES (?, ?, ?)
                ''', ("user1", "User 1", 1))  # First user is active by default
                
                cursor.execute('''
                    INSERT INTO users (username, display_name, is_active) 
                    VALUES (?, ?, ?)
                ''', ("user2", "User 2", 0))
                
                conn.commit()
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users 
                ORDER BY username
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_active_user(self) -> Optional[Dict[str, Any]]:
        """Get the currently active user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users 
                WHERE is_active = 1 
                LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def set_active_user(self, user_id: int):
        """Set a user as active and deactivate others"""
        with self.get_connection() as conn:
            # First, deactivate all users
            conn.execute('UPDATE users SET is_active = 0')
            # Then activate the selected user
            conn.execute('UPDATE users SET is_active = 1 WHERE id = ?', (user_id,))
            conn.commit()
    
    def add_user(self, username: str, display_name: str) -> int:
        """Add a new user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, display_name, is_active, created_at)
                VALUES (?, ?, 0, ?)
            ''', (username, display_name, datetime.now().isoformat()))
            conn.commit()
            return cursor.lastrowid
    
    def update_user(self, user_id: int, username: str, display_name: str):
        """Update user details"""
        with self.get_connection() as conn:
            conn.execute('''
                UPDATE users 
                SET username = ?, display_name = ?
                WHERE id = ?
            ''', (username, display_name, user_id))
            conn.commit()
    
    def delete_user(self, user_id: int):
        """Delete a user and all their data"""
        with self.get_connection() as conn:
            # Delete user's data from all tables
            conn.execute('DELETE FROM stocks WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM cash_transactions WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM other_expenses WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM dividends WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
