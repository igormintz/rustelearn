from datetime import datetime
import enum
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey, Boolean, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class DifficultyLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class AchievementType(enum.Enum):
    FIRST_LESSON = "first_lesson"
    STREAK_3_DAYS = "streak_3_days"
    STREAK_7_DAYS = "streak_7_days"
    STREAK_30_DAYS = "streak_30_days"
    TOPIC_MASTERY = "topic_mastery"
    PRACTICE_MASTER = "practice_master"
    CODE_WARRIOR = "code_warrior"
    RUST_EXPERT = "rust_expert"

class Topic(Base):
    __tablename__ = 'topics'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    content = Column(String, nullable=False)
    difficulty_level = Column(Enum(DifficultyLevel), nullable=False)
    prerequisites = Column(JSON, default=[])
    code_examples = Column(JSON)
    practice_exercises = Column(JSON)
    resources = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_progress = relationship("UserProgress", back_populates="topic")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String)
    current_level = Column(String, default='beginner')
    preferences = Column(JSON, default={})
    streak_count = Column(Integer, default=0)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    message_frequency = Column(String(10), default='once')
    
    # Relationships
    progress = relationship("UserProgress", back_populates="user")
    sessions = relationship("LearningSession", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")

class UserProgress(Base):
    __tablename__ = 'user_progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    topic_id = Column(Integer, ForeignKey('topics.id'))
    mastery_level = Column(Float, default=0.0)
    times_practiced = Column(Integer, default=0)
    last_practiced = Column(DateTime)
    next_review = Column(DateTime)
    is_bookmarked = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="progress")
    topic = relationship("Topic", back_populates="user_progress")

class LearningSession(Base):
    __tablename__ = 'learning_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    topics_covered = Column(JSON)
    performance_metrics = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="sessions")

class UserAchievement(Base):
    __tablename__ = 'user_achievements'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    achievement_type = Column(Enum(AchievementType), nullable=False)
    achieved_at = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="achievements") 