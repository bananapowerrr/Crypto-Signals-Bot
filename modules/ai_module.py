"""
AI Module - интеграция с OpenRouter для Long-сигналов, анализа скриншотов и диалога
"""
import os
import logging
import json
import base64
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Тяжёлая модель для анализа скриншотов и генерации Long-сигналов
HEAVY_MODEL = "google/gemini-2.0-flash-thinking-exp:free"
# Лёгкая модель для диалога и банк-менеджмента
LIGHT_MODEL = "google/gemma-3-12b-it:free"


async def call_openrouter(model: str, messages: list, max_tokens: int = 1500) -> str:
    """Базовый вызов OpenRouter API"""
    if not OPENROUTER_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://crypto-signals-bot.replit.app",
        "X-Title": "Crypto Signals Bot"
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenRouter error {response.status_code}: {response.text}")
                return None
    except Exception as e:
        logger.error(f"OpenRouter request failed: {e}")
        return None


async def generate_long_signal_ai(asset_name: str, timeframe: str, market_data: dict) -> dict:
    """
    Генерация Long-сигнала через тяжёлую AI-модель с рассуждениями.
    Возвращает сигнал с подробной аналитикой.
    """
    price = market_data.get('price', 0)
    rsi = market_data.get('rsi', 50)
    macd = market_data.get('macd', 0)
    trend = market_data.get('trend', 'NEUTRAL')
    volatility = market_data.get('volatility', 1.0)
    ema_20 = market_data.get('ema_20', price)
    ema_50 = market_data.get('ema_50', price)
    stoch_k = market_data.get('stoch_k', 50)

    prompt = f"""Ты профессиональный трейдер бинарных опционов на платформе Pocket Option.

Проанализируй актив и дай торговый сигнал:

АКТИВ: {asset_name}
ТАЙМФРЕЙМ: {timeframe}
ТЕКУЩАЯ ЦЕНА: {price:.5f}

ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ:
- RSI (14): {rsi:.1f}
- MACD: {macd:.6f}
- Stochastic K: {stoch_k:.1f}
- EMA 20: {ema_20:.5f}
- EMA 50: {ema_50:.5f}
- Тренд: {trend}
- Волатильность: {volatility:.2f}%

Дай ответ СТРОГО в формате JSON:
{{
  "signal": "CALL" или "PUT",
  "confidence": число от 70 до 92,
  "reasoning": "краткое объяснение на русском (2-3 предложения)",
  "key_factors": ["фактор 1", "фактор 2", "фактор 3"],
  "risk_level": "LOW" или "MEDIUM" или "HIGH",
  "expiration": "рекомендуемое время экспирации"
}}

Отвечай ТОЛЬКО JSON, без лишнего текста."""

    messages = [{"role": "user", "content": prompt}]
    response = await call_openrouter(HEAVY_MODEL, messages, max_tokens=500)

    if not response:
        return None

    try:
        # Извлечь JSON из ответа
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = response[start:end]
            result = json.loads(json_str)
            return result
    except Exception as e:
        logger.error(f"Failed to parse AI signal response: {e}")

    return None


async def analyze_screenshot_ai(image_bytes: bytes, user_context: dict = None) -> dict:
    """
    Анализ скриншота торгового терминала через тяжёлую AI-модель.
    Извлекает баланс, активные позиции, P&L.
    """
    if not OPENROUTER_API_KEY:
        return {"error": "AI не настроен"}

    # Конвертировать изображение в base64
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

    prompt = """Ты анализируешь скриншот торгового терминала Pocket Option.

Извлеки следующую информацию и верни СТРОГО в формате JSON:
{
  "balance": число или null (текущий баланс в USD/RUB),
  "currency": "USD" или "RUB" или null,
  "active_trades": число или null (количество активных сделок),
  "profit_loss": число или null (текущий P&L),
  "asset": "название актива" или null,
  "direction": "CALL" или "PUT" или null,
  "expiry": "время экспирации" или null,
  "stake": число или null (размер ставки),
  "is_demo": true или false (демо или реальный счёт),
  "analysis": "краткий анализ ситуации на русском (1-2 предложения)"
}

Если информация не видна на скриншоте - ставь null.
Отвечай ТОЛЬКО JSON."""

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}"
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]

    # Используем модель с поддержкой vision
    vision_model = "google/gemini-2.0-flash-exp:free"
    response = await call_openrouter(vision_model, messages, max_tokens=600)

    if not response:
        return {"error": "Не удалось проанализировать скриншот"}

    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = response[start:end]
            result = json.loads(json_str)
            return result
    except Exception as e:
        logger.error(f"Failed to parse screenshot analysis: {e}")

    return {"error": "Ошибка парсинга ответа AI", "raw": response[:200]}


async def chat_with_ai(user_message: str, user_data: dict, conversation_history: list = None) -> str:
    """
    Лёгкая AI-модель для диалога с пользователем.
    Консультирует по банк-менеджменту, отвечает на вопросы.
    """
    if not OPENROUTER_API_KEY:
        return "AI-консультант временно недоступен. Обратитесь в поддержку."

    # Формируем системный промпт с данными пользователя
    balance = user_data.get('current_balance', 0)
    initial_balance = user_data.get('initial_balance', 0)
    win_rate = user_data.get('win_rate', 0)
    total_signals = user_data.get('total_signals', 0)
    strategy = user_data.get('trading_strategy', 'не выбрана')

    profit = balance - initial_balance if initial_balance else 0
    profit_pct = (profit / initial_balance * 100) if initial_balance > 0 else 0

    system_prompt = f"""Ты AI-консультант торгового бота для бинарных опционов Pocket Option.
Ты помогаешь пользователям с управлением капиталом и торговыми стратегиями.

ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:
- Текущий баланс: {balance:.2f} ₽
- Начальный баланс: {initial_balance:.2f} ₽
- Прибыль/убыток: {profit:+.2f} ₽ ({profit_pct:+.1f}%)
- Win Rate: {win_rate:.1f}%
- Всего сделок: {total_signals}
- Стратегия: {strategy}

ПРАВИЛА:
1. Отвечай кратко и по делу (максимум 3-4 предложения)
2. Давай конкретные советы по управлению капиталом
3. Используй данные пользователя для персонализации
4. Предупреждай о рисках при агрессивных стратегиях
5. Отвечай на русском языке
6. Не гарантируй прибыль - это рискованная торговля
7. Если вопрос не о торговле - вежливо перенаправь"""

    messages = [{"role": "system", "content": system_prompt}]

    # Добавить историю диалога (последние 5 сообщений)
    if conversation_history:
        for msg in conversation_history[-5:]:
            messages.append(msg)

    messages.append({"role": "user", "content": user_message})

    response = await call_openrouter(LIGHT_MODEL, messages, max_tokens=300)

    if not response:
        return "Не удалось получить ответ. Попробуйте позже."

    return response


async def get_bankroll_advice_ai(user_data: dict) -> str:
    """
    Получить AI-совет по управлению банком на основе данных пользователя.
    """
    balance = user_data.get('current_balance', 0)
    initial_balance = user_data.get('initial_balance', 0)
    win_rate = user_data.get('win_rate', 0)
    total_signals = user_data.get('total_signals', 0)
    consecutive_losses = user_data.get('consecutive_losses', 0)

    if not OPENROUTER_API_KEY or balance <= 0:
        # Fallback без AI
        if win_rate >= 60:
            stake_pct = 2.5
            advice = "Хороший win rate! Можно использовать 2.5% от банка."
        elif win_rate >= 50:
            stake_pct = 2.0
            advice = "Умеренный win rate. Рекомендуется 2% от банка."
        else:
            stake_pct = 1.5
            advice = "Низкий win rate. Используйте консервативные 1.5% от банка."

        stake = balance * stake_pct / 100
        return f"💡 {advice}\n💰 Рекомендуемая ставка: {stake:.0f} ₽ ({stake_pct}%)"

    prompt = f"""Дай краткий совет по управлению банком для трейдера бинарных опционов.

Данные:
- Баланс: {balance:.0f} ₽ (начальный: {initial_balance:.0f} ₽)
- Win Rate: {win_rate:.1f}% ({total_signals} сделок)
- Подряд проигрышей: {consecutive_losses}

Дай совет в 2-3 предложения: какой % от банка ставить и почему.
Будь конкретным - назови точный процент и сумму ставки."""

    messages = [{"role": "user", "content": prompt}]
    response = await call_openrouter(LIGHT_MODEL, messages, max_tokens=200)

    return response or "Рекомендуется ставить 2% от банка для безопасной торговли."
