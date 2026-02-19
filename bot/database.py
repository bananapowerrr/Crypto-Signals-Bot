"""Модуль базы данных - все операции с SQLite"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных бота"""
    
    def __init__(self, db_path: str = 'crypto_signals_bot.db'):
        self.db_path = db_path
        self.conn = None
        self.setup_database()
    
    def get_connection(self):
        """Получить соединение с базой данных"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return self.conn
    
    def setup_database(self):
        """Инициализация таблиц базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
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
                current_balance REAL DEFAULT NULL,
                short_base_stake REAL DEFAULT 100,
                current_martingale_level INTEGER DEFAULT 0,
                consecutive_losses INTEGER DEFAULT 0,
                currency TEXT DEFAULT "RUB",
                martingale_type INTEGER DEFAULT 3,
                long_percentage REAL DEFAULT 2.5,
                subscription_type TEXT DEFAULT NULL,
                referral_code TEXT DEFAULT NULL,
                referred_by INTEGER DEFAULT NULL,
                new_user_discount_used BOOLEAN DEFAULT 0,
                referral_earnings REAL DEFAULT 0,
                pocket_option_registered BOOLEAN DEFAULT 0,
                pocket_option_login TEXT DEFAULT NULL,
                last_upgrade_offer TEXT DEFAULT NULL,
                language TEXT DEFAULT "ru",
                free_short_signals_today INTEGER DEFAULT 0,
                free_short_signals_date TEXT DEFAULT NULL,
                free_long_signals_today INTEGER DEFAULT 0,
                free_long_signals_date TEXT DEFAULT NULL,
                banned BOOLEAN DEFAULT 0,
                trading_strategy TEXT DEFAULT NULL,
                martingale_multiplier INTEGER DEFAULT 3,
                martingale_base_stake REAL DEFAULT NULL,
                percentage_value REAL DEFAULT 2.5,
                auto_trading_enabled BOOLEAN DEFAULT 0,
                pocket_option_email TEXT DEFAULT NULL,
                auto_trading_mode TEXT DEFAULT "demo",
                dalembert_base_stake REAL DEFAULT 100,
                dalembert_unit REAL DEFAULT 50,
                current_dalembert_level INTEGER DEFAULT 0,
                auto_trading_strategy TEXT DEFAULT "percentage",
                pocket_option_ssid TEXT DEFAULT NULL,
                pocket_option_connected BOOLEAN DEFAULT 0,
                ssid_automation_purchased BOOLEAN DEFAULT 0,
                ssid_automation_purchase_date DATETIME DEFAULT NULL
            )
        ''')
        
        # Таблица истории сигналов
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
                expiration_time TEXT,
                signal_tier TEXT DEFAULT "vip",
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица производительности сигналов
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
        
        # Таблица настроек бота
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                description TEXT,
                updated_at TEXT,
                updated_by INTEGER
            )
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully")
    
    # ========== НАСТРОЙКИ ==========
    
    def get_setting(self, key: str, default: str = '') -> str:
        """Получить значение настройки"""
        cursor = self.get_connection().cursor()
        cursor.execute('SELECT value FROM bot_settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        return result[0] if result and result[0] else default
    
    def set_setting(self, key: str, value: str, admin_id: int):
        """Установить значение настройки"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO bot_settings (key, value, updated_at, updated_by)
            VALUES (?, ?, ?, ?)
        ''', (key, value, datetime.now().isoformat(), admin_id))
        self.get_connection().commit()
    
    def is_admin(self, user_id: int, admin_user_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        admin_users = self.get_setting('admin_users', str(admin_user_id))
        admin_list = [int(uid.strip()) for uid in admin_users.split(',') if uid.strip()]
        return user_id in admin_list
    
    # ========== ПОЛЬЗОВАТЕЛИ ==========
    
    def get_user(self, user_id: int) -> Optional[Tuple]:
        """Получить данные пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Добавить нового пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, joined_date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, datetime.now().isoformat()))
        self.get_connection().commit()
    
    def check_subscription(self, user_id: int) -> Tuple[bool, Optional[str], int, int, Optional[str]]:
        """Проверить подписку пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute(
            'SELECT subscription_end, is_premium, signals_used, free_trials_used, subscription_type FROM users WHERE user_id = ?', 
            (user_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            return False, "Пользователь не найден", 0, 0, None
        
        subscription_end, is_premium, signals_used, free_trials_used, subscription_type = result
        
        # Пожизненные тарифы
        if subscription_type and not subscription_end:
            return True, None, signals_used, free_trials_used, subscription_type
        
        # Обычная подписка с датой окончания
        if subscription_end and datetime.now() < datetime.fromisoformat(subscription_end):
            return True, subscription_end, signals_used, free_trials_used, subscription_type
        
        # Пробный период (3 дня VIP для новых пользователей)
        if free_trials_used == 0:
            trial_end = datetime.now() + timedelta(days=3)
            cursor.execute(
                'UPDATE users SET subscription_end = ?, subscription_type = ?, free_trials_used = 1 WHERE user_id = ?',
                (trial_end.isoformat(), 'vip', user_id)
            )
            self.get_connection().commit()
            return True, trial_end.isoformat(), signals_used, 1, 'vip'
            
        return False, "Нет активной подписки", signals_used, free_trials_used, None
    
    def is_banned(self, user_id: int) -> bool:
        """Проверить, забанен ли пользователь"""
        cursor = self.get_connection().cursor()
        cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result and result[0] == 1
    
    def ban_user(self, user_id: int, admin_id: int):
        """Забанить пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute('UPDATE users SET banned = 1 WHERE user_id = ?', (user_id,))
        self.get_connection().commit()
        logger.info(f"Admin {admin_id} banned user {user_id}")
    
    def unban_user(self, user_id: int, admin_id: int):
        """Разбанить пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute('UPDATE users SET banned = 0 WHERE user_id = ?', (user_id,))
        self.get_connection().commit()
        logger.info(f"Admin {admin_id} unbanned user {user_id}")
    
    # ========== ЯЗЫК И ВАЛЮТА ==========
    
    def get_user_language(self, user_id: int) -> str:
        """Получить язык пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] else 'ru'
    
    def set_user_language(self, user_id: int, language: str):
        """Установить язык пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
        self.get_connection().commit()
    
    def get_currency(self, user_id: int) -> str:
        """Получить валюту пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute('SELECT currency FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] else "RUB"
    
    def set_currency(self, user_id: int, currency: str):
        """Установить валюту пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute('UPDATE users SET currency = ? WHERE user_id = ?', (currency, user_id))
        self.get_connection().commit()
    
    # ========== ПОДПИСКИ ==========
    
    def add_subscription(self, user_id: int, days: int = 30, subscription_type: str = 'vip'):
        """Добавить подписку"""
        cursor = self.get_connection().cursor()
        
        cursor.execute('SELECT subscription_end FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            current_end = datetime.fromisoformat(result[0])
            if current_end > datetime.now():
                new_end = current_end + timedelta(days=days)
            else:
                new_end = datetime.now() + timedelta(days=days)
        else:
            new_end = datetime.now() + timedelta(days=days)
        
        cursor.execute('''
            UPDATE users 
            SET subscription_end = ?, is_premium = 1, subscription_type = ?
            WHERE user_id = ?
        ''', (new_end.isoformat(), subscription_type, user_id))
        
        self.get_connection().commit()
        logger.info(f"Added {subscription_type.upper()} subscription for user {user_id} until {new_end}")
        
        return new_end
    
    def add_lifetime_subscription(self, user_id: int):
        """Добавить пожизненную подписку"""
        cursor = self.get_connection().cursor()
        lifetime_end = datetime.now() + timedelta(days=36500)
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, joined_date)
            VALUES (?, 'admin', 'Admin', ?)
        ''', (user_id, datetime.now().isoformat()))
        
        cursor.execute('''
            UPDATE users 
            SET subscription_end = ?, is_premium = 1, subscription_type = 'vip'
            WHERE user_id = ?
        ''', (lifetime_end.isoformat(), user_id))
        
        self.get_connection().commit()
        return lifetime_end
    
    # ========== СТАТИСТИКА ==========
    
    def get_bot_stats(self) -> Dict[str, int]:
        """Получить статистику бота"""
        cursor = self.get_connection().cursor()
        
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
    
    def get_user_signal_stats(self, user_id: int, timeframe_type: str = None, tier: str = None) -> Dict[str, Any]:
        """Получить статистику сигналов пользователя"""
        cursor = self.get_connection().cursor()
        
        short_timeframes = ['1M', '2M', '3M', '5M', '15M', '30M']
        long_timeframes = ['1H', '4H', '1D', '1W']
        
        filters = []
        params = [user_id]
        
        if timeframe_type == 'short':
            timeframe_filter = f"timeframe IN ({','.join('?' * len(short_timeframes))})"
            filters.append(timeframe_filter)
            params.extend(short_timeframes)
        elif timeframe_type == 'long':
            timeframe_filter = f"timeframe IN ({','.join('?' * len(long_timeframes))})"
            filters.append(timeframe_filter)
            params.extend(long_timeframes)
        
        if tier:
            filters.append("signal_tier = ?")
            params.append(tier)
        
        filter_clause = " AND " + " AND ".join(filters) if filters else ""
        
        query = f'''
            SELECT COALESCE(COUNT(*), 0) as total,
                   COALESCE(SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END), 0) as wins,
                   COALESCE(SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END), 0) as losses,
                   COALESCE(SUM(CASE WHEN result = 'win' THEN profit_loss ELSE 0 END), 0) as total_profit,
                   COALESCE(SUM(CASE WHEN result = 'loss' THEN profit_loss ELSE 0 END), 0) as total_loss,
                   COALESCE(AVG(confidence), 0) as avg_confidence
            FROM signal_history 
            WHERE user_id = ? AND result IS NOT NULL {filter_clause}
        '''
        cursor.execute(query, params)
        
        stats = cursor.fetchone()
        total, wins, losses, profit, loss, avg_conf = stats
        
        total = total or 0
        wins = wins or 0
        losses = losses or 0
        
        win_rate = (wins / total * 100) if total > 0 else 0
        net_profit = (profit or 0) + (loss or 0)
        
        return {
            'total_signals': total,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'net_profit': net_profit,
            'avg_confidence': avg_conf or 0
        }
    
    # ========== СИГНАЛЫ ==========
    
    def save_signal_to_history(self, user_id: int, asset: str, timeframe: str, 
                                signal_type: str, confidence: float, entry_price: float,
                                stake_amount: float = None) -> int:
        """Сохранить сигнал в историю"""
        cursor = self.get_connection().cursor()
        
        timeframe_minutes = {
            "1M": 1, "2M": 2, "3M": 3, "5M": 5, "15M": 15, "30M": 30,
            "1H": 60, "4H": 240, "1D": 1440, "1W": 10080
        }
        minutes = timeframe_minutes.get(timeframe, 5)
        expiration_time = (datetime.now() + timedelta(minutes=minutes)).isoformat()
        
        cursor.execute('''
            INSERT INTO signal_history 
            (user_id, asset, timeframe, signal_type, confidence, entry_price, stake_amount, 
             signal_date, expiration_time, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (user_id, asset, timeframe, signal_type, confidence, entry_price, 
              stake_amount, datetime.now().isoformat(), expiration_time))
        
        self.get_connection().commit()
        return cursor.lastrowid
    
    def update_signal_result(self, signal_id: int, result: str, profit_loss: float):
        """Обновить результат сигнала"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            UPDATE signal_history
            SET result = ?, profit_loss = ?, close_date = ?
            WHERE id = ?
        ''', (result, profit_loss, datetime.now().isoformat(), signal_id))
        self.get_connection().commit()
    
    def get_last_pending_signal(self, user_id: int) -> Optional[Tuple]:
        """Получить последний pending сигнал пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT id, asset, signal_type, confidence, stake_amount
            FROM signal_history
            WHERE user_id = ? AND result = 'pending'
            ORDER BY signal_date DESC
            LIMIT 1
        ''', (user_id,))
        return cursor.fetchone()
    
    def increment_signals_used(self, user_id: int):
        """Увеличить счетчик использованных сигналов"""
        cursor = self.get_connection().cursor()
        cursor.execute(
            'UPDATE users SET signals_used = signals_used + 1, last_signal_date = ? WHERE user_id = ?',
            (datetime.now().isoformat(), user_id)
        )
        self.get_connection().commit()
    
    # ========== FREE ЛИМИТЫ ==========
    
    def check_free_short_limit(self, user_id: int) -> Tuple[bool, int]:
        """Проверить лимит FREE шорт-сигналов (5 в день)"""
        cursor = self.get_connection().cursor()
        cursor.execute(
            'SELECT free_short_signals_today, free_short_signals_date FROM users WHERE user_id = ?',
            (user_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            return False, 0
        
        signals_today, last_date = result
        today = datetime.now().date().isoformat()
        
        if last_date != today:
            cursor.execute(
                'UPDATE users SET free_short_signals_today = 0, free_short_signals_date = ? WHERE user_id = ?',
                (today, user_id)
            )
            self.get_connection().commit()
            signals_today = 0
        
        if signals_today >= 5:
            return False, signals_today
        
        return True, signals_today
    
    def increment_free_short_signal(self, user_id: int) -> bool:
        """Увеличить счетчик FREE шорт-сигналов"""
        today = datetime.now().date().isoformat()
        cursor = self.get_connection().cursor()
        
        cursor.execute('''
            UPDATE users 
            SET free_short_signals_today = CASE 
                WHEN free_short_signals_date = ? THEN 
                    CASE WHEN free_short_signals_today < 5 THEN free_short_signals_today + 1 ELSE free_short_signals_today END
                ELSE 1
            END,
            free_short_signals_date = ?
            WHERE user_id = ? 
            AND (free_short_signals_date != ? OR free_short_signals_date IS NULL OR free_short_signals_today < 5)
        ''', (today, today, user_id, today))
        
        affected_rows = cursor.rowcount
        self.get_connection().commit()
        
        return affected_rows > 0
    
    # ========== МАРТИНГЕЙЛ ==========
    
    def get_martingale_stake(self, user_id: int) -> Tuple[float, int]:
        """Получить текущую ставку по мартингейлу"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT short_base_stake, martingale_base_stake, martingale_multiplier, 
                   current_martingale_level, consecutive_losses
            FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return 100.0, 0
        
        short_base_stake, martingale_base_stake, martingale_multiplier, level, losses = result
        
        base_stake = martingale_base_stake or short_base_stake or 100.0
        multiplier = martingale_multiplier or 3
        level = level or 0
        
        stake = base_stake * (multiplier ** level)
        return stake, level
    
    def update_martingale_after_win(self, user_id: int):
        """Сбросить мартингейл после выигрыша"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            UPDATE users 
            SET current_martingale_level = 0, consecutive_losses = 0
            WHERE user_id = ?
        ''', (user_id,))
        self.get_connection().commit()
    
    def update_martingale_after_loss(self, user_id: int):
        """Увеличить уровень мартингейла после проигрыша"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT current_martingale_level, consecutive_losses
            FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        
        if result:
            level, losses = result
            level = level or 0
            losses = losses or 0
            
            if losses < 6:
                new_level = min(level + 1, 6)
                new_losses = losses + 1
                cursor.execute('''
                    UPDATE users 
                    SET current_martingale_level = ?, consecutive_losses = ?
                    WHERE user_id = ?
                ''', (new_level, new_losses, user_id))
                self.get_connection().commit()
    
    # ========== РЕФЕРАЛЫ ==========
    
    def generate_referral_code(self, user_id: int) -> str:
        """Генерация уникального реферального кода"""
        import hashlib
        import time
        code_base = f"{user_id}_{int(time.time())}"
        code = hashlib.md5(code_base.encode()).hexdigest()[:8].upper()
        
        cursor = self.get_connection().cursor()
        cursor.execute('UPDATE users SET referral_code = ? WHERE user_id = ?', (code, user_id))
        self.get_connection().commit()
        
        return code
    
    def get_referral_code(self, user_id: int) -> str:
        """Получить реферальный код пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute('SELECT referral_code FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            return result[0]
        
        return self.generate_referral_code(user_id)
    
    # ========== АВТОТРЕЙДИНГ ==========
    
    def get_all_vip_users(self) -> List[int]:
        """Получить всех VIP подписчиков"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT user_id 
            FROM users 
            WHERE subscription_type = 'vip' 
            AND subscription_end IS NOT NULL 
            AND datetime(subscription_end) > datetime('now')
        ''')
        return [row[0] for row in cursor.fetchall()]
    
    def get_all_free_users(self) -> List[int]:
        """Получить всех FREE пользователей"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT user_id 
            FROM users 
            WHERE (subscription_type IS NULL OR subscription_type = 'free'
                   OR subscription_end IS NULL 
                   OR datetime(subscription_end) <= datetime('now'))
            AND user_id IS NOT NULL
        ''')
        return [row[0] for row in cursor.fetchall()]


# Глобальный экземпляр базы данных
db = Database()