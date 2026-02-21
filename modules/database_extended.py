"""
Extended Database Module - расширенные функции для работы с БД
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


class ExtendedDatabase:
    """Расширенный класс для работы с базой данных"""
    
    def __init__(self, db):
        """Инициализация с существующим экземпляром db"""
        self.db = db
    
    def get_connection(self):
        """Получить соединение"""
        return self.db.get_connection()
    
    # ========== УПРАВЛЕНИЕ ПОДПИСКАМИ ==========
    
    def get_user_subscription(self, user_id: int) -> Dict[str, Any]:
        """Получить полную информацию о подписке пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT user_id, subscription_type, subscription_end, is_premium, 
                   free_trials_used, signals_used, free_short_signals_today,
                   free_long_signals_today, language, currency
            FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return {
                'has_subscription': False,
                'subscription_type': None,
                'days_remaining': 0,
                'signals_used': 0,
                'free_short_remaining': 5,
                'free_long_remaining': 3,
                'language': 'ru',
                'currency': 'RUB'
            }
        
        user_id, sub_type, sub_end, is_premium, free_trials, signals_used, free_short, free_long, lang, currency = result
        
        has_sub = False
        days_remaining = 0
        
        if sub_type and not sub_end:
            has_sub = True
            days_remaining = 999
        elif sub_end:
            end_date = datetime.fromisoformat(sub_end)
            if end_date > datetime.now():
                has_sub = True
                days_remaining = (end_date - datetime.now()).days
        
        # Определение лимитов
        if sub_type == 'vip':
            free_short_remaining = 999
            free_long_remaining = 999
        elif sub_type == 'short':
            free_short_remaining = 999
            free_long_remaining = 0
        elif sub_type == 'long':
            free_short_remaining = 0
            free_long_remaining = 999
        else:
            free_short_remaining = max(0, 5 - (free_short or 0))
            free_long_remaining = max(0, 3 - (free_long or 0))
        
        return {
            'has_subscription': has_sub,
            'subscription_type': sub_type,
            'days_remaining': days_remaining,
            'signals_used': signals_used or 0,
            'free_short_remaining': free_short_remaining,
            'free_long_remaining': free_long_remaining,
            'language': lang or 'ru',
            'currency': currency or 'RUB',
            'is_premium': bool(is_premium)
        }
    
    def can_get_signal(self, user_id: int, signal_type: str) -> Tuple[bool, str]:
        """Проверить может ли пользователь получить сигнал"""
        sub_info = self.get_user_subscription(user_id)
        
        if sub_info['has_subscription']:
            return True, "Подписка активна"
        
        if signal_type == 'short':
            if sub_info['free_short_remaining'] > 0:
                return True, f"Бесплатный сигнал ({sub_info['free_short_remaining']} осталось)"
            return False, "Дневной лимит SHORT сигналов исчерпан"
        
        elif signal_type == 'long':
            if sub_info['free_long_remaining'] > 0:
                return True, f"Бесплатный сигнал ({sub_info['free_long_remaining']} осталось)"
            return False, "Дневной лимит LONG сигналов исчерпан"
        
        return False, "Нет доступа к сигналам"
    
    def use_free_signal(self, user_id: int, signal_type: str) -> bool:
        """Использовать бесплатный сигнал"""
        if signal_type == 'short':
            return self.db.increment_free_short_signal(user_id)
        elif signal_type == 'long':
            return self._increment_free_long_signal(user_id)
        return False
    
    def _increment_free_long_signal(self, user_id: int) -> bool:
        """Увеличить счетчик FREE long-сигналов"""
        today = datetime.now().date().isoformat()
        cursor = self.get_connection().cursor()
        
        cursor.execute('''
            UPDATE users 
            SET free_long_signals_today = CASE 
                WHEN free_long_signals_date = ? THEN 
                    CASE WHEN free_long_signals_today < 3 THEN free_long_signals_today + 1 ELSE free_long_signals_today END
                ELSE 1
            END,
            free_long_signals_date = ?
            WHERE user_id = ? 
            AND (free_long_signals_date != ? OR free_long_signals_date IS NULL OR free_long_signals_today < 3)
        ''', (today, today, user_id, today))
        
        affected_rows = cursor.rowcount
        self.get_connection().commit()
        return affected_rows > 0
    
    # ========== ИСТОРИЯ СИГНАЛОВ ==========
    
    def get_signal_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Получить историю сигналов пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT id, asset, timeframe, signal_type, confidence, 
                   entry_price, result, profit_loss, stake_amount,
                   signal_date, close_date
            FROM signal_history 
            WHERE user_id = ? 
            ORDER BY signal_date DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'asset': row[1],
                'timeframe': row[2],
                'signal_type': row[3],
                'confidence': row[4],
                'entry_price': row[5],
                'result': row[6],
                'profit_loss': row[7],
                'stake_amount': row[8],
                'signal_date': row[9],
                'close_date': row[10]
            })
        return results
    
    def get_active_positions(self, user_id: int) -> List[Dict]:
        """Получить активные позиции пользователя"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT id, asset, timeframe, signal_type, confidence, 
                   entry_price, stake_amount, signal_date, expiration_time
            FROM signal_history 
            WHERE user_id = ? AND result = 'pending'
            ORDER BY signal_date DESC
        ''', (user_id,))
        
        results = []
        for row in cursor.fetchall():
            exp_time = row[8]
            is_expired = False
            if exp_time:
                try:
                    exp_date = datetime.fromisoformat(exp_time)
                    is_expired = exp_date < datetime.now()
                except:
                    pass
            
            results.append({
                'id': row[0],
                'asset': row[1],
                'timeframe': row[2],
                'signal_type': row[3],
                'confidence': row[4],
                'entry_price': row[5],
                'stake_amount': row[6],
                'signal_date': row[7],
                'expiration_time': exp_time,
                'is_expired': is_expired
            })
        return results
    
    def close_expired_positions(self, user_id: int) -> int:
        """Закрыть истекшие позиции"""
        cursor = self.get_connection().cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE signal_history
            SET result = 'expired', close_date = ?
            WHERE user_id = ? 
            AND result = 'pending'
            AND expiration_time IS NOT NULL
            AND expiration_time < ?
        ''', (now, user_id, now))
        
        affected = cursor.rowcount
        self.get_connection().commit()
        return affected
    
    # ========== СТАТИСТИКА И АНАЛИТИКА ==========
    
    def get_detailed_stats(self, user_id: int) -> Dict[str, Any]:
        """Получить детальную статистику"""
        short_stats = self.db.get_user_signal_stats(user_id, 'short')
        long_stats = self.db.get_user_signal_stats(user_id, 'long')
        
        # Общая статистика
        total_signals = short_stats['total_signals'] + long_stats['total_signals']
        total_wins = short_stats['wins'] + long_stats['wins']
        total_losses = short_stats['losses'] + long_stats['losses']
        
        overall_win_rate = (total_wins / total_signals * 100) if total_signals > 0 else 0
        
        # Прибыльность
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT SUM(profit_loss) FROM signal_history 
            WHERE user_id = ? AND result = 'win'
        ''', (user_id,))
        total_profit = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT SUM(profit_loss) FROM signal_history 
            WHERE user_id = ? AND result = 'loss'
        ''', (user_id,))
        total_loss = cursor.fetchone()[0] or 0
        
        net_profit = total_profit + total_loss
        
        # Лучшие активы
        cursor.execute('''
            SELECT asset, COUNT(*) as cnt, 
                   SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins
            FROM signal_history 
            WHERE user_id = ? AND result IS NOT NULL
            GROUP BY asset
            ORDER BY cnt DESC
            LIMIT 5
        ''', (user_id,))
        
        top_assets = []
        for row in cursor.fetchall():
            asset_wins = row[2] or 0
            asset_cnt = row[1] or 1
            top_assets.append({
                'asset': row[0],
                'total': row[1],
                'wins': asset_wins,
                'win_rate': round(asset_wins / asset_cnt * 100, 1)
            })
        
        return {
            'total_signals': total_signals,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'overall_win_rate': round(overall_win_rate, 1),
            'short': short_stats,
            'long': long_stats,
            'total_profit': round(total_profit, 2),
            'total_loss': round(total_loss, 2),
            'net_profit': round(net_profit, 2),
            'top_assets': top_assets
        }
    
    # ========== НАСТРОЙКИ ТОРГОВЛИ ==========
    
    def get_trading_settings(self, user_id: int) -> Dict[str, Any]:
        """Получить настройки торговли"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT martingale_type, martingale_multiplier, martingale_base_stake,
                   percentage_value, short_base_stake, long_percentage,
                   auto_trading_enabled, auto_trading_mode, auto_trading_strategy,
                   pocket_option_connected, ssid_automation_purchased
            FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return {
                'martingale_type': 3,
                'martingale_multiplier': 3,
                'martingale_base_stake': 100,
                'percentage_value': 2.5,
                'short_base_stake': 100,
                'long_percentage': 2.5,
                'auto_trading_enabled': False,
                'auto_trading_mode': 'demo',
                'auto_trading_strategy': 'percentage',
                'pocket_option_connected': False,
                'ssid_automation_purchased': False
            }
        
        return {
            'martingale_type': result[0] or 3,
            'martingale_multiplier': result[1] or 3,
            'martingale_base_stake': result[2] or 100,
            'percentage_value': result[3] or 2.5,
            'short_base_stake': result[4] or 100,
            'long_percentage': result[5] or 2.5,
            'auto_trading_enabled': bool(result[6]),
            'auto_trading_mode': result[7] or 'demo',
            'auto_trading_strategy': result[8] or 'percentage',
            'pocket_option_connected': bool(result[9]),
            'ssid_automation_purchased': bool(result[10])
        }
    
    def update_trading_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Обновить настройки торговли"""
        cursor = self.get_connection().cursor()
        
        valid_keys = [
            'martingale_type', 'martingale_multiplier', 'martingale_base_stake',
            'percentage_value', 'short_base_stake', 'long_percentage',
            'auto_trading_enabled', 'auto_trading_mode', 'auto_trading_strategy'
        ]
        
        updates = []
        values = []
        for key, value in settings.items():
            if key in valid_keys:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(user_id)
        
        cursor.execute(f'''
            UPDATE users SET {', '.join(updates)} WHERE user_id = ?
        ''', values)
        
        self.get_connection().commit()
        return cursor.rowcount > 0
    
    # ========== POCKET OPTION ==========
    
    def connect_pocket_option(self, user_id: int, email: str = None, ssid: str = None) -> bool:
        """Подключить аккаунт Pocket Option"""
        cursor = self.get_connection().cursor()
        
        if email:
            cursor.execute(
                'UPDATE users SET pocket_option_email = ?, pocket_option_connected = 1 WHERE user_id = ?',
                (email, user_id)
            )
        
        if ssid:
            cursor.execute(
                'UPDATE users SET pocket_option_ssid = ?, pocket_option_connected = 1 WHERE user_id = ?',
                (ssid, user_id)
            )
        
        self.get_connection().commit()
        return True
    
    def disconnect_pocket_option(self, user_id: int) -> bool:
        """Отключить аккаунт Pocket Option"""
        cursor = self.get_connection().cursor()
        cursor.execute(
            'UPDATE users SET pocket_option_connected = 0 WHERE user_id = ?',
            (user_id,)
        )
        self.get_connection().commit()
        return True
    
    def get_pocket_option_status(self, user_id: int) -> Dict[str, Any]:
        """Получить статус подключения Pocket Option"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT pocket_option_email, pocket_option_connected, 
                   pocket_option_ssid, auto_trading_enabled, auto_trading_mode
            FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return {
                'connected': False,
                'email': None,
                'has_ssid': False,
                'auto_trading_enabled': False,
                'auto_trading_mode': 'demo'
            }
        
        return {
            'connected': bool(result[1]),
            'email': result[0],
            'has_ssid': bool(result[2]),
            'auto_trading_enabled': bool(result[3]),
            'auto_trading_mode': result[4] or 'demo'
        }
    
    # ========== РЕФЕРАЛЫ ==========
    
    def get_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """Получить статистику рефералов"""
        cursor = self.get_connection().cursor()
        
        # Количество рефералов
        cursor.execute(
            'SELECT COUNT(*) FROM users WHERE referred_by = ?',
            (user_id,)
        )
        total_referrals = cursor.fetchone()[0] or 0
        
        # Активные рефералы (с подпиской)
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE referred_by = ? 
            AND is_premium = 1
        ''', (user_id,))
        active_referrals = cursor.fetchone()[0] or 0
        
        # Заработок
        cursor.execute(
            'SELECT referral_earnings FROM users WHERE user_id = ?',
            (user_id,)
        )
        earnings = cursor.fetchone()[0] or 0
        
        return {
            'total_referrals': total_referrals,
            'active_referrals': active_referrals,
            'earnings': round(earnings, 2)
        }
    
    def add_referral_bonus(self, user_id: int, amount: float) -> bool:
        """Добавить бонус за реферала"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            UPDATE users 
            SET referral_earnings = referral_earnings + ?
            WHERE user_id = ?
        ''', (amount, user_id))
        self.get_connection().commit()
        return cursor.rowcount > 0
    
    # ========== АДМИН ФУНКЦИИ ==========
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Получить всех пользователей"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT user_id, username, first_name, joined_date, 
                   subscription_type, subscription_end, is_premium,
                   signals_used, banned
            FROM users 
            ORDER BY joined_date DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        results = []
        for row in cursor.fetchall():
            sub_type = row[4]
            sub_end = row[5]
            is_active = False
            
            if sub_type and not sub_end:
                is_active = True
            elif sub_end:
                try:
                    end_date = datetime.fromisoformat(sub_end)
                    is_active = end_date > datetime.now()
                except:
                    pass
            
            results.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'joined_date': row[3],
                'subscription_type': sub_type,
                'subscription_active': is_active,
                'is_premium': bool(row[6]),
                'signals_used': row[7] or 0,
                'banned': bool(row[8])
            })
        return results
    
    def search_users(self, query: str) -> List[Dict]:
        """Поиск пользователей"""
        cursor = self.get_connection().cursor()
        search_query = f"%{query}%"
        cursor.execute('''
            SELECT user_id, username, first_name, subscription_type, is_premium
            FROM users 
            WHERE username LIKE ? OR first_name LIKE ? OR CAST(user_id AS TEXT) LIKE ?
            LIMIT 50
        ''', (search_query, search_query, search_query))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'subscription_type': row[3],
                'is_premium': bool(row[4])
            })
        return results
    
    def broadcast_message(self, user_ids: List[int], message: str) -> Dict[str, int]:
        """Рассылка сообщений (возвращает статистику)"""
        cursor = self.get_connection().cursor()
        
        sent = 0
        failed = 0
        banned = 0
        
        for user_id in user_ids:
            cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            if not result:
                failed += 1
            elif result[0]:
                banned += 1
            else:
                sent += 1
        
        # Здесь должен быть код отправки сообщений через Telegram API
        # Это заглушка - реальная отправка делается в bot.py
        
        return {
            'sent': sent,
            'failed': failed,
            'banned': banned,
            'total': len(user_ids)
        }


# Функции для совместимости с существующим кодом
def get_extended_db():
    """Получить экземпляр расширенной БД"""
    from bot.database import db
    return ExtendedDatabase(db)


# Создаем глобальный экземпляр
extended_db = None

def init_extended_db(db_instance):
    """Инициализировать расширенную базу данных"""
    global extended_db
    extended_db = ExtendedDatabase(db_instance)
    return extended_db
