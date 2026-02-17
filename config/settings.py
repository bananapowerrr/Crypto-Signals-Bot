"""
Configuration settings for Crypto Signals Bot
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
SUPPORT_CONTACT = os.getenv("SUPPORT_CONTACT", "@banana_pwr")

# Database
DB_NAME = "crypto_signals_bot.db"

# Trading assets
MARKET_ASSETS = {
    "crypto_otc": {
        "BTC/USD": "BTC-USD",
        "ETH/USD": "ETH-USD",
        "XRP/USD": "XRP-USD",
        "SOL/USD": "SOL-USD",
        "ADA/USD": "ADA-USD",
        "DOGE/USD": "DOGE-USD",
        "DOT/USD": "DOT-USD",
        "MATIC/USD": "MATIC-USD",
    },
    "crypto_main": {
        "BTC/USD": "BTC-USD",
        "ETH/USD": "ETH-USD",
        "BNB/USD": "BNB-USD",
    },
    "forex_otc": {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "USD/JPY": "USDJPY=X",
        "AUD/USD": "AUDUSD=X",
    },
    "gold": {
        "XAU/USD": "XAUUSD=X",
    },
    "indices": {
        "US30": "^DJI",
        "US500": "^GSPC",
        "NAS100": "^IXIC",
    }
}

# Timeframes
SHORT_TIMEFRAMES = ["1M", "2M", "3M", "5M", "15M", "30M"]
LONG_TIMEFRAMES = ["1H", "4H", "1D", "1W"]
ALL_TIMEFRAMES = SHORT_TIMEFRAMES + LONG_TIMEFRAMES

# Technical indicators
INDICATORS = {
    "ema_short": 20,
    "ema_mid": 50,
    "ema_long": 100,
    "rsi": 14,
    "stoch_k": 14,
    "stoch_d": 3,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
}

# Signal generation
MIN_CONFIDENCE = 85
HIGH_CONFIDENCE = 90
VIP_CONFIDENCE = 95

# Default settings
DEFAULT_LANGUAGE = "ru"
DEFAULT_CURRENCY = "RUB"
DEFAULT_BALANCE = 10000
DEFAULT_STRATEGY = "martingale"
DEFAULT_PERCENTAGE = 2.5
DEFAULT_MARTINGALE_MULTIPLIER = 3.0

# Cache settings
CACHE_DURATION = 300  # 5 minutes

# Rate limiting
MAX_SIGNALS_PER_DAY = 100
SIGNAL_COOLDOWN = 5  # seconds between signals
