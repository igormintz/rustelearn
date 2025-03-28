from sqlalchemy import create_engine, text
from src.config.settings import DATABASE_URL
from src.database.models import Base

def run_migrations():
    """Run database migrations to update the schema."""
    engine = create_engine(DATABASE_URL)
    
    # Create all tables if they don't exist
    Base.metadata.create_all(engine)
    
    with engine.connect() as connection:
        # Check and add last_active column if it doesn't exist
        result = connection.execute(text("""
            PRAGMA table_info(users);
        """))
        columns = [row[1] for row in result.fetchall()]
        
        if 'last_active' not in columns:
            connection.execute(text("""
                ALTER TABLE users 
                ADD COLUMN last_active DATETIME;
            """))
        
        if 'message_frequency' not in columns:
            connection.execute(text("""
                ALTER TABLE users 
                ADD COLUMN message_frequency VARCHAR(10) DEFAULT 'once';
            """))
        
        connection.commit()

if __name__ == "__main__":
    run_migrations() 