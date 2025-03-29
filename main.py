import asyncio
import uuid
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from src.config.settings import TELEGRAM_BOT_TOKEN, setup_logging
from src.handlers.command_handlers import start, check_progress, mini_lesson
from src.handlers.callback_handlers import handle_callback
from src.database.connection import init_db
from src.utils.openai_tools import OpenAITools

logger = setup_logging()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages from users in the Telegram chat."""
    if not update.message or not update.message.text or update.message.text.startswith('/'):  
        return
        
    openai_tools = OpenAITools()
    response = openai_tools.chat(str(update.effective_user.id), update.message.text)
    await update.message.reply_text(response, parse_mode='Markdown')

async def main():
    """Start the bot."""
    try:
        # Initialize database
        init_db()
        
        # Create the Application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("progress", check_progress))
        application.add_handler(CommandHandler("mini", mini_lesson))
        application.add_handler(CallbackQueryHandler(handle_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # ✅ Manually start bot without closing the event loop
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        logger.info("Bot is running...")

        # Keep bot running without interfering with Railway’s event loop
        await asyncio.Event().wait()  # Keeps the event loop alive

    except Exception as e:
        logger.exception("Unhandled exception in main bot loop")

if __name__ == '__main__':
    try:
        asyncio.run(main())  # Runs without messing with the event loop
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
