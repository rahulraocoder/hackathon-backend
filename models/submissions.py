from sqlalchemy import Column, String, Integer, DateTime, Float, func, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from config import settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    echo=True,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'
    
    team_key = Column(String(35), primary_key=True)  # TM- + 32 chars
    team_name = Column(String(100))
    avatar = Column(String(255))
    submission_count = Column(Integer, default=0)
    last_submission = Column(DateTime)
    best_score = Column(Float)

class Submission(Base):
    __tablename__ = 'submissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_key = Column(String(35))  # Matches teams.team_key
    metrics = Column(String(2000))  # For JSON data
    score = Column(Float)
    status = Column(String(50))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    performance_metrics = Column(JSON)  # Stores performance metrics JSON

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
