
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import AsyncMongoClient


PROJECT_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(PROJECT_ROOT / ".env")


def create_client(
    uri: str | None = None,
) -> AsyncMongoClient:
    """Create an async MongoDB client with UTC-aware datetimes."""

    uri = uri or os.getenv("MONGODB_URI")

    if not uri:
        raise RuntimeError(
            "MONGODB_URI is missing. Check your .env file."
        )

    return AsyncMongoClient(
        uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,

        # IMPORTANT:
        # MongoDB datetimes must be timezone-aware.
        tz_aware=True,
    )


async def get_database(client: AsyncMongoClient):
    """Verify MongoDB connectivity and return the database."""

    await client.admin.command("ping")

    database_name = os.getenv(
        "MONGODB_DATABASE",
        "webintel_ai",
    )

    return client[database_name]
