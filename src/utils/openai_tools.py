from openai import OpenAI
from typing import Dict, List, Optional
from src.config.settings import OPENAI_API_KEY
from src.database.connection import get_db_session
from src.database.models import User, Topic, UserProgress, DifficultyLevel
import json

class OpenAITools:
    def __init__(self):
        """Initialize the OpenAI tools with API key and system prompt.
        
        This constructor sets up the OpenAI client with the configured API key
        and initializes a system prompt that defines the assistant's role as a
        Rust programming expert.
        """
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.db = get_db_session()
        self.system_prompt = """You are a helpful Rust programming assistant. You help users learn Rust by:
1. Providing clear, concise explanations
2. Showing practical code examples
3. Answering follow-up questions
4. Suggesting best practices
5. Explaining error messages
6. Recommending resources

Keep responses focused on Rust programming. If asked about other topics, politely redirect to Rust-related discussions."""

    def chat(self, user_id: str, message: str, current_topic: str = None) -> dict:
        """Generate a response to user input using OpenAI's API.
        
        This method handles general chat interactions and generates contextual
        responses based on the user's progress and current topic.
        
        Args:
            user_id (str): The user's Telegram ID
            message (str): The user's message or button action
            current_topic (str, optional): The current topic being discussed
            
        Returns:
            dict: A dictionary containing the response content and any additional data
        """
        try:
            # Get user's progress
            progress = self.check_user_progress(user_id)
            if "error" in progress:
                return {"error": "Could not fetch user progress"}
            
            # Create a prompt for the chat
            prompt = f"""You are a helpful Rust programming tutor. The user's current level is {progress['user_level']} 
and they have completed {progress['total_topics']} topics. Their strong topics are: {', '.join(progress['strong_topics'])} 
and weak topics are: {', '.join(progress['weak_topics'])}. Their average mastery level is {progress['average_mastery']:.1%}.

User message: {message}

Generate a helpful response that:
1. Addresses the user's question or request
2. Provides relevant examples or explanations
3. Encourages further learning
4. Uses Markdown formatting for code blocks and emphasis
5. Is concise and clear

Current topic (if any): {current_topic if current_topic else 'None'}

Format the response as JSON with these fields:
- content: The main response text
- code_example: Optional code example (if relevant)
- next_steps: Optional suggestions for what to learn next
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful Rust programming tutor."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Format the response with code example if present
            formatted_response = result['content']
            if result.get('code_example'):
                formatted_response += f"\n\n```rust\n{result['code_example']}\n```"
            if result.get('next_steps'):
                formatted_response += f"\n\n💡 *Next Steps:*\n{result['next_steps']}"
            
            # Add navigation buttons
            formatted_response += "\n\n_What would you like to do next?_"
            
            return {
                'content': formatted_response,
                'buttons': [
                    [
                        {"text": "Next Lesson ➡️", "callback_data": "next_lesson"},
                        {"text": "Practice 🎯", "callback_data": "lesson_practice"}
                    ],
                    [
                        {"text": "Try in Playground 💻", "url": "https://play.rust-lang.org/"}
                    ],
                    [
                        {"text": "Back to Menu 🏠", "callback_data": "start"},
                        {"text": "⚙️ Settings", "callback_data": "settings"}
                    ]
                ]
            }
            
        except Exception as e:
            return {"error": str(e)}

    def check_user_progress(self, telegram_id: str) -> Dict:
        """Check user's learning progress and generate statistics.
        
        This function retrieves and analyzes the user's learning data to provide
        a comprehensive progress report, including:
        - Current learning level
        - Topics mastered and in progress
        - Achievement status
        - Practice statistics
        
        Args:
            telegram_id (str): The Telegram ID of the user
            
        Returns:
            Dict: A dictionary containing progress statistics and recommendations
        """
        user = self.db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Get progress entries
        progress_entries = self.db.query(UserProgress).filter_by(user_id=user.id).all()
        
        # Calculate statistics
        total_topics = len(progress_entries)
        total_practice_sessions = sum(entry.times_practiced for entry in progress_entries)
        average_mastery = (
            sum(entry.mastery_level for entry in progress_entries) / total_topics 
            if total_topics > 0 else 0
        )
        
        # Get strong and weak topics
        strong_topics = [
            entry.topic.title 
            for entry in progress_entries 
            if entry.mastery_level >= 0.7
        ]
        weak_topics = [
            entry.topic.title 
            for entry in progress_entries 
            if entry.mastery_level < 0.7
        ]
        
        # Get achievements
        achievements = [
            achievement.achievement_type.value.replace('_', ' ').title()
            for achievement in user.achievements
        ]
        
        # Determine user level
        if average_mastery >= 0.8:
            user_level = "Advanced"
        elif average_mastery >= 0.5:
            user_level = "Intermediate"
        else:
            user_level = "Beginner"
        
        return {
            "user_level": user_level,
            "streak_count": user.streak_count,
            "strong_topics": strong_topics,
            "weak_topics": weak_topics,
            "achievements": achievements,
            "total_topics": total_topics,
            "average_mastery": average_mastery,
            "total_practice_sessions": total_practice_sessions
        }

    def generate_mini_lesson(self, telegram_id: str) -> Dict:
        """Generate a personalized mini Rust lesson.
        
        This function creates a customized lesson based on the user's current
        progress and learning level. The lesson includes:
        - A focused topic title
        - Detailed content with examples
        - Difficulty level matching user's progress
        - Related topics for further learning
        - Practice suggestions
        
        Args:
            telegram_id (str): The Telegram ID of the user
            
        Returns:
            Dict: A dictionary containing the lesson components or an error message
        """
        progress = self.check_user_progress(telegram_id)
        
        # Create a prompt based on user's progress
        prompt = self._create_lesson_prompt(progress)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Rust programming expert creating concise, engaging lessons."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            lesson_content = response.choices[0].message.content
            
            # Structure the lesson
            return {
                "title": self._extract_title(lesson_content),
                "content": lesson_content,
                "difficulty": progress["user_level"],
                "related_topics": self._get_related_topics(lesson_content),
                "practice_suggestions": self._generate_practice_suggestions(lesson_content)
            }
        except Exception as e:
            return {"error": f"Failed to generate lesson: {str(e)}"}

    def _get_weak_topics(self, progress_entries: List[UserProgress]) -> List[str]:
        """Identify topics where the user's mastery level is below 60%.
        
        This helper function analyzes the user's progress entries and returns
        a list of topic titles where the mastery level is below 0.6.
        
        Args:
            progress_entries (List[UserProgress]): List of user progress records
            
        Returns:
            List[str]: List of topic titles where mastery is below 60%
        """
        weak_topics = []
        for entry in progress_entries:
            if entry.mastery_level < 0.6:
                topic = self.db.query(Topic).filter_by(id=entry.topic_id).first()
                if topic:
                    weak_topics.append(topic.title)
        return weak_topics

    def _get_strong_topics(self, progress_entries: List[UserProgress]) -> List[str]:
        """Get topics where mastery level is above 0.8"""
        strong_topics = []
        for entry in progress_entries:
            if entry.mastery_level >= 0.8:
                topic = self.db.query(Topic).filter_by(id=entry.topic_id).first()
                if topic:
                    strong_topics.append(topic.title)
        return strong_topics

    def _get_recommended_topics(self, user: User, progress_entries: List[UserProgress]) -> List[str]:
        """Get recommended next topics based on prerequisites and current progress"""
        completed_topic_ids = {p.topic_id for p in progress_entries if p.mastery_level >= 0.7}
        recommended = []
        
        all_topics = self.db.query(Topic).filter_by(difficulty_level=user.current_level).all()
        for topic in all_topics:
            prerequisites = topic.prerequisites
            if all(prereq_id in completed_topic_ids for prereq_id in prerequisites):
                if topic.id not in completed_topic_ids:
                    recommended.append(topic.title)
        
        return recommended[:3]  # Return top 3 recommendations

    def _create_lesson_prompt(self, progress: Dict) -> str:
        """Create a prompt for GPT-4 based on user's progress"""
        return f"""Create a mini Rust programming lesson with the following considerations:
- User's current level: {progress['user_level']}
- Total topics: {progress['total_topics']}
- Average mastery: {progress['average_mastery']:.1%}
- Their weak areas are: {', '.join(progress['weak_topics']) if progress['weak_topics'] else 'None'}
- Their strong areas are: {', '.join(progress['strong_topics']) if progress['strong_topics'] else 'None'}
- Achievements: {', '.join(progress['achievements']) if progress['achievements'] else 'None'}

The lesson should:
1. Be concise but thorough (250-400 words)
2. Include a practical code example
3. Explain key concepts clearly
4. Reference previously mastered topics when relevant
5. Include a small challenge or exercise
6. Use proper Rust code formatting
"""

    def _extract_title(self, lesson_content: str) -> str:
        """Extract the title from the generated lesson content"""
        lines = lesson_content.split('\n')
        for line in lines:
            if line.strip().startswith('#'):
                return line.strip('#').strip()
        return "Rust Mini-Lesson"

    def _get_related_topics(self, lesson_content: str) -> List[str]:
        """Extract related topics from the lesson content"""
        common_rust_topics = [
            "ownership", "borrowing", "lifetimes", "traits", "generics",
            "error handling", "concurrency", "pattern matching", "structs",
            "enums", "modules", "testing", "cargo", "memory safety"
        ]
        
        related = []
        for topic in common_rust_topics:
            if topic.lower() in lesson_content.lower():
                related.append(topic)
        return related

    def _generate_practice_suggestions(self, lesson_content: str) -> List[str]:
        """Generate practice exercises based on lesson content.
        
        This function uses OpenAI to create three practical exercises that
        reinforce the concepts covered in the lesson. If the API call fails,
        it returns generic practice suggestions.
        
        Args:
            lesson_content (str): The content of the lesson
            
        Returns:
            List[str]: List of practice exercise suggestions
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Generate 3 short, practical exercises based on this Rust lesson."},
                    {"role": "user", "content": lesson_content}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            suggestions = response.choices[0].message.content.split('\n')
            return [s.strip('- ') for s in suggestions if s.strip()]
        except:
            return ["Practice implementing the concepts shown in the example",
                   "Try modifying the code to handle different cases",
                   "Write tests for the implementation"]

    def generate_practice_exercise(self, user_id: str, topic_title: str) -> dict:
        """Generate a practice exercise for a specific topic.
        
        Args:
            user_id (str): The user's Telegram ID
            topic_title (str): The title of the topic to practice
            
        Returns:
            dict: A dictionary containing the exercise description and code
        """
        try:
            # Get user's progress for this topic
            progress = self.check_user_progress(user_id)
            if "error" in progress:
                return {"error": "Could not fetch user progress"}
            
            # Create a prompt for generating a practice exercise
            prompt = f"""Create a practice exercise for the topic '{topic_title}'.
The user's current level is {progress['user_level']} and they have completed {progress['total_topics']} topics.
Their strong topics are: {', '.join(progress['strong_topics'])}
Their weak topics are: {', '.join(progress['weak_topics'])}

The exercise should:
1. Be challenging but achievable for their level
2. Include clear instructions and requirements
3. Provide a starting code template
4. Test understanding of the topic
5. Include hints if needed

Format the response as JSON with these fields:
- description: A clear explanation of what to do
- code: The starting code template
- hints: Optional hints for solving the exercise
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a Rust programming expert creating practice exercises."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            exercise = json.loads(response.choices[0].message.content)
            return exercise
            
        except Exception as e:
            return {"error": str(e)}
    
    def generate_solution(self, user_id: str, topic_title: str) -> dict:
        """Generate a solution for a practice exercise.
        
        Args:
            user_id (str): The user's Telegram ID
            topic_title (str): The title of the topic
            
        Returns:
            dict: A dictionary containing the solution explanation and code
        """
        try:
            # Get user's progress for this topic
            progress = self.check_user_progress(user_id)
            if "error" in progress:
                return {"error": "Could not fetch user progress"}
            
            # Create a prompt for generating a solution
            prompt = f"""Create a solution for a practice exercise on the topic '{topic_title}'.
The user's current level is {progress['user_level']} and they have completed {progress['total_topics']} topics.
Their strong topics are: {', '.join(progress['strong_topics'])}
Their weak topics are: {', '.join(progress['weak_topics'])}

The solution should:
1. Be well-documented and explained
2. Follow Rust best practices
3. Include comments explaining key concepts
4. Be appropriate for their skill level
5. Include alternative approaches if relevant

Format the response as JSON with these fields:
- explanation: A detailed explanation of the solution
- code: The complete solution code
- alternatives: Optional alternative approaches
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a Rust programming expert explaining solutions."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            solution = json.loads(response.choices[0].message.content)
            return solution
            
        except Exception as e:
            return {"error": str(e)} 