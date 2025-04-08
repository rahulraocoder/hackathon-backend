from pydantic_settings import BaseSettings
from pydantic import Field
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    DEBUG: bool = Field(False, description="Enable debug mode")
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    
    def configure_logging(self):
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s'
        )
        handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(self.LOG_LEVEL)
        root_logger.addHandler(handler)
        
        logger.info("Logging configured", extra={
            "log_level": self.LOG_LEVEL,
            "debug_mode": self.DEBUG
        })
    SUBMISSIONS_PER_TEAM: int = 5
    TEAM_KEY_PREFIX: str = "TM-"
    DATABASE_URL: str = "mysql+pymysql://root:password@mysql/hackathon"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
