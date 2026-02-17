"""Каркас тяжёлой модели — анализ скриншотов и сохранение результатов в БД.
Здесь находятся обёртки для запуска внешних/локальных CV/ML моделей.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def analyze_screenshot(image_bytes: bytes) -> Dict[str, Any]:
    """Анализ скриншота (placeholder).
    Возвращает структурированные данные, например: {'balance': 1234.5, 'markers': [...]}.
    Реальная реализация будет использовать CV модель или внешний inference.
    """
    # TODO: интегрировать OCR / CV модель
    logger.debug('analyze_screenshot called (placeholder)')
    return {
        'balance': None,
        'detected_text': None,
        'notes': 'Placeholder analysis — модель не настроена.'
    }
