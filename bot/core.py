"""
Core wrapper delegating to database module and providing helper methods
"""
from typing import Optional, Dict, List
import logging

from bot.database.db import db as Database

logger = logging.getLogger(__name__)


class CryptoSignalsBot:
    """Light wrapper that delegates to `bot.database.db.Database` instance."""

    def __init__(self):
        self.db = Database

    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        self.db.add_user(user_id, username, first_name)

    def ensure_user(self, user_id: int, username: str = None, first_name: str = None):
        return self.db.ensure_user(user_id, username, first_name)

    def get_user(self, user_id: int) -> Optional[Dict]:
        return self.db.get_user(user_id)

    def get_user_balance(self, user_id: int) -> float:
        user = self.db.get_user(user_id)
        if user and user.get('current_balance') is not None:
            return user['current_balance']
        return user['initial_balance'] if user and user.get('initial_balance') else 10000

    def set_user_balance(self, user_id: int, balance: float):
        self.db.update_user_balance(user_id, balance)

    def get_user_strategy(self, user_id: int) -> str:
        user = self.db.get_user(user_id)
        return user.get('trading_strategy') if user else 'martingale'

    def set_user_strategy(self, user_id: int, strategy: str, **params):
        self.db.update_user_strategy(user_id, strategy, **params)

    # Signal operations
    def save_signal(self, *args, **kwargs):
        return self.db.save_signal(*args, **kwargs)

    def update_signal_result(self, *args, **kwargs):
        return self.db.update_signal_result(*args, **kwargs)

    def get_user_signals(self, *args, **kwargs):
        return self.db.get_user_signals(*args, **kwargs)

    def get_user_stats(self, *args, **kwargs):
        return self.db.get_user_stats(*args, **kwargs)

    # Quota / referral helpers
    def can_use_signal(self, user_id: int, max_free_per_day: int = 3) -> bool:
        return self.db.can_use_signal(user_id, max_free_per_day)

    def increment_signal_count(self, user_id: int):
        return self.db.increment_signal_count(user_id)

    def set_referral_registered(self, user_id: int, registered: bool = True):
        return self.db.set_referral_registered(user_id, registered)

    def set_vip(self, user_id: int, vip: bool = True):
        return self.db.set_vip(user_id, vip)

    # Settings / admin
    def get_setting(self, *args, **kwargs):
        return self.db.get_setting(*args, **kwargs)

    def set_setting(self, *args, **kwargs):
        return self.db.set_setting(*args, **kwargs)

    def is_admin(self, user_id: int) -> bool:
        return self.db.get_setting('admin_users', '') and str(user_id) in self.db.get_setting('admin_users', '').split(',')


# Global instance
bot = CryptoSignalsBot()
