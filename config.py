from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DEBUG: bool = False
    SUBMISSIONS_PER_TEAM: int = 5
    TEAM_KEY_PREFIX: str = "TM-"
    DATABASE_URL: str = "sqlite:///evaluation.db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
