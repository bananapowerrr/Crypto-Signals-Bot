"""
Database module for Crypto Signals Bot
Handles all database operations
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_NAME = "crypto_signals_bot.db"


class Database:
    """Database manager for the bot"""
    
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self.conn = self._create_connection()
        self._initialize_tables()
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create database connection"""
        conn = sqlite3.connect(self.db_name, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _initialize_tables(self):
        """Initialize database tables"""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                language TEXT DEFAULT 'ru',
                currency TEXT DEFAULT 'RUB',
                initial_balance REAL DEFAULT 10000,
                current_balance REAL,
                trading_strategy TEXT DEFAULT 'martingale',
                martingale_multiplier REAL DEFAULT 3.0,
                percentage_value REAL DEFAULT 2.5,
                -- Fields for free quota / referral / VIP
                daily_signals_count INTEGER DEFAULT 0,
                daily_signals_date DATE,
                is_vip INTEGER DEFAULT 0,
                referral_registered INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Signal history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signal_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                asset TEXT,
                timeframe TEXT,
                signal_type TEXT,
                entry_price REAL,
                stake_amount REAL,
                result TEXT,
                confidence REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Bot settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                description TEXT
            )
        ''')

        # Screenshot analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screenshot_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                analysis_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        self.conn.commit()
        logger.info("✅ Database tables initialized")

        # Run migrations for older DBs (add missing columns if necessary)
        self._migrate_schema()

    def _migrate_schema(self):
        """Add missing columns to users table for backward compatibility"""
        cursor = self.conn.cursor()
        # helper to add column if not exists
        def add_column(name, col_type):
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {name} {col_type}")
            except Exception:
                pass

        add_column('daily_signals_count', 'INTEGER DEFAULT 0')
        add_column('daily_signals_date', 'DATE')
        add_column('is_vip', 'INTEGER DEFAULT 0')
        add_column('referral_registered', 'INTEGER DEFAULT 0')
        self.conn.commit()
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Database error: {e}")
            raise
    
    # User operations
    def add_user(self, user_id: int, username: str = None, first_name: str = None) -> bool:
        """Add new user to database"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute('''
                    INSERT OR IGNORE INTO users (user_id, username, first_name)
                    VALUES (?, ?, ?)
                ''', (user_id, username, first_name))
                return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False

    def ensure_user(self, user_id: int, username: str = None, first_name: str = None):
        """Ensure user exists and return user record"""
        self.add_user(user_id, username, first_name)
        return self.get_user(user_id)

    # Quota / referral operations
    def can_use_signal(self, user_id: int, max_free_per_day: int = 3) -> bool:
        """Return True if user can request another free signal today."""
        user = self.get_user(user_id)
        if not user:
            return True
        if user.get('is_vip'):
            return True
        if user.get('referral_registered'):
            return True

        today = datetime.utcnow().date().isoformat()
        if user.get('daily_signals_date') != today:
            return True
        return (user.get('daily_signals_count') or 0) < max_free_per_day

    def increment_signal_count(self, user_id: int):
        """Increment user's daily signal counter (resets on date change)."""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT daily_signals_count, daily_signals_date FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            today = datetime.utcnow().date().isoformat()
            if not row:
                cursor.execute('INSERT OR IGNORE INTO users (user_id, daily_signals_count, daily_signals_date) VALUES (?, ?, ?)', (user_id, 1, today))
                return
            count = row['daily_signals_count'] or 0
            date = row['daily_signals_date']
            if date != today:
                cursor.execute('UPDATE users SET daily_signals_count = ?, daily_signals_date = ? WHERE user_id = ?', (1, today, user_id))
            else:
                cursor.execute('UPDATE users SET daily_signals_count = ? WHERE user_id = ?', (count + 1, user_id))

    def set_referral_registered(self, user_id: int, registered: bool = True):
        with self.get_cursor() as cursor:
            cursor.execute('UPDATE users SET referral_registered = ? WHERE user_id = ?', (1 if registered else 0, user_id))

    def set_vip(self, user_id: int, vip: bool = True):
        with self.get_cursor() as cursor:
            cursor.execute('UPDATE users SET is_vip = ? WHERE user_id = ?', (1 if vip else 0, user_id))

    def save_screenshot_analysis(self, user_id: int, analysis: Dict[str, Any]) -> int:
        """Save screenshot analysis JSON blob to DB"""
        import json
        with self.get_cursor() as cursor:
            cursor.execute(
                'INSERT INTO screenshot_analysis (user_id, analysis_json) VALUES (?, ?)',
                (user_id, json.dumps(analysis, ensure_ascii=False))
            )
            return cursor.lastrowid
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_user_balance(self, user_id: int, balance: float):
        """Update user balance"""
        with self.get_cursor() as cursor:
            cursor.execute(
                'UPDATE users SET current_balance = ? WHERE user_id = ?',
                (balance, user_id)
            )
    
    def update_user_strategy(self, user_id: int, strategy: str, **params):
        """Update user's trading strategy and parameters"""
        with self.get_cursor() as cursor:
            if strategy == 'martingale':
                cursor.execute(
                    'UPDATE users SET trading_strategy = ?, martingale_multiplier = ? WHERE user_id = ?',
                    (strategy, params.get('multiplier', 3.0), user_id)
                )
            elif strategy == 'percentage':
                cursor.execute(
                    'UPDATE users SET trading_strategy = ?, percentage_value = ? WHERE user_id = ?',
                    (strategy, params.get('percentage', 2.5), user_id)
                )
    
    # Signal operations
    def save_signal(self, user_id: int, asset: str, timeframe: str, signal_type: str, 
                    entry_price: float, stake_amount: float, confidence: float) -> int:
        """Save signal to history"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO signal_history 
                (user_id, asset, timeframe, signal_type, entry_price, stake_amount, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, asset, timeframe, signal_type, entry_price, stake_amount, confidence))
            return cursor.lastrowid
    
    def update_signal_result(self, signal_id: int, result: str):
        """Update signal result (win/loss)"""
        with self.get_cursor() as cursor:
            cursor.execute(
                'UPDATE signal_history SET result = ? WHERE id = ?',
                (result, signal_id)
            )
    
    def get_user_signals(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's signal history"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM signal_history 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user trading statistics"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses
                FROM signal_history 
                WHERE user_id = ? AND result IS NOT NULL
            ''', (user_id,))
            row = cursor.fetchone()
            stats = dict(row) if row else {'total': 0, 'wins': 0, 'losses': 0}
            
            if stats['total'] > 0:
                stats['win_rate'] = (stats['wins'] / stats['total']) * 100
            else:
                stats['win_rate'] = 0
            
            return stats
    
    # Settings operations
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get bot setting"""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT value FROM bot_settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row['value'] if row else default
    
    def set_setting(self, key: str, value: str, description: str = ""):
        """Set bot setting"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO bot_settings (key, value, description)
                VALUES (?, ?, ?)
            ''', (key, value, description))
    
    # Admin operations
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all users"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM users ORDER BY user_id DESC LIMIT ? OFFSET ?
            ''', (limit, offset))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_total_users(self) -> int:
        """Get total number of users"""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT COUNT(*) as count FROM users')
            return cursor.fetchone()['count']
    
    def get_total_signals(self) -> int:
        """Get total number of signals"""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT COUNT(*) as count FROM signal_history')
            return cursor.fetchone()['count']
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Global database instance
db = Database()
