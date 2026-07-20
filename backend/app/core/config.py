from functools import lru_cache
from pydantic_settings import BaseSettings




class Settings(BaseSettings):
    # Database
    database_url: str

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    # LLM Provider Selection
    llm_provider: str = "ollama"        

    # # Ollama settings (used when llm_provider=ollama)
    # ollama_base_url: str = "http://localhost:11434"
    # ollama_main_model: str = "gemma3:4b"
    # ollama_fast_model: str = "gemma3:4b"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_fast_model: str = "llama-3.1-8b-instant"

    # LangSmith
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "insightforge-ai"

    # Upload
    max_upload_size_mb: int = 50
    allowed_extensions: str = "csv,xlsx"
    storage_path: str = "./app/storage"

    # App
    environment: str = "development"
    debug: bool = True

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.allowed_extensions.split(",")]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()




settings = get_settings()
