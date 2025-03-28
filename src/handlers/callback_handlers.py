from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from datetime import datetime
from src.database.connection import get_db_session
from src.database.models import User, Topic, UserProgress, LearningSession
from src.utils.openai_tools import OpenAITools
from src.utils.achievement_manager import AchievementManager

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
    """Update a user's progress for a specific topic.
    
    This function updates the user's mastery level for a given topic, increments
    the practice count, and updates the last practiced timestamp. The mastery
    level is capped at 1.0 (100%).
    
    Args:
        user_id (str): The Telegram ID of the user
        topic_title (str): The title of the topic to update
        mastery_increase (float, optional): Amount to increase mastery by. Defaults to 0.1.
        
    Returns:
        bool: True if the update was successful, False otherwise
    """
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
            
            # Check for achievements
            achievement_manager = AchievementManager(session)
            new_achievements = achievement_manager.check_and_award_achievements(user)
            
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
    """Handle callback queries from inline keyboard buttons.
    
    This function processes user interactions with inline keyboard buttons and
    generates appropriate responses. It handles various actions including:
    - Starting new lessons
    - Viewing progress
    - Practicing exercises
    - Accessing settings
    - Completing lessons
    - Moving to next topics
    
    Args:
        update (Update): The Telegram update object containing the callback query
        context (ContextTypes.DEFAULT_TYPE): The context object for the current update
        
    Returns:
        None
    """
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
        "playground": "Open Rust Playground to practice coding",
        "restart_learning": "Reset all learning progress and start fresh.",
        "change_frequency": "Change how often I receive learning messages.",
        "frequency_once": "Set message frequency to once per day.",
        "frequency_twice": "Set message frequency to twice per day.",
        "frequency_three": "Set message frequency to three times per day."
    }
    
    # Get the natural language meaning of the button
    button_meaning = button_meanings.get(query.data, query.data)
    
    try:
        if query.data == "settings":
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Restart Learning", callback_data="restart_learning"),
                    InlineKeyboardButton("⏰ Change Message Frequency", callback_data="change_frequency")
                ],
                [
                    InlineKeyboardButton("📝 Show Commands", callback_data="show_commands")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "⚙️ *Settings*\n\n"
                "Choose an option to configure your learning experience:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        elif query.data == "show_commands":
            commands_message = (
                "📝 *Available Commands*\n\n"
                "• /start - Start the bot and see the main menu\n"
                "• /progress - View your learning progress and statistics\n"
                "• /mini - Get a quick, personalized mini-lesson\n\n"
                "💡 *Additional Features*\n"
                "• Interactive buttons in messages for navigation\n"
                "• Settings menu for customization\n"
                "• Practice mode for hands-on learning\n"
                "• Rust Playground integration\n\n"
                "🔙 Use the back button to return to settings."
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                commands_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        elif query.data == "restart_learning":
            keyboard = [
                [
                    InlineKeyboardButton("✅ Yes, Reset Everything", callback_data="confirm_restart"),
                    InlineKeyboardButton("❌ No, Keep My Progress", callback_data="cancel_restart")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "⚠️ *Reset Learning Progress*\n\n"
                "Are you sure you want to reset all your learning progress? "
                "This action cannot be undone.",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        elif query.data == "confirm_restart":
            success = await reset_user_progress(user_id)
            if success:
                await query.message.reply_text(
                    "✅ Your learning progress has been reset. "
                    "You can now start fresh with your Rust learning journey!"
                )
            else:
                await query.message.reply_text(
                    "❌ Sorry, there was an error resetting your progress. "
                    "Please try again later."
                )
                
        elif query.data == "change_frequency":
            keyboard = [
                [
                    InlineKeyboardButton("Once per Day", callback_data="frequency_once"),
                    InlineKeyboardButton("Twice per Day", callback_data="frequency_twice")
                ],
                [
                    InlineKeyboardButton("Three Times per Day", callback_data="frequency_three")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "⏰ *Message Frequency*\n\n"
                "Choose how often you'd like to receive learning messages "
                "(between 8:00 and 21:00):",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        elif query.data.startswith("frequency_"):
            frequency = query.data.split("_")[1]
            success = await update_message_frequency(user_id, frequency)
            if success:
                frequency_text = {
                    "once": "once per day",
                    "twice": "twice per day",
                    "three": "three times per day"
                }.get(frequency, "once per day")
                
                await query.message.reply_text(
                    f"✅ Your message frequency has been set to {frequency_text}."
                )
            else:
                await query.message.reply_text(
                    "❌ Sorry, there was an error updating your message frequency. "
                    "Please try again later."
                )
                
        elif query.data == "main_menu":
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
            await query.message.reply_text(
                "🦀 *Welcome Back!*\n\n"
                "What would you like to do?",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        elif query.data == "lesson_start":
            # Send thinking message immediately
            thinking_message = await query.message.reply_text(
                "🤔 Generating a personalized lesson for you...\n"
                "This might take a few moments."
            )
            
            lesson = openai_tools.generate_mini_lesson(user_id)
            if "error" in lesson:
                await thinking_message.edit_text(
                    f"❌ Sorry, I couldn't generate a lesson right now: {lesson['error']}"
                )
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
                ],
                [
                    InlineKeyboardButton("⚙️ Settings", callback_data="settings")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Update the thinking message with the actual lesson
            await thinking_message.edit_text(
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
                f"Topics: {progress['total_topics']} total\n"
                f"Mastery: {progress['average_mastery']:.1%}\n"
                f"Practice Sessions: {progress['total_practice_sessions']}\n"
                f"Current Streak: {progress['streak_count']} days\n\n"
                f"Analysis:\n{analysis}"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("📚 Continue Learning", callback_data="lesson_start"),
                    InlineKeyboardButton("⚙️ Settings", callback_data="settings")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                progress_message, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        elif query.data == "lesson_practice":
            # Send thinking message immediately
            thinking_message = await query.message.reply_text(
                "🎯 Generating a practice exercise for you...\n"
                "This might take a few moments."
            )
            
            # Get the current topic from the message
            current_message = query.message.text
            topic_title = current_message.split('\n')[0].replace('🦀 *', '').replace('*', '')
            
            # Generate a practice exercise
            practice_exercise = openai_tools.generate_practice_exercise(user_id, topic_title)
            
            if "error" in practice_exercise:
                await thinking_message.edit_text(
                    f"❌ Sorry, I couldn't generate a practice exercise right now: {practice_exercise['error']}"
                )
                return
            
            keyboard = [
                [
                    InlineKeyboardButton("Try in Playground 💻", url="https://play.rust-lang.org/")
                ],
                [
                    InlineKeyboardButton("Show Solution 🔍", callback_data=f"show_solution:{topic_title}")
                ],
                [
                    InlineKeyboardButton("Back to Lesson 📚", callback_data="lesson_start")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await thinking_message.edit_text(
                f"🎯 *Practice Exercise: {topic_title}*\n\n"
                f"{practice_exercise['description']}\n\n"
                f"```rust\n{practice_exercise['code']}\n```\n\n"
                "💡 _Try to solve this exercise! You can use the Rust Playground to test your solution._",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        elif query.data.startswith("show_solution:"):
            topic_title = query.data.split(":", 1)[1]
            solution = openai_tools.generate_solution(user_id, topic_title)
            
            if "error" in solution:
                await query.message.reply_text(
                    f"❌ Sorry, I couldn't generate the solution right now: {solution['error']}"
                )
                return
            
            keyboard = [
                [
                    InlineKeyboardButton("Try in Playground 💻", url="https://play.rust-lang.org/")
                ],
                [
                    InlineKeyboardButton("Back to Practice 🎯", callback_data="lesson_practice")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                f"🔍 *Solution for {topic_title}*\n\n"
                f"{solution['explanation']}\n\n"
                f"```rust\n{solution['code']}\n```\n\n"
                "💡 _Try this solution in the Rust Playground to see how it works!_",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        elif query.data == "next_lesson":
            # Send thinking message immediately
            thinking_message = await query.message.reply_text(
                "🤔 Generating the next lesson for you...\n"
                "This might take a few moments."
            )
            
            # Get the current topic from the message
            current_message = query.message.text
            topic_title = current_message.split('\n')[0].replace('🦀 *', '').replace('*', '')
            
            # Generate the next lesson
            next_lesson = openai_tools.chat(user_id, "next_lesson", topic_title)
            
            if "error" in next_lesson:
                await thinking_message.edit_text(
                    f"❌ Sorry, I couldn't generate the next lesson right now: {next_lesson['error']}"
                )
                return
            
            # Create navigation keyboard
            keyboard = [
                [
                    InlineKeyboardButton("Practice 🎯", callback_data="lesson_practice"),
                    InlineKeyboardButton("Try in Playground 💻", url="https://play.rust-lang.org/")
                ],
                [
                    InlineKeyboardButton("Next Lesson ➡️", callback_data="next_lesson"),
                    InlineKeyboardButton("Back to Menu 🏠", callback_data="start")
                ],
                [
                    InlineKeyboardButton("⚙️ Settings", callback_data="settings")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await thinking_message.edit_text(
                next_lesson['content'],
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
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
            
            if "error" in response:
                await query.message.reply_text(f"❌ Sorry, something went wrong: {response['error']}")
                return
                
            # Create keyboard from the buttons in the response
            keyboard = []
            for row in response['buttons']:
                keyboard_row = []
                for button in row:
                    if 'url' in button:
                        keyboard_row.append(InlineKeyboardButton(button['text'], url=button['url']))
                    else:
                        keyboard_row.append(InlineKeyboardButton(button['text'], callback_data=button['callback_data']))
                keyboard.append(keyboard_row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(response['content'], parse_mode='Markdown', reply_markup=reply_markup)
            
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

async def reset_user_progress(user_id: str) -> bool:
    """Reset all learning progress for a user.
    
    This function deletes all progress records and learning sessions for the user,
    effectively resetting their learning journey.
    
    Args:
        user_id (str): The Telegram ID of the user
        
    Returns:
        bool: True if the reset was successful, False otherwise
    """
    session = get_db_session()
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            return False
            
        # Delete all progress records
        session.query(UserProgress).filter_by(user_id=user.id).delete()
        # Delete all learning sessions
        session.query(LearningSession).filter_by(user_id=user.id).delete()
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error resetting progress: {str(e)}")
        return False
    finally:
        session.close()

async def update_message_frequency(user_id: str, frequency: str) -> bool:
    """Update the user's preferred message frequency.
    
    This function updates how often the user wants to receive learning messages
    during the day (between 8:00 and 21:00).
    
    Args:
        user_id (str): The Telegram ID of the user
        frequency (str): The frequency setting ('once', 'twice', or 'three')
        
    Returns:
        bool: True if the update was successful, False otherwise
    """
    session = get_db_session()
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            return False
            
        user.message_frequency = frequency
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error updating message frequency: {str(e)}")
        return False
    finally:
        session.close() 