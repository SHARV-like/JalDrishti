from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    # The local fallback lives in an ignored temporary directory. Production
    # deployments must supply a PostgreSQL/PostGIS DATABASE_URL.
    database_url: str = "sqlite:///./tmp/jaldirshti.db"
    auth_mode: str = "development"  # oidc in production; development is never permitted there.
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_organisation_claim: str = "organisation_id"
    storage_backend: str = "local"
    storage_bucket: str = "jaldirshti-evidence"
    max_evidence_bytes: int = 10 * 1024 * 1024
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    def validate_security(self) -> None:
        if self.is_production and (self.auth_mode != "oidc" or not self.oidc_issuer or not self.oidc_audience):
            raise RuntimeError("Production requires AUTH_MODE=oidc plus OIDC_ISSUER and OIDC_AUDIENCE.")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_security()
    return settings


PROJECT_ROOT = Path(__file__).resolve().parents[3]
