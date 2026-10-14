
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    app_title: str
    app_version: str
    debug: bool
    mongodb_uri: str
    mongodb_database: str
    docs_enabled: bool = True


def get_settings() -> Settings:
    """Read application settings from the environment."""

    mongodb_uri = os.getenv("MONGODB_URI", "").strip()

    if not mongodb_uri:
        raise RuntimeError(
            "MONGODB_URI is missing. Check the root .env file."
        )

    return Settings(
        app_title=os.getenv(
            "WEBINTEL_API_TITLE",
            "WebIntel AI API",
        ),
        app_version=os.getenv(
            "WEBINTEL_API_VERSION",
            "0.1.0",
        ),
        debug=os.getenv(
            "WEBINTEL_API_DEBUG",
            "false",
        ).lower() in ("1", "true", "yes"),
        mongodb_uri=mongodb_uri,
        mongodb_database=os.getenv(
            "MONGODB_DATABASE",
            "webintel_ai",
        ),
        docs_enabled=os.getenv(
            "WEBINTEL_API_DOCS_ENABLED",
            "true",
        ).lower() in ("1", "true", "yes"),
    )
