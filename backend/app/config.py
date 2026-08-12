from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mongodb_uri: str = ""
    mongodb_db_name: str = "documentor_db"
    groq_api_key: str = ""
    llm_model: str = "llama-3.1-8b-instant"
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_model: str = "all-MiniLM-L6-v2"
    cors_origins: str = "http://localhost:5173"


settings = Settings()