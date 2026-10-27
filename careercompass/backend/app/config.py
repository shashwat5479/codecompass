from __future__ import annotations

import os

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET = "dev-secret-key-change-me"
DEFAULT_SQLITE_URL = "sqlite:///./careercompass.db"

# Vercel sets VERCEL=1 in every build/runtime environment.
ON_VERCEL = bool(os.getenv("VERCEL"))


class Settings(BaseSettings):
    app_name: str = "CareerCompass AI"
    secret_key: str = DEFAULT_SECRET
    database_url: str = DEFAULT_SQLITE_URL
    upload_directory: str = "./uploads"  # only used to read legacy on-disk resumes
    # Vercel Functions reject request bodies above 4.5 MB, so stay safely below it.
    max_upload_size: int = 4 * 1024 * 1024
    # None = auto (seed only the throw-away SQLite demo DB); "true" forces; "false" disables.
    auto_seed: bool | None = None
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

if ON_VERCEL and settings.secret_key == DEFAULT_SECRET:
    # Tokens are HMAC-signed with this key; the default is public in the repo, so anyone
    # could forge an admin token. Refuse to boot rather than run insecurely.
    raise RuntimeError(
        "SECRET_KEY is not set. Add a long random SECRET_KEY in Vercel -> Project -> "
        "Settings -> Environment Variables, then redeploy."
    )
