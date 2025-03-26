from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from datetime import datetime
from src.database.connection import get_db_session
from src.database.models import User, Topic, UserProgress, LearningSession
from src.utils.openai_tools import OpenAITools

async def save_or_update_topic(user_id: str, title: str, content: str, difficulty_level: str):
    """Save or update a topic and user progress"""
    session = get_db_session()
    try:
        # Get or create user
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            user = User(telegram_id=user_id)
            session.add(user)
            session.flush()
        
        # Get or create topic
        topic = session.query(Topic).filter_by(title=title).first()
        if not topic:
            topic = Topic(
                title=title,
                content=content,
                difficulty_level=difficulty_level
            )
            session.add(topic)
            session.flush()
        
        # Update user progress
        progress = session.query(UserProgress).filter_by(
            user_id=user.id,
            topic_id=topic.id
        ).first()
        
        if not progress:
            progress = UserProgress(
                user_id=user.id,
                topic_id=topic.id,
                mastery_level=0.0,
                times_practiced=0,
                last_practiced=datetime.utcnow()
            )
            session.add(progress)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error saving progress: {str(e)}")
        return False
    finally:
        session.close()

async def update_user_progress(user_id: str, topic_title: str, mastery_increase: float = 0.1):
    """Update user progress for a specific topic"""
    session = get_db_session()
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            return False
            
        topic = session.query(Topic).filter_by(title=topic_title).first()
        if not topic:
            return False
            
        progress = session.query(UserProgress).filter_by(
            user_id=user.id,
            topic_id=topic.id
        ).first()
        
        if progress:
            progress.mastery_level = min(1.0, progress.mastery_level + mastery_increase)
            progress.times_practiced += 1
            progress.last_practiced = datetime.utcnow()
            session.commit()
            return True
            
        return False
    except Exception as e:
        session.rollback()
        print(f"Error updating progress: {str(e)}")
        return False
    finally:
        session.close()

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    # Immediately acknowledge the callback query
    await query.answer()
    
    # Show typing indicator
    await update.effective_chat.send_chat_action("typing")
    
    openai_tools = OpenAITools()
    user_id = str(update.effective_user.id)
    
    # Map button actions to natural language for OpenAI
    button_meanings = {
        "lesson_start": "Generate a new mini-lesson based on my current progress and level.",
        "view_progress": "Show me my learning progress and suggest what to focus on next.",
        "practice": "Create a practice exercise that matches my current skill level.",
        "settings": "Show available settings and configuration options.",
        "lesson_more_details": "Provide more detailed explanation of the current topic with examples.",
        "lesson_practice": "Generate a specific practice exercise for the current topic.",
        "lesson_complete": "Mark the current topic as completed and update my progress.",
        "lesson_next": "Move on to the next lesson based on my progress.",
        "playground": "Open Rust Playground to practice coding"
    }
    
    # Get the natural language meaning of the button
    button_meaning = button_meanings.get(query.data, query.data)
    
    try:
        if query.data == "lesson_start":
            lesson = openai_tools.generate_mini_lesson(user_id)
            if "error" in lesson:
                await query.message.reply_text(f"❌ Sorry, I couldn't generate a lesson right now: {lesson['error']}")
                return
            
            # Save the lesson and create initial progress
            await save_or_update_topic(
                user_id,
                lesson['title'],
                lesson['content'],
                'BEGINNER'  # You might want to determine this based on user's level
            )
            
            # Create lesson navigation buttons with Playground
            keyboard = [
                [
                    InlineKeyboardButton("More Details ℹ️", callback_data="lesson_more_details"),
                    InlineKeyboardButton("Practice 🎯", callback_data="lesson_practice")
                ],
                [
                    InlineKeyboardButton("Try in Playground 💻", url="https://play.rust-lang.org/")
                ],
                [
                    InlineKeyboardButton("Complete ✅", callback_data=f"lesson_complete:{lesson['title']}"),
                    InlineKeyboardButton("Next Lesson ➡️", callback_data="lesson_next")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                f"🦀 *{lesson['title']}*\n\n{lesson['content']}\n\n💡 _Click 'Try in Playground' to practice this code in the Rust online editor!_",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        elif query.data == "view_progress":
            progress = openai_tools.check_user_progress(user_id)
            if "error" in progress:
                await query.message.reply_text("❌ Sorry, I couldn't find your progress data.")
                return
            
            # Get AI-generated progress analysis
            analysis = openai_tools.chat(user_id, button_meaning)
            
            progress_message = (
                "📊 *Your Progress*\n\n"
                f"Level: {progress['user_level']}\n"
                f"Completed: {progress['topics_completed']}/{progress['total_topics']} topics\n"
                f"Mastery: {progress['average_mastery']:.1f}%\n\n"
                f"Analysis:\n{analysis}"
            )
            
            await query.message.reply_text(progress_message, parse_mode='Markdown')
            
        else:
            # Handle lesson completion
            if query.data.startswith("lesson_complete:"):
                topic_title = query.data.split(":", 1)[1]
                # Update progress for the completed topic
                success = await update_user_progress(user_id, topic_title)
                if success:
                    await query.message.reply_text("✅ Progress saved! Great job completing this topic!")
            
            # For all other buttons, use OpenAI to generate a contextual response
            response = openai_tools.chat(user_id, button_meaning)
            await query.message.reply_text(response, parse_mode='Markdown')
            
            # If this was a lesson completion, show next steps
            if query.data.startswith("lesson_complete:"):
                keyboard = [
                    [
                        InlineKeyboardButton("Next Lesson ➡️", callback_data="lesson_next"),
                        InlineKeyboardButton("Practice More 🎯", callback_data="practice")
                    ],
                    [
                        InlineKeyboardButton("Try in Playground 💻", url="https://play.rust-lang.org/")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text(
                    "What would you like to do next?",
                    reply_markup=reply_markup
                )
    
    except Exception as e:
        await query.message.reply_text(f"❌ Sorry, something went wrong: {str(e)}") 