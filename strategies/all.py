"""
All Trading Strategies - Unified module
Contains Martingale, Percentage, and D'Alembert strategies
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    @abstractmethod
    def calculate_stake(self, balance: float, base_stake: float = None) -> float:
        """Calculate the stake amount based on the strategy"""
        pass
    
    @abstractmethod
    def after_win(self, current_stake: float, base_stake: float) -> float:
        """Calculate stake after a win"""
        pass
    
    @abstractmethod
    def after_loss(self, current_stake: float, base_stake: float) -> float:
        """Calculate stake after a loss"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name"""
        pass


class MartingaleStrategy(BaseStrategy):
    """
    Martingale Strategy
    Doubles stake after each loss, returns to base after win
    High risk, high reward
    """
    
    def __init__(self, multiplier: float = 3.0):
        self.multiplier = multiplier
    
    def calculate_stake(self, balance: float, base_stake: float = None) -> float:
        if base_stake is None:
            base_stake = balance / 364  # 0.1% of balance per day assuming 4 years
        return base_stake
    
    def after_win(self, current_stake: float, base_stake: float) -> float:
        return base_stake
    
    def after_loss(self, current_stake: float, base_stake: float) -> float:
        return current_stake * self.multiplier
    
    def get_name(self) -> str:
        return "martingale"


class PercentageStrategy(BaseStrategy):
    """
    Percentage Strategy
    Uses fixed percentage of balance for each trade
    Lower risk, steady growth
    """
    
    def __init__(self, percentage: float = 2.5):
        self.percentage = percentage / 100  # Convert to decimal
    
    def calculate_stake(self, balance: float, base_stake: float = None) -> float:
        return balance * self.percentage
    
    def after_win(self, current_stake: float, base_stake: float) -> float:
        return base_stake  # Returns to percentage of current balance
    
    def after_loss(self, current_stake: float, base_stake: float) -> float:
        return base_stake  # Returns to percentage of current balance
    
    def get_name(self) -> str:
        return "percentage"


class DAlembertStrategy(BaseStrategy):
    """
    D'Alembert Strategy
    Increases stake by unit after loss, decreases by unit after win
    Moderate risk
    """
    
    def __init__(self, unit: float = 10.0):
        self.unit = unit
    
    def calculate_stake(self, balance: float, base_stake: float = None) -> float:
        if base_stake is None:
            base_stake = balance * 0.02  # Default 2%
        return base_stake
    
    def after_win(self, current_stake: float, base_stake: float) -> float:
        return max(base_stake, current_stake - self.unit)
    
    def after_loss(self, current_stake: float, base_stake: float) -> float:
        return current_stake + self.unit
    
    def get_name(self) -> str:
        return "dalembert"


class ConservativeStrategy(BaseStrategy):
    """
    Conservative Strategy
    Fixed small percentage, very low risk
    """
    
    def __init__(self, percentage: float = 1.0):
        self.percentage = percentage / 100
    
    def calculate_stake(self, balance: float, base_stake: float = None) -> float:
        return balance * self.percentage
    
    def after_win(self, current_stake: float, base_stake: float) -> float:
        return base_stake
    
    def after_loss(self, current_stake: float, base_stake: float) -> float:
        return base_stake
    
    def get_name(self) -> str:
        return "conservative"


# Strategy registry
STRATEGIES = {
    'martingale': MartingaleStrategy,
    'percentage': PercentageStrategy,
    'dalembert': DAlembertStrategy,
    'conservative': ConservativeStrategy,
}


def get_strategy(strategy_name: str, **kwargs) -> BaseStrategy:
    """
    Get strategy instance by name
    
    Args:
        strategy_name: Name of the strategy
        **kwargs: Additional parameters for strategy
        
    Returns:
        Strategy instance
    """
    strategy_class = STRATEGIES.get(strategy_name.lower())
    if strategy_class is None:
        logger.warning(f"Unknown strategy: {strategy_name}, using martingale")
        strategy_class = MartingaleStrategy
    return strategy_class(**kwargs)


def calculate_stake(
    balance: float,
    strategy: str = 'martingale',
    current_stake: float = None,
    base_stake: float = None,
    is_win: bool = None,
    **kwargs
) -> float:
    """
    Calculate stake using specified strategy
    
    Args:
        balance: Current balance
        strategy: Strategy name
        current_stake: Current stake amount
        base_stake: Base stake amount
        is_win: Was the last trade a win? (None for new trade)
        **kwargs: Additional strategy parameters
        
    Returns:
        Calculated stake amount
    """
    strat = get_strategy(strategy, **kwargs)
    
    if current_stake is None or is_win is None:
        # New trade
        return strat.calculate_stake(balance, base_stake)
    
    # After win or loss
    if is_win:
        return strat.after_win(current_stake, base_stake)
    else:
        return strat.after_loss(current_stake, base_stake)


def get_recommended_stake(balance: float, strategy: str = 'martingale') -> float:
    """
    Get recommended stake for a given balance and strategy
    
    Args:
        balance: Current balance
        strategy: Strategy name
        
    Returns:
        Recommended stake amount
    """
    strat = get_strategy(strategy)
    return strat.calculate_stake(balance)


# Default strategy settings
DEFAULT_STRATEGY = 'martingale'
DEFAULT_MARTINGALE_MULTIPLIER = 3.0
DEFAULT_PERCENTAGE = 2.5
DEFAULT_DALEMBERT_UNIT = 10.0
DEFAULT_CONSERVATIVE_PERCENTAGE = 1.0
