from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    database_url: str = "sqlite:///" + str(ROOT / "backend/data/stoic.db")
    qdrant_url: str = ""
    data_dir: Path = ROOT / "backend/data"
    demo_mode: bool = True
    openai_api_key: str = ""
    chat_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_provider: str = "demo"
    generation_provider: Literal["auto", "demo", "openai"] = "auto"
    embedding_cache_dir: Path | None = None
    corpus_version: str = "v1"
    vector_namespace: str = ""
    auth0_domain: str = ""
    auth0_audience: str = ""
    admin_token: str = ""
    debug_enabled: bool = True
    cors_origin: str = "http://localhost:3000"
    retrieval_mode: str = "hybrid"
    chunk_strategy: str = "structure"
    rerank: bool = True
    max_output_tokens: int = 1600
    requests_per_minute: int = 12
    guest_message_limit: int = 30
    monthly_budget_usd: float = 10
    input_usd_per_million: float = 1.0
    output_usd_per_million: float = 5.0
    embedding_usd_per_million: float = 0.02

    @property
    def use_demo_generation(self) -> bool:
        return self.generation_provider == "demo" or (self.generation_provider == "auto" and self.demo_mode)

    def validate_runtime(self):
        if (not self.use_demo_generation or self.embedding_provider == "openai") and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for the selected live providers")
        if not self.demo_mode and (not self.auth0_domain or not self.auth0_audience):
            raise ValueError("AUTH0_DOMAIN and AUTH0_AUDIENCE are required when guest access is disabled")
        if not self.demo_mode and (self.embedding_provider == "demo" or self.use_demo_generation):
            raise ValueError("Production authentication requires live embedding and generation providers")


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
