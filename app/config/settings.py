from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_database_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate

    volume_mount = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
    if volume_mount:
        return (Path(volume_mount) / candidate.name).resolve()

    return (ROOT_DIR / candidate).resolve()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    app_host: str
    app_port: int
    base_url: str
    database_path: Path
    enable_reload: bool
    is_railway: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))
    app_host = os.getenv("APP_HOST", "127.0.0.1").strip()
    app_port = int(os.getenv("APP_PORT", "8000"))

    railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    base_url = os.getenv("BASE_URL", "").strip().rstrip("/")
    if not base_url:
        if railway_public_domain:
            base_url = f"https://{railway_public_domain}"
        else:
            base_url = f"http://{app_host}:{app_port}"

    return Settings(
        bot_token=os.getenv("BOT_TOKEN", "").strip(),
        app_host=app_host,
        app_port=app_port,
        base_url=base_url,
        database_path=_resolve_database_path(os.getenv("DATABASE_PATH", "data/finance_tracker.db")),
        enable_reload=_env_flag("ENABLE_RELOAD", False),
        is_railway=is_railway,
    )
