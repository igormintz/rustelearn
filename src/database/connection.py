from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config.settings import DATABASE_URL
from src.database.models import Base

def init_db():
    """Initialize the database connection and create tables"""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    return engine

def get_db_session():
    """Get a database session"""
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session() 