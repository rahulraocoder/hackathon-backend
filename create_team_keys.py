import secrets
import string
import hashlib
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'
    team_key = Column(String(35), primary_key=True)  # TM- + 32 chars
    team_name = Column(String(100))
    avatar = Column(String(255))
    submission_count = Column(Integer, default=0)
    last_submission = Column(DateTime)
    best_score = Column(Float)

# Database setup
engine = create_engine(settings.DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def generate_team_key():
    """Generate cryptographically secure team key using SECRET_KEY"""
    if not settings.SECRET_KEY or settings.SECRET_KEY == 'your-secret-key-here':
        raise ValueError("SECRET_KEY must be set in .env file")
    
    if settings.TEAM_KEY_LENGTH < 16:
        raise ValueError("TEAM_KEY_LENGTH must be at least 16 for security")
    
    # Combine secret key with random bytes for additional entropy
    random_part = secrets.token_bytes(16)
    combined = settings.SECRET_KEY.encode() + random_part
    digest = hashlib.sha256(combined).hexdigest()
    
    # Take first N characters of the digest
    key_length = min(settings.TEAM_KEY_LENGTH, 64)  # SHA256 produces 64 char hex
    return f"{settings.TEAM_KEY_PREFIX}{digest[:key_length]}"

def create_teams(num_teams=5):
    """Create teams with secure random keys"""
    if num_teams < 1 or num_teams > 100:
        raise ValueError("Number of teams must be between 1 and 100")
    session = Session()
    
    try:
        # Clear existing teams
        session.query(Team).delete()
        
        # Create new teams with sequential names
        for i in range(1, num_teams + 1):
            team = Team(
                team_key=generate_team_key(),
                team_name=f"Team {i}",
                avatar=f"Team {i}",
                submission_count=0,
                best_score=None,
                last_submission=None
            )
            session.add(team)
        
        session.commit()
        
        # Print created teams
        teams = session.query(Team).all()
        print(f"Created {len(teams)} teams:")
        for team in teams:
            print(f"- {team.team_key} ({team.team_name})")
            
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    create_teams()
