import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Default to SQLite
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./multitenant.db")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis (optional)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)
    
    # App
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    class Config:
        case_sensitive = True

settings = Settings()