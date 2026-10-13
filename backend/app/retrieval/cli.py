
import argparse
import asyncio
import json
import os

from dotenv import load_dotenv

from app.embeddings.indexer import IndexConfig
from app.embeddings.model import (
    EMBEDDING_DIMENSION,
    SentenceTransformerProvider,
)
from app.retrieval.engine import (
    RetrievalEngine,
    SearchFilters,
)
from app.storage.mongodb import create_client


def retrieval_config() -> IndexConfig:
    load_dotenv()

    return IndexConfig(
        model_id=os.getenv(
            "WEBINTEL_EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        ),
        model_revision=os.getenv(
            "WEBINTEL_EMBEDDING_REVISION",
            "main",
        ),
        chunk_words=int(os.getenv(
            "WEBINTEL_CHUNK_WORDS", "120"
        )),
        overlap_words=int(os.getenv(
            "WEBINTEL_CHUNK_OVERLAP", "25"
        )),
        dimension=EMBEDDING_DIMENSION,
    )


async def search_documents(args):
    config = retrieval_config()

    provider = await asyncio.to_thread(
        SentenceTransformerProvider,
        model_id=config.model_id,
        revision=config.model_revision,
        batch_size=int(os.getenv(
            "WEBINTEL_EMBEDDING_BATCH_SIZE",
            "16",
        )),
    )

    client = create_client()

    try:
        await client.admin.command("ping")

        engine = RetrievalEngine(
            database=client[args.database],
            provider=provider,
            config=config,
        )

        # Model inference is synchronous CPU work.
        # Running search via a thread keeps the
        # CLI architecture simple; the API will
        # handle request concurrency separately.
        results = await engine.search(
            query=args.query,
            mode=args.mode,
            limit=args.limit,
            filters=SearchFilters(
                document_type=args.document_type,
                source_domain=args.source_domain,
            ),
        )

        print(json.dumps({
            "query": args.query,
            "mode": args.mode,
            "database": args.database,
            "count": len(results),
            "results": results,
        }, indent=2))

    finally:
        await client.close()


def main():
    parser = argparse.ArgumentParser(
        description="WebIntel AI retrieval"
    )

    parser.add_argument(
        "--database",
        required=True,
    )
    parser.add_argument(
        "--query",
        required=True,
    )
    parser.add_argument(
        "--mode",
        choices=[
            "semantic",
            "keyword",
            "hybrid",
        ],
        default="hybrid",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--document-type",
        default=None,
    )
    parser.add_argument(
        "--source-domain",
        default=None,
    )

    args = parser.parse_args()

    asyncio.run(search_documents(args))


if __name__ == "__main__":
    main()
