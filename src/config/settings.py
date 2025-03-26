import os
import logging

# Bot Token
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Please set TELEGRAM_BOT_TOKEN environment variable")

# OpenAI
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Database
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///rust_learning_bot.db')

# Logging Configuration
def setup_logging():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    # Silence httpx logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return logging.getLogger(__name__) 