
import argparse
import asyncio
import json
from pathlib import Path

from app.processing.lineage import (
    DocumentRevision,
    SourceObservation,
)
from app.processing.schemas import WebDocument
from app.storage.mongodb import create_client, get_database
from app.storage.repository import MongoRepository


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_jsonl(path: Path, model=None):
    """Load validated records from a JSONL snapshot."""

    if not path.exists():
        raise FileNotFoundError(
            f"Required data file not found: {path}"
        )

    result = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                if model is None:
                    item = json.loads(line)
                else:
                    item = model.model_validate_json(line)
            except Exception as exc:
                raise ValueError(
                    f"Invalid JSONL at {path}:{line_number}"
                ) from exc

            result.append(item)

    return result


async def import_snapshots(
    repository: MongoRepository,
    directory: Path,
) -> dict:
    """Import a full local snapshot into MongoDB."""

    directory = Path(directory)

    documents = load_jsonl(
        directory / "documents.jsonl",
        WebDocument,
    )

    observations = load_jsonl(
        directory / "provenance.jsonl",
        SourceObservation,
    )

    revisions = load_jsonl(
        directory / "revisions.jsonl",
        DocumentRevision,
    )

    links = load_jsonl(
        directory / "near_duplicates.jsonl",
    )

    # Every file is parsed before any database writes.
    await repository.ensure_indexes()

    # Preserve evidence and revision history first.
    for observation in observations:
        await repository.upsert_observation(observation)

    for revision in revisions:
        await repository.upsert_revision(revision)

    for link in links:
        await repository.upsert_similarity_link(link)

    current_documents_written = 0

    for document in documents:
        changed = await repository.upsert_document(
            document
        )

        if changed:
            current_documents_written += 1

    return {
        "input_documents": len(documents),
        "input_observations": len(observations),
        "input_revisions": len(revisions),
        "input_similarity_links": len(links),
        "current_documents_written":
            current_documents_written,
        "database_counts": await repository.counts(),
    }


async def main_async(directory: Path):
    client = create_client()

    try:
        database = await get_database(client)
        repository = MongoRepository(database)

        report = await import_snapshots(
            repository,
            directory,
        )

        print(json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ))

    finally:
        await client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Import WebIntel AI JSONL into MongoDB"
    )

    parser.add_argument(
        "--directory",
        type=Path,
        default=DATA_DIR / "processed",
    )

    args = parser.parse_args()

    asyncio.run(
        main_async(args.directory)
    )


if __name__ == "__main__":
    main()
