"""Главный модуль Telegram бота"""
import logging
import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Optional

# Добавляем родительскую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

from bot.config import (
    BOT_TOKEN, ADMIN_USER_ID, SUPPORT_CONTACT,
    POCKET_OPTION_REF_LINK, PROMO_CODE, TRANSLATIONS
)
from bot.database import db
from bot.analyzer import analyzer

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class CryptoSignalsBot:
    """Главный класс Telegram бота"""
    
    def __init__(self):
        self.application = None
        self.admin_user_id = ADMIN_USER_ID
    
    # ========== УТИЛИТЫ ==========
    
    def t(self, user_id: int, key: str) -> str:
        """Получить перевод для пользователя"""
        lang = db.get_user_language(user_id)
        translations = TRANSLATIONS.get(lang, TRANSLATIONS['ru'])
        return translations.get(key, key)
    
    def get_referral_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура с реферальной ссылкой"""
        keyboard = [
            [InlineKeyboardButton("📝 Зарегистрироваться на Pocket Option", url=POCKET_OPTION_REF_LINK)],
            [InlineKeyboardButton("📋 Мой промокод", callback_data="my_referral_code")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # ========== КЛАВИАТУРЫ ==========
    
    def get_main_keyboard(self, user_id: int) -> ReplyKeyboardMarkup:
        """Главная клавиатура - все сигналы доступны бесплатно"""
        keyboard = [
            [KeyboardButton(f"⚡️ {self.t(user_id, 'short_signal')}")],
            [KeyboardButton(f"🔵 {self.t(user_id, 'long_signal')}")],
            [KeyboardButton(f"📊 {self.t(user_id, 'my_stats')}")],
            [KeyboardButton(f"⚙️ {self.t(user_id, 'settings')}"), KeyboardButton(f"💰 Рефералка")],
            [KeyboardButton(f"❓ {self.t(user_id, 'help')}")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_settings_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        """Клавиатура настроек"""
        lang = db.get_user_language(user_id)
        currency = db.get_currency(user_id)
        
        keyboard = [
            [InlineKeyboardButton(f"🌍 Язык: {lang.upper()}", callback_data="settings_language")],
            [InlineKeyboardButton(f"💱 Валюта: {currency}", callback_data="settings_currency")],
            [InlineKeyboardButton(f"📊 Моя статистика", callback_data="my_stats")],
            [InlineKeyboardButton(f"◀️ {self.t(user_id, 'back')}", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_language_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура выбора языка"""
        keyboard = [
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
             InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
             InlineKeyboardButton("🇧🇷 Português", callback_data="lang_pt")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_currency_keyboard(self) -> InlineKeyboardMarkup:
        """Клавиатура выбора валюты"""
        keyboard = [
            [InlineKeyboardButton("🇷🇺 Рубли (₽)", callback_data="curr_RUB"),
             InlineKeyboardButton("🇺🇸 Доллары ($)", callback_data="curr_USD")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # ========== ОБРАБОТЧИКИ КОМАНД ==========
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user
        user_id = user.id
        
        # Проверка бана
        if db.is_banned(user_id):
            await update.message.reply_text("🚫 Вы заблокированы.")
            return
        
        # Добавление пользователя
        db.add_user(user_id, user.username, user.first_name)
        
        # Приветственное сообщение с реферальной ссылкой
        welcome_text = f"""👋 Добро пожаловать, {user.first_name}!

🤖 **Crypto Signals Bot** - профессиональные торговые сигналы

📊 **Наши преимущества:**
• Точность сигналов до 92%
• SHORT сигналы (1-5 минут)
• LONG сигналы (1-4 часа)
• Мартингейл стратегия
• Мультиязычность

🎁 **Бот полностью бесплатный!**

💰 **Зарабатывайте с нами:**
Используйте реферальную ссылку для регистрации на Pocket Option и получайте бонусы!
"""
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=self.get_referral_keyboard()
        )
        
        # Отправляем главное меню
        await update.message.reply_text(
            "🏠 Главное меню:",
            reply_markup=self.get_main_keyboard(user_id)
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        user_id = update.effective_user.id
        
        help_text = f"""❓ **Справка по боту**

**⚡️ SHORT сигналы:**
• Таймфрейм: 1-5 минут
• Стратегия: Мартингейл x3
• Доходность: до 92%

**🔵 LONG сигналы:**
• Таймфрейм: 1-4 часа
• Стратегия: Процентная ставка 2.5%
• Доходность: до 92%

🎁 **Бот полностью бесплатный!**

💰 **Зарабатывайте с нами:**
Зарегистрируйтесь на Pocket Option по нашей ссылке и получайте бонусы!

**💰 Регистрация на Pocket Option:**
[Зарегистрироваться]({POCKET_OPTION_REF_LINK})
Промокод: `{PROMO_CODE}`

**📞 Поддержка:** {SUPPORT_CONTACT}"""
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            disable_web_page_preview=True,
            reply_markup=self.get_main_keyboard(user_id)
        )
    
    async def cmd_short(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получить SHORT сигнал - БЕСПЛАТНО"""
        user_id = update.effective_user.id
        
        if db.is_banned(user_id):
            return
        
        await update.message.reply_text("🔍 Анализирую рынок...")
        
        # Получение сигнала
        try:
            signals = await analyzer.scan_market_signals('short')
            
            if signals:
                asset_name, signal_info, timeframe = signals[0]
                
                # Сохранение сигнала
                signal_id = db.save_signal_to_history(
                    user_id, asset_name, timeframe,
                    signal_info['signal'], signal_info['confidence'],
                    signal_info.get('price', 0)
                )
                
                db.increment_signals_used(user_id)
                
                # Формирование сообщения
                signal_emoji = "🟢" if signal_info['signal'] == 'CALL' else "🔴"
                pocket_asset = analyzer.get_pocket_option_asset_name(asset_name)
                
                signal_text = f"""{signal_emoji} **SHORT СИГНАЛ**

📊 **Актив:** {pocket_asset}
📈 **Направление:** {signal_info['signal']}
⏱ **Экспирация:** {analyzer.get_expiration_time(timeframe)}
💰 **Уверенность:** {signal_info['confidence']}%

{'🐋 Обнаружен крупный игрок!' if signal_info.get('whale_detected') else ''}

💰 **Регистрация:** [Pocket Option]({POCKET_OPTION_REF_LINK})"""
                
                keyboard = [[
                    InlineKeyboardButton("✅ Результат WIN", callback_data=f"result_win_{signal_id}"),
                    InlineKeyboardButton("❌ Результат LOSS", callback_data=f"result_loss_{signal_id}")
                ]]
                
                await update.message.reply_text(
                    signal_text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_text(
                    "⏳ Нет подходящих сигналов в данный момент.\n"
                    "Попробуйте через 1-2 минуты."
                )
        
        except Exception as e:
            logger.error(f"Error getting short signal: {e}")
            await update.message.reply_text("❌ Ошибка при анализе рынка. Попробуйте позже.")
    
    async def cmd_long(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получить LONG сигнал - БЕСПЛАТНО"""
        user_id = update.effective_user.id
        
        if db.is_banned(user_id):
            return
        
        await update.message.reply_text("🔍 Анализирую рынок (LONG)...")
        
        try:
            signals = await analyzer.scan_market_signals('long')
            
            if signals:
                asset_name, signal_info, timeframe = signals[0]
                
                signal_id = db.save_signal_to_history(
                    user_id, asset_name, timeframe,
                    signal_info['signal'], signal_info['confidence'],
                    signal_info.get('price', 0)
                )
                
                db.increment_signals_used(user_id)
                
                signal_emoji = "🟢" if signal_info['signal'] == 'CALL' else "🔴"
                pocket_asset = analyzer.get_pocket_option_asset_name(asset_name)
                
                signal_text = f"""{signal_emoji} **LONG СИГНАЛ**

📊 **Актив:** {pocket_asset}
📈 **Направление:** {signal_info['signal']}
⏱ **Экспирация:** {analyzer.get_expiration_time(timeframe)}
💰 **Уверенность:** {signal_info['confidence']}%

{'🐋 Обнаружен крупный игрок!' if signal_info.get('whale_detected') else ''}

💰 **Регистрация:** [Pocket Option]({POCKET_OPTION_REF_LINK})"""
                
                keyboard = [[
                    InlineKeyboardButton("✅ Результат WIN", callback_data=f"result_win_{signal_id}"),
                    InlineKeyboardButton("❌ Результат LOSS", callback_data=f"result_loss_{signal_id}")
                ]]
                
                await update.message.reply_text(
                    signal_text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_text(
                    "⏳ Нет подходящих LONG сигналов.\n"
                    "Попробуйте через 15-30 минут."
                )
        
        except Exception as e:
            logger.error(f"Error getting long signal: {e}")
            await update.message.reply_text("❌ Ошибка при анализе рынка.")
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статистика пользователя"""
        user_id = update.effective_user.id
        
        # Статистика сигналов
        short_stats = db.get_user_signal_stats(user_id, 'short')
        long_stats = db.get_user_signal_stats(user_id, 'long')
        
        # Получаем реферальный код
        referral_code = db.get_referral_code(user_id)
        
        stats_text = f"""📊 **Ваша статистика**

🎁 **Статус:** БЕСПЛАТНЫЙ

**⚡️ SHORT сигналы:**
• Всего: {short_stats['total_signals']}
• Побед: {short_stats['wins']}
• Поражений: {short_stats['losses']}
• Win Rate: {short_stats['win_rate']:.1f}%

**🔵 LONG сигналы:**
• Всего: {long_stats['total_signals']}
• Побед: {long_stats['wins']}
• Поражений: {long_stats['losses']}
• Win Rate: {long_stats['win_rate']:.1f}%

💰 **Ваш реферальный код:** `{referral_code}`
📎 **Реферальная ссылка:** {POCKET_OPTION_REF_LINK}"""
        
        await update.message.reply_text(
            stats_text, 
            parse_mode='Markdown',
            reply_markup=self.get_main_keyboard(user_id)
        )
    
    async def cmd_referral(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать реферальную ссылку"""
        user_id = update.effective_user.id
        referral_code = db.get_referral_code(user_id)
        
        referral_text = f"""💰 **Реферальная программа**

Зарегистрируйтесь на Pocket Option по вашей ссылке и получайте бонусы!

🔗 **Ваша реферальная ссылка:**
{POCKET_OPTION_REF_LINK}

🎯 **Ваш промокод:** `{PROMO_CODE}`

📊 **Ваш уникальный код:** `{referral_code}`

💡 **Как это работает:**
1. Поделитесь ссылкой с друзьями
2. Друг регистрируется по вашей ссылке
3. Вы получаете бонусы от Pocket Option

🎁 **Также вы можете использовать промокод:** `{PROMO_CODE}`"""
        
        await update.message.reply_text(
            referral_text,
            parse_mode='Markdown',
            reply_markup=self.get_main_keyboard(user_id)
        )
    
    async def cmd_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Настройки"""
        user_id = update.effective_user.id
        await update.message.reply_text(
            "⚙️ Настройки:",
            reply_markup=self.get_settings_keyboard(user_id)
        )
    
    # ========== ОБРАБОТЧИКИ CALLBACK ==========
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback запросов"""
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        await query.answer()
        
        # Выбор языка
        if data.startswith("lang_"):
            lang = data.split("_")[1]
            db.set_user_language(user_id, lang)
            await query.edit_message_text(f"✅ Язык установлен: {lang.upper()}")
        
        # Выбор валюты
        elif data.startswith("curr_"):
            currency = data.split("_")[1]
            db.set_currency(user_id, currency)
            await query.edit_message_text(f"✅ Валюта установлена: {currency}")
        
        # Настройки
        elif data == "settings_language":
            await query.edit_message_text(
                "🌍 Выберите язык:",
                reply_markup=self.get_language_keyboard()
            )
        
        elif data == "settings_currency":
            await query.edit_message_text(
                "💱 Выберите валюту:",
                reply_markup=self.get_currency_keyboard()
            )
        
        elif data == "my_stats":
            await self.cmd_stats(update, context)
        
        elif data == "back_main":
            await query.edit_message_text(
                "🏠 Главное меню",
                reply_markup=self.get_settings_keyboard(user_id)
            )
        
        # Мой реферальный код
        elif data == "my_referral_code":
            referral_code = db.get_referral_code(user_id)
            await query.edit_message_text(
                f"💰 **Ваш реферальный код:**\n\n`{referral_code}`\n\n"
                f"🔗 **Ссылка:** {POCKET_OPTION_REF_LINK}\n\n"
                f"🎯 **Промокод:** `{PROMO_CODE}`",
                parse_mode='Markdown'
            )
        
        # Результат сигнала
        elif data.startswith("result_"):
            parts = data.split("_")
            result = parts[1]  # win или loss
            signal_id = int(parts[2])
            
            # Обновление результата
            profit_loss = 100 if result == 'win' else -100  # Пример
            db.update_signal_result(signal_id, result, profit_loss)
            
            # Обновление мартингейла
            if result == 'win':
                db.update_martingale_after_win(user_id)
            else:
                db.update_martingale_after_loss(user_id)
            
            result_emoji = "✅" if result == 'win' else "❌"
            await query.edit_message_text(
                f"{result_emoji} Результат записан: {result.upper()}"
            )
    
    # ========== ОБРАБОТКА СООБЩЕНИЙ ==========
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text
        
        if db.is_banned(user_id):
            return
        
        # Навигация по клавиатуре
        if "SHORT" in text and "сигнал" in text.lower():
            await self.cmd_short(update, context)
        elif "LONG" in text and "сигнал" in text.lower():
            await self.cmd_long(update, context)
        elif "статистик" in text.lower():
            await self.cmd_stats(update, context)
        elif "реферал" in text.lower():
            await self.cmd_referral(update, context)
        elif "настройк" in text.lower():
            await self.cmd_settings(update, context)
        elif "помощь" in text.lower() or "справка" in text.lower():
            await self.cmd_help(update, context)
    
    # ========== АДМИН КОМАНДЫ ==========
    
    async def cmd_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Админ панель"""
        user_id = update.effective_user.id
        
        if not db.is_admin(user_id, self.admin_user_id):
            await update.message.reply_text("🚫 Доступ запрещен.")
            return
        
        stats = db.get_bot_stats()
        
        admin_text = f"""🔐 **Админ панель**

📊 **Статистика бота:**
• Пользователей: {stats['total_users']}
• Всего сигналов: {stats['total_signals']}

🎁 **Бот работает в бесплатном режиме**

**Команды:**
/ban <user_id> - Забанить
/unban <user_id> - Разбанить
/broadcast <message> - Рассылка"""
        
        await update.message.reply_text(admin_text, parse_mode='Markdown')
    
    async def cmd_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Забанить пользователя"""
        user_id = update.effective_user.id
        
        if not db.is_admin(user_id, self.admin_user_id):
            return
        
        try:
            target_id = int(context.args[0])
            db.ban_user(target_id, user_id)
            await update.message.reply_text(f"🚫 Пользователь {target_id} забанен.")
        except:
            await update.message.reply_text("Использование: /ban <user_id>")
    
    async def cmd_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Разбанить пользователя"""
        user_id = update.effective_user.id
        
        if not db.is_admin(user_id, self.admin_user_id):
            return
        
        try:
            target_id = int(context.args[0])
            db.unban_user(target_id, user_id)
            await update.message.reply_text(f"✅ Пользователь {target_id} разбанен.")
        except:
            await update.message.reply_text("Использование: /unban <user_id>")
    
    # ========== ЗАПУСК ==========
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("short", self.cmd_short))
        self.application.add_handler(CommandHandler("long", self.cmd_long))
        self.application.add_handler(CommandHandler("stats", self.cmd_stats))
        self.application.add_handler(CommandHandler("referral", self.cmd_referral))
        self.application.add_handler(CommandHandler("settings", self.cmd_settings))
        
        # Админ команды
        self.application.add_handler(CommandHandler("admin", self.cmd_admin))
        self.application.add_handler(CommandHandler("ban", self.cmd_ban))
        self.application.add_handler(CommandHandler("unban", self.cmd_unban))
        
        # Callback
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Сообщения
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def run(self):
        """Запуск бота"""
        if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            logger.error("❌ BOT_TOKEN не установлен в .env файле!")
            return
        
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
        
        logger.info("🤖 Бот запускается...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Точка входа"""
    bot = CryptoSignalsBot()
    bot.run()


if __name__ == "__main__":
    main()
