from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:////app/data/spendsense.db"

    # API
    api_v1_prefix: str = "/api/v1"

    # CORS
    backend_cors_origins: list[str] = ["http://localhost:3001"]

    # Application
    app_name: str = "SpendSense"
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
