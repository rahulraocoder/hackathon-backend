import random
import string
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Database setup (matches evaluator's DB config)
Base = declarative_base()
engine = create_engine(settings.DATABASE_URL)

class Team(Base):
    __tablename__ = 'teams'
    team_key = Column(String, primary_key=True)
    submission_count = Column(Integer, default=0)
    last_submission = Column(DateTime)
    best_score = Column(Float)

# Drop and recreate tables to ensure clean state
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def generate_team_keys(num_teams):
    session = Session()
    chars = string.ascii_uppercase + string.digits
    
    try:
        # Clear existing teams and verify schema
        Base.metadata.create_all(engine)
        
        # Generate teams with configured limits
        for i in range(1, num_teams + 1):
            team_key = f"TM-{''.join(random.choices(chars, k=6))}" 
            team = Team(
                team_key=team_key,
                submission_count=0,
                best_score=0.0
            )
            session.add(team)
        
        session.commit()
        
        # Print results
        teams = session.query(Team).all()
        print(f"Generated {len(teams)} team keys:")
        for team in teams:
            print(f"{team.team_key}")
            
        return teams
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    team_count = int(input("Enter number of teams: "))
    generate_team_keys(team_count)
