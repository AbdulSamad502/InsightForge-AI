import itertools
from functools import lru_cache
from pydantic_settings import BaseSettings




class Settings(BaseSettings):
    # Database
    database_url: str

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Groq
    groq_api_key: str
    groq_api_keys: str = ""
    groq_main_model: str = "llama-3.1-8b-instant"
    groq_fast_model: str = "llama-3.1-8b-instant"

    # LangSmith
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "ai-data-analyst"

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

class KeyRotator:
    def __init__(self, keys: str):
        key_list = [k.strip() for k in keys.split(",")]
        self._cycle = itertools.cycle(key_list)
    
    def next(self) -> str:
        return next(self._cycle)



settings = get_settings()
key_rotator = KeyRotator(settings.groq_api_keys)
