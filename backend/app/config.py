from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mongodb_uri: str = ""
    mongodb_db_name: str = "documentor_db"
    groq_api_key: str = ""
    plan_model: str = "qwen/qwen3.6-27b"
    evaluate_model: str = "openai/gpt-oss-20b"
    answer_model: str = "openai/gpt-oss-120b"
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_model: str = "all-MiniLM-L6-v2"
    cors_origins: str = "http://localhost:5173"
    max_agent_iterations: int = 2
    default_top_k: int = 3
    max_accumulated_chunks: int = 10


settings = Settings()