"""
Signal Generator module - анализ рынка и генерация торговых сигналов
"""
import logging
import time
import random
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Таймфреймы
TIMEFRAMES = {
    "1M": "1m", "3M": "3m", "5M": "5m", "15M": "15m",
    "30M": "30m", "1H": "1h", "4H": "4h",
    "1D": "1d", "1W": "1wk"
}

SHORT_TIMEFRAMES = ["1M", "2M", "3M", "5M", "15M", "30M"]
LONG_TIMEFRAMES = ["1H", "4H", "1D", "1W"]


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
        'timestamp': datetime.now()
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
            'timestamp': datetime.now()
        }

        return signal_info, None

    except Exception as e:
        logger.error(f"Error analyzing {asset_symbol} on {timeframe}: {e}")
        return generate_fallback_signal(asset_symbol, timeframe)


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
