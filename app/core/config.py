import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env without overriding existing environment variables.
# This keeps container-injected values (for example, from docker-compose)
# as the source of truth when present.
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(env_path, override=False)

class Settings(BaseSettings):
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "anthropic/claude-3.5-sonnet"
    POSTGRES_USER: str = "bet_user"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "bet_data"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: str = "5432"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=env_path, env_file_encoding="utf-8")

settings = Settings()
