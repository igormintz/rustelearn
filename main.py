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

def main():
    """Initialize and start the Telegram bot.
    
    This function sets up the bot's infrastructure including:
    - Logging configuration for monitoring and debugging
    - Database initialization and connection setup
    - Application creation with bot token
    - Registration of all command and message handlers:
        * /start: Initializes user profile and shows welcome message
        * /progress: Shows user's learning progress and statistics
        * /mini: Generates a personalized mini-lesson
    - Registration of callback handlers for:
        * Interactive buttons and menus
        * Settings management
        * Progress tracking
        * Lesson navigation
    - Message handler for regular chat interactions
    - Starting the polling loop for continuous operation
    
    The bot maintains persistent data through SQLite database, preserving:
    - User profiles and preferences
    - Learning progress and achievements
    - Topic mastery levels
    - Learning sessions and history
    
    Returns:
        None
    """
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