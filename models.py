import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Add connection pooling and retry settings for better stability
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"sslmode": "require"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserStats(Base):
    __tablename__ = "user_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, index=True)  # Discord user ID
    username = Column(String, index=True)  # Discord username for easier tracking
    total_minutes = Column(Integer, default=0)  # Total focus minutes
    sessions_completed = Column(Integer, default=0)  # Number of completed sessions
    last_session = Column(DateTime, default=datetime.utcnow)  # Last session timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FocusSession(Base):
    __tablename__ = "focus_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(BigInteger, index=True)  # Discord server ID
    creator_id = Column(BigInteger, index=True)  # Session creator
    duration_minutes = Column(Integer)  # Planned duration
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    participant_count = Column(Integer, default=1)  # Number of participants
    status = Column(String, default="active")  # active, completed, cancelled

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Database helper functions
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, will be closed manually

def close_db(db):
    db.close()
