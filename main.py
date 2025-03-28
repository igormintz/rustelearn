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
    """Handle regular text messages from users in the Telegram chat.
    
    This function processes non-command text messages from users and generates appropriate responses
    using the OpenAI integration. It ignores messages that start with '/' as those are handled by
    command handlers.
    
    Args:
        update (Update): The Telegram update object containing the message
        context (ContextTypes.DEFAULT_TYPE): The context object for the current update
        
    Returns:
        None
    """
    if update.message.text.startswith('/'):  # Ignore commands
        return
        
    openai_tools = OpenAITools()
    response = openai_tools.chat(str(update.effective_user.id), update.message.text)
    await update.message.reply_text(response, parse_mode='Markdown')

async def main():
    """Start the bot."""
    application = None
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
        
        # Start the bot
        await application.initialize()
        await application.start()
        
        # Run polling
        await application.updater.start_polling()
        application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
        
        # Keep the application running using asyncio
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour, then continue

    except Exception as e:
        logger.error(f"Error in bot operation: {e}", exc_info=True)
    
    finally:
        # Gracefully stop the application if it exists
        if application:
            try:
                await application.stop()
                await application.updater.stop()
            except Exception as stop_error:
                logger.error(f"Error stopping application: {stop_error}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())