"""
Async Database Manager - Non-blocking database operations with connection pooling
Fixes UI freezing issues from synchronous database calls
"""

import asyncio
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional, Dict, Any
from queue import Queue, Empty
import os


class ConnectionPool:
    """Simple SQLite connection pool to reuse connections"""
    
    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self.pool = Queue(maxsize=max_connections)
        self.active_connections = 0
        self._lock = threading.Lock()
        
        # Pre-populate pool with connections
        for _ in range(min(2, max_connections)):
            self._create_connection()
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrent access
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=memory")
        return conn
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool with automatic return"""
        conn = None
        try:
            # Try to get existing connection from pool
            try:
                conn = self.pool.get_nowait()
            except Empty:
                # Create new connection if pool is empty and under limit
                with self._lock:
                    if self.active_connections < self.max_connections:
                        conn = self._create_connection()
                        self.active_connections += 1
                    else:
                        # Wait for available connection
                        conn = self.pool.get(timeout=10)
            
            yield conn
            
        except Exception as e:
            # If connection is bad, don't return it to pool
            if conn:
                try:
                    conn.close()
                except:
                    pass
                with self._lock:
                    self.active_connections -= 1
            raise e
        else:
            # Return healthy connection to pool
            if conn:
                try:
                    self.pool.put_nowait(conn)
                except:
                    # Pool is full, close connection
                    conn.close()
                    with self._lock:
                        self.active_connections -= 1
    
    def close_all(self):
        """Close all connections in pool"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except Empty:
                break
        self.active_connections = 0


class AsyncDatabaseManager:
    """
    Non-blocking database manager using thread pool execution
    Prevents UI freezing during database operations
    """
    
    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self.connection_pool = ConnectionPool(db_path, max_connections=3)
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="AsyncDB")
        
        # Initialize database schema
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema synchronously on startup"""
        with self.connection_pool.get_connection() as conn:
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
                    transaction_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    transaction_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
                
                CREATE TABLE IF NOT EXISTS other_expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
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
                    dividend_type TEXT DEFAULT 'regular',
                    tax_deducted REAL DEFAULT 0,
                    net_dividend REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
                
                CREATE TABLE IF NOT EXISTS stock_adjustments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    adjustment_type TEXT NOT NULL,
                    adjustment_date TEXT NOT NULL,
                    ratio_from INTEGER NOT NULL,
                    ratio_to INTEGER NOT NULL,
                    description TEXT,
                    shares_before REAL,
                    shares_after REAL,
                    price_before REAL,
                    price_after REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Add performance indexes
            conn.executescript('''
                CREATE INDEX IF NOT EXISTS idx_stocks_user_symbol ON stocks(user_id, symbol);
                CREATE INDEX IF NOT EXISTS idx_stocks_user_id ON stocks(user_id);
                CREATE INDEX IF NOT EXISTS idx_price_cache_symbol ON price_cache(symbol);
                CREATE INDEX IF NOT EXISTS idx_price_cache_updated ON price_cache(last_updated);
                CREATE INDEX IF NOT EXISTS idx_cash_transactions_user ON cash_transactions(user_id);
                CREATE INDEX IF NOT EXISTS idx_cash_transactions_date ON cash_transactions(transaction_date);
            ''')
            
            conn.commit()
            
        # Initialize default users if none exist
        self._init_default_users()
    
    def _init_default_users(self):
        """Initialize default users if none exist"""
        with self.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                cursor.execute('''
                    INSERT INTO users (username, display_name, is_active) 
                    VALUES (?, ?, ?)
                ''', ("user1", "User 1", 1))
                
                cursor.execute('''
                    INSERT INTO users (username, display_name, is_active) 
                    VALUES (?, ?, ?)
                ''', ("user2", "User 2", 0))
                
                conn.commit()
    
    # Async wrapper methods
    async def get_all_stocks_async(self) -> List[Dict[str, Any]]:
        """Get all stocks asynchronously"""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, self._get_all_stocks_sync
        )
    
    async def add_stock_async(self, **kwargs) -> int:
        """Add stock asynchronously"""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, self._add_stock_sync, kwargs
        )
    
    async def update_stock_async(self, stock_id: int, **kwargs) -> None:
        """Update stock asynchronously"""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, self._update_stock_sync, stock_id, kwargs
        )
    
    async def delete_stock_async(self, stock_id: int) -> None:
        """Delete stock asynchronously"""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, self._delete_stock_sync, stock_id
        )
    
    async def update_price_cache_async(self, symbol: str, price: float) -> None:
        """Update price cache asynchronously"""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, self._update_price_cache_sync, symbol, price
        )
    
    # Synchronous methods that run in thread pool
    def _get_all_stocks_sync(self) -> List[Dict[str, Any]]:
        """Get all stocks (runs in thread pool)"""
        with self.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get active user
            active_user = self._get_active_user_sync(conn)
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
    
    def _add_stock_sync(self, stock_data: Dict[str, Any]) -> int:
        """Add stock (runs in thread pool)"""
        with self.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get active user
            active_user = self._get_active_user_sync(conn)
            if not active_user:
                raise Exception("No active user found")
            
            # Calculate cash invested if not provided
            cash_invested = stock_data.get('cash_invested', 0)
            if cash_invested == 0:
                cash_invested = stock_data['quantity'] * stock_data['purchase_price']
            
            cursor.execute('''
                INSERT INTO stocks (user_id, symbol, company_name, quantity, purchase_price, 
                                  purchase_date, broker, cash_invested, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                active_user['id'],
                stock_data['symbol'].upper(),
                stock_data.get('company_name', ''),
                stock_data['quantity'],
                stock_data['purchase_price'],
                stock_data['purchase_date'],
                stock_data.get('broker', ''),
                cash_invested,
                datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid
    
    def _update_stock_sync(self, stock_id: int, stock_data: Dict[str, Any]) -> None:
        """Update stock (runs in thread pool)"""
        with self.connection_pool.get_connection() as conn:
            cash_invested = stock_data.get('cash_invested')
            if cash_invested is None:
                cash_invested = stock_data['quantity'] * stock_data['purchase_price']
            
            conn.execute('''
                UPDATE stocks 
                SET symbol = ?, company_name = ?, quantity = ?, purchase_price = ?,
                    purchase_date = ?, broker = ?, cash_invested = ?
                WHERE id = ?
            ''', (
                stock_data['symbol'].upper(),
                stock_data.get('company_name', ''),
                stock_data['quantity'],
                stock_data['purchase_price'],
                stock_data['purchase_date'],
                stock_data.get('broker', ''),
                cash_invested,
                stock_id
            ))
            conn.commit()
    
    def _delete_stock_sync(self, stock_id: int) -> None:
        """Delete stock (runs in thread pool)"""
        with self.connection_pool.get_connection() as conn:
            conn.execute('DELETE FROM stocks WHERE id = ?', (stock_id,))
            conn.commit()
    
    def _update_price_cache_sync(self, symbol: str, price: float) -> None:
        """Update price cache (runs in thread pool)"""
        with self.connection_pool.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO price_cache (symbol, current_price, last_updated)
                VALUES (?, ?, ?)
            ''', (symbol.upper(), price, datetime.now().isoformat()))
            conn.commit()
    
    def _get_active_user_sync(self, conn: sqlite3.Connection = None) -> Optional[Dict[str, Any]]:
        """Get active user (synchronous)"""
        if conn is None:
            with self.connection_pool.get_connection() as conn:
                return self._get_active_user_sync(conn)
        
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE is_active = 1 LIMIT 1')
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # Synchronous compatibility methods (for backward compatibility)
    def get_all_stocks(self) -> List[Dict[str, Any]]:
        """Synchronous version for backward compatibility"""
        return self._get_all_stocks_sync()
    
    def add_stock(self, **kwargs) -> int:
        """Synchronous version for backward compatibility"""
        return self._add_stock_sync(kwargs)
    
    def update_stock(self, stock_id: int, **kwargs) -> None:
        """Synchronous version for backward compatibility"""
        return self._update_stock_sync(stock_id, kwargs)
    
    def delete_stock(self, stock_id: int) -> None:
        """Synchronous version for backward compatibility"""
        return self._delete_stock_sync(stock_id)
    
    def update_price_cache(self, symbol: str, price: float) -> None:
        """Synchronous version for backward compatibility"""
        return self._update_price_cache_sync(symbol, price)
    
    def get_active_user(self) -> Optional[Dict[str, Any]]:
        """Synchronous version for backward compatibility"""
        with self.connection_pool.get_connection() as conn:
            return self._get_active_user_sync(conn)
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        with self.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users ORDER BY username')
            return [dict(row) for row in cursor.fetchall()]
    
    def set_active_user(self, user_id: int):
        """Set active user"""
        with self.connection_pool.get_connection() as conn:
            conn.execute('UPDATE users SET is_active = 0')
            conn.execute('UPDATE users SET is_active = 1 WHERE id = ?', (user_id,))
            conn.commit()
    
    def get_current_cash_balance(self) -> float:
        """Get current cash balance"""
        with self.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            active_user = self._get_active_user_sync(conn)
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
    
    def close(self):
        """Close database connections and thread pool"""
        self.executor.shutdown(wait=True)
        self.connection_pool.close_all()