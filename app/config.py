from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    QDRANT_URL: str
    QDRANT_API_KEY: str | None = None
    DIGITALOCEAN_BGE_KEY: str
    DIGITALOCEAN_BGE_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
