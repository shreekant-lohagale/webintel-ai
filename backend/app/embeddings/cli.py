
import argparse
import asyncio
import json
import os

from dotenv import load_dotenv

from app.embeddings.indexer import (
    DocumentChunkIndexer,
    IndexConfig,
)
from app.embeddings.model import (
    EMBEDDING_DIMENSION,
    SentenceTransformerProvider,
)
from app.storage.mongodb import create_client


def load_configuration() -> tuple[IndexConfig, int]:
    load_dotenv()

    config = IndexConfig(
        model_id=os.getenv(
            "WEBINTEL_EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        ),
        model_revision=os.getenv(
            "WEBINTEL_EMBEDDING_REVISION",
            "main",
        ),
        chunk_words=int(
            os.getenv(
                "WEBINTEL_CHUNK_WORDS",
                "120",
            )
        ),
        overlap_words=int(
            os.getenv(
                "WEBINTEL_CHUNK_OVERLAP",
                "25",
            )
        ),
        dimension=EMBEDDING_DIMENSION,
    )

    batch_size = int(
        os.getenv(
            "WEBINTEL_EMBEDDING_BATCH_SIZE",
            "16",
        )
    )

    return config, batch_size


async def run_indexing(
    database_name: str,
    limit: int | None,
):
    config, batch_size = load_configuration()

    print(
        f"Embedding model: {config.model_id}"
    )
    print(
        f"Model revision: {config.model_revision}"
    )
    print(
        f"Config key: {config.key}"
    )

    provider = SentenceTransformerProvider(
        model_id=config.model_id,
        revision=config.model_revision,
        batch_size=batch_size,
    )

    client = create_client()

    try:
        await client.admin.command("ping")

        database = client[database_name]

        indexer = DocumentChunkIndexer(
            database=database,
            provider=provider,
            config=config,
            batch_size=batch_size,
        )

        await indexer.ensure_indexes()

        result = await indexer.index_all(
            limit=limit,
        )

        print(
            json.dumps(
                result,
                indent=2,
            )
        )

    finally:
        await client.close()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Incrementally embed WebIntel AI "
            "MongoDB documents"
        )
    )

    parser.add_argument(
        "--database",
        default=os.getenv(
            "MONGODB_DATABASE",
            "webintel_ai",
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    asyncio.run(
        run_indexing(
            database_name=args.database,
            limit=args.limit,
        )
    )


if __name__ == "__main__":
    main()
