"""
Trading Strategy Analyzer
Analyzes market data and generates trading signals
"""
import logging
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio

logger = logging.getLogger(__name__)

# Technical indicators
INDICATOR_CONFIG = {
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


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculate MACD"""
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3):
    """Calculate Stochastic Oscillator"""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period).mean()
    return k, d


def calculate_support_resistance(close: pd.Series, window: int = 20) -> Tuple[float, float]:
    """Calculate support and resistance levels"""
    recent = close.tail(window)
    resistance = recent.max()
    support = recent.min()
    return support, resistance


class StrategyAnalyzer:
    """Analyzes market data and generates trading signals"""
    
    def __init__(self):
        self.indicator_config = INDICATOR_CONFIG
    
    async def fetch_market_data(self, ticker: str, timeframe: str = "1h", period: str = "5d") -> Optional[pd.DataFrame]:
        """Fetch market data from Yahoo Finance"""
        try:
            # Map timeframes to Yahoo Finance intervals
            tf_map = {
                "1M": "1m", "2M": "2m", "3M": "3m", "5M": "5m", 
                "15M": "15m", "30M": "30m",
                "1H": "1h", "4H": "4h", "1D": "1d", "1W": "1wk"
            }
            interval = tf_map.get(timeframe, "1h")
            
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No data for {ticker}")
                return None
                
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """Analyze market data and return indicators"""
        if df is None or len(df) < 50:
            return {}
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        
        # Calculate indicators
        indicators = {
            "ema_20": calculate_ema(close, 20),
            "ema_50": calculate_ema(close, 50),
            "ema_100": calculate_ema(close, 100),
            "rsi": calculate_rsi(close, 14),
        }
        
        macd, signal, hist = calculate_macd(close)
        indicators["macd"] = macd
        indicators["macd_signal"] = signal
        indicators["macd_hist"] = hist
        
        stoch_k, stoch_d = calculate_stochastic(high, low, close)
        indicators["stoch_k"] = stoch_k
        indicators["stoch_d"] = stoch_d
        
        support, resistance = calculate_support_resistance(close)
        indicators["support"] = support
        indicators["resistance"] = resistance
        
        return indicators
    
    def generate_signal(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Generate trading signal based on indicators"""
        if not indicators:
            return {"signal": "neutral", "confidence": 0, "reason": "Insufficient data"}
        
        scores = {"call": 0, "put": 0, "neutral": 0}
        reasons = []
        
        close = df['Close'].iloc[-1]
        
        # EMA Trend
        ema_20 = indicators["ema_20"].iloc[-1]
        ema_50 = indicators["ema_50"].iloc[-1]
        ema_100 = indicators["ema_100"].iloc[-1]
        
        if ema_20 > ema_50 > ema_100:
            scores["call"] += 2
            reasons.append("Восходящий тренд (EMA)")
        elif ema_20 < ema_50 < ema_100:
            scores["put"] += 2
            reasons.append("Нисходящий тренд (EMA)")
        
        # RSI
        rsi = indicators["rsi"].iloc[-1]
        if rsi < 30:
            scores["call"] += 1.5
            reasons.append(f"RSI перепродан ({rsi:.1f})")
        elif rsi > 70:
            scores["put"] += 1.5
            reasons.append(f"RSI перекуплен ({rsi:.1f})")
        
        # MACD
        macd = indicators["macd"].iloc[-1]
        macd_signal = indicators["macd_signal"].iloc[-1]
        macd_hist = indicators["macd_hist"].iloc[-1]
        
        if macd > macd_signal and macd_hist > 0:
            scores["call"] += 1
            reasons.append("MACD бычий")
        elif macd < macd_signal and macd_hist < 0:
            scores["put"] += 1
            reasons.append("MACD медвежий")
        
        # Stochastic
        stoch_k = indicators["stoch_k"].iloc[-1]
        stoch_d = indicators["stoch_d"].iloc[-1]
        
        if stoch_k < 20 and stoch_d < 20:
            scores["call"] += 1
            reasons.append("Stochastic перепродан")
        elif stoch_k > 80 and stoch_d > 80:
            scores["put"] += 1
            reasons.append("Stochastic перекуплен")
        
        # Support/Resistance
        support = indicators["support"]
        resistance = indicators["resistance"]
        
        if close < support + (resistance - support) * 0.2:
            scores["call"] += 0.5
            reasons.append("Цена у поддержки")
        elif close > resistance - (resistance - support) * 0.2:
            scores["put"] += 0.5
            reasons.append("Цена у сопротивления")
        
        # Determine signal
        max_score = max(scores.values())
        total = sum(scores.values())
        
        if max_score < 1:
            signal = "neutral"
            confidence = 50
        else:
            if scores["call"] >= scores["put"] + 1:
                signal = "call"
                confidence = min(50 + (scores["call"] / total) * 50, 95)
            elif scores["put"] >= scores["call"] + 1:
                signal = "put"
                confidence = min(50 + (scores["put"] / total) * 50, 95)
            else:
                signal = "neutral"
                confidence = 50
        
        return {
            "signal": signal,
            "confidence": round(confidence, 1),
            "reasons": reasons,
            "scores": scores,
            "price": close
        }
    
    async def analyze_asset(self, ticker: str, timeframe: str = "1h") -> Optional[Dict]:
        """Full analysis of an asset"""
        df = await self.fetch_market_data(ticker, timeframe)
        if df is None:
            return None
        
        indicators = self.analyze(df)
        signal_data = self.generate_signal(df, indicators)
        
        return {
            "ticker": ticker,
            "timeframe": timeframe,
            "indicators": indicators,
            "signal": signal_data
        }


# Singleton instance
analyzer = StrategyAnalyzer()


async def analyze_market(asset: str, ticker: str, timeframe: str = "1h") -> Optional[Dict]:
    """Analyze market for given asset"""
    return await analyzer.analyze_asset(ticker, timeframe)
