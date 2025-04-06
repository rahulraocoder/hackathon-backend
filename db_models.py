import uuid
from sqlalchemy import create_engine, Column, String, Integer, Float, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class TeamSubmissionCount(Base):
    __tablename__ = 'team_limits'
    
    team_name = Column(String, primary_key=True)
    submissions = Column(Integer, default=0)

class SubmissionResult(Base):
    __tablename__ = 'submission_results'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    participant_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String)
    score = Column(Integer, nullable=False, default=0)
    details = Column(JSON)
    processed_data = Column(JSON)
    processing_time = Column(Float)

# Database setup
engine = create_engine('sqlite:///evaluation.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
