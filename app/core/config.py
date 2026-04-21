import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Override existing system environment variables with .env file variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(env_path, override=True)

class Settings(BaseSettings):
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "anthropic/claude-3.5-sonnet"
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

    model_config = SettingsConfigDict(env_file=env_path, env_file_encoding="utf-8")

settings = Settings()
