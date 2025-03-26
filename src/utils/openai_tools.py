from openai import OpenAI
from typing import Dict, List, Optional
from src.config.settings import OPENAI_API_KEY
from src.database.connection import get_db_session
from src.database.models import User, Topic, UserProgress, DifficultyLevel

class OpenAITools:
    def __init__(self):
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

    def chat(self, telegram_id: str, user_message: str, context: List[Dict] = None) -> str:
        """
        Handle a chat message from the user
        """
        user = self.db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return "Please start with /start first to initialize your learning profile."

        # Get user's progress for context
        progress = self.check_user_progress(telegram_id)
        
        # Build the conversation context
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"""The user is at {progress['user_level']} level.
Their strong topics are: {', '.join(progress['strong_topics']) if progress['strong_topics'] else 'None yet'}.
Their weak topics are: {', '.join(progress['weak_topics']) if progress['weak_topics'] else 'None yet'}.
Adapt your explanations accordingly."""}
        ]

        # Add previous context if available
        if context:
            messages.extend(context)

        # Add user's current message
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"

    def check_user_progress(self, telegram_id: str) -> Dict:
        """
        Check user's learning progress in the database
        Returns a detailed progress report
        """
        user = self.db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return {"error": "User not found"}

        progress_entries = self.db.query(UserProgress).filter_by(user_id=user.id).all()
        
        # Calculate progress metrics
        total_topics = self.db.query(Topic).count()
        completed_topics = sum(1 for p in progress_entries if p.mastery_level >= 0.8)
        avg_mastery = sum(p.mastery_level for p in progress_entries) / len(progress_entries) if progress_entries else 0
        
        return {
            "user_level": user.current_level.value,
            "topics_completed": completed_topics,
            "total_topics": total_topics,
            "completion_percentage": (completed_topics / total_topics * 100) if total_topics > 0 else 0,
            "average_mastery": avg_mastery,
            "streak_count": user.streak_count,
            "weak_topics": self._get_weak_topics(progress_entries),
            "strong_topics": self._get_strong_topics(progress_entries),
            "next_topics": self._get_recommended_topics(user, progress_entries)
        }

    def generate_mini_lesson(self, telegram_id: str) -> Dict:
        """
        Generate a personalized mini Rust lesson based on user's progress
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
        """Get topics where mastery level is below 0.6"""
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
- They have completed {progress['topics_completed']} out of {progress['total_topics']} topics
- Their weak areas are: {', '.join(progress['weak_topics']) if progress['weak_topics'] else 'None'}
- Their strong areas are: {', '.join(progress['strong_topics']) if progress['strong_topics'] else 'None'}
- Recommended next topics: {', '.join(progress['next_topics']) if progress['next_topics'] else 'Basic concepts'}

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
        """Generate practice suggestions based on the lesson content"""
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