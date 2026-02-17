"""Лёгкая модель — простые промпты и ответы для общения с пользователем.
Использует OpenRouter клиент для генерации ответов (или локальные правила).
"""
from typing import Dict, Any
import logging
from bot.integrations.openrouter_client import call_openrouter

logger = logging.getLogger(__name__)


DEFAULT_PROMPT_BANK_ADVICE = (
    "Ты помощник по банк-менеджменту. Дай краткий, понятный совет по управлению капиталом и рекомендованную ставку."
)


def advise_bank_management(balance: float, risk_pct: float = 2.5) -> Dict[str, Any]:
    prompt = f"{DEFAULT_PROMPT_BANK_ADVICE}\nБаланс: {balance} RUB. Риск: {risk_pct}%"
    res = call_openrouter(prompt, model='gpt-4o-mini', max_tokens=200)
    return {'advice': res.get('text', ''), 'raw': res.get('raw')}
