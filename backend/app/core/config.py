from pydantic_settings import BaseSettings, SettingsConfigDict
import functools


class Settings(BaseSettings):
    # These will be read from environment variables or a .env file
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    IGDB_CLIENT_ID: str
    IGDB_CLIENT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # This tells pydantic to look for a .env file
    model_config = SettingsConfigDict(env_file=".env")


# Create a single instance to be imported elsewhere
@functools.lru_cache()
def settings() -> Settings:
    return Settings()
