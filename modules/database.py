"""
Database module - работа с SQLite базой данных
"""
import sqlite3
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def get_connection(db_path='crypto_signals_bot.db'):
    """Получить соединение с БД"""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return conn


def setup_database(conn):
    """Создать все таблицы и добавить недостающие колонки"""
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_date DATETIME,
            subscription_end DATETIME,
            is_premium BOOLEAN DEFAULT 0,
            free_trials_used INTEGER DEFAULT 0,
            signals_used INTEGER DEFAULT 0,
            last_signal_date DATETIME,
            initial_balance REAL DEFAULT NULL,
            current_balance REAL DEFAULT NULL
        )
    ''')

    # Добавить недостающие колонки (миграции)
    optional_columns = [
        ('initial_balance', 'REAL DEFAULT NULL'),
        ('current_balance', 'REAL DEFAULT NULL'),
        ('short_base_stake', 'REAL DEFAULT 100'),
        ('current_martingale_level', 'INTEGER DEFAULT 0'),
        ('consecutive_losses', 'INTEGER DEFAULT 0'),
        ('currency', 'TEXT DEFAULT "RUB"'),
        ('martingale_type', 'INTEGER DEFAULT 3'),
        ('long_percentage', 'REAL DEFAULT 2.5'),
        ('subscription_type', 'TEXT DEFAULT NULL'),
        ('referral_code', 'TEXT DEFAULT NULL'),
        ('referred_by', 'INTEGER DEFAULT NULL'),
        ('new_user_discount_used', 'BOOLEAN DEFAULT 0'),
        ('referral_earnings', 'REAL DEFAULT 0'),
        ('pocket_option_registered', 'BOOLEAN DEFAULT 0'),
        ('pocket_option_login', 'TEXT DEFAULT NULL'),
        ('last_upgrade_offer', 'TEXT DEFAULT NULL'),
        ('language', 'TEXT DEFAULT "ru"'),
        ('free_short_signals_today', 'INTEGER DEFAULT 0'),
        ('free_short_signals_date', 'TEXT DEFAULT NULL'),
        ('free_long_signals_today', 'INTEGER DEFAULT 0'),
        ('free_long_signals_date', 'TEXT DEFAULT NULL'),
        ('banned', 'BOOLEAN DEFAULT 0'),
        ('trading_strategy', 'TEXT DEFAULT NULL'),
        ('martingale_multiplier', 'INTEGER DEFAULT 3'),
        ('martingale_base_stake', 'REAL DEFAULT NULL'),
        ('percentage_value', 'REAL DEFAULT 2.5'),
        ('auto_trading_enabled', 'BOOLEAN DEFAULT 0'),
        ('pocket_option_email', 'TEXT DEFAULT NULL'),
        ('auto_trading_mode', 'TEXT DEFAULT "demo"'),
        ('dalembert_base_stake', 'REAL DEFAULT 100'),
        ('dalembert_unit', 'REAL DEFAULT 50'),
        ('current_dalembert_level', 'INTEGER DEFAULT 0'),
        ('auto_trading_strategy', 'TEXT DEFAULT "percentage"'),
        ('pocket_option_ssid', 'TEXT DEFAULT NULL'),
        ('pocket_option_connected', 'BOOLEAN DEFAULT 0'),
        ('ssid_automation_purchased', 'BOOLEAN DEFAULT 0'),
        ('ssid_automation_purchase_date', 'DATETIME DEFAULT NULL'),
        ('referral_bonus_pending', 'TEXT DEFAULT NULL'),
    ]

    for col_name, col_def in optional_columns:
        try:
            cursor.execute(f'SELECT {col_name} FROM users LIMIT 1')
        except sqlite3.OperationalError:
            cursor.execute(f'ALTER TABLE users ADD COLUMN {col_name} {col_def}')
            logger.info(f"✅ Added column {col_name} to users table")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signal_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            asset TEXT,
            timeframe TEXT,
            signal_type TEXT,
            confidence REAL,
            entry_price REAL,
            result TEXT,
            profit_loss REAL,
            stake_amount REAL,
            signal_date DATETIME,
            close_date DATETIME,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    for col_name, col_def in [('expiration_time', 'TEXT'), ('signal_tier', 'TEXT DEFAULT "vip"')]:
        try:
            cursor.execute(f'SELECT {col_name} FROM signal_history LIMIT 1')
        except sqlite3.OperationalError:
            cursor.execute(f'ALTER TABLE signal_history ADD COLUMN {col_name} {col_def}')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signal_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            total_signals INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            win_rate REAL DEFAULT 0.0,
            adaptive_weight REAL DEFAULT 1.0,
            last_updated TEXT NOT NULL,
            UNIQUE(asset, timeframe)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timeframe_type TEXT,
            created_at TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT,
            updated_at TEXT,
            updated_by INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            price REAL,
            volatility REAL,
            volume REAL,
            avg_volume REAL,
            volume_ratio REAL,
            whale_detected INTEGER DEFAULT 0,
            trend TEXT,
            rsi REAL,
            macd REAL,
            stoch_k REAL,
            ema_20 REAL,
            ema_50 REAL,
            signal_generated TEXT,
            confidence REAL,
            score INTEGER
        )
    ''')

    conn.commit()
    logger.info("✅ Database setup complete")


def init_default_settings(conn, admin_user_id):
    """Инициализировать настройки по умолчанию"""
    cursor = conn.cursor()
    default_settings = [
        ('reviews_group', '@cryptosignalsbot_otz', 'Telegram группа с отзывами'),
        ('reviews_enabled', 'true', 'Показывать кнопку отзывов'),
        ('admin_users', str(admin_user_id), 'Список ID администраторов'),
        ('bot_configured', 'false', 'Завершена ли первичная настройка'),
        ('vip_price_rub', '9990', 'Цена VIP в рублях'),
        ('short_price_rub', '4990', 'Цена SHORT в рублях'),
        ('long_price_rub', '6990', 'Цена LONG в рублях'),
        ('support_contact', '@banana_pwr', 'Контакт поддержки'),
        ('webhook_url', '', 'URL для webhook'),
        ('webhook_secret', '', 'Секрет webhook'),
        ('webhook_enabled', 'false', 'Включить webhook'),
        ('min_signal_score', '2', 'Минимальный score сигнала'),
        ('min_score_difference', '0', 'Минимальная разница score'),
        ('min_confidence', '70', 'Минимальная уверенность'),
        ('max_confidence', '92', 'Максимальная уверенность'),
        ('bot_name', 'CRYPTO SIGNALS BOT', 'Название бота'),
    ]
    for key, value, description in default_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO bot_settings (key, value, description, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (key, value, description, datetime.now().isoformat()))
    conn.commit()


def get_setting(conn, key, default=''):
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM bot_settings WHERE key = ?', (key,))
    result = cursor.fetchone()
    return result[0] if result and result[0] else default


def set_setting(conn, key, value, admin_id, main_admin_id):
    if key == 'admin_users':
        admin_list = [uid.strip() for uid in str(value).split(',') if uid.strip()]
        if str(main_admin_id) not in admin_list:
            admin_list.insert(0, str(main_admin_id))
            value = ','.join(admin_list)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO bot_settings (key, value, updated_at, updated_by)
        VALUES (?, ?, ?, ?)
    ''', (key, value, datetime.now().isoformat(), admin_id))
    conn.commit()


def is_admin(conn, user_id, main_admin_id):
    admin_users = get_setting(conn, 'admin_users', str(main_admin_id))
    admin_list = [int(uid.strip()) for uid in admin_users.split(',') if uid.strip()]
    return user_id in admin_list


def is_banned(conn, user_id):
    cursor = conn.cursor()
    cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result and result[0] == 1


def get_user_language(conn, user_id):
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result and result[0] else 'ru'


def set_user_language(conn, user_id, language):
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
    conn.commit()


def get_bot_stats(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_premium = 1')
    premium_users = cursor.fetchone()[0]
    cursor.execute('SELECT SUM(signals_used) FROM users')
    total_signals = cursor.fetchone()[0] or 0
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE subscription_end IS NOT NULL 
        AND datetime(subscription_end) > datetime('now')
    ''')
    active_subs = cursor.fetchone()[0]
    return {
        'total_users': total_users,
        'premium_users': premium_users,
        'active_subscriptions': active_subs,
        'total_signals': total_signals
    }
