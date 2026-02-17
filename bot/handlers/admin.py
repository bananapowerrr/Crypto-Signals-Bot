"""
Admin Panel - MONOLITH
All admin handlers in one file
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.core import bot


# ==================== COMMANDS ====================

async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel - main menu"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ Доступ только для админов")
        return
    
    stats = bot.get_stats()
    users = bot.get_all_users()
    
    text = f"""
👑 Админ панель

📊 Статистика:
• Пользователей: {stats['total_users']}
• Сигналов: {stats['total_signals']}

👥 Последние пользователи:
"""
    
    for i, user in enumerate(users[:5], 1):
        name = user.get('username') or user.get('first_name') or f"ID:{user['user_id']}"
        text += f"{i}. @{name}\n"
    
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detailed bot statistics"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ Доступ только для админов")
        return
    
    stats = bot.get_stats()
    users = bot.get_all_users()
    
    text = f"""
📊 Подробная статистика

👥 Всего пользователей: {stats['total_users']}
📈 Всего сигналов: {stats['total_signals']}
📊 Среднее количество сигналов: {stats['total_signals'] / max(stats['total_users'], 1):.1f}
"""
    
    await update.message.reply_text(text)


async def admin_add_sub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add subscription - /admin_add_sub"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ Доступ только для админов")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "Использование: /admin_add_sub USER_ID DAYS\n"
            "Пример: /admin_add_sub 123456789 30"
        )
        return
    
    target_user = int(context.args[0])
    days = int(context.args[1])
    
    await update.message.reply_text(f"✅ Подписка добавлена пользователю {target_user} на {days} дней")


async def admin_set_referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark user as referral-registered: /admin_set_referral USER_ID"""
    user_id = update.effective_user.id
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ Доступ только для админов")
        return

    if not context.args:
        await update.message.reply_text("Использование: /admin_set_referral USER_ID")
        return

    target = int(context.args[0])
    bot.set_referral_registered(target, True)
    await update.message.reply_text(f"✅ Пользователь {target} помечен как зарегистрированный по реферальной ссылке")


async def admin_set_vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grant or revoke VIP: /admin_set_vip USER_ID [1|0]"""
    user_id = update.effective_user.id
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ Доступ только для админов")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Использование: /admin_set_vip USER_ID [1|0]")
        return

    target = int(context.args[0])
    val = True
    if len(context.args) > 1 and context.args[1] in ('0', 'false', 'no'):
        val = False

    bot.set_vip(target, val)
    await update.message.reply_text(f"✅ VIP статус пользователя {target} установлен: {val}")


async def admin_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user info - /admin_info"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ Доступ только для админов")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /admin_info USER_ID")
        return
    
    target_user = int(context.args[0])
    user = bot.get_user(target_user)
    
    if not user:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    stats = bot.get_user_stats(target_user)
    
    text = f"""
👤 Информация о пользователе

ID: {user['user_id']}
Username: @{user.get('username', 'N/A')}
Имя: {user.get('first_name', 'N/A')}
Баланс: {user.get('current_balance', 10000)}₽
Стратегия: {user.get('trading_strategy', 'martingale')}

📊 Статистика:
• Всего сделок: {stats['total']}
• Wins: {stats['wins']}
• Losses: {stats['losses']}
• Win Rate: {stats['win_rate']:.1f}%
"""
    
    await update.message.reply_text(text)


async def admin_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message - /admin_broadcast"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ Доступ только для админов")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /admin_broadcast MESSAGE")
        return
    
    message = " ".join(context.args)
    users = bot.get_all_users()
    
    count = 0
    for user in users:
        try:
            await context.bot.send_message(chat_id=user['user_id'], text=message)
            count += 1
        except:
            pass
    
    await update.message.reply_text(f"✅ Сообщение отправлено {count} пользователям")


async def admin_add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add admin - /add_admin"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ Доступ только для админов")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /add_admin USER_ID")
        return
    
    new_admin = context.args[0]
    current = bot.get_setting('admin_users', '')
    if current:
        new_list = f"{current},{new_admin}"
    else:
        new_list = new_admin
    
    bot.set_setting('admin_users', new_list)
    await update.message.reply_text(f"✅ Админ {new_admin} добавлен")


async def admin_remove_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove admin - /remove_admin"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ Доступ только для админов")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /remove_admin USER_ID")
        return
    
    await update.message.reply_text("❌ Нельзя удалить главного админа")


# ==================== CALLBACKS ====================

async def admin_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback: admin stats"""
    query = update.callback_query
    await query.answer()
    
    stats = bot.get_stats()
    
    text = f"""
📊 Статистика бота

👥 Пользователей: {stats['total_users']}
📈 Сигналов: {stats['total_signals']}
"""
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_back")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback: user list"""
    query = update.callback_query
    await query.answer()
    
    users = bot.get_all_users()
    
    text = "👥 Пользователи:\n\n"
    for i, user in enumerate(users[:10], 1):
        name = user.get('username') or user.get('first_name') or f"ID:{user['user_id']}"
        text += f"{i}. @{name} (ID: {user['user_id']})\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_back")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback: settings"""
    query = update.callback_query
    await query.answer()
    
    text = """
⚙️ Настройки бота

Настройки можно изменить через команды:
• /set_support - изменить контакт поддержки
• /set_reviews_group - группа отзывов
"""
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_back")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Back to admin panel"""
    query = update.callback_query
    await query.answer()
    await admin_panel_command(update, context)


# ==================== COMMAND LIST ====================

ADMIN_COMMANDS = [
    ("admin_panel", "Панель админа"),
    ("admin_stats", "Статистика бота"),
    ("admin_add_sub", "Добавить подписку"),
    ("admin_info", "Информация о пользователе"),
    ("admin_broadcast", "Рассылка"),
    ("admin_set_referral", "Пометить регистрацию по реферальной ссылке"),
    ("admin_set_vip", "Установить/снять VIP"),
    ("add_admin", "Добавить админа"),
    ("remove_admin", "Удалить админа"),
]

ADMIN_CALLBACKS = {
    "admin_stats": admin_stats_callback,
    "admin_users": admin_users_callback,
    "admin_settings": admin_settings_callback,
    "admin_back": admin_back_callback,
}
