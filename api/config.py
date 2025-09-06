import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./data/gym_assets.db"
    database_url_async: Optional[str] = None
    
    # API Configuration
    api_title: str = "GymRegister API"
    api_version: str = "1.0.0"
    api_description: str = "FastAPI service for gym equipment asset management with AI-powered analysis"
    
    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    api_key: str = "gym-api-key-123"  # Simple API key for demo
    access_token_expire_minutes: int = 30
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-vision-preview"
    
    # File Storage
    upload_dir: str = "./data/uploads"
    max_file_size: int = 20 * 1024 * 1024  # 20MB
    
    # Pagination
    default_page_size: int = 50
    max_page_size: int = 100
    
    # Background Tasks
    use_celery: bool = False  # Set to True for production with Redis/RabbitMQ
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

# Initialize settings
settings = get_settings()