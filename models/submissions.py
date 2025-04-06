from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float, func, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./evaluation.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'
    
    team_key = Column(String, primary_key=True)
    submission_count = Column(Integer, default=0)
    last_submission = Column(DateTime)
    best_score = Column(Float)

class Submission(Base):
    __tablename__ = 'submissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_key = Column(String)
    metrics = Column(String)  # Stores JSON string of metrics
    score = Column(Float)
    status = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    performance_metrics = Column(JSON)  # Stores performance metrics JSON

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
