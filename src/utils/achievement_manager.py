from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.database.models import User, UserAchievement, AchievementType

class AchievementManager:
    def __init__(self, db: Session):
        self.db = db

    def check_and_award_achievements(self, user: User) -> list[UserAchievement]:
        """Check user's progress and award any new achievements."""
        new_achievements = []
        
        # Get existing achievements
        existing_achievements = {
            achievement.achievement_type 
            for achievement in user.achievements
        }
        
        # Check streak achievements
        if user.streak_count >= 3 and AchievementType.STREAK_3_DAYS not in existing_achievements:
            new_achievements.append(self._create_achievement(
                user, 
                AchievementType.STREAK_3_DAYS,
                {"streak_count": user.streak_count}
            ))
            
        if user.streak_count >= 7 and AchievementType.STREAK_7_DAYS not in existing_achievements:
            new_achievements.append(self._create_achievement(
                user,
                AchievementType.STREAK_7_DAYS,
                {"streak_count": user.streak_count}
            ))
            
        if user.streak_count >= 30 and AchievementType.STREAK_30_DAYS not in existing_achievements:
            new_achievements.append(self._create_achievement(
                user,
                AchievementType.STREAK_30_DAYS,
                {"streak_count": user.streak_count}
            ))
        
        # Check topic mastery achievements
        for progress in user.progress:
            if (progress.mastery_level >= 0.8 and 
                AchievementType.TOPIC_MASTERY not in existing_achievements):
                new_achievements.append(self._create_achievement(
                    user,
                    AchievementType.TOPIC_MASTERY,
                    {
                        "topic": progress.topic.title,
                        "mastery_level": progress.mastery_level
                    }
                ))
                break
        
        # Check practice achievements
        total_practice_count = sum(p.times_practiced for p in user.progress)
        if (total_practice_count >= 50 and 
            AchievementType.PRACTICE_MASTER not in existing_achievements):
            new_achievements.append(self._create_achievement(
                user,
                AchievementType.PRACTICE_MASTER,
                {"total_practice_count": total_practice_count}
            ))
        
        # Check code warrior achievement (completion of advanced topics)
        advanced_topics_completed = sum(
            1 for p in user.progress 
            if p.topic.difficulty_level.value == "advanced" and p.mastery_level >= 0.7
        )
        if (advanced_topics_completed >= 3 and 
            AchievementType.CODE_WARRIOR not in existing_achievements):
            new_achievements.append(self._create_achievement(
                user,
                AchievementType.CODE_WARRIOR,
                {"advanced_topics_completed": advanced_topics_completed}
            ))
        
        # Check Rust expert achievement (overall mastery)
        if (len(user.progress) >= 10 and 
            all(p.mastery_level >= 0.8 for p in user.progress) and
            AchievementType.RUST_EXPERT not in existing_achievements):
            new_achievements.append(self._create_achievement(
                user,
                AchievementType.RUST_EXPERT,
                {
                    "total_topics": len(user.progress),
                    "average_mastery": sum(p.mastery_level for p in user.progress) / len(user.progress)
                }
            ))
        
        return new_achievements

    def _create_achievement(
        self, 
        user: User, 
        achievement_type: AchievementType, 
        details: Dict[str, Any]
    ) -> UserAchievement:
        """Create a new achievement record."""
        achievement = UserAchievement(
            user_id=user.id,
            achievement_type=achievement_type,
            achieved_at=datetime.utcnow(),
            details=details
        )
        self.db.add(achievement)
        self.db.commit()
        return achievement

    def get_achievement_message(self, achievement: UserAchievement) -> str:
        """Generate a message for the achievement."""
        messages = {
            AchievementType.FIRST_LESSON: "🎉 First Lesson Completed! You've taken your first step in learning Rust!",
            AchievementType.STREAK_3_DAYS: "🔥 3-Day Streak! You're building a great learning habit!",
            AchievementType.STREAK_7_DAYS: "🌟 7-Day Streak! Your dedication is impressive!",
            AchievementType.STREAK_30_DAYS: "🏆 30-Day Streak! You're a true Rust enthusiast!",
            AchievementType.TOPIC_MASTERY: f"🎯 Topic Mastery! You've mastered {achievement.details['topic']}!",
            AchievementType.PRACTICE_MASTER: "💪 Practice Master! You've completed 50 practice exercises!",
            AchievementType.CODE_WARRIOR: "⚔️ Code Warrior! You've mastered 3 advanced topics!",
            AchievementType.RUST_EXPERT: "👑 Rust Expert! You've achieved mastery across multiple topics!"
        }
        return messages.get(achievement.achievement_type, "🎉 New Achievement Unlocked!") 