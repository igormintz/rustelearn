from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
from src.database.models import Base
from src.database.migrations import run_migrations

# Load environment variables
load_dotenv()

# Get database URL from environment variable, fallback to SQLite for local development
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///rust_learning.db')

# If using PostgreSQL (Railway), we need to modify the URL slightly
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize the database connection and create all necessary tables.
    
    This function creates a new database engine using the configured DATABASE_URL,
    creates all tables defined in the SQLAlchemy models if they don't exist,
    and returns the engine instance for further use.
    
    Returns:
        sqlalchemy.engine.Engine: The configured database engine instance
    """
    Base.metadata.create_all(engine)
    run_migrations()  # Run migrations to add new columns
    return engine

def get_db_session():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 