"""
Crypto Signals Bot - Main Entry Point
Modular structure with separated concerns
"""
import os
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import handlers
from bot.core import bot
from bot.handlers.commands import (
    start_command, short_command, long_command, my_stats_command,
    set_bank_command, set_strategy_command, help_command,
    report_win_command, report_loss_command, COMMANDS
)
from bot.handlers.commands import photo_handler
from bot.handlers.admin import (
    admin_panel_command, admin_stats_command, 
    admin_add_sub_command, admin_user_info, ADMIN_COMMANDS
)

# Import strategies
from strategies.all import calculate_stake, get_strategy
from strategies.manager import analyze_market

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))


async def error_handler(update, context):
    """Error handler"""
    logger.error(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже."
        )


def main():
    """Main function to run the bot"""
    logger.info("🚀 Starting Crypto Signals Bot...")
    
    # Initialize application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    for cmd, desc in COMMANDS:
        handler = CommandHandler(cmd, globals()[f"{cmd}_command"])
        app.add_handler(handler)

    # Photo (screenshot) handler
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    
    # Add admin command handlers
    for cmd, desc in ADMIN_COMMANDS:
        handler = CommandHandler(cmd, globals()[f"{cmd}_command"])
        app.add_handler(handler)
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    # Set bot commands
    async def post_init(app):
        all_commands = COMMANDS + ADMIN_COMMANDS
        await app.bot.set_my_commands(all_commands)
    
    app.post_init = post_init
    
    logger.info("✅ Bot initialized successfully")
    logger.info("Run /admin_panel for admin features")
    
    # Start polling
    app.run_polling(allowed_updates=['message', 'callback_query'])


if __name__ == "__main__":
    main()
