from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database.connection import get_db_session
from src.database.models import User
from src.utils.openai_tools import OpenAITools

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
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
    """Handle the /progress command"""
    openai_tools = OpenAITools()
    progress = openai_tools.check_user_progress(str(update.effective_user.id))
    
    if "error" in progress:
        await update.message.reply_text(
            "❌ Sorry, I couldn't find your progress data. Please start with /start first."
        )
        return
    
    progress_message = (
        "📊 *Your Learning Progress Report*\n\n"
        f"🎯 Level: {progress['user_level']}\n"
        f"📚 Topics Completed: {progress['topics_completed']}/{progress['total_topics']}\n"
        f"📈 Completion: {progress['completion_percentage']:.1f}%\n"
        f"⭐️ Average Mastery: {progress['average_mastery']:.1f}%\n"
        f"🔥 Current Streak: {progress['streak_count']} days\n\n"
        "💪 *Strong Topics:*\n"
        f"{bullet_list(progress['strong_topics'])}\n"
        "📝 *Areas for Improvement:*\n"
        f"{bullet_list(progress['weak_topics'])}\n"
        "👉 *Recommended Next Topics:*\n"
        f"{bullet_list(progress['next_topics'])}"
    )
    
    await update.message.reply_text(progress_message, parse_mode='Markdown')

async def mini_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /mini command for a quick, personalized lesson"""
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
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        lesson_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def bullet_list(items: list) -> str:
    """Helper function to format bullet point lists"""
    if not items:
        return "None yet"
    return "\n".join(f"• {item}" for item in items) 