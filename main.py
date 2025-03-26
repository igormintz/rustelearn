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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages"""
    if update.message.text.startswith('/'):  # Ignore commands
        return
        
    openai_tools = OpenAITools()
    response = openai_tools.chat(str(update.effective_user.id), update.message.text)
    await update.message.reply_text(response, parse_mode='Markdown')

def main():
    """Start the bot"""
    # Setup logging
    logger = setup_logging()
    
    # Initialize database
    init_db()
    
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("progress", check_progress))
    application.add_handler(CommandHandler("mini", mini_lesson))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Add message handler for chat
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 