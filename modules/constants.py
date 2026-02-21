"""
Constants module - все константы бота
"""
import os
from datetime import timezone, timedelta

# Загрузка переменных окружения
from dotenv import load_dotenv
load_dotenv()

# Основные конфигурации
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
SUPPORT_CONTACT = "@banana_pwr"

# Московский часовой пояс (UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))

# Реферальная ссылка Pocket Option
POCKET_OPTION_REF_LINK = "https://pocket-friends.com/r/ugauihalod"

# Промокод для новых пользователей
PROMO_CODE = "FRIENDUGAUIHALOD"

# Выплата в процентах
PAYOUT_PERCENT = 92


# Команды бота по умолчанию
DEFAULT_BOT_COMMANDS = [
    ("start", "🏠 Главное меню"),
    ("settings", "⚙️ Настройки"),
    ("short", "⚡ SHORT сигнал (1-5 мин)"),
    ("long", "🔵 LONG сигнал (1-4 часа)"),
    ("my_stats", "📊 Моя статистика"),
    ("help", "❓ Помощь и инструкции"),
]

# Система мультиязычности
TRANSLATIONS = {
    'ru': {
        'choose_language': '🌍 Выберите язык / Choose language:',
        'language_selected': '✅ Язык установлен: Русский',
        'choose_currency': '💱 Выберите валюту для отображения цен:',
        'currency_selected': '✅ Валюта установлена',
        'welcome': '👋 Добро пожаловать в бот торговых сигналов!',
        'welcome_desc': 'Бот работает в бесплатном режиме - все сигналы доступны!',
        'my_stats': 'Моя статистика',
        'my_longs': 'Мои лонги',
        'help': 'Помощь',
        'settings': 'Настройки',
        'short_signal': 'Короткий сигнал',
        'long_signal': 'Длинный сигнал',
        'get_signal': '🎯 Получить сигнал',
        'back': '◀️ Назад',
        'call': '🟢 CALL',
        'put': '🔴 PUT',
        'price': 'Цена',
        'balance': 'Баланс',
        'win_rate': 'Доходность сигналов',
        'profit': 'Прибыль',
    },
    'en': {
        'choose_language': '🌍 Choose language:',
        'language_selected': '✅ Language set: English',
        'choose_currency': '💱 Choose currency for price display:',
        'currency_selected': '✅ Currency set',
        'welcome': '👋 Welcome to Trading Signals Bot!',
        'welcome_desc': 'Bot works in free mode - all signals available!',
        'my_stats': 'My Statistics',
        'my_longs': 'My Longs',
        'help': 'Help',
        'settings': 'Settings',
        'short_signal': 'Short Signal',
        'long_signal': 'Long Signal',
        'get_signal': '🎯 Get Signal',
        'back': '◀️ Back',
        'call': '🟢 CALL',
        'put': '🔴 PUT',
        'price': 'Price',
        'balance': 'Balance',
        'win_rate': 'Signal Profitability',
        'profit': 'Profit',
    },
    'es': {
        'choose_language': '🌍 Elige idioma:',
        'language_selected': '✅ Idioma establecido: Español',
        'choose_currency': '💱 Elige la moneda para mostrar precios:',
        'currency_selected': '✅ Moneda establecida',
        'welcome': '👋 ¡Bienvenido al Bot de Señales de Trading!',
        'welcome_desc': '¡El bot funciona en modo gratuito - todas las señales disponibles!',
        'my_stats': 'Mis Estadísticas',
        'my_longs': 'Mis Largos',
        'help': 'Ayuda',
        'settings': 'Configuración',
        'short_signal': 'Señal Corta',
        'long_signal': 'Señal Larga',
        'get_signal': '🎯 Obtener Señal',
        'back': '◀️ Atrás',
        'call': '🟢 CALL',
        'put': '🔴 PUT',
        'price': 'Precio',
        'balance': 'Saldo',
        'win_rate': 'Rentabilidad de Señales',
        'profit': 'Ganancia',
    },
    'pt': {
        'choose_language': '🌍 Escolha o idioma:',
        'language_selected': '✅ Idioma definido: Português',
        'choose_currency': '💱 Escolha a moeda para exibição de preços:',
        'currency_selected': '✅ Moeda definida',
        'welcome': '👋 Bem-vindo ao Bot de Sinais de Trading!',
        'welcome_desc': 'Bot funciona no modo gratuito - todos os sinais disponíveis!',
        'my_stats': 'Minhas Estatísticas',
        'my_longs': 'Meus Longos',
        'help': 'Ajuda',
        'settings': 'Configurações',
        'short_signal': 'Sinal Curto',
        'long_signal': 'Sinal Longo',
        'get_signal': '🎯 Obter Sinal',
        'back': '◀️ Voltar',
        'call': '🟢 CALL',
        'put': '🔴 PUT',
        'price': 'Preço',
        'balance': 'Saldo',
        'win_rate': 'Rentabilidade de Sinais',
        'profit': 'Lucro',
    }
}

# АКТУАЛЬНЫЕ АКТИВЫ POCKET OPTION с указанием типа (OTC/обычный) и доходности
MARKET_ASSETS = {
    # Криптовалюты OTC (приоритет - максимальная доходность 92%)
    "crypto_otc": {
        "BTC/USD OTC": {"symbol": "BTC-USD", "type": "otc", "payout": 92},
        "ETH/USD OTC": {"symbol": "ETH-USD", "type": "otc", "payout": 92},
        "ADA/USD OTC": {"symbol": "ADA-USD", "type": "otc", "payout": 92},
        "LINK/USD OTC": {"symbol": "LINK-USD", "type": "otc", "payout": 92},
        "SOL/USD OTC": {"symbol": "SOL-USD", "type": "otc", "payout": 92},
        "TRX/USD OTC": {"symbol": "TRX-USD", "type": "otc", "payout": 92},
        "AVAX/USD OTC": {"symbol": "AVAX-USD", "type": "otc", "payout": 92},
        "LTC/USD OTC": {"symbol": "LTC-USD", "type": "otc", "payout": 92},
        "BNB/USD OTC": {"symbol": "BNB-USD", "type": "otc", "payout": 92},
        "TON/USD OTC": {"symbol": "TON11419-USD", "type": "otc", "payout": 92},
    },
    
    # Криптовалюты обычные (85% доходность)
    "crypto": {
        "BTC/USD": {"symbol": "BTC-USD", "type": "regular", "payout": 85},
        "ETH/USD": {"symbol": "ETH-USD", "type": "regular", "payout": 85},
        "LTC/USD": {"symbol": "LTC-USD", "type": "regular", "payout": 85},
        "XRP/USD": {"symbol": "XRP-USD", "type": "regular", "payout": 85},
        "ADA/USD": {"symbol": "ADA-USD", "type": "regular", "payout": 85},
        "BNB/USD": {"symbol": "BNB-USD", "type": "regular", "payout": 85},
    },
    
    # Форекс OTC (92% доходность)
    "forex_otc": {
        "EUR/USD OTC": {"symbol": "EURUSD=X", "type": "otc", "payout": 92},
        "GBP/USD OTC": {"symbol": "GBPUSD=X", "type": "otc", "payout": 92},
        "USD/JPY OTC": {"symbol": "JPY=X", "type": "otc", "payout": 92},
        "AUD/USD OTC": {"symbol": "AUDUSD=X", "type": "otc", "payout": 92},
    },
    
    # Форекс обычные (85% доходность)
    "forex": {
        "EUR/USD": {"symbol": "EURUSD=X", "type": "regular", "payout": 85},
        "GBP/USD": {"symbol": "GBPUSD=X", "type": "regular", "payout": 85},
        "USD/JPY": {"symbol": "JPY=X", "type": "regular", "payout": 85},
        "AUD/USD": {"symbol": "AUDUSD=X", "type": "regular", "payout": 85},
        "USD/CHF": {"symbol": "CHF=X", "type": "regular", "payout": 85},
        "EUR/GBP": {"symbol": "EURGBP=X", "type": "regular", "payout": 85},
        "USD/CAD": {"symbol": "CAD=X", "type": "regular", "payout": 85},
        "NZD/USD": {"symbol": "NZDUSD=X", "type": "regular", "payout": 85},
        "EUR/JPY": {"symbol": "EURJPY=X", "type": "regular", "payout": 85},
        "GBP/JPY": {"symbol": "GBPJPY=X", "type": "regular", "payout": 85},
    },
    
    # Акции OTC (92% доходность)
    "stocks_otc": {
        "AAPL OTC": {"symbol": "AAPL", "type": "otc", "payout": 92},
        "INTC OTC": {"symbol": "INTC", "type": "otc", "payout": 92},
    },
    
    # Акции обычные (85% доходность)
    "stocks": {
        "AAPL": {"symbol": "AAPL", "type": "regular", "payout": 85},
        "MSFT": {"symbol": "MSFT", "type": "regular", "payout": 85},
        "AMZN": {"symbol": "AMZN", "type": "regular", "payout": 85},
        "TSLA": {"symbol": "TSLA", "type": "regular", "payout": 85},
        "META": {"symbol": "META", "type": "regular", "payout": 85},
        "INTC": {"symbol": "INTC", "type": "regular", "payout": 85},
        "BA": {"symbol": "BA", "type": "regular", "payout": 85},
    },
    
    # Товары и индексы OTC (высокая доходность)
    "commodities_otc": {
        "GOLD OTC": {"symbol": "GC=F", "type": "otc", "payout": 80},
        "AUS200 OTC": {"symbol": "^AXJO", "type": "otc", "payout": 67},
    },
    
    # Товары и индексы обычные (36-85%)
    "commodities": {
        "XAU/USD": {"symbol": "GC=F", "type": "regular", "payout": 85},
        "XAG/USD": {"symbol": "SI=F", "type": "regular", "payout": 85},
        "OIL/USD": {"symbol": "CL=F", "type": "regular", "payout": 85},
        "BRENT": {"symbol": "BZ=F", "type": "regular", "payout": 85},
        "NG/USD": {"symbol": "NG=F", "type": "regular", "payout": 85},
        "S&P500": {"symbol": "^GSPC", "type": "regular", "payout": 85},
        "NASDAQ": {"symbol": "^IXIC", "type": "regular", "payout": 85},
        "DOW": {"symbol": "^DJI", "type": "regular", "payout": 85},
        "FTSE": {"symbol": "^FTSE", "type": "regular", "payout": 85},
    }
}

# Таймфреймы
TIMEFRAMES = {
    "1M": "1m", "2M": "2m", "3M": "3m", "5M": "5m", "15M": "15m", 
    "30M": "30m", "1H": "1h", "4H": "4h", 
    "1D": "1d", "1W": "1wk"
}

SHORT_TIMEFRAMES = ["1M", "2M", "3M", "5M", "15M", "30M"]
LONG_TIMEFRAMES = ["1H", "4H", "1D", "1W"]

# Система приоритетов пользователей
USER_PRIORITY = {
    'admin': 100,
    'vip': 80,
    'long': 60,
    'short': 60,
    'free': 20
}

# Таймауты сканирования в секундах по приоритету
SCAN_TIMEOUTS = {
    'admin': 10,
    'vip': 15,
    'long': 20,
    'short': 20,
    'free': 45
}

# Кэш и константы
CACHE_DURATION = 180  # Кэш на 3 минуты
MAX_RECENT_ASSETS = 5  # Максимум последних активов для исключения
MAX_CONSECUTIVE_LOSSES = 2  # Максимум проигрышей подряд перед блокировкой
