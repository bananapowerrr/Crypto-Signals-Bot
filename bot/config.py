"""Конфигурация бота - все константы и настройки"""
import os
from datetime import timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

# Основные настройки
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
        'welcome_desc': 'Выберите тариф для начала работы:',
        'short_plan': '⚡️ SHORT',
        'short_desc': 'Быстрые сигналы (1-5 мин)\nМартингейл x3 стратегия',
        'long_plan': '🔵 LONG',
        'long_desc': 'Длинные сигналы (1-4 часа)\n2.5% процентная ставка',
        'vip_plan': '💎 VIP',
        'vip_desc': 'Все сигналы + 5 ежедневных рассылок',
        'free_plan': '🆓 FREE',
        'free_desc': 'LONG сигналы (10 рассылок/день)',
        'buy_subscription': 'Купить подписку',
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
        'subscription': 'Подписка',
        'expires': 'Истекает',
        'balance': 'Баланс',
        'win_rate': 'Доходность сигналов',
        'profit': 'Прибыль',
        'month': 'месяц',
        'months': 'месяцев',
    },
    'en': {
        'choose_language': '🌍 Choose language:',
        'language_selected': '✅ Language set: English',
        'choose_currency': '💱 Choose currency for price display:',
        'currency_selected': '✅ Currency set',
        'welcome': '👋 Welcome to Trading Signals Bot!',
        'welcome_desc': 'Choose a plan to get started:',
        'short_plan': '⚡️ SHORT',
        'short_desc': 'Fast signals (1-5 min)\nMartingale x3 strategy',
        'long_plan': '🔵 LONG',
        'long_desc': 'Long signals (1-4 hours)\n2.5% percentage rate',
        'vip_plan': '💎 VIP',
        'vip_desc': 'All signals + 5 daily broadcasts',
        'free_plan': '🆓 FREE',
        'free_desc': 'LONG signals (10 broadcasts/day)',
        'buy_subscription': 'Buy Subscription',
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
        'subscription': 'Subscription',
        'expires': 'Expires',
        'balance': 'Balance',
        'win_rate': 'Signal Profitability',
        'profit': 'Profit',
        'month': 'month',
        'months': 'months',
    },
    'es': {
        'choose_language': '🌍 Elige idioma:',
        'language_selected': '✅ Idioma establecido: Español',
        'choose_currency': '💱 Elige la moneda para mostrar precios:',
        'currency_selected': '✅ Moneda establecida',
        'welcome': '👋 ¡Bienvenido al Bot de Señales de Trading!',
        'welcome_desc': 'Elige un plan para comenzar:',
        'short_plan': '⚡️ CORTO',
        'short_desc': 'Señales rápidas (1-5 min)\nEstrategia Martingala x3',
        'long_plan': '🔵 LARGO',
        'long_desc': 'Señales largas (1-4 horas)\nTasa porcentual del 2.5%',
        'vip_plan': '💎 VIP',
        'vip_desc': 'Todas las señales + 5 transmisiones diarias',
        'free_plan': '🆓 GRATIS',
        'free_desc': 'Señales LONG (10 transmisiones/día)',
        'buy_subscription': 'Comprar Suscripción',
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
        'subscription': 'Suscripción',
        'expires': 'Expira',
        'balance': 'Saldo',
        'win_rate': 'Rentabilidad de Señales',
        'profit': 'Ganancia',
        'month': 'mes',
        'months': 'meses',
    },
    'pt': {
        'choose_language': '🌍 Escolha o idioma:',
        'language_selected': '✅ Idioma definido: Português',
        'choose_currency': '💱 Escolha a moeda para exibição de preços:',
        'currency_selected': '✅ Moeda definida',
        'welcome': '👋 Bem-vindo ao Bot de Sinais de Trading!',
        'welcome_desc': 'Escolha um plano para começar:',
        'short_plan': '⚡️ CURTO',
        'short_desc': 'Sinais rápidos (1-5 min)\nEstratégia Martingale x3',
        'long_plan': '🔵 LONGO',
        'long_desc': 'Sinais longos (1-4 horas)\nTaxa percentual de 2.5%',
        'vip_plan': '💎 VIP',
        'vip_desc': 'Todos os sinais + 5 transmissões diárias',
        'free_plan': '🆓 GRÁTIS',
        'free_desc': 'Sinais LONG (10 transmissões/dia)',
        'buy_subscription': 'Comprar Assinatura',
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
        'subscription': 'Assinatura',
        'expires': 'Expira',
        'balance': 'Saldo',
        'win_rate': 'Rentabilidade de Sinais',
        'profit': 'Lucro',
        'month': 'mês',
        'months': 'meses',
    }
}

# Курсы валют для конвертации
CURRENCY_RATES = {
    'RUB': 1.0,
    'USD': 0.011,
}

CURRENCY_SYMBOLS = {
    'RUB': '₽',
    'USD': '$',
}

# Система приоритетов пользователей
USER_PRIORITY = {
    'admin': 100,
    'vip': 80,
    'long': 60,
    'short': 60,
    'free': 20
}

# Таймауты сканирования в секундах
SCAN_TIMEOUTS = {
    'admin': 10,
    'vip': 15,
    'long': 20,
    'short': 20,
    'free': 45
}

# АКТУАЛЬНЫЕ АКТИВЫ POCKET OPTION
MARKET_ASSETS = {
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
    "crypto": {
        "BTC/USD": {"symbol": "BTC-USD", "type": "regular", "payout": 85},
        "ETH/USD": {"symbol": "ETH-USD", "type": "regular", "payout": 85},
        "LTC/USD": {"symbol": "LTC-USD", "type": "regular", "payout": 85},
        "XRP/USD": {"symbol": "XRP-USD", "type": "regular", "payout": 85},
        "ADA/USD": {"symbol": "ADA-USD", "type": "regular", "payout": 85},
        "BNB/USD": {"symbol": "BNB-USD", "type": "regular", "payout": 85},
    },
    "forex_otc": {
        "EUR/USD OTC": {"symbol": "EURUSD=X", "type": "otc", "payout": 92},
        "GBP/USD OTC": {"symbol": "GBPUSD=X", "type": "otc", "payout": 92},
        "USD/JPY OTC": {"symbol": "JPY=X", "type": "otc", "payout": 92},
        "AUD/USD OTC": {"symbol": "AUDUSD=X", "type": "otc", "payout": 92},
    },
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
    "stocks_otc": {
        "AAPL OTC": {"symbol": "AAPL", "type": "otc", "payout": 92},
        "INTC OTC": {"symbol": "INTC", "type": "otc", "payout": 92},
    },
    "stocks": {
        "AAPL": {"symbol": "AAPL", "type": "regular", "payout": 85},
        "MSFT": {"symbol": "MSFT", "type": "regular", "payout": 85},
        "AMZN": {"symbol": "AMZN", "type": "regular", "payout": 85},
        "TSLA": {"symbol": "TSLA", "type": "regular", "payout": 85},
        "META": {"symbol": "META", "type": "regular", "payout": 85},
        "INTC": {"symbol": "INTC", "type": "regular", "payout": 85},
        "BA": {"symbol": "BA", "type": "regular", "payout": 85},
    },
    "commodities_otc": {
        "GOLD OTC": {"symbol": "GC=F", "type": "otc", "payout": 80},
        "AUS200 OTC": {"symbol": "^AXJO", "type": "otc", "payout": 67},
    },
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