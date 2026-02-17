"""Simple OpenRouter / OpenAI client wrapper (placeholder)
Provides function to call free models via OpenRouter/OpenAI.
"""
import os
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

OPENROUTER_API = os.getenv('OPENROUTER_API_URL', 'https://api.openrouter.ai')
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')


def call_openrouter(prompt: str, model: str = 'gpt-4o-mini', max_tokens: int = 512) -> Dict[str, Any]:
    """Call OpenRouter/OpenAI-compatible API. Returns parsed JSON with 'text'.
    This is a simple synchronous helper — replace with async if needed.
    """
    if not OPENROUTER_KEY:
        logger.warning('OPENROUTER_API_KEY not set; returning placeholder response')
        return {'text': 'Placeholder response: OpenRouter API key not configured.'}

    headers = {
        'Authorization': f'Bearer {OPENROUTER_KEY}',
        'Content-Type': 'application/json'
    }

    body = {
        'model': model,
        'prompt': prompt,
        'max_tokens': max_tokens
    }

    try:
        resp = httpx.post(f"{OPENROUTER_API}/v1/chat/completions", json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Try typical response shapes
        if 'choices' in data and len(data['choices']) > 0:
            text = data['choices'][0].get('message', {}).get('content') or data['choices'][0].get('text')
            return {'text': text, 'raw': data}
        return {'text': str(data), 'raw': data}
    except Exception as e:
        logger.error(f'OpenRouter call failed: {e}')
        return {'text': f'Error: {e}'}
