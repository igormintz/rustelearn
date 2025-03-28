import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Get environment variables with fallbacks
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Validate required environment variables
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Database settings
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///rust_learning.db')

# Bot settings
DEFAULT_MESSAGE_FREQUENCY = "once"  # once, twice, or three times per day
MINIMUM_TIME_BETWEEN_MESSAGES = 4  # hours
MAX_MESSAGES_PER_DAY = 3

# Logging Configuration
def setup_logging():
    """Configure logging for the application.
    
    This function sets up the logging configuration with:
    - Timestamp format
    - Log level names
    - Message format
    - Default log level set to INFO
    - Suppressed httpx logging to reduce noise
    
    Returns:
        logging.Logger: The configured logger instance
    """
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    # Silence httpx logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return logging.getLogger(__name__) 