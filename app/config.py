from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://search:search@postgres:5432/search"
    elasticsearch_url: str = "http://elasticsearch:9200"
    elasticsearch_index: str = "documents"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
