from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database.connection import get_db_session
from src.database.models import User
from src.utils.openai_tools import OpenAITools

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command from users.
    
    This function initializes a new user's profile in the database if they don't exist,
    and sends a welcome message with interactive buttons for various learning options.
    
    Args:
        update (Update): The Telegram update object containing the command
        context (ContextTypes.DEFAULT_TYPE): The context object for the current update
        
    Returns:
        None
    """
    db = get_db_session()
    user = db.query(User).filter_by(telegram_id=str(update.effective_user.id)).first()
    
    if not user:
        user = User(
            telegram_id=str(update.effective_user.id),
            username=update.effective_user.username
        )
        db.add(user)
        db.commit()
    
    welcome_message = (
        "🦀 Welcome to the Rust Learning Bot! 🚀\n\n"
        "I'm here to help you master Rust programming through:\n"
        "• Daily lessons and exercises\n"
        "• Interactive practice sessions\n"
        "• Progress tracking\n"
        "• Spaced repetition learning\n\n"
        "Let's start your Rust journey! Choose an option below:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Start Today's Lesson", callback_data="lesson_start"),
            InlineKeyboardButton("View Progress", callback_data="view_progress")
        ],
        [
            InlineKeyboardButton("Practice Mode", callback_data="practice"),
            InlineKeyboardButton("Settings", callback_data="settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    db.close()

async def check_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /progress command to show user's learning progress.
    
    This function retrieves the user's learning statistics from the database and
    generates a formatted message showing their progress, including:
    - Overall learning level
    - Topics mastered
    - Topics in progress
    - Recent activity
    - Achievements earned
    
    Args:
        update (Update): The Telegram update object containing the command
        context (ContextTypes.DEFAULT_TYPE): The context object for the current update
        
    Returns:
        None
    """
    openai_tools = OpenAITools()
    progress = openai_tools.check_user_progress(str(update.effective_user.id))
    
    # Format the progress message
    progress_message = (
        f"📊 *Your Learning Progress*\n\n"
        f"🎯 *Current Level:* {progress['user_level']}\n"
        f"🔥 *Streak:* {progress['streak_count']} days\n\n"
        f"📚 *Topics Mastered:*\n{bullet_list(progress['strong_topics'])}\n\n"
        f"📖 *Topics in Progress:*\n{bullet_list(progress['weak_topics'])}\n\n"
        f"🏆 *Achievements:*\n{bullet_list(progress['achievements'])}\n\n"
        f"💪 *Practice Stats:*\n"
        f"• Total Topics: {progress['total_topics']}\n"
        f"• Average Mastery: {progress['average_mastery']:.1%}\n"
        f"• Total Practice Sessions: {progress['total_practice_sessions']}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📚 Continue Learning", callback_data="lesson_start"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        progress_message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def mini_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /mini command to generate a personalized mini-lesson.
    
    This function generates a customized Rust programming lesson based on the user's
    current progress and learning level. The lesson includes:
    - A focused topic
    - Detailed explanation
    - Code examples
    - Related topics
    - Practice suggestions
    
    Args:
        update (Update): The Telegram update object containing the command
        context (ContextTypes.DEFAULT_TYPE): The context object for the current update
        
    Returns:
        None
    """
    await update.message.reply_text("🤔 Generating a personalized mini-lesson for you...")
    
    openai_tools = OpenAITools()
    lesson = openai_tools.generate_mini_lesson(str(update.effective_user.id))
    
    if "error" in lesson:
        await update.message.reply_text(
            f"❌ Sorry, I couldn't generate a lesson right now: {lesson['error']}"
        )
        return
    
    # Send the main lesson content
    lesson_message = (
        f"🦀 *{lesson['title']}*\n\n"
        f"{lesson['content']}\n\n"
        "🔍 *Related Topics:*\n"
        f"{bullet_list(lesson['related_topics'])}\n\n"
        "💪 *Practice Suggestions:*\n"
        f"{bullet_list(lesson['practice_suggestions'])}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📚 More Details", callback_data="lesson_more_details"),
            InlineKeyboardButton("💻 Practice Now", callback_data="lesson_practice")
        ],
        [
            InlineKeyboardButton("✅ Mark as Complete", callback_data="lesson_complete"),
            InlineKeyboardButton("⏭️ Next Topic", callback_data="lesson_next")
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        lesson_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def bullet_list(items: list) -> str:
    """Format a list of items into a bullet-pointed string.
    
    This helper function takes a list of items and formats them into a string
    with each item prefixed with a bullet point (•).
    
    Args:
        items (list): List of items to format
        
    Returns:
        str: Formatted string with bullet points, or "None yet" if the list is empty
    """
    if not items:
        return "None yet"
    return "\n".join(f"• {item}" for item in items) 