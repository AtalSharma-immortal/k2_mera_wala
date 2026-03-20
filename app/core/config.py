import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

def _default_database_url() -> str:
    # Vercel serverless functions have writable ephemeral storage under /tmp.
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/property_registry.db"
    return "postgresql+psycopg://postgres:postgres@localhost:5432/property_registry"

class Settings(BaseSettings):
    app_name: str = "Blockchain Property Registry"
    database_url: str = _default_database_url()
    storage_path: str = "/tmp/storage"
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
