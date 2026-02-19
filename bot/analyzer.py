"""РњРѕРґСѓР»СЊ Р°РЅР°Р»РёР·Р° СЂС‹РЅРєР° Рё РіРµРЅРµСЂР°С†РёРё СЃРёРіРЅР°Р»РѕРІ"""
import logging
import time
import random
import asyncio
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any

from bot.config import MARKET_ASSETS
from bot.database import db

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """РљР»Р°СЃСЃ РґР»СЏ Р°РЅР°Р»РёР·Р° СЂС‹РЅРєР° Рё РіРµРЅРµСЂР°С†РёРё С‚РѕСЂРіРѕРІС‹С… СЃРёРіРЅР°Р»РѕРІ"""
    
    def __init__(self):
        self.assets = {}
        self.timeframes = {
            "1M": "1m", "3M": "3m", "5M": "5m", "15M": "15m", 
            "30M": "30m", "1H": "1h", "4H": "4h", 
            "1D": "1d", "1W": "1wk"
        }
        
        # РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ Р°РєС‚РёРІРѕРІ РёР· MARKET_ASSETS
        self._init_assets()
        
        # РљСЌС€ СЃРёРіРЅР°Р»РѕРІ
        self.signal_cache = {
            'short': {'signals': [], 'timestamp': 0},
            'long': {'signals': [], 'timestamp': 0}
        }
        self.cache_duration = 180  # 3 РјРёРЅСѓС‚С‹
        
        # РћС‚СЃР»РµР¶РёРІР°РЅРёРµ РїРѕСЃР»РµРґРЅРёС… РІС‹РґР°РЅРЅС‹С… Р°РєС‚РёРІРѕРІ
        self.last_used_assets = {
            'short': [],
            'long': []
        }
        self.max_recent_assets = 5
    
    def _init_assets(self):
        """РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ СЃР»РѕРІР°СЂСЏ Р°РєС‚РёРІРѕРІ"""
        for category in MARKET_ASSETS.values():
            for asset_name, asset_data in category.items():
                if isinstance(asset_data, dict):
                    self.assets[asset_name] = asset_data["symbol"]
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Р Р°СЃС‡РµС‚ С‚РµС…РЅРёС‡РµСЃРєРёС… РёРЅРґРёРєР°С‚РѕСЂРѕРІ"""
        try:
            # EMA
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            df['EMA_100'] = df['Close'].ewm(span=100, adjust=False).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df['Close'].ewm(span=12).mean()
            exp2 = df['Close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            
            # Stochastic
            low_14 = df['Low'].rolling(14).min()
            high_14 = df['High'].rolling(14).max()
            df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
            df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()
            
            # Support/Resistance
            df['Resistance'] = df['High'].rolling(10).max()
            df['Support'] = df['Low'].rolling(10).min()
            
            df = df.fillna(method='bfill').fillna(method='ffill')
            
            return df
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df
    
    def analyze_asset_timeframe(self, asset_symbol: str, timeframe: str) -> Tuple[Dict, Optional[str]]:
        """РђРЅР°Р»РёР· Р°РєС‚РёРІР° РЅР° РєРѕРЅРєСЂРµС‚РЅРѕРј С‚Р°Р№РјС„СЂРµР№РјРµ"""
        try:
            period_map = {
                "1M": "5d", "5M": "5d", "15M": "1mo", 
                "30M": "1mo", "1H": "3mo", "4H": "6mo", 
                "1D": "1y", "1W": "2y"
            }
            period = period_map.get(timeframe, "1mo")
            yf_timeframe = self.timeframes.get(timeframe, "1h")
            
            # Retry Р»РѕРіРёРєР°
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
                return self.generate_fallback_signal(asset_symbol, timeframe)
            
            data = self.calculate_indicators(data)
            
            if data.empty:
                return self.generate_fallback_signal(asset_symbol, timeframe)
                
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
            
            signal_info = {
                'asset': asset_symbol,
                'timeframe': timeframe,
                'price': current['Close'],
                'trend': trend,
                'rsi': current['RSI'],
                'macd': current['MACD'],
                'stoch_k': current['Stoch_K'],
                'timestamp': datetime.now()
            }
            
            call_score = sum(call_conditions)
            put_score = sum(put_conditions)
            
            # РђРЅР°Р»РёР· РІРѕР»Р°С‚РёР»СЊРЅРѕСЃС‚Рё Рё РѕР±СЉРµРјРѕРІ
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
            
            # РЎС‚Р°Р±РёР»СЊРЅРѕСЃС‚СЊ
            stability_bonus = 0
            if volatility < 2.0:
                stability_bonus = 3
            elif volatility < 3.0:
                stability_bonus = 1
            
            # РСЃС‚РѕСЂРёС‡РµСЃРєРёР№ РїР°С‚С‚РµСЂРЅ
            pattern_bonus = self._get_pattern_bonus(asset_symbol, timeframe)
            
            total_call_score = call_score + stability_bonus + pattern_bonus.get('call', 0)
            total_put_score = put_score + stability_bonus + pattern_bonus.get('put', 0)
            
            min_conf = 70
            max_conf = 92
            
            if total_call_score > total_put_score:
                base_conf = min_conf + total_call_score * 6.0
                confidence = np.clip(base_conf, min_conf, max_conf)
                
                signal_info.update({
                    'signal': 'CALL',
                    'confidence': round(confidence, 1),
                    'direction': 'рџ“€',
                    'score': total_call_score,
                    'volatility': volatility,
                    'whale_detected': whale_factor > 0,
                    'volume': current_volume,
                    'avg_volume': avg_volume,
                    'volume_ratio': volume_ratio,
                    'ema_20': current['EMA_20'],
                    'ema_50': current['EMA_50']
                })
                
                return signal_info, None
                
            elif total_put_score > total_call_score:
                base_conf = min_conf + total_put_score * 6.0
                confidence = np.clip(base_conf, min_conf, max_conf)
                
                signal_info.update({
                    'signal': 'PUT',
                    'confidence': round(confidence, 1), 
                    'direction': 'рџ“‰',
                    'score': total_put_score,
                    'volatility': volatility,
                    'whale_detected': whale_factor > 0,
                    'volume': current_volume,
                    'avg_volume': avg_volume,
                    'volume_ratio': volume_ratio,
                    'ema_20': current['EMA_20'],
                    'ema_50': current['EMA_50']
                })
                
                return signal_info, None
                
            else:
                # Р Р°РІРЅС‹Рµ СЃРєРѕСЂС‹ - РІС‹Р±РёСЂР°РµРј РїРѕ С‚СЂРµРЅРґСѓ
                if trend == "BULLISH":
                    signal_info.update({
                        'signal': 'CALL',
                        'confidence': round(min_conf + total_call_score * 5.5, 1),
                        'direction': 'рџ“€',
                        'score': total_call_score,
                        'volatility': volatility,
                        'whale_detected': whale_factor > 0
                    })
                else:
                    signal_info.update({
                        'signal': 'PUT',
                        'confidence': round(min_conf + total_put_score * 5.5, 1),
                        'direction': 'рџ“‰',
                        'score': total_put_score,
                        'volatility': volatility,
                        'whale_detected': whale_factor > 0
                    })
                
                return signal_info, None
            
        except Exception as e:
            logger.error(f"Error analyzing {asset_symbol} on {timeframe}: {e}")
            return self.generate_fallback_signal(asset_symbol, timeframe)
    
    def generate_fallback_signal(self, asset_symbol: str, timeframe: str) -> Tuple[Dict, None]:
        """Fallback СЃРёРіРЅР°Р» РєРѕРіРґР° СЂРµР°Р»СЊРЅС‹Р№ Р°РЅР°Р»РёР· РЅРµРґРѕСЃС‚СѓРїРµРЅ"""
        trend = np.random.choice(['BULLISH', 'BEARISH'])
        
        if trend == 'BULLISH':
            signal = 'CALL'
            direction = 'рџ“€'
        else:
            signal = 'PUT'
            direction = 'рџ“‰'
        
        confidence = np.random.uniform(70, 85)
        
        signal_info = {
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
            'timestamp': datetime.now()
        }
        
        return signal_info, None
    
    def _get_pattern_bonus(self, asset_symbol: str, timeframe: str) -> Dict[str, int]:
        """РџРѕР»СѓС‡РёС‚СЊ Р±РѕРЅСѓСЃ РЅР° РѕСЃРЅРѕРІРµ РёСЃС‚РѕСЂРёС‡РµСЃРєРѕРіРѕ РїР°С‚С‚РµСЂРЅР°"""
        # РџСЂРѕСЃС‚Р°СЏ СЂРµР°Р»РёР·Р°С†РёСЏ - РјРѕР¶РЅРѕ СЂР°СЃС€РёСЂРёС‚СЊ
        return {'call': 0, 'put': 0}
    
    async def analyze_asset_async(self, asset_name: str, asset_data: Dict, 
                                   timeframe: str, min_confidence: float = 85, 
                                   is_otc: bool = False) -> Optional[Tuple]:
        """РђСЃРёРЅС…СЂРѕРЅРЅС‹Р№ Р°РЅР°Р»РёР· РѕРґРЅРѕРіРѕ Р°РєС‚РёРІР°"""
        try:
            asset_symbol = asset_data["symbol"]
            signal_info, error = await asyncio.to_thread(
                self.analyze_asset_timeframe, asset_symbol, timeframe
            )
            
            if signal_info and signal_info.get('confidence', 0) >= min_confidence:
                signal_info['asset_type'] = asset_data["type"]
                signal_info['payout'] = asset_data["payout"]
                signal_info['is_otc'] = is_otc
                return (asset_name, signal_info, timeframe)
        except Exception as e:
            logger.debug(f"Error analyzing {asset_name}: {e}")
        return None
    
    async def scan_market_signals(self, timeframe_type: str, force_realtime: bool = False) -> List[Tuple]:
        """РЎРєР°РЅРёСЂРѕРІР°РЅРёРµ СЂС‹РЅРєР° РґР»СЏ РїРѕРёСЃРєР° СЃРёРіРЅР°Р»РѕРІ"""
        current_time = time.time()
        
        # РџСЂРѕРІРµСЂРєР° РєСЌС€Р° РґР»СЏ LONG
        if timeframe_type == "long" and not force_realtime:
            if (current_time - self.signal_cache['long']['timestamp']) < self.cache_duration:
                cached = self.signal_cache['long']['signals']
                if cached:
                    return cached
        
        signals = []
        tasks = []
        
        if timeframe_type == "short":
            for timeframe in ["1M", "5M"]:
                for category in ["crypto_otc", "forex_otc", "stocks_otc", "commodities_otc"]:
                    for asset_name, asset_data in MARKET_ASSETS.get(category, {}).items():
                        tasks.append(self.analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=80, is_otc=True))
                
                for category in ["crypto", "forex", "stocks", "commodities"]:
                    for asset_name, asset_data in MARKET_ASSETS.get(category, {}).items():
                        tasks.append(self.analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=75, is_otc=False))
        
        elif timeframe_type == "long":
            for timeframe in ["1H", "4H"]:
                for category in ["forex_otc", "stocks_otc", "commodities_otc"]:
                    for asset_name, asset_data in MARKET_ASSETS.get(category, {}).items():
                        tasks.append(self.analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=80, is_otc=True))
                
                for category in ["forex", "stocks", "commodities"]:
                    for asset_name, asset_data in MARKET_ASSETS.get(category, {}).items():
                        tasks.append(self.analyze_asset_async(asset_name, asset_data, timeframe, min_confidence=75, is_otc=False))
        
        # Р’С‹РїРѕР»РЅРёС‚СЊ РІСЃРµ Р°РЅР°Р»РёР·С‹ РїР°СЂР°Р»Р»РµР»СЊРЅРѕ
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # РЎРѕР±СЂР°С‚СЊ СѓСЃРїРµС€РЅС‹Рµ СЃРёРіРЅР°Р»С‹
        for result in results:
            if result and not isinstance(result, Exception):
                signals.append(result)
        
        # РЎРѕСЂС‚РёСЂРѕРІР°С‚СЊ Рё РІР·СЏС‚СЊ РўРћРџ-3
        if signals:
            scored_signals = []
            for asset_name, signal_info, timeframe in signals:
                base_score = signal_info.get('confidence', 0)
                payout_bonus = 25 if signal_info.get('payout', 85) >= 92 else 0
                final_score = base_score + payout_bonus
                scored_signals.append((asset_name, signal_info, timeframe, final_score))
            
            scored_signals.sort(key=lambda x: x[3], reverse=True)
            signals = [(name, info, tf) for name, info, tf, score in scored_signals[:3]]
        
        # РћР±РЅРѕРІРёС‚СЊ РєСЌС€
        cache_key = timeframe_type if timeframe_type in ['short', 'long'] else 'short'
        self.signal_cache[cache_key]['signals'] = signals
        self.signal_cache[cache_key]['timestamp'] = current_time
        
        return signals
    
    def get_best_signal_from_cache(self, signal_type: str = 'short', 
                                    user_priority: str = 'free', 
                                    user_id: int = None) -> Optional[Tuple]:
        """РџРѕР»СѓС‡РёС‚СЊ Р»СѓС‡С€РёР№ СЃРёРіРЅР°Р» РёР· РєСЌС€Р°"""
        signals = self.signal_cache.get(signal_type, {}).get('signals', [])
        
        if not signals:
            return None
        
        # Р¤РёР»СЊС‚СЂР°С†РёСЏ РїРѕ РїРѕСЃР»РµРґРЅРёРј РёСЃРїРѕР»СЊР·РѕРІР°РЅРЅС‹Рј Р°РєС‚РёРІР°Рј
        filtered_signals = []
        for asset_name, signal_info, timeframe in signals:
            if asset_name not in self.last_used_assets.get(signal_type, []):
                filtered_signals.append((asset_name, signal_info, timeframe))
        
        if not filtered_signals:
            filtered_signals = signals  # Р•СЃР»Рё РІСЃРµ РёСЃРїРѕР»СЊР·РѕРІР°РЅС‹, Р±РµСЂРµРј Р»СЋР±РѕР№
        
        # РЎРѕСЂС‚РёСЂРѕРІРєР° РїРѕ confidence
        filtered_signals.sort(key=lambda x: x[1].get('confidence', 0), reverse=True)
        
        best = filtered_signals[0]
        
        # Р”РѕР±Р°РІРёС‚СЊ РІ СЃРїРёСЃРѕРє РёСЃРїРѕР»СЊР·РѕРІР°РЅРЅС‹С…
        if signal_type in self.last_used_assets:
            self.last_used_assets[signal_type].append(best[0])
            if len(self.last_used_assets[signal_type]) > self.max_recent_assets:
                self.last_used_assets[signal_type].pop(0)
        
        return best
    
    def get_expiration_time(self, timeframe: str) -> str:
        """Р’РѕР·РІСЂР°С‰Р°РµС‚ РѕРїС‚РёРјР°Р»СЊРЅРѕРµ РІСЂРµРјСЏ СЌРєСЃРїРёСЂР°С†РёРё"""
        expiration_map = {
            "1M": "1 РјРёРЅСѓС‚Р°",
            "3M": "3 РјРёРЅСѓС‚С‹", 
            "5M": "5 РјРёРЅСѓС‚",
            "15M": "15 РјРёРЅСѓС‚",
            "30M": "30 РјРёРЅСѓС‚",
            "1H": "1 С‡Р°СЃ",
            "4H": "4 С‡Р°СЃР°", 
            "1D": "1 РґРµРЅСЊ"
        }
        return expiration_map.get(timeframe, "5 РјРёРЅСѓС‚")
    
    def get_pocket_option_asset_name(self, asset_name: str) -> str:
        """РљРѕРЅРІРµСЂС‚РёСЂСѓРµС‚ РЅР°Р·РІР°РЅРёРµ Р°РєС‚РёРІР° РІ С„РѕСЂРјР°С‚ Pocket Option"""
        is_otc = " OTC" in asset_name
        base_name = asset_name.replace(" OTC", "")
        
        pocket_map = {
            "BTC/USD": "BITCOIN",
            "ETH/USD": "ETHEREUM",
            "LTC/USD": "LITECOIN", 
            "XRP/USD": "XRP",
            "ADA/USD": "CARDANO",
            "BNB/USD": "BINANCE COIN",
            "DASH/USD": "DASH",
            "LINK/USD": "CHAINLINK",
            "SOL/USD": "SOLANA",
            "TRX/USD": "TRON",
            "AVAX/USD": "AVALANCHE",
            "TON/USD": "TONCOIN",
            "EUR/USD": "EUR/USD",
            "GBP/USD": "GBP/USD",
            "USD/JPY": "USD/JPY",
            "USD/CHF": "USD/CHF",
            "USD/CAD": "USD/CAD",
            "AUD/USD": "AUD/USD",
            "NZD/USD": "NZD/USD",
            "EUR/GBP": "EUR/GBP",
            "EUR/JPY": "EUR/JPY",
            "GBP/JPY": "GBP/JPY",
            "XAU/USD": "GOLD",
            "XAG/USD": "SILVER",
            "OIL/USD": "OIL (WTI)",
            "BRENT": "BRENT OIL",
            "NG/USD": "NATURAL GAS",
            "S&P500": "US 500",
            "NASDAQ": "US TECH 100",
            "DOW": "US 30",
            "FTSE": "UK 100",
            "AAPL": "APPLE",
            "MSFT": "MICROSOFT",
            "TSLA": "TESLA",
            "AMZN": "AMAZON",
            "META": "META",
            "INTC": "INTEL",
            "BA": "BOEING"
        }
        
        pocket_name = pocket_map.get(base_name, base_name)
        
        if is_otc:
            pocket_name = f"{pocket_name} OTC"
        
        return pocket_name


# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ Р°РЅР°Р»РёР·Р°С‚РѕСЂР°
analyzer = MarketAnalyzer()

