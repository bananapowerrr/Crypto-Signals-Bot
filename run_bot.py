#!/usr/bin/env python3
"""
Точка входа для запуска Crypto Signals Bot
==========================================

Для запуска бота:
    python run_bot.py

Перед запуском убедитесь, что в файле .env указаны:
    BOT_TOKEN - токен Telegram бота
    ADMIN_USER_ID - ID администратора
"""
import sys
import os

# Настройка UTF-8 для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_dependencies():
    """Проверка установленных зависимостей"""
    missing = []
    
    try:
        import telegram
    except ImportError:
        missing.append("python-telegram-bot")
    
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    try:
        import yfinance
    except ImportError:
        missing.append("yfinance")
    
    try:
        from dotenv import load_dotenv
    except ImportError:
        missing.append("python-dotenv")
    
    if missing:
        print("❌ Отсутствуют необходимые зависимости:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n📦 Установите их командой:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True


def check_env():
    """Проверка переменных окружения"""
    from dotenv import load_dotenv
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN", "")
    admin_id = os.getenv("ADMIN_USER_ID", "0")
    
    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN не установлен!")
        print("   Создайте файл .env и добавьте:")
        print("   BOT_TOKEN=your_telegram_bot_token")
        return False
    
    if admin_id == "0":
        print("⚠️ ADMIN_USER_ID не установлен. Админ-команды не будут работать.")
        print("   Добавьте в .env файл:")
        print("   ADMIN_USER_ID=your_telegram_id")
    
    return True


def main():
    """Главная функция запуска"""
    print("=" * 50)
    print("🤖 Crypto Signals Bot v2.0")
    print("=" * 50)
    print()
    
    # Проверка зависимостей
    print("🔍 Проверка зависимостей...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ Все зависимости установлены")
    print()
    
    # Проверка окружения
    print("🔍 Проверка конфигурации...")
    if not check_env():
        sys.exit(1)
    print("✅ Конфигурация в порядке")
    print()
    
    # Запуск бота
    print("🚀 Запуск бота...")
    print("-" * 50)
    
    try:
        from bot.bot import main as run_bot
        run_bot()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
