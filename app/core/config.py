import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    POSTGRES_USER: str = "bet_user"
    POSTGRES_PASSWORD: str = "bet_password"
    POSTGRES_DB: str = "bet_data"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: str = "5432"
    
    BET_BASE_URL: str = "https://bet.hu"
    BET_NEWS_API_URL: str = "https://bet.hu/kereso?category=NEWS_NOT_BET"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"

settings = Settings()
