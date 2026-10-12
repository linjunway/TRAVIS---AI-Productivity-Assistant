from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class RagSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRAVIS_", env_file=".env", extra="ignore")

    qdrant_url: str = "http://localhost:6333"
    collection: str = "chunks"
    data_dir: Path = Path("data")

    dense_model: str = "BAAI/bge-small-en-v1.5"
    dense_dim: int = 384
    sparse_model: str = "Qdrant/bm25"
    rerank_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"

    parent_max_tokens: int = 1200
    child_max_tokens: int = 250
    child_overlap_tokens: int = 40


settings = RagSettings()