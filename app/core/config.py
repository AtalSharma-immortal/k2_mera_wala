import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data"


def _default_database_url() -> str:
    # Vercel serverless functions have writable ephemeral storage under /tmp only.
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/property_registry.db"

    data_dir = _project_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(data_dir / 'property_registry.db').as_posix()}"


def _default_storage_path() -> str:
    if os.getenv("VERCEL"):
        return "/tmp/storage"

    storage_dir = _project_data_dir() / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir.as_posix()


class Settings(BaseSettings):
    app_name: str = "Blockchain Property Registry"
    database_url: str = _default_database_url()
    storage_path: str = _default_storage_path()
    admin_token: str = "change-me-admin-token"
    authorized_nodes: str = "validator-a,validator-b,validator-c"
    poa_quorum: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def authorized_node_list(self) -> list[str]:
        return [n.strip() for n in self.authorized_nodes.split(",") if n.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
