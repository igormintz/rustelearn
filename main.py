import asyncio
import uuid
from telegram import Update, Bot
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
from src.database.connection import init_db, get_db_session
from src.utils.openai_tools import OpenAITools
import schedule
import time
from datetime import datetime
from src.database.models import User

logger = setup_logging()
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages from users in the Telegram chat."""
    if not update.message or not update.message.text or update.message.text.startswith('/'):  
        return
        
    openai_tools = OpenAITools()
    response = openai_tools.chat(str(update.effective_user.id), update.message.text)
    await update.message.reply_text(response, parse_mode='Markdown')

def send_scheduled_messages():
    """Send messages to users based on their message frequency."""
    session = get_db_session()
    try:
        users = session.query(User).all()
        current_hour = datetime.now().hour

        for user in users:
            if user.message_frequency == "once" and current_hour == 9:  # Example: 9 AM
                bot.send_message(chat_id=user.telegram_id, text="Your daily Rust lesson is ready!")
            elif user.message_frequency == "twice" and current_hour in [9, 17]:  # 9 AM and 5 PM
                bot.send_message(chat_id=user.telegram_id, text="Your Rust lesson is ready!")
            elif user.message_frequency == "three" and current_hour in [9, 13, 17]:  # 9 AM, 1 PM, 5 PM
                bot.send_message(chat_id=user.telegram_id, text="Your Rust lesson is ready!")
    except Exception as e:
        print(f"Error sending scheduled messages: {e}")
    finally:
        session.close()

# Schedule the task
schedule.every().hour.at(":00").do(send_scheduled_messages)

def run_scheduler():
    """Run the scheduler in a loop."""
    while True:
        schedule.run_pending()
        time.sleep(1)

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
    import threading
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    try:
        asyncio.run(main())  # Runs without messing with the event loop
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
