from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./trashloop.db"
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    allow_local_paths: bool = False  # dev/test only: local paths are trusted, GitHub clones are not
    clone_timeout_s: int = 120
    max_clone_mb: int = 200
    extra: dict = field(default_factory=dict)

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            database_url=os.environ.get("DATABASE_URL", "sqlite:///./trashloop.db"),
            cors_origins=tuple(o for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",") if o),
            allow_local_paths=os.environ.get("ALLOW_LOCAL_PATHS", "0") == "1",
        )
