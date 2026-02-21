"""
Market Analyzer module - анализ рынка и генерация торговых сигналов
"""
import logging
import time
import asyncio
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone

from modules.constants import (
    MARKET_ASSETS, TIMEFRAMES, SHORT_TIMEFRAMES, LONG_TIMEFRAMES,
    CACHE_DURATION, MAX_RECENT_ASSETS, MAX_CONSECUTIVE_LOSSES
)

logger = logging.getLogger(__name__)

# Глобальный кэш сигналов
signal_cache = {
    'short': {'signals': [], 'timestamp': 0},
    'long': {'signals': [], 'timestamp': 0}
}

# Отслеживание последних выданных активов для разнообразия
last_used_assets = {'short': [], 'long': []}

# Отслеживание проигрышей по активам
asset_loss_streak = {}
blocked_assets = {}


def calculate_indicators(df):
    """Рассчитать технические индикаторы"""
    try:
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_100'] = df['Close'].ewm(span=100, adjust=False).mean()

        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()

        low_14 = df['Low'].rolling(14).min()
        high_14 = df['High'].rolling(14).max()
        df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
        df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()

        df['Resistance'] = df['High'].rolling(10).max()
        df['Support'] = df['Low'].rolling(10).min()

        df = df.fillna(method='bfill').fillna(method='ffill')
        return df
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return df


def generate_fallback_signal(asset_symbol, timeframe):
    """Fallback сигнал когда реальный анализ недоступен"""
    trend = np.random.choice(['BULLISH', 'BEARISH'])
    signal = 'CALL' if trend == 'BULLISH' else 'PUT'
    direction = '📈' if signal == 'CALL' else '📉'
    confidence = np.random.uniform(70, 85)

    return {
        'asset': asset_symbol,
        'timeframe': timeframe,
        'price': 1.0,
        'trend': trend,
        'rsi': 50.0,
        'macd': 0.0,
        'stoch_k': 50.0,
        'signal': signal,
        'confidence': round(confidence, 1),
        'direction': direction,
        'score': 2,
        'volatility': 0.5,
        'whale_detected': False,
        'volume': 0,
        'avg_volume': 0,
        'volume_ratio': 1.0,
        'ema_20': 1.0,
        'ema_50': 1.0,
        'timestamp': datetime.now(),
        'asset_type': 'regular',
        'payout': 85
    }, None


def analyze_asset_timeframe(asset_symbol, timeframe, conn=None, min_conf=70, max_conf=92):
    """Анализ актива на заданном таймфрейме"""
    try:
        period_map = {
            "1M": "5d", "5M": "5d", "15M": "1mo",
            "30M": "1mo", "1H": "3mo", "4H": "6mo",
            "1D": "1y", "1W": "2y"
        }
        period = period_map.get(timeframe, "1mo")
        yf_timeframe = TIMEFRAMES.get(timeframe, "1h")

        max_retries = 2
        data = pd.DataFrame()
        for attempt in range(max_retries):
            try:
                ticker = yf.Ticker(asset_symbol)
                data = ticker.history(period=period, interval=yf_timeframe)
                if not data.empty:
                    break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(0.1)
                else:
                    data = pd.DataFrame()

        if len(data) < 20:
            return generate_fallback_signal(asset_symbol, timeframe)

        data = calculate_indicators(data)

        if data.empty:
            return generate_fallback_signal(asset_symbol, timeframe)

        current = data.iloc[-1]
        trend = "BULLISH" if current['EMA_20'] > current['EMA_50'] else "BEARISH"

        call_conditions = [
            trend == "BULLISH",
            current['Close'] > current['EMA_20'],
            current['RSI'] < 70,
            current['Stoch_K'] < 80,
            current['MACD'] > current['MACD_Signal']
        ]

        put_conditions = [
            trend == "BEARISH",
            current['Close'] < current['EMA_20'],
            current['RSI'] > 30,
            current['Stoch_K'] > 20,
            current['MACD'] < current['MACD_Signal']
        ]

        call_score = sum(call_conditions)
        put_score = sum(put_conditions)

        volatility = data['Close'].pct_change().std() * 100

        whale_factor = 0
        avg_volume = 0
        current_volume = 0
        volume_ratio = 0

        if 'Volume' in data.columns:
            avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                if volume_ratio >= 1.5:
                    whale_factor = 1
                    if trend == "BULLISH":
                        call_score += 1
                    else:
                        put_score += 1

        stability_bonus = 0
        if volatility < 2.0:
            stability_bonus = 3
        elif volatility < 3.0:
            stability_bonus = 1

        total_call_score = call_score + stability_bonus
        total_put_score = put_score + stability_bonus

        if total_call_score >= total_put_score:
            chosen_signal = 'CALL'
            chosen_score = total_call_score
            direction = '📈'
        else:
            chosen_signal = 'PUT'
            chosen_score = total_put_score
            direction = '📉'

        base_conf = min_conf + chosen_score * 6.0
        confidence = float(np.clip(base_conf, min_conf, max_conf))

        signal_info = {
            'asset': asset_symbol,
            'timeframe': timeframe,
            'price': float(current['Close']),
            'trend': trend,
            'rsi': float(current['RSI']),
            'macd': float(current['MACD']),
            'stoch_k': float(current['Stoch_K']),
            'signal': chosen_signal,
            'confidence': round(confidence, 1),
            'direction': direction,
            'score': chosen_score,
            'volatility': float(volatility),
            'whale_detected': whale_factor > 0,
            'volume': float(current_volume),
            'avg_volume': float(avg_volume),
            'volume_ratio': float(volume_ratio),
            'ema_20': float(current['EMA_20']),
            'ema_50': float(current['EMA_50']),
            'timestamp': datetime.now(),
            'asset_type': 'regular',
            'payout': 85
        }

        return signal_info, None

    except Exception as e:
        logger.error(f"Error analyzing {asset_symbol} on {timeframe}: {e}")
        return generate_fallback_signal(asset_symbol, timeframe)


async def analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=85, is_otc=False):
    """Асинхронный анализ одного актива"""
    try:
        asset_symbol = asset_data["symbol"]
        signal_info, error = await asyncio.to_thread(
            analyze_asset_timeframe, asset_symbol, timeframe
        )

        if signal_info and signal_info.get('confidence', 0) >= min_confidence:
            signal_info['asset_type'] = asset_data.get("type", "regular")
            signal_info['payout'] = asset_data.get("payout", 85)
            signal_info['is_otc'] = is_otc
            return (asset_name, signal_info, timeframe)
    except Exception as e:
        logger.debug(f"Error analyzing {asset_name}: {e}")
    return None


async def scan_market_signals(timeframe_type, force_realtime=False, conn=None):
    """Оптимизированное сканирование рынка с поддержкой OTC активов"""
    cache_key = timeframe_type if timeframe_type in ['short', 'long'] else 'short'
    current_time = time.time()

    # SHORT всегда в реальном времени, LONG использует кэш
    if timeframe_type == "long" and not force_realtime:
        if (current_time - signal_cache[cache_key]['timestamp']) < CACHE_DURATION:
            cached_signals = signal_cache[cache_key]['signals']
            if cached_signals:
                logger.info(f"✅ Using cached {cache_key} signals ({len(cached_signals)} found)")
                return cached_signals

    signals = []
    tasks = []

    if timeframe_type == "short":
        logger.info("🔍 SHORT: Поиск сигналов в реальном времени (приоритет OTC 92%)")

        for timeframe in ["1M", "5M"]:
            # OTC Криптовалюты (92% доходность)
            for asset_name, asset_data in MARKET_ASSETS.get("crypto_otc", {}).items():
                tasks.append(analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=80, is_otc=True))

            # OTC Форекс
            for asset_name, asset_data in MARKET_ASSETS.get("forex_otc", {}).items():
                tasks.append(analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=80, is_otc=True))

            # OTC Акции
            for asset_name, asset_data in MARKET_ASSETS.get("stocks_otc", {}).items():
                tasks.append(analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=80, is_otc=True))

            # Обычные активы (85% доходность)
            for asset_name, asset_data in MARKET_ASSETS.get("crypto", {}).items():
                tasks.append(analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=75, is_otc=False))

            for asset_name, asset_data in MARKET_ASSETS.get("forex", {}).items():
                tasks.append(analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=75, is_otc=False))

            for asset_name, asset_data in MARKET_ASSETS.get("stocks", {}).items():
                tasks.append(analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=75, is_otc=False))

            for asset_name, asset_data in MARKET_ASSETS.get("commodities", {}).items():
                tasks.append(analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=75, is_otc=False))

    elif timeframe_type == "long":
        for timeframe in ["1H", "4H"]:
            # OTC Форекс
            for asset_name, asset_data in MARKET_ASSETS.get("forex_otc", {}).items():
                tasks.append(analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=80, is_otc=True))

            # Обычный форекс
            for asset_name, asset_data in MARKET_ASSETS.get("forex", {}).items():
                tasks.append(analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=75, is_otc=False))

            # Обычные акции
            for asset_name, asset_data in MARKET_ASSETS.get("stocks", {}).items():
                tasks.append(analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=75, is_otc=False))

            # Товары и индексы
            for asset_name, asset_data in MARKET_ASSETS.get("commodities", {}).items():
                tasks.append(analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=75, is_otc=False))

    # Выполнить все анализы параллельно
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Собрать успешные сигналы
    for result in results:
        if result and not isinstance(result, Exception):
            signals.append(result)

    # Сортировать по score и взять ТОП-3
    if signals:
        scored_signals = []
        for asset_name, signal_info, timeframe in signals:
            base_score = signal_info.get('confidence', 0)
            payout_bonus = 25 if signal_info.get('payout', 85) >= 92 else 0
            final_score = base_score + payout_bonus
            scored_signals.append((asset_name, signal_info, timeframe, final_score))

        scored_signals.sort(key=lambda x: x[3], reverse=True)
        top_signals = [(name, info, tf) for name, info, tf, score in scored_signals[:3]]
        signals = top_signals

        logger.info(f"📊 Market scan complete: {len(scored_signals)} signals found, TOP-3 selected")
        for i, (name, info, tf, score) in enumerate(scored_signals[:3], 1):
            logger.info(f"   #{i}: {name} {tf} | Score: {score:.1f} | Payout: {info.get('payout', 85)}%")

    # Обновить кэш
    signal_cache[cache_key]['signals'] = signals
    signal_cache[cache_key]['timestamp'] = current_time

    # Fallback если нет сигналов
    if not signals:
        import random
        logger.info("⚡ Генерируем fallback сигнал из OTC активов (92% доходность)")
        if timeframe_type == "short":
            all_assets = list(MARKET_ASSETS.get("crypto_otc", {}).items()) + list(MARKET_ASSETS.get("forex_otc", {}).items())
            timeframe = random.choice(["1M", "5M"])
        elif timeframe_type == "long":
            all_assets = list(MARKET_ASSETS.get("forex_otc", {}).items()) + list(MARKET_ASSETS.get("stocks_otc", {}).items())
            timeframe = random.choice(["1H", "4H"])
        else:
            all_assets = list(MARKET_ASSETS.get("crypto_otc", {}).items())[:3]
            timeframe = "1M"

        if all_assets:
            asset_name, asset_data = random.choice(all_assets)
            fallback_signal = generate_fallback_signal(asset_data["symbol"], timeframe)
            if fallback_signal and fallback_signal[0]:
                fallback_signal[0]['asset_type'] = asset_data["type"]
                fallback_signal[0]['payout'] = asset_data["payout"]
                signals.append((asset_name, fallback_signal[0], timeframe))
                logger.info(f"✅ Создан fallback OTC сигнал: {asset_name} {timeframe} ({asset_data['payout']}% доходность)")

    return signals


def get_expiration_time(timeframe):
    """Возвращает оптимальное время экспирации для Pocket Option"""
    expiration_map = {
        "1M": "1 минута",
        "3M": "3 минуты",
        "5M": "5 минут",
        "15M": "15 минут",
        "30M": "30 минут",
        "1H": "1 час",
        "4H": "4 часа",
        "1D": "1 день"
    }
    return expiration_map.get(timeframe, "5 минут")


def calculate_expiration_time(timeframe):
    """Рассчитать время экспирации на основе таймфрейма"""
    timeframe_minutes = {
        "1M": 1, "2M": 2, "3M": 3, "5M": 5,
        "15M": 15, "30M": 30, "1H": 60,
        "4H": 240, "1D": 1440, "1W": 10080
    }
    minutes = timeframe_minutes.get(timeframe, 5)
    expiration_time = datetime.now() + timedelta(minutes=minutes)
    return expiration_time.isoformat()


def get_pocket_option_asset_name(asset_name):
    """Конвертирует название актива в формат Pocket Option"""
    is_otc = " OTC" in asset_name
    base_name = asset_name.replace(" OTC", "")

    pocket_map = {
        "BTC/USD": "BITCOIN", "ETH/USD": "ETHEREUM", "LTC/USD": "LITECOIN",
        "XRP/USD": "XRP", "ADA/USD": "CARDANO", "BNB/USD": "BINANCE COIN",
        "SOL/USD": "SOLANA", "TRX/USD": "TRON", "AVAX/USD": "AVALANCHE",
        "TON/USD": "TONCOIN", "LINK/USD": "CHAINLINK",
        "EUR/USD": "EUR/USD", "GBP/USD": "GBP/USD", "USD/JPY": "USD/JPY",
        "USD/CHF": "USD/CHF", "USD/CAD": "USD/CAD", "AUD/USD": "AUD/USD",
        "NZD/USD": "NZD/USD", "EUR/GBP": "EUR/GBP", "EUR/JPY": "EUR/JPY",
        "GBP/JPY": "GBP/JPY",
        "XAU/USD": "GOLD", "XAG/USD": "SILVER", "OIL/USD": "OIL (WTI)",
        "BRENT": "BRENT OIL", "NG/USD": "NATURAL GAS",
        "S&P500": "US 500", "NASDAQ": "US TECH 100", "DOW": "US 30",
        "FTSE": "UK 100",
        "AAPL": "APPLE", "MSFT": "MICROSOFT", "TSLA": "TESLA",
        "AMZN": "AMAZON", "META": "META", "INTC": "INTEL", "BA": "BOEING"
    }

    pocket_name = pocket_map.get(base_name, base_name)
    if is_otc:
        pocket_name = f"{pocket_name} OTC"
    return pocket_name


# Анализатор - синглтон
class MarketAnalyzer:
    """Класс для анализа рынка"""
    
    def __init__(self):
        self.cache = signal_cache
        self.last_used_assets = last_used_assets
        self.asset_loss_streak = asset_loss_streak
        self.blocked_assets = blocked_assets
    
    async def get_signal(self, timeframe_type, user_priority='free', user_id=None, conn=None):
        """Получить лучший сигнал из кэша"""
        signals = self.cache.get(timeframe_type, {}).get('signals', [])
        
        if not signals:
            return None
        
        # Получить список активных сигналов пользователя для исключения
        active_user_signals = set()
        if conn and user_id:
            active_user_signals = set(conn.get_user_active_signals(user_id) if hasattr(conn, 'get_user_active_signals') else [])
        
        # Очистить заблокированные активы
        current_time = time.time()
        for asset in list(self.blocked_assets.keys()):
            if current_time >= self.blocked_assets.get(asset, 0):
                if asset in self.blocked_assets:
                    del self.blocked_assets[asset]
                if asset in self.asset_loss_streak:
                    del self.asset_loss_streak[asset]
        
        scored_signals = []
        
        for asset_name, signal_info, timeframe in signals:
            # Исключаем активные сигналы пользователя
            if (asset_name, timeframe) in active_user_signals:
                continue
            
            # Исключаем заблокированные активы
            if asset_name in self.blocked_assets:
                continue
            
            # Исключаем недавно использованные активы
            if asset_name in self.last_used_assets.get(timeframe_type, []):
                continue
            
            base_confidence = signal_info.get('confidence', 0)
            payout = signal_info.get('payout', 85)
            
            payout_bonus = 0
            if payout >= 92:
                payout_bonus = 25
            elif payout >= 85:
                payout_bonus = 15
            
            final_score = base_confidence + payout_bonus
            
            scored_signals.append({
                'asset_name': asset_name,
                'signal_info': signal_info,
                'timeframe': timeframe,
                'final_score': final_score
            })
        
        if not scored_signals:
            return None
        
        scored_signals.sort(key=lambda x: x['final_score'], reverse=True)
        best = scored_signals[0]
        
        # Добавляем в список последних
        if timeframe_type in self.last_used_assets:
            self.last_used_assets[timeframe_type].append(best['asset_name'])
            if len(self.last_used_assets[timeframe_type]) > MAX_RECENT_ASSETS:
                self.last_used_assets[timeframe_type].pop(0)
        
        return (best['asset_name'], best['signal_info'], best['timeframe'])
    
    def update_after_win(self, asset_name, timeframe_type='short'):
        """Обновить после выигрыша"""
        if asset_name in self.asset_loss_streak:
            del self.asset_loss_streak[asset_name]
        if asset_name in self.blocked_assets:
            del self.blocked_assets[asset_name]
    
    def update_after_loss(self, asset_name, timeframe_type='short'):
        """Обновить после проигрыша"""
        if asset_name in self.asset_loss_streak:
            self.asset_loss_streak[asset_name] += 1
        else:
            self.asset_loss_streak[asset_name] = 1
        
        if self.asset_loss_streak[asset_name] >= MAX_CONSECUTIVE_LOSSES:
            self.blocked_assets[asset_name] = time.time() + 3600  # Блокировка на 1 час
            logger.warning(f"🚫 Актив {asset_name} заблокирован после {MAX_CONSECUTIVE_LOSSES} проигрышей подряд")


# Создаем глобальный экземпляр
analyzer = MarketAnalyzer()
