import random
import string
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'
    team_key = Column(String, primary_key=True)
    team_name = Column(String)
    avatar = Column(String)
    submission_count = Column(Integer, default=0)
    last_submission = Column(DateTime)
    best_score = Column(Float)

# Database setup
engine = create_engine(settings.DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def generate_team_key():
    chars = string.ascii_uppercase + string.digits
    return f"TM-{''.join(random.choices(chars, k=6))}"

def create_teams(num_teams=5):
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
