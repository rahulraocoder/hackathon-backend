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
    TEAM_KEY_PREFIX: str = Field("TM-", description="Prefix for team keys")
    SECRET_KEY: str = Field(..., description="Cryptographic secret key")
    TEAM_KEY_LENGTH: int = Field(32, description="Length of generated team keys")
    RDS_HOST: str = Field("localhost", description="Database host")
    RDS_PORT: int = Field(3306, description="Database port")
    RDS_DB_NAME: str = Field("hackathon", description="Database name")
    RDS_USERNAME: str = Field("root", description="Database username")
    RDS_PASSWORD: str = Field("password", description="Database password")
    DB_DRIVER: str = Field("mysql+pymysql", description="SQLAlchemy database driver")
    
    @property
    def DATABASE_URL(self) -> str:
        # URL-encode password if it contains special characters
        from urllib.parse import quote_plus
        password = quote_plus(self.RDS_PASSWORD)
        return f"{self.DB_DRIVER}://{self.RDS_USERNAME}:{password}@{self.RDS_HOST}:{self.RDS_PORT}/{self.RDS_DB_NAME}?charset=utf8mb4"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
