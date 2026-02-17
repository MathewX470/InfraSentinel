import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "mysql+pymysql://monitor_user:monitor_pass@db:3306/monitoring"
    
    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # Admin credentials (hardcoded for single admin system)
    admin_username: str = "admin"
    admin_password: str = "admin123"
    
    # Host paths for monitoring
    host_proc: str = "/host/proc"
    host_sys: str = "/host/sys"
    host_root: str = "/host/root"
    
    # Metrics collection interval (seconds)
    metrics_interval: int = 5
    
    # Process list limit
    process_limit: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
